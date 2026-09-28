# World 2.4 New York: later right-wall reveal at frame 6300

The saved New York survey shows the right wall ending against open sky after
a turn at completed frame 6300. This is later than the already studied 3600
and 6000 margin wedges, so I screened the active non-road margin option on
the same saved drive rather than assuming the earlier result generalizes.

Frozen diagnostic native `f762e01d63b` ran matched control/candidate
6,320-input prefixes on the physical 2560×1440 primary with literal FFB0.
Both raw reports **PASS** original input/native comparison, display watch and
owned worker shutdown. The control completed 6300 CRT image is byte-identical
to the earlier 25-view survey. The option adds 329,969 submitted quads over
the full prefix; this number does not measure visible gain. The completed
candidate image changes **70,605 RGB pixels**, bounded by x=2173..2476,
y=371..751 of 2544×1353. All changes lie in the right third; the center is
pixel-exact. In the inspected pair, the distant wall and building continue
around the turn where control shows sky. Only 32 candidate-new near-black
RGB pixels appear by the loose review heuristic, not a texture-defect count.

Matched indexed-mirror control/candidate replays pass 6,310 inputs each and
produce completed 6300 images byte-identical to their quiet counterparts.
They have the same physical page, exact original-only index/tag planes and
exact 4:3 indexed center. The candidate changes **98,129 indexed pixels** in
the right margin, x=2392..2735, y=706..1177 of 2736×1600. All were
game-owned (`tag 1`) and become host-owned (`tag 5`); none was previously
unowned or auxiliary-owned. Thus this is **backdrop replacement**, not a
measured zero-owned gap fill.

A third 6,302-input original-DMA replay passes the same checks and reproduces
the control image and all indexed mirror planes exactly. With its captured
texture, an isolated raster of the current original DMA reproduces all
98,129 overwritten original indices. Every pixel traces to **one** original
DMA quad, ordinal 3, native box `(441,-17)..(697,237)`. It belongs to the
five-tile repeated upper panorama strip, ordinals 0..4. The source-hashed
structural backdrop screen reports zero unclassified foreground pixels for
this sampled view. The candidate's exact added packet identities and full
depth order are not yet checked.

This is a separate visible late-course benefit with source-qualified original
ownership. It does not prove continuous appearance between sampled views,
repair all New York black artifacts, explain the former finish-line crash,
or qualify another World course, physical 4K, wheel output or release. No
native source/binary, deployed renderer, personal installation or public
release changed. The first two prepare-only requests **FAILED before launch**
because this recorded case requires an explicit host-failure fallback policy;
the corrected v2 plans passed and their raw failures remain local.

Local evidence under `results/diagnostics/world-new-york-20260927-live-1`:
`active-nonroads-6300-{control,trial}-run/report.json`,
`active-nonroads-6300-paired-v1.json`,
`active-nonroads-6300-mirror-{control,trial}-run/report.json`,
`active-nonroads-6300-indexed-v1.json`,
`active-nonroads-6300-original-dma-run/report.json`,
`active-nonroads-6300-overdraw-v1.json`,
`active-nonroads-6300-backdrop-v1.json`, and the combined
`world-backdrop-overdraw-screen-v4.json`.
