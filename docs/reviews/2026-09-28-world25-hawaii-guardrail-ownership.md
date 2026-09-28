# World 2.5 Hawaii: right-margin guardrail ownership at frame 5760

The [dense Hawaii interval](2026-09-28-world25-hawaii-dense-transition.md)
found a distinct right-margin change at completed frame 5760: the active
non-road candidate visually continues the guardrail toward the edge, while
the other sampled changes are left-edge foliage. Because a coherent-looking
image can still overwrite a valid game object, I checked its indexed owner
and exact original DMA source before treating it as a safe-looking sample.

Frozen diagnostic native `f762e01d63b` replayed the same saved World 2.5
drive with active non-road margins off/on. The two 5,770-input mirror runs
and a 5,762-input original-DMA source run all **PASS** recorded input/native,
physical 2560×1440 display watch, literal FFB0 and owned worker shutdown.
Each completed 5760 CRT capture is byte-identical to its matching image in
the earlier dense pair. Control and candidate complete on physical page 0;
their original-only index and tag planes are byte-identical, and the 4:3
indexed center is exact.

The candidate changes **8,209 indexed pixels** within x=2570..2735,
y=567..681 of the 2736×1600 mirror. All 8,209 were game-owned (`tag 1`)
in control and match its original-only index/tag exactly. The candidate
marks 8,206 as host (`tag 5`) and three as host dither (`tag 7`). None was
previously empty or host-owned. An isolated raster of the exact current
original DMA with the captured texture reproduces the control index at
every one of those pixels. All 8,209 trace to original DMA ordinal 9,
native box `(556,209)..(812,380)`. That quad is the rightmost member of
the game's five-tile lower panorama strip (ordinals 5..9), not a road,
vehicle or foreground command. The structural backdrop checker reports
**zero unclassified original pixels** for this one frame. The completed
CRT crop shows the candidate's guardrail continuation over the ocean edge.

An earlier matched detailed Hawaii pair already contains the source scene
selected by the completed 5760 auxiliary prefix: source frame 5756, page
control 513. Its 2,951 control and 3,298 candidate packets have the **exact
count and ordered fingerprint** recorded by the respective completed-frame
mirror runs. All 2,951 old packets remain an ordered subsequence; the
candidate adds 347 packets from 88 objects. An isolated raster of those
added packets with the captured 5760 texture reproduces the candidate index
at **all 8,209** changed pixels. The last added contributors are two active
objects: `0xc001094a` / model `0xf3b98f` for 6,195 pixels and
`0xc001099e` / model `0xf3b8ea` for 2,014. This is an exact selected-pixel
packet/material attribution across matched saved replays; it does not
reconstruct the full ordered compositor or prove per-fragment depth.

`harness/screen_world_added_packet_coverage.py` now enforces the cross-replay
case/binary/display/input/FFB/shutdown checks, completed source-scene
fingerprints, original-only and 4:3 preservation, old-packet order, and
isolated new-packet coverage. It accepts a longer detailed source trace only
when its exact source fingerprint matches the shorter completed mirror.
Python compilation and the actual source-hashed 8,209/8,209 screen pass.
The preliminary one-off v1 report is retained; v2 is the reusable checker.

This establishes original and added-packet source at 5760. A structural
panorama label and isolated raster do not prove correct depth or occlusion
on every frame. It does not imply the entire World 2.5
route is safe, that the distant mountains appear earlier, or that the
authored dark rectangle at 5900 is fixed. No native source, binary,
renderer deployment, personal installation or public release changed.

Local evidence under `results/diagnostics/world-new-york-20260927-live-1`:
`world25-5760-mirror-{control,nonroads}-run/report.json`,
`world25-5760-original-dma-run/report.json`,
`world25-5760-indexed-ownership-v1.json`,
`world25-5760-overdraw-v1.json`,
`world25-5760-panorama-v1.json`,
`world25-5760-backdrop-v1.json`, and
`world25-5760-added-packet-screen-v1.json` and `-v2.json`, plus
`world25-5760-right-crop.png`. The prepared plans are separately retained.
