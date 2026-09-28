# New York active-margin turn sequence — September 28

The source-qualified active non-road margin candidate was compared against its
own opt-in control across nine completed World 2.4 New York frames, 3560–3640
at ten-frame intervals. This is the same recorded drive and frozen
`f762e01d63b` native binary on both sides. Both bounded 3,650-input replays
passed the recorded input and native-motion checks, used literal FFB0 on the
stable physical 2560×1440 display, and finished with owned shutdown. The
candidate submitted 119,729 more host quads across 908 scenes. No live wheel
or 4K acceptance is implied.

The paired completed-image check passes its preservation contract: all nine
images have the same dimensions, every changed pixel lies in the right third,
and the center third is exact in every image. The differences are intentional,
so the standalone exact-pixel comparator reports **FAIL** for equality; that
raw result is retained. The first standalone run also failed because it was
given the parent report folders instead of their `run` folders; its raw report
is retained. The corrected report and three-point contact sheet were made
without rerunning either game.

Across the nine frames, 258,118 completed pixels change (11,847–45,896 per
frame). A near-black *review heuristic* counts 112,386 recovered pixels and
56 candidate-new near-black pixels across those frames. These are accumulated
frame counts, not a unique defect area or a material classifier. In the
completed 3600 view, the large far-right black opening beyond the road is
replaced by road shoulder/wall geometry; the neighboring 3590, 3610, 3620,
3630 and 3640 images show that geometry continuing as the turn moves. The
extra geometry and skyline in the inspected images look coherent at this
cadence. This checks a short motion interval, not every intermediate frame or
the entire course. It does not establish a fade or eliminate scenery pop-in.

The prior source-time overlap report remains the exact material attribution
for frame 3600: added active non-road packets explain all 50,390 changed
indexed pixels there, including 25,631 already game-owned pixels. The corrected
[ownership analysis](2026-09-28-world-new-york-overlap-source.md) shows these
pixels exactly match the original-only mirror before the host candidate draws.
All 25,631 trace to one original backdrop strip in this frame.
The present
completed images strengthen temporal visual evidence but do not replace that
indexed/source check, and nine sampled frames cannot prove that active host
overlap never causes a wrong occlusion elsewhere. The narrow ten-pixel indexed
edge at 3600 remains unowned. Further promotion needs denser turns on another
World course, 4K, and broader stability/appearance gates.

Local evidence is under `results/diagnostics/world-new-york-20260927-live-1`:
`active-nonroads-3600-temporal-{control,candidate}-run/report.json`,
`active-nonroads-3600-temporal-paired-v1.json`, raw failed `...-gl-v1.json`,
corrected exact-difference `...-gl-v2.json`, and
`active-nonroads-3600-temporal-contact.png`. The source review is
`docs/reviews/2026-09-28-world-new-york-overlap-source.md`. Neither native
code nor the personal/public builds changed.
