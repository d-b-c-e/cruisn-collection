# Off-Road left opening: matched source and completed page

The El Paso sharp-turn opening at completed frame 3120 persists because the
sampled 3× host scene has no polygon reaching a narrow strip between distant
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
`x=15, y=159..162` (the corresponding narrow strip). This is a conservative
bounds test; it does not identify which unsupported or authored source would
ideally continue that terrain. A larger global distance limit alone cannot
make an absent projected polygon fill this sampled strip.

The reusable `harness/analyze_vunit_margin_gap.py` independently checks the
passing replay, mirror/source join and producer bytes before reporting sampled
indices and projected coverage. Its saved report is
`left-gap-source-analysis.json`; the analyzer does not rasterize or fill
geometry. Seventeen focused analyzer/mirror/runtime tests pass.

Local evidence is under `results/diagnostics/offroad-full-20260910`:
`left-gap-source-run/report.json` retains the verifier failure on the wrong
capture window, while `left-gap-matched-run/report.json` passes. The latter
contains `vunit-fade-producer.bin`, byte-identical consumer metadata,
`offroad-host-scenes.csv`, verified mirror planes and the completed image.
The earlier [margin diagnosis](2026-09-23-offroad-left-margin-gap.md) retains
the ordinary/3× 4K images and the first capture-mode run. No renderer code,
installed build or public release changed. Next investigate the active ground
edge or unsupported source classes before attempting geometry generation;
avoid a generic skirt or stretched texture.
