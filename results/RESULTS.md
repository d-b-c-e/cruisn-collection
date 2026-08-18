# POC Results — 2026-08-18 (overnight session)

Both load-bearing claims of the feasibility study are now **proven**, not argued.

## 1. The oracle is real

`run_oracle.py`: two cleanroom runs of Cruis'n USA attract mode (deployed
mame286 binary, seeded calibrated NVRAM, fresh cfg, unthrottled, headless)
produce **bit-identical pixels at all 8 sampled frames** — from CPU-board test
through the animated title screen. ~11 s per run.

## 2. The interception point is complete — bit-exact re-render

The `vunit.exe` subtarget build (113 MB vs 666 MB full MAME; **one incremental
build cycle** on the 20-core box) with a ~60-line env-gated patch captured:

- **1,249,062 quads** over frames 738–2399 (38 bytes each, 47.5 MB)
- videoram + textureram + paletteram dumps at frame 2398

`rasterize.py` — a Python port of MAME's exact pipeline (float32 everywhere,
`round_coordinate`'s midpoint-toward-−∞, the `+0.001f` inclusive nudges, the
forward/backward edge walk, C float→int32 truncation with the cvttss2si
INT_MIN case) — replayed the final 8 frames:

```
coverage : 204800/204800 = 100.00%   (whole page redrawn every cycle)
raw u16  : 204800/204800 = 100.00%   BIT-EXACT vs MAME's framebuffer
```

`rerendered.png` is the Golden Gate title screen — bridge, logo shading,
opponent cars, INSERT COINS text — reproduced outside MAME **to the bit**.

## Stream statistics (renderer sizing data)

| metric | value |
|---|---|
| quads/frame | mean 769, median 241, **max 2,654** |
| mode: tex | 84.1% |
| mode: textrans | 10.5% |
| mode: flat | 3.4% |
| mode: textransmask | 2.0% |
| dithered quads | 0.4% |
| texture RAM | 8 MB total, 256-px row stride, 8-bit texels |
| palette | 32,768 pens, xRRRRRGGGGGBBBBB |

Max 2,654 quads/frame is nothing for any GPU of the last 25 years. Four
shader variants cover the entire hardware.

## Traps documented for the real implementation

- **Page semantics**: dest page = `page_control & 4`, visible = `& 1`, and the
  flip lands mid-frame — a dump/present can catch the pointer one step stale.
  The freshly completed frame is the dest page of the last full frame.
- **Frame numbering off-by-one**: a snapshot at Lua frame N runs screen_update
  with `frame_number() == N-1`.
- **First boot** parks on CALIBRATE CONTROLS; seed NVRAM (fixture included).
- **Degenerate quads exist in the real stream** (zero-width extents with huge
  dpdx). C's float→int32 conversion semantics (INT_MIN) must be honored.
- **The game redraws the entire back page every cycle** — no incremental
  damage tracking needed in a replacement renderer.
- 3D begins at frame ~738; everything before is direct-CPU videoram writes
  (boot screens), which a quad-only renderer correctly ignores.

## Feasibility study updates

- "Does texture RAM get rewritten often enough for cache invalidation to be a
  perf issue?" — textures were fully stable across the captured window; a
  write-invalidated cache will be nearly idle in attract. (Gameplay unmeasured.)
- "Can per-quad perspective be recovered from u/v gradients?" — the capture
  contains everything needed to prototype this offline against real data,
  without touching MAME again.

## Environment notes

- MSYS2 reinstalled to **E:\msys64** (C:\msys64 died with the C: wipe).
  GCC 16.2.0 builds MAME 0.286 fine with `NOWERROR=1`.
- MAME's makefile needs `OS=Windows_NT` exported *inside* the MSYS2 login
  shell — the profile clears the inherited value.
- Build: `make SUBTARGET=vunit SOURCES=src/mame/midway/midvunit.cpp
  REGENIE=1 NOWERROR=1 TOOLS=0 -j18`

---

# Widescreen spike — 2026-08-18 (follow-up session)

**The gating unknown is RESOLVED: true Hor+ 16:9 needs NO game-code changes.**

The decisive fact was already in the captured stream: **the TMS32031 does not
clip projected geometry to the viewport.** Vertex x runs −8427..12935 against
a 0..511 screen with no pile-up at boundary values (no DSP clamping), ~7% of
vertices land outside 4:3 horizontally, and **65,698 quads lie entirely
outside the 4:3 window** — submitted by the game, discarded by MAME's
rasterizer at its cliprect. The 4:3 picture is a raster-time crop, not a
game-side frustum.

`widescreen.py` re-rendered two captured scenes into a 684×400 window
(16:9 at the original pixel aspect, 86 px margins each side):

| scene | margin pixels rendered | centre vs MAME dump |
|---|---|---|
| title screen (frame 2398) | **100.00%** both sides | 99.99% (DDA drift, see below) |
| canyon demo race (frame 7998) | **100.00%** both sides | **100.00%** |

Proof images: `results/proof/widescreen-title.png`, `widescreen-canyon.png`.
Canyon walls, road edges and lane markings continue seamlessly into the
margins in both scenes.

Additional findings:

- **Scene/page structure**: consecutive frames sharing a `page_control` form
  one scene (~27-quad setup chunk + ~1,200-quad body in attract; ~105 + ~1,230
  in gameplay). The last complete scene is the second-to-last run — a
  quad-count threshold is not a robust way to find it.
- **DDA drift**: quads MAME clips at x=0/511 get u/v starts adjusted
  analytically at the clip edge; the wide render reaches the same pixels by
  int32 DDA stepping from further left. Same math, different rounding —
  ~0.01% of centre pixels. Irrelevant to a real GPU renderer (which
  interpolates analytically per-pixel anyway); visible only against the
  software oracle.
- Capture backstop must scale with the dump frame (`-str` at 120 s ends
  before frame ~6,900).

**Honest caveats**: two scenes tested; objects the game distance-culls could
still pop in at margins during long play — sweep more frames during real
development. HUD/text stays 4:3-centred (authentic). Vertical overhang exists
too (y −4956..1481), so 21:9 is likely equally free.
