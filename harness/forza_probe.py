"""Standalone Forza-packet probe: proves the EMIT side independently of SimHub.

Listens on the Forza telemetry port and live-prints what the emulator is
actually sending (speed, RPM, gear), so emitter and SimHub can be tested
separately:

  1. CLOSE SimHub (it holds the port).
  2. Run:  python harness/forza_probe.py        (default port 8000)
  3. Launch USA from the shell and drive - watch the line update.
     Speed should rise AND fall with the car; "drops seen" counts every
     time speed decreased, so a non-zero count proves it falls.
  4. Ctrl+C for a summary. Then close this, reopen SimHub, and compare.

If this probe shows correct values but SimHub's dash doesn't, the issue is
the SimHub game profile (packet layout), not the emitter.
"""
import os
import socket
import struct
import sys
import time

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PORT))
sock.settimeout(0.5)
LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "forza_probe_log.csv")
logf = open(LOG, "w")
logf.write("t,src,mph,rpm,maxrpm,gear\n")
print(f"listening on UDP {PORT} (Forza Data Out)... Ctrl+C to stop")
print(f"logging every packet to {LOG}")

n = 0
last_mph = 0.0
max_mph = 0.0
max_rpm = 0.0
drops = 0
sizes = set()
t0 = time.time()
try:
    while True:
        try:
            d, _ = sock.recvfrom(2048)
        except socket.timeout:
            continue
        n += 1
        sizes.add(len(d))
        if len(d) != 324:
            continue
        is_on, = struct.unpack_from("<i", d, 0)
        maxr, idler, cur = struct.unpack_from("<fff", d, 8)
        spd_ms, = struct.unpack_from("<f", d, 256)
        gear = d[319]
        mph = spd_ms / 0.44704
        src = "keeper" if d[323] == 0x4B else "game"
        logf.write(f"{time.time()-t0:.2f},{src},{mph:.1f},{cur:.0f},"
                   f"{maxr:.0f},{gear}\n")
        if mph < last_mph - 0.5:
            drops += 1
        last_mph = mph
        max_mph = max(max_mph, mph)
        max_rpm = max(max_rpm, cur)
        if n % 6 == 0:
            sys.stdout.write(
                f"\r  race={is_on} speed={mph:6.1f} mph  rpm={cur:6.0f}"
                f"/{maxr:.0f}  gear={gear}  | session max {max_mph:.0f} mph"
                f"  drops seen={drops}   ")
            sys.stdout.flush()
except KeyboardInterrupt:
    pass
logf.close()
dt = time.time() - t0
print(f"\n\nsummary: {n} packets in {dt:.0f}s ({n/max(dt,1):.0f}/s), "
      f"sizes {sorted(sizes)}")
print(f"full timeline logged: {LOG}")
print(f"  max speed {max_mph:.1f} mph, max rpm {max_rpm:.0f}, "
      f"speed decreases seen: {drops}")
if drops > 0:
    print("  -> speed DOES fall in the emitted packets (emit side OK)")
