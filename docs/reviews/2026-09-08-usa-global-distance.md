# USA global distance experiment — 2026-09-08

USA 4.5 now has an optional **command-line** global distance adapter. It combines
projection and pending/active scenery limits without a model or level allowlist.
The ordinary launcher defaults are unchanged. This is an instrumented candidate,
not a claim that pop-in is eliminated or that its new route has been accepted.

Collection implementation `9e70f6a`; native `8b151aa9c2f27d64c80f77b73d680d941e6b9532`,
built at `E:/Source/mame-src/vunit.exe`, SHA256
`638c74ff4227532d0ff42be4cd46cb8a358a1a343549abb107bb56050e91bd74`.
The 126-patch export reconstructs tree `5e10f68c9badba2385d38d6178eaae1be02d48b6`.
The released v0.4.0 tag/ZIP and all original recordings remain intact.

## What changed

`native/usa_distance.h` guards USA's actual instructions, table pointer and all
five renderer clamp groups, including the easy-to-miss `277/278` dynamic-model
path. The checked game patch changes the 80,000 far word and positive projection
clamps. Host-owned reciprocal values serve only attributed reads with the correct
base registers; they never overwrite the adjacent guest object RAM. The existing
World six-decimal tail generator is reused because the original USA and World
tables match exactly. Other games do not inherit USA addresses.

USA's pending-list admission is depth-based: 75,000 admission and 80,000 removal.
Guarded reads extend both windows proportionally while the original guest code
continues to transfer objects. `MIDV_USA_RESIDENCY=0` leaves both windows stock,
providing a projection-only control. `MIDV_USA_FAR` accepts 80000, 100000, 160000
and 240000. All hooks are absent when this option is unset. CSV counters distinguish
far tests, extended reads, attached-effect reads and both residency consumers.

The separate `823E` helper computes screen-space extrema and explicitly rejects
indices >=4999; that behavior is preserved. The unclamped `A728` lookup scales an
attached object using its parent's cached depth. It is guarded and covered by
the host tail, with a separate counter. No extended reads from it occurred in
these trials, so there is no runtime evidence for that path beyond its static
signature and range checks.

`replay.py`, `derive_case.py`, `record_drive.py` and the recording launcher accept
`--usa-far`/`--usa-residency`. An explicit recording distance takes precedence over
the saved legacy USA Draw Limit. Patch conflicts fail rather than partially apply.
`run_usa_distance_trials.py` runs a serialized matrix with physical force disabled;
it retains original-image FAIL results and separates camera, actual ADC and timing
verdicts. `usa_motion_trace.lua` reads the verified fast-RAM camera and actual ADC
read events. The existing strict comparison code now supports a USA trace profile.

## Full LA Freeway-derived matrix

Each trial completed 5,012 frames and 83 native snapshots, plus 19 completed GL
captures at frames 2500..4300, every 100 frames. Those matrix captures are 512×451
window images, not a 4K acceptance test. Camera/ADC observation spans 1500..5000.
Frame-level input and emulated-time logs match the original throughout every run.

| Trial | Extra far tests | Extended reads | First camera difference | Emulation rate |
|---|---:|---:|---:|---:|
| original | 0 | 0 | none | 99.9900% |
| far2-only | 15 | 35,441 | 3012 | 99.9925% |
| far125-residency | 50,744 | 2,194,160 | 2222 | 99.9905% |
| far2-residency | 98,467 | 3,995,943 | 2222 | 100.0013% |
| far3-residency | 101,725 | 4,727,443 | 2222 | 100.0002% |

The original control passes its input/native comparison. Projection-only 2× changes
three native snapshots and only three pixels in one of the 19 GL images. It differs
in one of 3,501 camera samples (3012), with equal actual ADC frame/value/PC sequences
but different ADC timestamps. This is not evidence of a useful visible extension.

Extending residency changes the later route substantially, including a collision
with the embankment. First camera differences appear at2222; actual interpolated
ADC values can differ even though recorded frame-level wheel values match. This
is why the old drive is retained as a diagnostic control, not replaced or claimed
as a matching drive. A fresh attended recording remains necessary for route and
handling acceptance if the option is promoted.

2× and 3× share the same camera until3902; actual ADC frame/value/PC sequences match,
while their timestamps differ. Five GL samples differ (3900..4300); the first has
73 changed pixels in the HUD area, and later samples include camera/route differences.
These images do not demonstrate extra visible scenery from3×. Additional reads
and admissions alone are not a visual-quality result.

## Verification checkpoint

The separate2× candidate repeats all5,012 input frames,83 native snapshots and
19 completedGL images exactly. Derivation now accepts `--gl-capture`/`--gl-every`,
requires the full capture interval and runs its identity replay with `--compare-gl`.
These candidate captures are1904×993, not4K. The original recording stays intact.
The initial local unit check caught a non-serializable range for this new report
field; the fix materializes its frame list before recording.

All seven default regressions pass on the final native: both USA cases, both
World revisions, full Germany, Off Road and Exotica. Actual telemetry/independent
memory checks and existing World passthrough/Exotica force checks pass with physical
output disabled. Exotica also matches21 completed4KGL references. This is automated
component evidence, not a new release or attended wheel/handling acceptance.
139Python tests and all four CI jobs34202538087 at3628c96 pass. All237 source hashes
match locally, on Windows CI and on Linux CI, identity
`946fc6523f110ddc2d91e5a481b4a6cbdd0cc067d73452cc3ab923e42023974c`.
The native vectors pass against the actual captured USA program. A later receipt
rerun first lacked the MSYS DLL runtime; that startup failure is retained separately
from the successful rerun with the compiler runtime on PATH.

The [107-file proof archive](../../results/proof/2026-09-08-usa-global-distance/README.md)
verifies run/source/native bindings and recomputes five distance/motion/input
comparisons without ROMs. Full BMPs remain local; archived GL receipts bind their
hashes, and contact sheets illustrate limitations. No USA menu option is promoted;
geometry/order/resource and attended acceptance remain open.

Runtime evidence is in `results/diagnostics/usa-global-20260908`. The bounded
projection/residency probes also retain independent guest-list events. Earlier
partial/control runs remain separate from the final full matrix.

## Follow-up

- Obtain geometry/texture/order comparisons at matching camera states before
  declaring the additional scenery correct. Test another level and a fresh drive.
- Examine why admission changes actual ADC sampling and game history; camera
  identity is a useful detector but not a complete traffic/physics oracle.
- Keep the legacy Draw Limit distinct until there is enough evidence to replace
  it with one clearly described global option. Do not silently migrate preferences.
- Continue Off Road and Exotica adapters independently. Off Road's table generator
  has now been identified exactly; its 63,680 clipping plane and vertex consumers
  still need separate profiling before a larger global extension.
