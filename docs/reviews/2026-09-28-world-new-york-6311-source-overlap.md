# World 2.4 New York: source and overlap at the 6311 wall transition

The [one-frame-cadence turn](2026-09-28-world-new-york-late-wall-dense.md)
locates a renewed right-side opening in the ordinary completed image at frame
6311. The active non-road margin candidate continues a textured wall there;
its completed CRT difference footprint is 61,100 RGB pixels. This check uses
the saved New York drive to identify exactly what the candidate covers in that
one frame. It does not change or deploy the renderer.

Frozen diagnostic native `f762e01d63b` ran three narrow 6,313-input prefixes:
an original-DMA/control capture, a candidate indexed mirror, and a read-only
source-time tap. All three raw reports **PASS** recorded input/native motion,
physical 2560×1440 display watch, literal FFB0 and owned worker shutdown.
Their completed frame-6311 control/trial BMPs are byte-identical to the
independently saved dense control/trial BMPs. The control and source-tap
indexed mirrors and completed control BMP also match exactly. The first
source-tap preflight **FAIL**ed before launch because it omitted the required
metadata toggle; the corrected preflight and replay passed. The failed plan
is retained locally.

The completed indexed page changes **85,554** pixels only in the right margin,
with original-only planes and the 4:3 center exact. None was previously
unowned: **72,172** were original-game pixels and **13,382** were earlier
host-owned pixels. Captured current original DMA independently reproduces all
72,172 original indices. Every one belongs to upper panorama ordinal 3, part
of the repeated 0..4 strip; no original foreground quad is identified under
the change. This structural classification is narrower than visual safety.

The completed auxiliary prefix selects source frame **6308**, page control
513. A read-only C31 source tap captured RAM and resources at that exact host
scene read. Independent native scene reconstruction produces **4,300** control
and **5,054** candidate packets; both ordered fingerprints exactly match the
live completed-page submissions. All control packets remain in order, and
**754** packets from 97 objects are added. An isolated raster of those added
packets reproduces the candidate index at **all 85,554** changed pixels.

The separate [native prior-host screen](../../harness/screen_world_native_prior_host.py)
reproduces both old and new indices at all **13,382** earlier host-owned
positions. The added objects have smaller logged center depth at every one
of those positions: 13,382 nearer, zero equal or farther. The old objects'
center-depth range is 75,278..152,172; the added objects' is 21,867..72,086.
This supports a near-over-far wall replacement at the sampled view, but
object-center depth is not per-fragment depth. The screen verifies hashes of
the prior ownership and source-pixel reports, both native packet files, mirror
planes and texture before attributing pixels. A one-word-mutated packet file
correctly fails its source-fingerprint gate; the raw negative error is kept.
The script compiles and the positive/negative saved-evidence checks pass.

Local reports under `results/diagnostics/world-new-york-20260927-live-1` are
`active-nonroads-6311-{overdraw,backdrop,native-source-pixels,prior-host}-v1.json`,
the three `...-run/report.json` receipts, source-time native packet files, and
the preserved preflight/negative failures. The completed RGB image and exact
indexed ownership answer different questions; submitted quads alone do not
measure visibility. This one New York transition supports keeping the option
under diagnostic study, not promoting it to product defaults. Full ordered
fragment depth, other course transitions, 4K, pacing and attended wheel/FFB
remain open. Personal Stream Deck renderer and public release are unchanged.
