# Findings from the recorded LA Freeway drive

Investigation begun 5 September 2026, continuing after midnight UTC. The user's
`results/diagnostics/my-drive` remains unchanged. It contains 5,012 effective
input frames and 83 native snapshots, covering the entire car-selection
countdown and about 40 seconds driving LA Freeway. Every wheel/pedal input,
emulated timestamp and sampled native image matched on identity playback.
Physical FFB was deliberately disabled in recording and replay.

## Regular stutter and sustained slowdown were separate problems

PNG encoding ran on the emulation thread. Over frames 1680–4800, the original
recording's capture-adjacent callback interval had median **79.52 ms**, versus
**22.01 ms** on other frames. Raw snapshot capture followed by PNG encoding
after exit reduced that capture-adjacent median to **18.25 ms**. All 83 decoded
images still matched the original. Raw disk writes remain synchronous; this
removes the measured encoding hitch, not every possible source of uneven pacing.

MAME's underlying GDI window was also expensive near 4K, even when the GL overlay
was disabled. Changing the underlying backend to D3D retained the true widescreen
GL overlay and produced these results on the same input recording:

| Presentation, raw native capture | Selection 1680–2280 | Racing 2700–4800 |
|---|---:|---:|
| GL scale 4 over GDI | 77.59% emulation speed | 83.73% |
| GL scale 4 over D3D | 100.00% | 99.99% |

All 83 native images matched in both runs. V-Unit now defaults to D3D;
`CRUISN_VUNIT_VIDEO=gdi` retains a compatibility fallback. A new 600-frame
recording through the actual launcher, followed by headless replay, passed.
These measurements are USA on this rig, not acceptance of every game/wheel.
One earlier GL-disabled native control was stretched by the recorded window
settings; native controls now explicitly preserve aspect. It was a diagnostic
control, not a change to the recorded widescreen renderer.

## Colored road seams: texture atlas overreach, not missing coverage

At capture frame 3440, pixel (1460,820) on the 2736×1600 internal canvas was red
(`0x1d36`) and was **covered by current-scene road polygon 782**. Its native
coordinates are `(279,205), (291,205), (291,206), (279,206)`; texture base is
`0x2b3`, palette base `0x1d00`. The road maps 160 texture rows into a quad only
one source pixel tall.

The prior rectangle seam repair expands every axis-aligned rectangle by half a
source pixel and extrapolates UVs to preserve the interior gradient. That is
useful for adjacent menu tiles, but it also applies to distant road rectangles.
Here the expansion samples dozens of rows beyond the intended road tile and
reads unrelated atlas contents. This reproduces in a frozen capture, so live
texture queue ordering is not required to explain this particular artifact.

The fix retains original UV bounds before dilation and clamps **quality-mode**
sampling to that domain. It preserves expanded coverage and interior UV slope.
Native integer DDA is unchanged. The observed red pixel becomes road index
`0x1d19`; the scene's coverage mask is unchanged. Clamped transparent edge texels
can correctly change polygon ownership without changing overall coverage.

![Original above, bounded sampling below](../../results/proof/2026-09-05-road-texture-bounds.png)

Validation: six archived native captures spanning USA, World and Off Road remain
**100.0000%** exact. The rebuilt live executable passes the full 5,012-frame
recording and all 83 native screenshots. A ROM-free GPU regression checks thin
rectangles at 1×/2×/3×/4×/6×, adjacent tile coverage, transparent polygon ownership
and scalar/vectorized builder equivalence. Removing the bounds in a negative
control produces 56/86/224/504 foreign texels at 2×/3×/4×/6×. CI now also runs
these GPU fixtures with Mesa software rendering.

## Crack filler: a limited reconstruction option, not a general graphics fix

With margin extension disabled, as on the user's rig, crack filling changes
**zero pixels** in frame 3440. It cannot repair covered pixels carrying the wrong
texture, or a backdrop already drawn through absent terrain.

Six other frozen captures show 0–594 changed pixels in about 4.38 million output
pixels. Some stale seam pixels disappear, but the replacement is copied from a
nearby surface, not reconstructed from geometry or UVs. It can introduce short
streaks or extend a contrasting surface across a gap. Both results matter:

![Raw rendering on left, crack fill on right](../../results/proof/2026-09-05-crackfill-audit.png)

My reassessment: retain it as an explicit, reversible enhancement while fixing
identified causes; do not increase its radius or cite it as evidence that the
renderer is correct. Prefer actual surface coverage, correct texture domains
and ordered resources. Its nearest-neighbor and checkerboard heuristics do not
establish material identity or intentional transparency. More precise source
geometry is the long-term solution for genuinely quantized shared-edge gaps.

The offline preview previously tied `--crackfill` to backdrop suppression and
margin extension, unlike the live rig's settings. Those are now separate options
(`--marginfill` is explicit), so crack-filler experiments no longer silently
change the margin policy. The runtime crack-filler default is unchanged.

## Blue ground holes and visibility: still under investigation

At frame 3440, internal pixel (30,1075) belongs to backdrop polygon 17, texture
base `0x25f9`, with index `0x4676`. Adjacent pixels above/below belong to grass
and road polygons. This is submitted backdrop visible between terrain surfaces,
not a missing texture upload or a pixel the scene left unwritten.

An experimental removal of USA's two left whole-polygon rejection branches,
combined with wider right bounds, recovered terrain in the corresponding route
section, but native frames diverged from frame 2940. It remains a diagnostic,
not an enabled product patch. A bounded replacement is being investigated with
effective program-word checks. The original assumption that USA needs no
game-side widescreen work is not established by simply seeing some margin quads.

Draw distance remains a separate investigation. The known far gate, reciprocal
lookup cap, LOD selection and section/node lifetime must be tested independently.
No new distance extension is enabled by these texture and display fixes.

## Reproduce the evidence

See [diagnostic workflow](../DIAGNOSTIC-REPLAY.md). Frozen ownership/coverage can
be exported with `gpu/renderer.py CAPTURE --scale 4 --wide --buffers output.npz`.
The NPZ includes original quads, current-scene owner IDs (65535 = no owner),
coverage and palette indices. Ownership now respects transparent texels; the
old debug path returned before the transparency discard.

Full local evidence is gitignored. Key runs:

| Run under results/diagnostics | Scope |
|---|---|
| replay-20260906T015718Z-29qhi1t8 | Original live GL defects, GDI, PNG capture |
| replay-20260906T020535Z-cyvi_o9s | Correct raw capture, GL + GDI |
| replay-20260906T020825Z-5xlvd_7z | Correct raw capture, GL + D3D |
| replay-20260906T021337Z-d71ect3r | Native-verified frozen frame 3440, ownership and texture A/B |
| replay-20260906T021721Z-oug1q689 | Native-verified frozen frame 3800 |
| replay-20260906T022330Z-wih4t_lq | Rebuilt bounded-UV executable, full native replay PASS |
| crackfill-audit | Six raw/fill comparisons and changed-pixel counts |

Failed experiments remain retained too. In particular, `screen:pixels()` read
the wrong double buffer and failed native comparison; the implemented recorder
uses `video:snapshot_pixels()`. The harness did not bless the failed images.
