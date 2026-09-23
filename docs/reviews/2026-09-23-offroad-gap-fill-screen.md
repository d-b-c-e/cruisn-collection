# Off-Road margin gap: offline fill screen

The saved El Paso frame 3120 can be reconstructed from its verified indexed
page and palette without another game run. The offline OpenGL palette pass on
the current shader reproduces the captured 2544×1353 client view closely:
16,685 of 3,442,032 pixels differ, but only 121 differ by more than one channel
value. The largest channel difference is 62. This is **not byte-exact** and
cannot substitute for a completed native frame in acceptance tests. The source
palette was captured at scene 3116; the saved palette from the later original
run is identical, but the few larger differences have not been attributed.

The [gap screen](2026-09-23-vunit-sky-gap-screen.md) finds 5,841 indexed sky
pixels in the left 16:9 margin where 3× auxiliary terrain borders the upper
edge and ordinary ground borders the lower edge. Four offline fills copied
neighboring existing pens into only those pixels: nearest edge, mirrored
texture rows, ground edge throughout, and host edge throughout. They change
4,441–4,624 completed pixels in client box `(69,516)..(213,562)` and leave
all other reconstructed pixels unchanged. The local comparison is
`results/diagnostics/offroad-full-20260910/left-gap-visual-trial-verified/comparison-crop.png`;
`python harness/offroad_gap_visual_trial.py --output <new-directory>`
reproduces it from the saved inputs and refuses to overwrite a prior report.

**Decision: reject all four as a renderer fix.** The comparison shows obvious
repeated texture bands or a sharp material cutoff. It also leaves the right
tip of the blue opening visible. At indexed x=164..220, that tip is bounded by
ordinary material rather than auxiliary terrain, so a rule that depends on
the host/ordinary edge cannot cover the whole artifact. Increasing the gap
screen's allowed height from 16 to 32 coarse pixels still reports the same
5,841-pixel subset. A generally useful correction needs to address the
underlying surface geometry or source/culling relationship, with more than one
frame and course to check continuity. Neither legacy Margin Fill nor a
single-frame pen copy should be promoted.

The test remains local and read-only. No emulator, shipped setting, release or
physical force-feedback behavior changed. The exact input/index/palette/image
SHA-256 values and per-variant pixel boxes are in the local
`left-gap-visual-trial-verified/report.json`. The earlier source and DMA checks remain in
[the margin-source review](2026-09-23-offroad-left-margin-source.md).
