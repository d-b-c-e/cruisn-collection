# World 2.5 global-distance adapter — 2026-09-08

World 2.5 now supports the same optional global distance and independent scenery
lookahead controls as 2.4. The source launcher exposes Off / 2× / 3× and +0 / +8 /
+12 in Settings → Experiments → World. Fresh distance defaults remain **Off**;
saved family preferences are preserved. Selective Distant Scenery remains 2.4-only.
Widescreen and internal scale greater than one are still required by the launcher.

Source feature commit: `117e8fb`; native: `dae2569f79347d1260ecdf31a77b3afefd4e4721`.
The built source `E:/Source/mame-src/vunit.exe` SHA256 is
`f06a160b57c72737e89aedcc159f87cbe173c82620722ea109e84dcdffe70252`.
It is the binary used by the Stream Deck source launcher. The 125-patch export
reconstructs native tree `2f4f89c388ba380aa578036143049a723dcad00c` from `mame0286`.
Published v0.4.0 and its exact ZIP remain untouched. There is no new release ZIP.

## Implementation boundary

The two World versions share verified clamp and projection instructions, but
different reciprocal bases (`B66F` / `B665`), selected-model globals (`D4BF` /
`D4B9`) and pending thresholds (`D58C` / `D586`, consumer PCs `7B51` / `7B43`).
`native/world_distance.h` holds separate layouts and independently checked pending
instruction sequences. Wrong-revision program captures fail the native guards.

The virtual reciprocal tail remains host-owned; no adjacent guest object RAM is
overwritten. The guest performs list transfers and drawing. There is no model or
level allowlist. When the environment option is absent, these hooks remain absent.
The default renderer, telemetry producers and force algorithms are unchanged.

## Measured results

| Trial, full 6,000 frames | Extra far tests | Extended reciprocal reads | Compared with original drive | Emulation ratio |
|---|---:|---:|---|---:|
| Original 80,000 / +0 | 0 | 0 | All native inputs/images and sampled camera state match | 100.0002% |
| 2× / +8 | 342,430 | 8,140,818 | Inputs match; later camera/native images differ | 100.0024% |
| 3× / +8 | 345,770 | 8,217,625 | Inputs match; later camera/native images differ | 100.0000% |

Ratios cover frames 1800–5990 and describe emulation, not presentation latency.
All three runs complete their 42 requested GL captures. Candidate comparison FAILs
against the old route are retained, not relabeled as visual success. This synthetic
case includes attract scenes before entering Hawaii; it is not an attended full race.

The 2× candidate was separately recorded and replayed. All 6,000 input frames,
100 native reference images and 11 completed GL images (5480–5490) repeat exactly.
This establishes candidate repeatability, **not** original-route equivalence.

At equal +8 lookahead, 2× and 3× match all 100 native images and all 42 sampled GL
images. However, 33 of 4,191 camera samples differ, starting at 3486, and actual
ADC read timestamps differ while frame/value/PC sequences match. Keep that stricter
motion FAIL. There is no extra visible distance demonstrated by 3× in this sample.

The existing World 2.4 global 2× Germany candidate also replays successfully with
this build. Native helper tests pass against both real captured programs, including
wrong-revision and damaged-instruction rejection. 132 Python tests pass, and the
World 2.5 menu was inspected from an offscreen preview without saving settings.
All seven default driving regressions pass, including actual telemetry/independent
memory checks, World force passthrough checks and Exotica's 21 completed 4K GL
comparisons. Their bounded emulation ratios are 99.9731–100.0035%. All four CI jobs
at `b720b98` pass (run34199270158); Windows, Linux and local agree on all229 source
inputs, identity `85ad5a17558ffc18d7f3d8eac431151e6c7582ba6359bd3b8ad3392e573ee152`.
The 67-file checkpoint archive recomputes the distance and USA residency counters
and checks source/native bindings. These are component gates, not a new frozen
package release gate. No emulator remains running at the checkpoint.

## Product limits and next work

This is an optional adapter, not a claim of artifact-free rendering or reduced
pop-in on every level. No new geometry/order/resource acceptance has been completed
for extended 2.5 scenes, and no attended drive has accepted its changed route/feel.
The World New York 3×/+12 finish crash and black flashing remain unresolved; +12
was not exercised in these new 2.5 driving trials. World FFB tuning stays deferred.

The next useful cross-game experiment is USA's verified pending admission window:
see [the residency trace](2026-09-08-usa-residency.md). Off Road has a separate
floating-point far test and ROM reciprocal table. Exotica's sampled far test rejects
nothing, so its earlier activation and CPU visibility logic need investigation.
Do not transplant World addresses or advertise larger multipliers without evidence.

Evidence: `results/diagnostics/world25-global-20260908` and
`results/proof/2026-09-08-world25-distance`. The archive preserves failed route and
motion comparisons, invocation/binary bindings and recomputable native counters.
All automated runs disable physical force; original recordings remain unchanged.
