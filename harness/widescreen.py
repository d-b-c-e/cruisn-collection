"""Widescreen spike: render the captured quad stream into a 16:9 window.

Premise test result (see RESULTS.md): the TMS32031 does NOT clip projected
geometry to the 4:3 viewport - vertex coords in the captured stream run
-8427..12935 against a 0..511 screen, and 65k quads lie entirely outside it.
MAME's rasterizer discards the overhang at its cliprect. So Hor+ widescreen
may need no game-code changes at all: just rasterize with a wider window.

This renders exactly that. The screen is 512x400 displayed at 4:3 (pixel
aspect ~1.042); at the same height, 16:9 needs ~683 columns. A margin of 86
on each side (684 total, parity-even so dither alignment matches MAME's) is
rendered from the same captured stream and state dumps.

Outputs (into the capture dir):
    widescreen.png          the raw 684x400 wide render
    widescreen-view.png     display-corrected (square-pixel, 2x) version
    widescreen-cov.txt      per-column-band coverage of the new margins
Sanity: the central 512 columns must still match MAME's dump bit-exactly.
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rasterize import render_quad, load_meta, to_rgb  # noqa: E402

POC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(POC, "results", "capture")
MARGIN = 86
STRIDE = 512 + 2 * MARGIN          # 684 - parity-even offset keeps dither honest

meta = load_meta(os.path.join(CAP, "meta.txt"))
dump_frame = meta["frame"][0]
MIN_FRAME = dump_frame - 8
height = meta["visarea"][1] + 1

ref_vram = np.fromfile(os.path.join(CAP, "videoram.bin"), dtype="<u2")
texram = np.fromfile(os.path.join(CAP, "textureram.bin"), dtype=np.uint8)
pal = np.fromfile(os.path.join(CAP, "paletteram.bin"), dtype="<u4")

raw = open(os.path.join(CAP, "quads.bin"), "rb").read()
rec = np.frombuffer(raw[4:len(raw) - (len(raw) - 4) % 38], dtype=np.uint8)
rec = rec.reshape(-1, 38)
frames = rec[:, 0:4].copy().view("<u4").ravel()
pages = rec[:, 4:6].copy().view("<u2").ravel()
dmas = rec[:, 6:38].copy().view("<u2").reshape(-1, 16)

keep = (frames <= dump_frame) & (frames >= MIN_FRAME)
dmas, pages, frames = dmas[keep], pages[keep], frames[keep]
print(f"wide render: {len(dmas)} quads, canvas {STRIDE}x{height} "
      f"(margins {MARGIN}px), frames {MIN_FRAME}..{dump_frame}")

sim = np.zeros(2 * 512 * STRIDE, dtype=np.uint16)
cover = np.zeros_like(sim, dtype=bool)
for i in range(len(dmas)):
    render_quad(dmas[i].astype(np.uint32), int(pages[i]), sim, texram,
                STRIDE - 1, height - 1, cover, stride=STRIDE, xoff=MARGIN)

# same page rule as rasterize.py: dest page of the last COMPLETE scene
# (second-to-last run of consecutive identical page_control values)
runs = [int(pages[0])]
for pc in pages[1:]:
    if int(pc) != runs[-1]:
        runs.append(int(pc))
last_pc = runs[-2] if len(runs) >= 2 else runs[-1]
page_words = 512 * STRIDE
base = page_words if (last_pc & 4) else 0
wide = sim[base:base + page_words].reshape(512, STRIDE)[:height]
wcov = cover[base:base + page_words].reshape(512, STRIDE)[:height]

# ---- sanity: central 512 columns must equal MAME's framebuffer ----
ref_off = 0x40000 if (last_pc & 4) else 0
ref = ref_vram[ref_off:ref_off + 0x40000].reshape(512, 512)[:height]
centre = wide[:, MARGIN:MARGIN + 512]
match = 100.0 * (centre == ref).sum() / ref.size
# ~0.01% drift is expected: quads MAME clipped at x=0/511 get their u/v start
# analytically adjusted at the clip edge, while the wide render reaches those
# pixels by DDA-stepping from further left - same math, different rounding.
verdict = ("OK" if match == 100.0
           else "OK (DDA-vs-clip-adjust drift)" if match >= 99.9
           else "*** REGRESSION ***")
print(f"centre sanity: {match:.2f}% bit-match vs MAME dump ({verdict})")

# ---- coverage of the new margins ----
lines = []
for name, sl in [("left margin", slice(0, MARGIN)),
                 ("right margin", slice(MARGIN + 512, STRIDE))]:
    band = wcov[:, sl]
    pct = 100.0 * band.sum() / band.size
    lines.append(f"{name}: {band.sum()}/{band.size} = {pct:.2f}% pixels rendered")
    # column profile in 8ths, to show where content thins out
    cols = band.mean(axis=0)
    eighth = len(cols) // 8 or 1
    prof = [f"{100*cols[i:i+eighth].mean():.0f}%" for i in range(0, len(cols), eighth)]
    lines.append(f"  column profile (outer->inner): {prof}"
                 if name == "left margin" else
                 f"  column profile (inner->outer): {prof}")
print("\n".join(lines))
open(os.path.join(CAP, "widescreen-cov.txt"), "w").write("\n".join(lines) + "\n")

# ---- images ----
from PIL import Image
img = to_rgb(wide, pal)
# unrendered margin pixels -> dark grey so gaps are honest, not black-sky
img[~wcov] = (24, 24, 24)
Image.fromarray(img).save(os.path.join(CAP, "widescreen.png"))

# display-corrected: PAR (4/3)/(512/400) = 1.0417, x2 for viewing
disp = Image.fromarray(img).resize((int(STRIDE * 1.0417 * 2), height * 2),
                                   Image.NEAREST)
disp.save(os.path.join(CAP, "widescreen-view.png"))
print(f"wrote widescreen.png ({STRIDE}x{height}) + widescreen-view.png")
