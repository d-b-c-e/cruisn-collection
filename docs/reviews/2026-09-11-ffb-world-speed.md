# World speed evidence for force normalization

The World Germany recording now supplies verified memory speed for offline FFB
comparison. This closes the OCR coverage gap identified in the first condition
analysis. It does not change runtime telemetry, force defaults or the installed
build, and it does not establish equal force across games.

## What was verified

World 2.4's player update reads the C31 float at player +42, multiplies it by
**0.489990234375**, truncates it to an integer, and stores that value at EBBD.
The MPH HUD reads EBBD. The multiplier comes from the actual instruction operand;
it was not fitted to OCR. Addresses are C31 word addresses and apply only to the
checked World 2.4 layout.

The bounded, read-only `harness/probes/world24_speed.lua` checks those producer,
HUD and lifetime instructions, records actual writes and MPH reads with emulated
timestamps, and samples state/player/speed at frames 1000..9269. It retains errors
from memory callbacks and rejects incomplete captures. All raw game evidence
remains local.

On the same frozen native795fc executable used for the other FFB baselines:

| Check | Result |
|---|---|
| Full Germany replay | All 9,269 inputs/times and 154 native snapshots match the original |
| Actual speed producer | All 3,486 conversions exactly match the independent C31 calculation |
| Actual MPH HUD | 3,656 reads match the latest observed player/speed write; 126 earlier reads have no captured writer and are excluded |
| Independent earlier memory trace | All 8,270 state/flags/player/raw-speed samples match |
| Existing force and telemetry | Source, gate, speed and drivetrain CSV files are byte-identical to the accepted earlier native795fc replay |
| Physical output | Disabled |

The producer writes occur in state 4. State 5 can still read the old displayed
speed, which is why a valid-looking number alone must not imply active driving.
The analyzer requires state 4 and its driving flag, the observed player owner,
and a fresh producer after an observed inactive interval. It retains the actual
write time instead of refreshing age each time a frame samples the same number.
The force comparison's existing 100 ms speed-age limit still applies.

## Harness and resulting coverage

`harness/world_speed_evidence.py RUN --output NEW_DIRECTORY` validates the exact
canonical collector, completion/counts, producer arithmetic, consumer holds,
clock joins and state transitions. It emits analysis-only memory speed samples.
`harness/force_segments.py --world-speed-probe` uses them for World and preserves
their receipt in the four-game report. Missing or mismatched evidence fails;
there is no automatic fallback to OCR. Other games use their existing sources.

World now provides **117.248 seconds** of eligible driving conditions with OCR
excluded. USA remains 40.136 seconds, Off Road 117.076, and Exotica 89.298. The
new data still produces only two shared bins with at least two seconds per game:
center/steady and negative-medium/slow input at 40–60 m/s. The World turn bin
grows to 4.471 seconds, but its longest continuous fragment is only 0.259 seconds.
There is still no adequately covered matching positive-direction turn bin.

This is progress in measurement, not a justification for selecting gains. Next:
verify steering/actual-ADC comparability, label clean cornering and contacts,
reconstruct final conditioning, then fit a versioned strength-50 candidate with
impact headroom. Attended common-wheel acceptance remains necessary. World menu
passthrough and Exotica DIP-aware polarity remain separate from normalization.

All **383 Python tests pass with no skips**, including eight new tests covering
C31 units, incorrect arithmetic/owner/PC/mask, missing collector evidence,
unsupported HUD branches, clock/order errors, unknown writers, stale samples
and inactive transitions. Source identity:
`cfbe0d71921f12fe155ddffb9673e86ae9168331556205546bf6f1f87be24169`.
No MAME build or new native/GPU suite was needed for this analysis-only change.
World 2.5, metric display and physical force are not accepted by this capture.

LOCAL: `results/diagnostics/exotica-amazon-20260909/ffb-world-speed-producer`,
`ffb-condition-world-memory-final` and `ffb-world-speed-python-checks`.
[Public receipts](../../results/proof/2026-09-11-ffb-world-speed/README.md) verify
source/hash and receipt consistency; they do not rerun the raw game evidence.
