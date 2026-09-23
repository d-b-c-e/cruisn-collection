# Off-Road left opening: matched source and completed page

The El Paso sharp-turn opening at completed frame 3120 persists because the
sampled 3× host scene has no scenery polygon reaching a narrow strip between distant
terrain and near ground. This is stronger than counting distant admissions,
but it is still a **single scene**, not a general source-level fix.

The first metadata run captured source frame 3118. The completed mirror selects
physical page 1, whose last complete host scene was actually prepared at 3116;
3118 belongs to page 0. That run's original `report.json` remains **FAIL**.
Its continuous scene journal also exposed a verifier assumption: scene rows
legitimately continue outside the short metadata-capture interval. The verifier
now records the continuous runtime stop frame, accepts those bounded rows,
and still checks the total scene/packet count, captured-frame packet bytes,
ordered source hash, and exact displayed-page preparation. It does not excuse
a wrong source/display join. Sixteen focused mirror/runtime tests pass.

A corrected bounded replay captures source **3116** and completed frame **3120**.
It passes all 3,200 recorded inputs/times and native snapshots, one completed
2544×1353 client image on a physical 2560×1440 display, topology watch,
producer/consumer metadata bytes,
visible-page ownership and joined renderer shutdown. Its 708 captured host
quad packets match the scene hash `6d3888267d377a9d`, with zero reported
far-limit crossings in that scene. The completed mirror reports page 1 and
32,066 auxiliary-written fine pixels, all in the left band of this view.

At mirrored fine pixel `(60, 960)` on page 1, the extended and original index
are the same sky/background pen 6970 and the mask is ordinary tag 1. At the
same x, y=940 is textured ground pen 18744, while y=990 is an auxiliary
terrain pen replacing original sky. The gap thus lies **between** covered
host terrain and near ground; it is visible in the completed image. Decoding
all 708 captured projected quads finds no bounding box covering native
`x=-71, y=158..161` (the corresponding narrow strip after subtracting the
86-coarse-pixel widescreen margin). This is a conservative
bounds test; it does not identify which unsupported or authored source would
ideally continue that terrain. A larger global distance limit alone cannot
make an absent projected polygon fill this sampled strip.

The reusable `harness/analyze_vunit_margin_gap.py` independently checks the
passing replay, mirror/source join and producer bytes before reporting sampled
indices and projected coverage. Its corrected report is
`left-gap-source-analysis-v2.json`; it derives the native box from the verified
scale, margin and bottom-up page geometry. The original
`left-gap-source-analysis.json` remains as a **superseded coordinate analysis**:
it used x=15 without subtracting the widescreen margin and therefore did not
test the sampled x=60 opening. The revised analyzer does not rasterize or fill
geometry. Eighteen focused analyzer/mirror/runtime tests pass.

## Original command and saved-source cross-check

One further 3,200-input read-only resource replay captures Off-Road RAM, ROM,
texture and palette state at the **actual** source callback 3116. Its scene row
matches the prior replay's page 516, 708 quads and exact hash
`6d3888267d377a9d`. Independent saved-RAM reconstruction yields 245 accepted
host objects and the same 708 quads. Of 3,010 future definitions, 693 have
unsupported class flags; 424 of these are static billboard class `0x800804`.
Those counts do not make the skipped classes terrain or show they would fill
the observed opening.

A separate bounded replay captures the original DMA journal and an indexed
mirror at completed frame 3120. It passes the recorded input and native-image
prefix; its completed 2544×1353 image and all eight indexed mirror planes have
the **same hashes** as the matched host-source run. The completed-page selector
chooses 499 original commands drawn to page 1 over frames 3116–3117. In the
conservative native box `(-71,158)..(-71,161)`, only original backdrop command
1 intersects. The closest original near-ground command 66 begins at y=163;
the nearest host command 470 ends at y=156. Thus the indexed sky pen in this
small opening is consistent with a gap between two rendered surfaces, rather
than a black material sample or a dropped host command in that strip. The
host quad uses masked-texture mode (`0x900`), so joining these surfaces by
stretching it would need material and transparency checks before any live trial.

`harness/analyze_vunit_margin_gap.py --original-run` validates the separate
replay's case, executable, completed GL image, all mirror planes and DMA
capture receipt before reporting original and host projected bounds. The
combined `left-gap-source-analysis-v5.json` is the current report;
`left-gap-source-analysis-v2.json` remains the correct host-only predecessor.
The first combined report v3 lacked an independent original-run source-hash
check; it is retained, and v4 adds that check. Twenty-four focused
analyzer/mirror/runtime/original-scene tests pass. No
source or renderer correction is accepted from this single frame.

The v5 report also ranks neighboring projected host packets by rectangle gap.
Host quad 470 is two native units above the sampled opening, with masked
texture mode `0x900`, palette 27648 and texture 14336. Original near-ground
quad 66 starts two units below, with mode `0x100`, palette 18688 and texture
10513. Their source materials differ, so even a geometrically plausible direct
weld is not a texture-continuity fix. The ranking is conservative bounds, not
proof of exact visible-pixel ownership; the saved indexed page establishes the
actual color and coverage at the sampled fine pixels. Three focused projected-
bounds tests pass for the analyzer extension. The separate [offline fill
screen](2026-09-23-offroad-gap-fill-screen.md) rejects four visible pen-copy
variants without changing the renderer.

## Why the old Margin Fill is not a safe repair

The currently tested renderer has `MIDV_GL_MARGINFILL=0` and crack fill on.
The original backdrop command is the verified Off-Road sky class: texture-base
low byte `0x7f`, projected wider than 200 coarse pixels. The native shader's
Margin Fill path suppresses that class throughout the widescreen margin, then
redirects unwritten pixels to the first covered 4:3 boundary column. At fine
row 960, 194 consecutive left-margin pixels are sky indices beginning at x=0,
while boundary x=344 is ground pen 27207. Across seven nearby rows the sky
prefix is 146–224 pixels and every boundary sample is ground. Thus the current
policy would replace this blue opening with a horizontal run of one ground
column per row, a plausible **smear**, not restored terrain geometry. This is
a shader-source prediction against saved indexed pixels, not a live Margin
Fill on/off image. It supports leaving the retired global setting off while
investigating a source-aware join. Local reproducible screen:
`left-gap-marginfill-screen.py` and `left-gap-marginfill-screen.json`.

Local evidence is under `results/diagnostics/offroad-full-20260910`:
`left-gap-source-run/report.json` retains the verifier failure on the wrong
capture window, while `left-gap-matched-run/report.json` passes. The latter
contains `vunit-fade-producer.bin`, byte-identical consumer metadata,
`offroad-host-scenes.csv`, verified mirror planes and the completed image.
`left-gap-resource-run` and `left-gap-original-run` hold the two later passing
cross-checks, and `left-gap-original-selection.json` records the current DMA
group. The original command journal and ROM/material operands stay local.
The earlier [margin diagnosis](2026-09-23-offroad-left-margin-gap.md) retains
the ordinary/3× 4K images and the first capture-mode run. No renderer code,
installed build or public release changed. Next investigate the active ground
edge or unsupported source classes before attempting geometry generation;
avoid a generic skirt or stretched texture.
