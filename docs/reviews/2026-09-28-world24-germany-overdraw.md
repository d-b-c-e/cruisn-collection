# World 2.4 Germany building reveal ownership — September 28

The active non-road candidate adds a small building at the left edge of the
saved Germany drive at completed frame 7280. An indexed-mirror and original-DMA
check now identifies what it replaces. This is a cross-course admission sample,
not a fix for Germany's distant mountain/tree pop-in or reported black road.

On frozen native `f762e01d63b`, matched control and candidate replays each
pass 7,285 recorded inputs, native comparison, physical 2560×1440 display
watch, literal FFB0 and owned shutdown. A 7,282-input control capture of the
original DMA/resource state reproduces the first control's completed frame
7280 CRT image and all eight indexed mirror planes byte-for-byte. Both new
CRT images also equal their corresponding frame-7280 images from the earlier
nine-frame Germany interval. The paired replay adds 142,215 submitted host
quads over the same 2,804 scenes. It changes 13,727 completed RGB pixels only
in the left third; the center remains exact.

The candidate changes 19,471 indexed pixels at fine `x=0..262, y=847..1078`.
Every changed control pixel has ordinary game tag `1` and every candidate
pixel has host tag `5`; there is **no** newly owned or prior host-owned pixel
in this changed set. The original-only planes are exact and carry the same
index/tag as all 19,471 control pixels. An isolated raster of the current
original DMA with the captured texture bytes reproduces those indices exactly:

| Original DMA | Changed pixels | Native bounds | Interpretation |
| --- | ---: | --- | --- |
| 0 | 19,327 | `(-285,-17)..(-29,223)` | leftmost upper panorama strip |
| 1 | 144 | `(-30,-17)..(226,223)` | adjoining upper panorama strip |

The commands are the first two adjacent top-of-view backdrop strips; the
completed image shows the added building against the sky. This frame gives no
evidence that the candidate overdraws road or other foreground scenery. It
also gives no evidence of filling a black gap or moving the guest's original
mountain/tree activation distance. New York 3600 and Hawaii 5775 likewise
trace their game-owned changes to panorama strips, but these three frames do
not qualify every World scene or transition. Hawaii alone in this set has a
small prior-host overlap, still without exact host-packet attribution.

The source-hashed report is
`results/diagnostics/world-new-york-20260927-live-1/germany-7280-overdraw-v1.json`;
the three raw replay reports and `germany-7280-mirror-paired-v1.json` are in
the same local directory. The reusable screen is
`harness/screen_vunit_margin_overdraw.py`. No new native code, binary,
renderer deployment, personal installation or public release changed.
