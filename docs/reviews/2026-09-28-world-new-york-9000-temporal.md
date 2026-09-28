# World 2.4 New York: late left-edge opening through motion

The [frame-9000 source check](2026-09-28-world-new-york-9000-source.md)
attributes a real left-edge gap repair at one source-qualified view. I checked
the neighboring completed views to see whether the visible repair survives
the car and camera movement around that point.

Frozen diagnostic native `f762e01d63b` replayed the saved New York drive
through input 9010 twice: continuous 3× control and the separately gated
active-nonroad-margin candidate. Both prepare-only plans and both raw replay
reports **PASS** recorded input/native comparison, physical 2560×1440 display
watch, literal FFB0 and owned shutdown. The captures explicitly request CRT
on, 4× internal scale and native height 400. The paired comparator verifies
those settings, the same 3,588 host scenes and 13 completed frames at
8994..9006, with 481,655 additional candidate quads over the prefix.

All 13 completed images differ only in the **left third**. Their changed RGB
areas range from 2,550 to 4,751 pixels per frame, totaling 47,860
frame-pixels. The center and right thirds are exact in every image. The
candidate-new near-black heuristic is zero in all 13; the recovered
near-black heuristic totals 28,871 frame-pixels. These color thresholds are
review hints, not an exact gap measure or proof of texture correctness.
The inspected 8994, 9000 and 9006 candidate views carry left road-edge
scenery through the turn. The difference footprint shrinks toward 9006 as
ordinary scenery catches up; it does not disappear and reappear within this
sampled interval. Frame 9000 in both modes is byte-identical to the earlier
one-frame source-qualification captures, so the temporal check refers to the
same defect. The adjacent-step analyzer **PASS**es 12 pairs; its counts locate
motion transitions and do not establish geometry identity or visual quality
on their own.

A read-only callback-cadence screen of the saved frame 8800..9010 logs has
211 intervals in each run. Both cover essentially the same 3,649 ms of host
time. The control has 14 intervals over 25 ms and a 25.87 ms maximum; the
candidate has 13 and a 69.03 ms maximum. The candidate maximum is the single
interval immediately after a scheduled native snapshot at 8940. That is an
**unresolved isolated timing outlier**, not evidence of a sustained speed
regression or a clean pacing pass. Screenshot/snapshot I/O and host scheduling
are present, and these callback timestamps do not measure GPU presentation or
wheel latency. Source-hashed `new-york-9000-{control,trial}-cadence-v1.json`
retain the exact distinction without another replay.

Local evidence under `results/diagnostics/world-new-york-20260927-live-1`:
`new-york-9000-temporal-{control,trial}-{prepared,run}` (plans and raw
receipts), `new-york-9000-temporal-paired-v1.json` and
`new-york-9000-temporal-adjacent-v1.json`. The paired report's exact-image
comparator correctly says **FAIL** because the intended margin pixels differ;
its route, presentation, center-preservation and capture-inventory gates
**PASS**. The screen is a short physical-1440/FFB0 temporal safety check,
not full-course, other-course, 4K, fragment-depth or FFB acceptance. No
renderer, personal Stream Deck build or public release changed.
