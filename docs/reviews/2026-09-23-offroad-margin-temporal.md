# Off-Road El Paso margin opening through a turn

The blue left-margin opening is visible through a short moving sequence, not
just the previously analyzed frame 3120. A bounded replay of the existing
attended El Paso drive captures completed frames 3100–3140 every four frames
(about 0.7 seconds). The 3× host range, CRT, 4× internal scale, native candidate
and source recording match the earlier source-joined run. Physical FFB was
disabled. All 3,200 input/time and native-image rows pass, the 11 requested
2544×1353 client captures are present on visible page 1 with zero dropped
messages, the display watch saw no topology change, and the owned worker
stopped cleanly. Frame 3120 is **byte-exact** to the prior capture-mode image.

The local `left-gap-temporal-screen-contact.png` shows the opening changing
shape throughout the sampled turn, including a much wider triangular wedge
near 3132–3140. A fixed client ROI `(40,475)..(400,625)` has a sky-like blue
CRT color signature in all 11 images. Paired-column counts range from 863 to
3,903; these are a review heuristic, **not exact missing-geometry area**. The
mask can include other blue material and omit some sky after CRT distortion.
The visual sequence and the source-joined indexed frame are the stronger
evidence of a persistent surface-continuity problem.

A second bounded replay turns host scenery off while keeping the same recorded
inputs, emulator, window, CRT and 11-frame capture schedule. It also passes
all 3,200 input/time and native-image rows, completed capture receipts,
display watch and normal exit. The paired completed images differ at
529–37,898 pixels per frame. In the fixed left ROI, 3× has 3–3,377 fewer
sky-like paired pixels than no-host in every sampled frame. The
`left-gap-temporal-control-comparison-v3.png` contact sheet confirms the
direction: added terrain covers part of the sky, but the lower opening remains
visible and changes shape. Color counts do not establish the exact amount of
missing ground or whether every blue pixel is a defect. The game-state/native
comparisons and the image receipts are independent gates.

This changes the repair requirement: a proposal needs a coherent moving
surface/material transition across the turn, not a frame-3120 pen substitution.
The [source review](2026-09-23-offroad-left-margin-source.md) shows the two
nearest quads have different palettes/textures, and the [offline fill
screen](2026-09-23-offroad-gap-fill-screen.md) rejects simple copies. A broad
static billboard admission also cannot fill the sampled opening. The current
3× distance remains a diagnostic candidate, not a shipped treatment.

## Second source-joined frame

One additional bounded capture joins source 3132 to completed page/frame 3136,
including the original DMA journal and indexed mirror in the same run. It
passes the 3,138-input prefix and normal worker shutdown; the completed
3136 BMP is byte-exact to the earlier temporal 3× capture. The source has
689 host packets. At fine `(60,970)`, the extended and original index both
show backdrop sky; at `(60,1030)` auxiliary terrain replaces ordinary sky.
The sampled center maps to native `(-71,156)..(-71,158)`. No host projected
bounds intersect that small box; the nearest host masked-texture quad ends at
y146, while an original non-backdrop polygon begins at y165 in that x band.
This corroborates a wider surface separation as the turn progresses. It does
not identify a safe polygon continuation.

The 32-coarse-pixel [sky-gap screen](2026-09-23-vunit-sky-gap-screen.md)
finds a 7,438-pixel host-bounded span at 3136 and a connected 11,649-pixel
envelope. Its original 16-coarse-pixel threshold reported zero at this frame,
because the sky run reaches about 102 fine pixels. The first 3136 prepare-only
plan failed the existing finite-scene-bounds preflight: host last 3150 exceeded
the requested drain at 3136. The corrected plan ends host observation at
3136; no game ran from the failed plan, and its raw report is retained.

The first prepare-only plan accidentally used the shared preset's Off-Road
host-last frame 2250, which would have disabled host drawing during this turn.
No game ran from it. A second prepare-only attempt correctly rejected an
override because the preset owns that value. The executed explicit plan kept
host drawing through 3150 and matches the previous run's renderer settings
apart from capture/journal policy. These preflight attempts are retained.

Local evidence is under `results/diagnostics/offroad-full-20260910`:
`left-gap-temporal-run/report.json`,
`left-gap-temporal-control-run/report.json`,
`left-gap-3136-source-run/report.json`,
`left-gap-3136-source-analysis.json`,
`left-gap-temporal-screen-v4.json`,
`left-gap-temporal-screen-contact.png`, and
`left-gap-temporal-control-comparison-v3.png`.
`harness/offroad_gap_temporal_screen.py` verifies every completed image against
both replay pixel receipts, checks the 3120 byte match, and reproduces the
color counts and contact sheets. The v1–v3 screen reports are preserved;
v2 added per-image receipt verification, v3 added the no-host control,
and v4 also verifies its visible page. No native source, installed build, release or
wheel settings changed.
