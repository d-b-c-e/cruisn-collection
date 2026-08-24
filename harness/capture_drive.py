"""One-command driving capture for the telemetry RAM hunts (B2 RPM etc.).

Launches a game exactly like the shell does (full wheel + FFB + GL overlay)
but with DSP work-RAM dumped every few frames into a timestamped folder, so
a real driving session can be differential-analysed offline against the
already-confirmed speed word.

Usage (from E:\\Source\\cruisn-collection):
    python harness/capture_drive.py            # crusnusa, the RPM target
    python harness/capture_drive.py crusnwld   # any rom

Then DRIVE (see the on-screen prompt), Esc out, and tell Claude the folder
it prints. Dumps land in results/drive-capture-<rom>-<stamp>/ram (gitignored).
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_rig

POC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    rom = sys.argv[1] if len(sys.argv) > 1 else "crusnusa"
    every = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = os.path.join(POC, "results", f"drive-capture-{rom}-{stamp}")
    ram = os.path.join(out, "ram")
    os.makedirs(ram, exist_ok=True)

    os.environ["MIDV_RAMDUMP_DIR"] = ram
    os.environ["MIDV_RAMDUMP_EVERY"] = str(every)

    print("=" * 64)
    print(f"  DRIVING CAPTURE  -  {rom}")
    print("=" * 64)
    print("  For the RPM hunt (crusnusa): do 2-3 STANDING-START, FULL-")
    print("  THROTTLE runs. If the cabinet has a HI/LO shifter, start in")
    print("  LO, rev out, then shift to HI (one clean shift = one clean")
    print("  RPM drop I can spot). Then Esc out.")
    print(f"  Dumps -> {ram}")
    print("  (a faint microstutter from disk writes is normal and does not")
    print("   affect the analysis.)")
    print("=" * 64)

    rc = run_rig.launch_game(rom=rom)
    n = len(os.listdir(ram)) if os.path.isdir(ram) else 0
    print(f"\ncaptured {n} RAM dumps -> {ram}")
    print(f"Tell Claude:  {out}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
