"""Screen-rate flashing diagnostic - the thing a screenshot can't catch.

Records the desktop at 60 fps with ffmpeg gdigrab while the game runs, then
frame-diffs consecutive frames. Present-fighting (MAME's window vs the GL
overlay) shows as a high-frequency X.X.X.X alternation pattern; healthy
output shows near-zero diffs with occasional legit screen transitions.

Usage: python harness/record_diag.py [seconds] [x y w h]
"""
import glob, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image

secs = sys.argv[1] if len(sys.argv) > 1 else "6"
x, y, w, h = (sys.argv[2:6] + ["0", "0", "1600", "900"][len(sys.argv) - 2:])[:4]
out = os.path.join(tempfile.gettempdir(), "mvgl_vid")
os.makedirs(out, exist_ok=True)
for f in glob.glob(os.path.join(out, "f*.png")):
    os.remove(f)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "gdigrab",
                "-framerate", "60", "-offset_x", x, "-offset_y", y,
                "-video_size", f"{w}x{h}", "-t", secs, "-i", "desktop",
                "-vf", "scale=800:-1", os.path.join(out, "f%03d.png")])
files = sorted(glob.glob(os.path.join(out, "f*.png")))
prev, diffs = None, []
for f in files:
    a = np.asarray(Image.open(f).convert("L"), dtype=np.int16)
    if prev is not None:
        diffs.append(float(np.abs(a - prev).mean()))
    prev = a
d = np.array(diffs)
print(f"{len(files)} frames  diff mean={d.mean():.2f} max={d.max():.2f}")
big = d > max(2 * d.mean(), d.mean() + d.std())
print("pattern (X=large change; X.X.X.X = present-fighting):")
print("".join("X" if b else "." for b in big))
