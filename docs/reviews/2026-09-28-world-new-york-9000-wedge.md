# World 2.4 New York: later left-edge opening at frame 9000

The saved New York full-drive survey shows a small dark opening at the far
left road edge at completed frame 9000. That survey's auxiliary World draw
window had stopped at frame 2250, so its image could not show whether the
current continuous 3× path helps. I replayed this one saved 9,004-input
prefix with the frozen diagnostic `f762e01d63b` binary, explicit CRT on,
4× internal scale, native height 400, physical 2560×1440 display watch and
literal FFB0. The continuous 3× control and its active-nonroad-margin candidate
both **PASS** original input/native comparison and owned worker shutdown.

The completed control BMP at frame 9000 is **byte-identical** to the earlier
survey capture. Thus continuous 3× alone does not change this opening at the
sampled view. The separately gated active non-road option submits 481,071
additional quads over the long prefix, but the completed image changes only
**3,719 RGB pixels**, bounded by x=68..346, y=606..782 in the 2544×1353
CRT capture. All differences lie in the left third; the center and right
thirds are exact. The inspected candidate extends the distant left road-edge
scenery into the dark opening. The loose color heuristic counts 2,434
previously near-black pixels becoming brighter and zero candidate-new
near-black pixels. Those color counts are review hints, not a measured
unowned-gap area or proof of a texture repair.

`harness/compare_world_nonroad_course.py` **PASS**es the matched case, binary,
input prefix, physical display, explicit CRT=1/scale=4/height=400, native
scene count, center preservation and completed-image inventory. Local evidence
under `results/diagnostics/world-new-york-20260927-live-1` is
`new-york-9000-continuous-control-run/report.json`,
`new-york-9000-nonroads-run/report.json`, and
`new-york-9000-nonroads-paired-v1.json`, plus the prepare-only plans. The
earlier survey and this control have identical completed BMP SHA256
`d7b956fdac8e…c281057f5c`.

This is a later-course positive *appearance* sample. It has no indexed owner,
original DMA or source-packet attribution yet, and one frame cannot establish
motion safety, route-wide repair, 4K appearance or physical FFB. Do not
promote the option or conflate its extra submitted quads with visible gain.
No renderer deployment, personal Stream Deck installation or public release
changed. Next bounded gate: matched indexed mirrors and current original DMA
at frame 9000; if prior host pixels change, inspect their exact source/depth.
