"""Synthetic Forza Horizon telemetry: proves the READ side (SimHub) against
a known-good data pattern, independent of the game.

Emits the FH4/5 324-byte "Data Out" packet at 60 Hz with a scripted drive:
speed triangles 0 -> 200 mph -> 0 every ~24s, RPM sweeps idle -> redline
within each of 4 gears (sawtooth), gear steps 1-4 with the speed. The
console prints what is being sent so it can be compared 1:1 with the dash.

Usage (SimHub OPEN, Forza Horizon profile selected, listening on the port):
    python harness/forza_synth.py           # port 8000
    python harness/forza_synth.py 5300      # other port

If the dash mirrors this pattern, the packet layout is right and SimHub is
fine - any remaining weirdness is the values the emulator feeds it.
"""
import socket
import struct
import sys
import time

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
ADDR = ("127.0.0.1", PORT)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print(f"emitting synthetic FH4/5 packets to udp://{ADDR[0]}:{PORT} at 60 Hz")
print("pattern: speed 0->200->0 mph triangle (~24s), 4 gears, RPM sawtooth")
print("Ctrl+C to stop\n")

MAXRPM, IDLERPM = 7500.0, 700.0
GEAR_TOP = [50.0, 95.0, 145.0, 200.0]   # mph at which each gear tops out

t0 = time.time()
ms = 0
try:
    while True:
        t = time.time() - t0
        # triangle wave 0..1..0 with 24 s period
        ph = (t % 24.0) / 12.0
        tri = ph if ph <= 1.0 else 2.0 - ph
        mph = 200.0 * tri

        # gear from speed; RPM sweeps idle->redline across the gear's band
        gear = 1
        lo = 0.0
        for i, top in enumerate(GEAR_TOP):
            if mph <= top or i == len(GEAR_TOP) - 1:
                gear = i + 1
                hi = top
                break
            lo = top
        frac = 0.0 if hi <= lo else max(0.0, min(1.0, (mph - lo) / (hi - lo)))
        rpm = IDLERPM + (MAXRPM - 500.0 - IDLERPM) * frac

        spd_ms = mph * 0.44704
        ms += 17
        pkt = bytearray(324)
        struct.pack_into("<i", pkt, 0, 1)            # IsRaceOn
        struct.pack_into("<I", pkt, 4, ms)           # TimestampMS
        struct.pack_into("<f", pkt, 8, MAXRPM)       # EngineMaxRpm
        struct.pack_into("<f", pkt, 12, IDLERPM)     # EngineIdleRpm
        struct.pack_into("<f", pkt, 16, rpm)         # EngineCurrentRpm
        struct.pack_into("<f", pkt, 40, spd_ms)      # VelocityZ
        struct.pack_into("<f", pkt, 256, spd_ms)     # Speed (m/s)
        pkt[319] = gear                              # Gear
        sock.sendto(bytes(pkt), ADDR)

        sys.stdout.write(f"\r  sending: {mph:6.1f} mph  rpm {rpm:5.0f}"
                         f"  gear {gear}   ")
        sys.stdout.flush()
        time.sleep(1.0 / 60.0)
except KeyboardInterrupt:
    print("\nstopped")
