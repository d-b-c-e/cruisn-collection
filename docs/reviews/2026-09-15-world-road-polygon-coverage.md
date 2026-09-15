# World road coverage at the widescreen boundary

The remaining Germany holes at completed frame7280 / game elapsed1:35.69 have
two demonstrated causes. Neither requires increasing the far plane or inventing
road textures.

* Three polygons from active roads0x151d4 / model0xca076c and0x117a4 /
  model0xca06a9 cross into the native viewport by1..7 pixels. The first active
  road repair rejected an entire polygon unless it was wholly outside4:3.
  That unnecessarily discards its useful margin coverage.
* Road0x1280c / model0xca037f contains vertices down to depth442.32, so the first
  repair rejected its entire model. Eight polygons have all their own vertices
  safely above1000; one covers the lower-left hole. Two other intersecting
  active road models also contain safe polygons.

The implementation preserves the original object-admission predicate and fresh
active-list ownership. It now checks depth per polygon, retaining invalid vertex
slots and excluding every polygon referencing one. It does not clamp or clip
near-plane vertices. Future/pending geometry retains whole-model rejection.

A separate change carries a margin-only coverage permission beside the original
quad. The renderer discards fragments inside the native512-pixel viewport while
preserving all corners, UV interpolation and material words. This avoids the
texture distortion that would result from moving a polygon's boundary vertices.
The permission requires an explicitly enabled active-road experiment and the
existing split host layer. Original commands never acquire it. Fade metadata
accepts it only on authored roads and with explicit harness permission.

## Saved-scene evidence

A7282-input replay with frozen native62f2d62a42f captures exact scene-entry
resources at7277 and7279. All5482 camera samples and16446 ADC events match the
retained full drive; completed7280 is pixel-identical. Its3756898 original DMA
records through7280 also match the full drive. The embedded order tap was still
configured for7336..7341, so PC/AR provenance is unavailable. That initial
qualifier failure is retained; a separate recheck qualifies the actual available
evidence without claiming the missing trace or rerunning the game.

The canonical compiled successor preserves all future quad/depth bytes and
independently matches186 active polygons at7277. The scene grows2463 to2485
polygons:19 from the per-polygon depth change, three from boundary coverage.
The initial local depth qualifier incorrectly expected only the target road's
eight additions; all19 had already matched the independent reference. Both the
failed expectation and corrected result are retained.

Saved Germany7337/7339 and World2.5 Hawaii5900 retain all2521/2479/5922 future
rows respectively. Their active additions are56/46/0. Four targeted native tests
and24 focused Python tests pass, including texture-preserving coverage at native
and4x scales and rejection of unqualified margin/fade metadata.

The offline renderer was corrected locally to reproduce the native margin clear
before current-scene draws. Its control now matches **every indexed pixel** of
the actual2736x1600 displayed page. Rendering the compiled successor's polygons
with the canonical fragment mask changes14052 RGB pixels, changes zero native
center pixels and creates zero new black pixels. It repairs5600/5602 pixels in
the upper target and2986/2988 in the lower target. The four remaining boundary
pixels already have polygon ownership; this does not establish a new region of
missing geometry. The proposed image was inspected.

## Live successor

Native0ce0f02457a is built and separately frozen with SHA256
`0ce0468292f0e33828ae8b1bf855cca5db6cf34b08e9e025a377077f3bf32d53`.
The231-patch export reconstructs tree
`93cad1c2f3b2744e469233c3b9b30be4053dd88d`. Nativeb553c01eb91 contains the polygon
depth change;0ce0f02457a adds fragment coverage, so they remain separately reversible.

The full9269-input Germany replay passes. All7461 camera samples and22383 ADC
reads, the complete original DMA journal, original framebuffer and captured
materials are byte-identical to the previous candidate. All four scene-entry
snapshots7277/7279/7337/7339 match their controls, and the sampled host fingerprints
match the canonical analyzer. The corrected PC trace joins1453 original commands.
At7280 both original-only GPU pages and every native-center plane are exact.
The **entire displayed2736x1600 indexed candidate page matches the offline
prediction byte for byte**. The completed4K image was inspected: both targeted
holes are filled, and the adjacent distorted strip is replaced by road texture.

Across31 completed3824x2073 CRT frames7060..7360,11 change and20 stay exact.
They repair121369 formerly black pixels in aggregate beyond the previous repair.
The fixed image interior remains exact throughout. At7270 a large pale road gap
also gains road coverage; a smaller pre-existing pale triangle remains beside
the native viewport boundary.

The literal zero-new-black metric is not satisfied: two pixels at7230 previously
had channels no brighter than2/255;208 at7270 include formerly bright pixels.
Those208 form no four-connected group larger than six pixels, mostly along the
outer curved display boundary. The paired7270 images were inspected without
finding a newly missing textured region. Counts, coordinates, prior colors and
connectivity are retained; this is not a claim that every changed pixel is black-
artifact-free or that all tracks are accepted. The live integrity/prediction
report passes separately from that strict pixel metric.

World2.5 also passes6000 recorded inputs,4191 camera samples and12573 ADC reads.
Its1666 source/frontier rows remain stable, with75 additional polygons across the
segment. All eight GPU planes at5900, the captured resources and completed1280x720
image match the earlier active-road candidate. This is a second-revision segment
on the4K monitor, not a renewed full4K cross-track qualification. Its metadata-
enabled path consumes4121980 packets and195330 authored road packets; the5922
captured producer/consumer packets are byte-identical and independently decoded.
No distance fade is enabled in that compatibility check.

The preselected Germany5000..6500 window, before resource or screenshot captures,
measures100.0044% in the control and100.0084% in the successor. Preparation totals
are1.22865s and1.23872s. This single instrumented pair shows neither a meaningful
speed gain nor a throughput regression in that window. Whole-run averages include
the deliberate snapshot stalls and do not establish final uninstrumented speed.
No additional runs were made merely to improve the timing result.

No deployment or public release is authorized by these checks. Personal/Stream
Deck87d and publicv0.5.0 are unchanged. Remaining work includes other tracks,
World's authored terrain edge, visible distance transitions and the final package
and attended acceptance gates.

Local evidence is under `results/diagnostics/world25-roads-20260914/`:
`germany-residual-resources`, `germany-residual-qualified/resources-qualified-v2.json`,
`polygon-depths-initial-failure.json`, `polygon-depths-qualified-v2.json`,
`coverage-scenes-qualified.json`, `coverage-native-pixels.json`,
`germany-polygon-coverage-qualified.json`, `germany-polygon-new-black.json`,
`world25-polygon-coverage-qualified.json`, and `germany-polygon-coverage-cost.json`.
