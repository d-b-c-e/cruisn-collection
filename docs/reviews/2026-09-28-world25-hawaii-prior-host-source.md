# World 2.5 Hawaii: prior-host overlap at completed frame 5775

The active non-road margin candidate replaces 972 previously host-owned indexed
pixels while revealing left-edge trees at Hawaii completed frame 5775. This
check attributes both sides of that replacement to exact saved host packets.
It does not promote the diagnostic renderer path.

The existing matched control/candidate/original-DMA replays passed 5,780,
5,780 and 5,777 recorded inputs respectively, native comparison, physical
1440p display watch, literal FFB0 and owned worker shutdown. Their completed
control/source image and mirror hashes match; the earlier
[ownership check](2026-09-28-world25-hawaii-overdraw.md) remains the source for those
qualifications. No new game replay was made here.

The completed control mirror selects physical page 0. Its auxiliary submission
prefix identifies the *last fully consumed visible-page* host scene at source
frame 5772, raw page control 513; the candidate selects the same clock and
page. The detailed CSV scene fingerprints match the submission receipts.
There are 3,022 control packets and 3,628 candidate packets. Every original
packet remains an ordered subsequence; 606 packets were added.

An independent isolated raster of the exact control scene reproduces the
original index at **all 972** overwritten host pixels. They span fine indexed
`x=0..268, y=753..799`; 21 last-owning control packets from ten object IDs
contribute. An isolated raster of the 606 new packets reproduces the candidate
index at **all 972** of those pixels; 22 last-owning new packets from seven
active object IDs contribute. At each such pixel, the new packet's logged
object depth is smaller than the old packet's (972 nearer, zero equal or
farther). This supports an ordinary near-over-far replacement at this frame,
but object-center depth is not a full per-fragment depth proof.

The first two single-scene probes are retained as **FAIL**: frame 5774/page
516 matched only 14/972 indices, and frame 5770/page 516 matched 18/972.
Those both target physical page 1; guessing a source from proximity to the
completed frame was wrong. The corrected manual frame 5772/page 513 probe and
the automatic completed-prefix probe pass 972/972. The final v6 report adds
ordered trial packet attribution and depth counts. Local source-hashed reports
are under `results/diagnostics/world-new-york-20260927-live-1` as
`world25-5775-prior-host-screen-v1.json` through `-v6.json`.

`harness/screen_vunit_prior_host_overlap.py` now derives the source scene from
the completed auxiliary prefix, checks both detailed fingerprints, verifies
original packet order and independently rasters old/new packets. This is one
completed indexed view. It cannot prove all overdraw is visually correct,
exclude pop-in or texture defects in motion, or qualify other World courses or
4K. The authored dark Hawaii rectangle remains unchanged in both modes.
No native build, renderer deployment, release or personal installation changed.
