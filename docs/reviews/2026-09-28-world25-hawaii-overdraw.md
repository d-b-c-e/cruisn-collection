# World 2.5 Hawaii margin ownership at frame 5775 — September 28

The active non-road candidate visibly adds trees on the far-left edge of the
saved Hawaii drive at completed frame 5775. A matched indexed-mirror check now
shows what those trees replace. This is a one-frame admission screen, not
course-wide occlusion safety or a fix for Hawaii's separate dark terrain edge.

The frozen `f762e01d63b` binary ran the same recorded World 2.5 case three
times on the physical 2560×1440 primary with literal FFB0. Control and opt-in
candidate each pass 5,780 recorded inputs, native comparison, display watch and
owned worker shutdown. A third control replay captures original DMA and texture
with a 5,777-input prefix. Its completed frame-5775 CRT image and all eight
indexed mirror planes are byte-identical to the first control. Both control
and candidate CRT images are also byte-identical to the corresponding 5775
images in the earlier nine-frame Hawaii interval. The pair adds 95,523
submitted host quads over 1,857 scenes; the completed center third is exact.

The candidate changes 35,638 indexed pixels, all in the far-left margin
(`x=0..285` of 2,736). **None was previously unowned.** The control tags are
34,666 ordinary game pixels (`1`), 911 host pixels (`5`), and 61 host dither
pixels (`7`). Candidate tags are 35,621 host (`5`) and 17 host dither (`7`).
All 34,666 overwritten game pixels have the same index and tag in the
original-only mirror. An isolated raster of the 811 current original DMA quads
with the saved texture bytes reproduces every overwritten game index exactly.
It attributes 34,116 pixels to DMA ordinal 1, native box `(-209,-17)..(47,237)`,
and 550 to ordinal 6, box `(-209,209)..(47,380)`. These are two vertically
stacked strips among the game's contiguous panorama/backdrop commands. The
saved completed images show sky/ocean behind the new left-edge trees. The 972
prior host pixels have **not** been attributed to exact prior host packets by
this screen; they remain a separate overlap risk, though the inspected image
does not show a clear defect.

Saved callback timestamps over frames 5750–5775 show 13 of 26 intervals above
25 ms in both control and candidate. Total interval time is 453.25 versus
458.90 ms, with maxima 31.80 versus 32.37 ms. These short, instrumented
callback windows show no new threshold-count spike at this reveal. They do
not measure GPU presentation or physical wheel latency.

This is visible coverage but only a small outer-edge gain. The nine-frame
Hawaii interval and this source-qualified frame do not show earlier appearance
of the distant mountains, repair of the authored dark rectangle at 5900, or
elimination of pop-in. It is important that the New York 3600 and Hawaii 5775
overlaps are now described by mask tags and exact original DMA, rather than
calling every occupied pixel “host-owned.” This frame's guest overlap is
backdrop replacement; another scene could still overdraw real foreground.

`harness/screen_vunit_margin_overdraw.py` enforces same ROM/binary/display,
passing input/native/shutdown, FFB0, exact control/source mirror and completed
image, original-only preservation, unchanged 4:3 center, host-tagged candidate
changes, and exact current-DMA attribution of changed game pixels. Its report
includes SHA-256 for the reports, original DMA, texture and indexed planes.
The existing paired comparator initially rejected explicit control
`active_nonroads=off` even though omission meant the same state; it emitted
`ValueError: replays differ in more than active non-road margin selection`
before writing a report. The comparator now normalizes those two control
forms, and both this one-frame pair and the prior nine-frame Hawaii pair pass.
The first prepare-only mirror request also failed before game launch because
the default capture cadence did not include frame 5775; its raw report remains
local. The corrected prepared plans and all passing replays are retained.

Local reports are under `results/diagnostics/world-new-york-20260927-live-1`:
`world25-5775-mirror-{control,nonroads}-run`,
`world25-5775-original-dma-run`, `world25-5775-mirror-paired-v2.json`, and
`world25-5775-overdraw-v1.json`; the two `world25-5775-*-cadence-v1.json`
reports hold source-hashed callback timing. No native source, binary, renderer deployment,
personal Stream Deck installation or public release changed.
