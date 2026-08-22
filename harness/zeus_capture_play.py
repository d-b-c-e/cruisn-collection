"""Launch Exotica with the Zeus GAMEPLAY capture armed - just drive.

Coin up (5), Start (1), and be racing within the first minute; the
capture fires automatically at the ~60s mark (first frame with >=4000
quads past frame 3600) and logs "MIDZ capture complete". Esc quits back
when you're done. Each run writes a fresh results/capture-zeus-playN dir;
re-run for a second capture on a different track.

Track request: AMAZON first (the water-skier level - its sprites use the
texture-alpha mode no attract capture reaches).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_rig  # noqa: E402

n = 1
while os.path.isdir(base := os.path.join(
        run_rig.POC, "results", f"capture-zeus-play{n}")):
    n += 1
os.makedirs(base)
os.environ["MIDZ_CAPTURE"] = base
os.environ["MIDZ_CAPTURE_FRAME"] = os.environ.get("MIDZ_CAPTURE_FRAME", "3600")
os.environ["MIDZ_CAPTURE_MINQUADS"] = "4000"

print(__doc__)
print(f"capture dir: {base}\n")
proc, hwnd = run_rig.launch_game_async(rom="crusnexo", scale=4)
proc.wait()
ok = os.path.isfile(os.path.join(base, "regs.txt"))
print(f"\ncapture {'COMPLETE' if ok else 'DID NOT TRIGGER (be racing by ~60s and try again)'}: {base}")
