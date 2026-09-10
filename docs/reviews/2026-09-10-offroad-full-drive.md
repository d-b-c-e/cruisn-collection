# Off Road complete El Paso drive — September 10, 2026

The new attended recording completes El Paso in first place, using automatic
transmission. The results screen shows 1:52.66. This replaces the coverage gap
left by the earlier scripted test, which spent much of its time near one hillside.
It does not establish coverage of other courses or manual transmission.

## Original recording and replay

The immutable case is local at
`results/diagnostics/drive-offroadc-20260910-175036`. It contains 9,644 input
frames over 166.481673344817 emulated seconds. Input SHA256:
`7618b9fd29d4a145264850c5e460801e6240bf1a15659ee9db9dd6e58ce86831`.
The attended drive used personal v0.5.0, 4× rendering, widescreen, CRT on and
the stock guest distance. Host scenery was disabled. Physical force was enabled
for the attended recording and is zero in the automated replays.

Two archived-binary replays preserve all recorded inputs/times and native
snapshots. The two replays also match all 7,831 camera samples and 31,324 actual
analog reads, including their timestamps, over frames 1800–9630. All 66 completed
display images match exactly, covering frames 1800–9600 every 120 frames.
The requested monitor is 3840×2160; the actual V-Unit client captures are
3824×2073. These are client images with window borders excluded, not full-monitor
3840×2160 captures. Whole-run average speeds are 99.78% and 99.92%.

The separately built native `431f4810a86` also passes the same full-drive
comparison with host scenery off: all inputs, native snapshots, camera/ADC
timing and all 66 completed display images match. Average speed is 100.00%.
Its only native change from `9ed` optimizes Exotica wide-packet serialization;
it does not change the Off Road host implementation.

## Final-section failure and correction

The first full-route 3× trial fails at native frame 8986 with the host
scene/model/material guard, before the finish. The emulator exits with code 3;
60 requested display captures completed before the stop, and final capture
draining correctly reports incomplete coverage. The failed run is retained.
Normal rendering completes this same recorded route. A read-only original-scene
probe also completes it, preserving all inputs, camera/ADC timing and all 66
display samples. Its additional instrumentation lowers average speed to 99.04%.

The failure is an end-of-course bookkeeping assumption. The final loaded section
is 58 of 59; the current section advances from 55 to 56 while the lead counter
still says three for one scene instead of two. The same event occurs at current
section 57, where the counter briefly says two instead of one. The original
probe records both transitions at Lua frames 8987 and 9087, with no unfinished
allocation. All 3,864 observed scene frontiers fit the settled or one-scene-delay
rule; 54 show that delay, including these two final-section cases.

The decoder already recognized this delay earlier in the track, but incorrectly
required another section to exist after the loaded front. The correction applies
the same bounded rule at the final entry. It keeps the future range empty and
continues rejecting larger counter mismatches, malformed end markers and
out-of-range pointers. It changes no game memory or original allocations.

Three exact scene snapshots around the first failure now pass independent native
and Python reconstruction at 1×/2×/3×, for pending and future sources: 18 cold/warm
comparisons. At the formerly rejected scene, 2× and 3× each reconstruct 56 pending
objects and 132 polygons, with zero future descriptors. New synthetic regression
cases cover the final boundary and the remaining invalid-state rejections.

Native `583481f82833f9e3087af5be30ef3d3e4664f82e` is built separately and frozen as
`build/candidates/583481f8283/vunit.exe`, SHA256
`eb4d790ddb8c84a6488cc43b89fe7f7528f1fb78e74004c677d302e87f31b850`.
Its 184-patch export reconstructs tree
`c942ec9ae50c30296d97021d7e41bc54d9f093e2` exactly. The correction is isolated
in collection commit `1ad1bd9`; the preceding Exotica packet optimization is
separate in `7282583`. Both source commits and native candidates are pushed.

Local checks pass 352 Python tests with no skips, 48 native test programs and
136 commands, including GPU contracts. The unchanged before/after source identity
is `6c2c6e3f99c291f00912158a028ccda89f4272b05c86941b14f7f73a886cd315`.
This is not a renewal of the seven default gameplay regressions.

## Corrected full-drive results

Full 3×, 2× and 3× repeat runs now complete all 9,644 input frames. Each preserves
the original camera/ADC timing and all 160 native snapshots, and completes all
66 requested display images. Average emulation speeds are 99.81%, 100.00% and
99.93%, respectively, with ordinary diagnostics and display captures enabled.
These averages do not establish smoothness under every condition.

The 3× repeat matches all 66 completed display images and the ordered counts and
geometry fingerprints across 3,865 scenes / 3,675,128 polygons. The corrected run
also preserves all 60 completed images and all 3,542 scene fingerprints from
before the retained failure. The fix has not changed the earlier scenery.

The full 3× run changes 40 of 66 images over normal rendering. Three-times differs
from 2× in 22 of 66 images, including the starting grid. Inspected driving images
show additional distant terrain near the finish at race time 1:46.90. At 1:48.90,
extended drawing shows the large mesa behind the finish line where normal
rendering shows sky. These are useful visible gains on this route; they are not
evidence that every object appears smoothly or that pop-in is eliminated.

The [public checkpoint](../../results/proof/2026-09-10-offroad-full-drive/README.md)
verifies source identity, capture coverage, image-signature comparisons and
consistency of the recorded test/build/route/geometry receipts. Raw native
execution, original pixels, geometry and full material ownership remain separate
local evidence; the public verifier does not rerun them.

Independent integrated later-course geometry/material checks, original resource
comparisons and runs without dense instrumentation remain necessary. A bounded
live geometry probe around both repaired transitions is next. The existing short
Off Road evidence is documented in
[the host-rendering review](2026-09-09-offroad-host-rendering.md).
Local trials and evidence are under `results/diagnostics/offroad-full-20260910`.
Raw game resources and screenshots remain local. Personal v0.5.0 is unchanged.
