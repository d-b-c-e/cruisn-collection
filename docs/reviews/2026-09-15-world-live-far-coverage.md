# World private far-plane coverage trial

World now has a gated live implementation of the saved-scene coverage prototype.
It admits part of a distant model instead of rejecting the entire model when a
vertex crosses the far plane. The fresh Hawaii comparison shows additional
mountain geometry. The authored floating terrain bottom remains visibly wrong;
this is not a terrain-gap fix or release-ready four-game parity.

The harness option `--world-host-far-coverage on` requires an explicit candidate,
World future drawing at 3×, and physical FFB disabled. It preserves each quad's
texture mapping and clips its coverage using separately carried camera depths.
Projection is bounded to 480,000 units, with coverage ending at 240,000. Original
game memory, commands and the ordinary renderer remain unchanged. No launcher
option or personal deployment was added. The method approximates clipping after
quantized projection; it does not reproduce the original game's clipping code.

## Evidence

Both runs used frozen native `676985e833a`, 5,902 recorded inputs, CRT enabled,
4× internal rendering and the current 3840×2160 monitor. Their 21 completed
captures cover frames 5880–5900 at a 3824×2073 client size.

- Original native-image checks pass. All 4,101 camera samples and 12,303 ADC
  samples match. Captured original DMA, framebuffer, texture, palette and
  metadata bytes match at frame 5900.
- All 3,889 transported crossing packets match GPU preparation records in
  order. An independent reconstruction matches every 64-byte coverage mask.
  These records precede `DrawArrays`; they are not raster-completion receipts.
- Frame 5900 retains all 8,403 old ordered quads exactly, adding 194 quads from
  36 objects. All added quads and all 81 crossing quads belong to independently
  reconstructed future sources. Existing pending quads are preserved exactly,
  but are not independently reconstructed by the future-source verifier.
- Eighteen of 21 completed images change, by 218–3,980 pixels. Changes are in
  the distant terrain area. The entire area below y=1200 is identical in every
  image. An initial lower-half ROI included mountains; its differing-pixel
  counts are retained rather than relabeled as a foreground failure.
- Up to 34 pixels become near-black under the measured threshold. Inspected
  crops show dark foliage at added terrain tips. This is not a claim that every
  black-artifact case is repaired or that all newly dark texels are validated.

Capture pacing and diagnostics were enabled. No performance or full-drive
temporal handover acceptance is claimed. Partial coverage helps one admission
boundary; authored mesh limits, allocation, LOD and other visibility decisions
can still cause pop-in.

Before the live pair, 15 saved World 2.4/2.5 snapshots qualified the geometry;
four dedicated GPU cases and 32 shared renderer cases passed. Focused native
and Python checks cover the depth format, default behavior and harness gates.
The new reusable receipt checker has four focused tests.

Two implementation failures remain recorded: the initial Python reference
overwrote model words with emitted DMA words on a multi-polygon model; a focused
regression case now covers this. The first Windows native build encountered
the platform's `far` macro; the wire field is now `far_limit`, with a macro
compatibility test. Neither failure was hidden by replacing its report.

## Reproducibility and next work

Candidate SHA-256:
`708c285acf12bb706a7d193b3e8af88cf4916cd655ba258f415ea0040b221deb`.
The 216-patch export reconstructs tree
`e0b88c24d7b09e5fe15a90fc8ffdbf85ac4a63ab`.

Local evidence is in `results/diagnostics/world25-roads-20260914/`:
`far-integration-checks-v2`, `far-coverage-live-off`, `far-coverage-live-on`,
`far-coverage-live-receipts.json`, `far-coverage-live-qualified-v2.json`, and
`far-coverage-native-export.json`. The v2 qualification narrows the original
report's independent-geometry wording and clarifies the foreground ROI.

Next, evaluate reuse against saved USA and Off-Road models before another
native build or replay. Their projection units and model formats require
separate adapters. Exotica's depth renderer needs its own boundary policy.
Personal native87d, public v0.5.0, FFB behavior and launcher menus are unchanged.
