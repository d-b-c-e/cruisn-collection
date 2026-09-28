# USA Golden Gate: red screenshot pixels versus genuinely new host coverage

The saved Golden Gate partial-far-coverage pair has 4,906 candidate-only red
CRT pixels in the fixed far-left ROI at completed frame 10476. The earlier
[packet-to-pixel check](2026-09-28-usa-bridge-pixel-source.md) established
2,558 exact indexed center samples from two newly admitted bridge objects.
I revisited the same source-qualified frame to distinguish those additions
from red samples whose packet already existed in ordinary 3× output.

`harness/screen_usa_bridge_candidate_pixels.py` now also isolates the
ordinary 3× source scene with the exact saved texture. The rerun on existing
evidence **PASS**es the same source/resource, live-scene fingerprint,
completed-image, input/native, display, FFB0 and owned-shutdown gates. Of
4,906 unique candidate-only red CRT center samples, **4,862** match an exact
candidate host index. The other 44 remain unattributed by this center-sample
test.

For **2,558** samples, the candidate's last isolated packet is newly added
and the isolated ordinary host scene has **no coverage** at that indexed
point. These split into 1,779 from object `0x800a0040` and 779 from
`0x800a0042`. That is the strongest measured early bridge-coverage gain at
this frame. For the other **2,304** exact host samples, the candidate's last
packet already exists in ordinary output, and the isolated ordinary scene
produces the **same index** at the same point. Thirteen older source objects
contribute these center samples. Thus all 4,906 screenshot-red changes should
not be counted as 4,906 newly drawn bridge pixels. CRT neighborhood mixing,
original/auxiliary composition or occlusion can make a screenshot center
change even when its isolated host index matches; the current data do not
separate those causes.

This classification uses one sampled 1440p frame, a fixed red predicate and
isolated host rasterization. It does not measure the whole bridge silhouette,
prove smooth entry, reconstruct the full ordered original/host compositor,
or qualify 4K, another USA course, GPU pacing or a release default. In
particular, this original source-only screen had no matching *control indexed
mirror* at 10476, so it could not claim that the completed control pixel was
identical. The subsequent [matched control indexed check](2026-09-28-usa-bridge-control-indexed.md)
shows 2,348 candidate-only red CRT centers with identical completed
index/tag, including those 2,304 source-attributed points. The
partial-far-coverage option remains gated.

No game/GPU replay, native build, deployed renderer, personal installation
or public release changed. Python compilation and the source-hashed offline
`usa-bridge-candidate-pixels-v3.json` report pass; v1/v2 are retained under
`results/diagnostics/race-transitions-20260916/`. The checker scans the
existing detailed trace and saved source resources.
