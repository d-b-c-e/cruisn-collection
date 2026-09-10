# Exotica fade reconstruction and future-rendering cost

The new future renderer has a measurable CPU cost even without expensive image
readbacks. Correct original alpha updates are also now available as a standalone
helper. Neither result makes the development candidate ready for deployment.

## Performance isolated from heavy captures

These runs use native `9edda839517`, the original complete Amazon recording,
8,860 input frames, requested 3840×2160 output and the same rendering fixes.
They retain ordinary session snapshots, motion traces and summary timings, but
disable completed GL captures, model dumps and private-buffer readbacks.
There is no new pixel-based 4K acceptance from these performance runs.

| Mode | Whole-run emulation speed |
| --- | ---: |
| Original renderer | 99.99% |
| Original scene duplicated into the private wide-depth target | 99.99% |
| Prepare/validate/upload future 3×, without drawing it | 90.77% |
| Draw and display future 2× | 94.69% |
| Draw and display future 3× | 90.79% |
| Repeat future 3× | 90.23% |

All six preserve the original 7,060 camera samples and 21,180 actual ADC reads,
including their emulated timestamps. Both 3× runs and the 2× run match their
earlier dense-presentation geometry across all 6,953 scenes. This establishes
route and geometry consistency, not full-speed acceptance. A bounded repository
search overlapped the repeat; treat its timing as corroboration rather than an
uncontended benchmark. The first 3× and observation runs independently establish
the performance gap.

The 3× observation path is already slow before future drawing. Duplicating only
the original geometry remains at full average speed. These comparisons point
toward CPU scene preparation and packet handling as substantial costs; they do
not establish a single root cause or prove that GPU drawing is free.

In the first 3× drawing run, mean/p99 scene assembly is 1.828/5.107 ms. Ordered
geometry hashing costs 0.641/2.085 ms. Material handling, including the future
packet construction and queue submission, costs 0.761/2.662 ms. These timings
overlap with some finer-grained timers and must not all be added together.
Initial material upload also produces a large isolated cost. Full average speed
and consistent frame pacing remain separate acceptance requirements.

The native `zeus-depth-mirror.csv` field `mirror_us` is cumulative submission
time. The first four local summaries incorrectly treated it as per-event time;
their files are retained. A separate corrected extraction differences successive
values. This correction does not change recorded emulation speeds, route checks
or the actual per-event assembly/material timings. Submission timing is not GPU
execution timing.

## Original fade update

The standalone `native/exotica_fade.h` implements the bounded render-field update
previously observed in the game's original fade routine. The independent Python
verifier uses a separate byte-lane expression. Both match all 489 retained
original writes: 472 continuing updates and 17 completions, with increment eight.
The helper is not linked into MAME and does not change guest memory or rendering.

The source alpha advances over time after original admission; reaching 247 ends
the fade. This is not a distance-only formula. Future descriptors often retain
the initial source-alpha value of eight, so simply decoding more descriptors
does not make their scenery strongly visible.

The bounded canonical Lua probe checks the routine signatures through direct
RAM access, captures the actual writes and declares its frame windows and event
budget. Native/Python tests cover completion boundaries, preserved unrelated
bits, rejected inputs and incomplete/corrupt evidence. Fresh probe/control pairs
now pass on Hong Kong (6,000 inputs each) and the complete Amazon drive (8,860
inputs each). All preserve the original camera/actual ADC values and timestamps.
Each pair matches all 21 completed 3840×2160 images; all 84 captures complete.
Hong Kong also matches the earlier 21-image control.

The promoted probe observes 489 Hong Kong updates and 2,539 Amazon updates. The
final native helper and independent Python expression match all 3,028 writes,
including 103 completions. These windows do not prove a full object lifetime or
the host-to-original handover.

Two failures are retained. The first post-replay analyzer invocation lacked its
MinGW runtime directory; setting its PATH allowed verification of the same
retained replay. A separate malformed-input test exposed acceptance of a trailing
incomplete operand row. The analyzer now rejects it. The process-level check
passes 633 independent fade steps and ten malformed/domain/budget cases.

The final local suite passes 351 Python tests with no skips, 48 native test
programs and the GPU checks across 136 commands. Its 510-file source identity is
`f21d7e7834f14b1c67f750bdae9b0e6ce3edf41773f9a0f47a9e5519c0a7a5c9`.
MAME itself remains the existing `9ed` candidate; this standalone helper does
not renew the seven default-game regressions.

## Rejected optimization

An isolated cache of model texture-format validation preserves exact geometry
and instances across five captured scenes, with 100 assemblies per batch and
alternating old/new runs. Measured changes range from approximately 2% faster to
1% slower, without consistent benefit. The experiment stays local and does not
change the renderer. More useful targets are packet serialization, repeated
projection work and the cost of full-frame diagnostic fingerprints.

## Next implementation work

1. Connect the verified fade updates to actual section allocations and check
   identity through reuse, membership changes and the original fade completion.
2. Give future scenery a verified fade lifetime and identify its corresponding
   original object at activation. Keep the host copy through the original fade
   only when identity, material ownership, depth and blending are verified.
3. Reduce measured repeated model validation, serialization and unnecessary
   allocation. Compare exact geometry/material packets and repeat the quiet
   performance runs before claiming improvement.

Do not force all future polygons opaque or bypass correct foreground depth to
manufacture a larger 3× difference. Broader material lifetime, handover, other
tracks and default regressions remain open. Personal Stream Deck and the public
release remain v0.5.0; physical FFB stays disabled in automated work.

Local evidence is under `results/diagnostics/exotica-amazon-20260909`, with
`future-performance-*` runs and corrected `future-performance-timings-*` output.
Raw resources, captured game images and write operands remain local.
The [public archive](../../results/proof/2026-09-10-exotica-fade-performance/README.md)
checks scalar-receipt and source/hash consistency. Actual replay, fade writes,
pixels, native builds and GPU execution remain hash-bound receipts there.
