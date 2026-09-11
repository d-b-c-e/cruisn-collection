# Exotica FFB plugin audit and normalization starting point

Checked September 10, 2026. No force tune, physical output policy or deployed
binary changed in this audit. The maintainer has now made four-game normalization
a near-term priority; see the [delivery checklist](../FFB-NORMALIZATION.md).

## Upstream identified

The relevant update is Endprodukt's **FFBPluginRacerMAME 1.996**, released
September 6. It adds Exotica motor support, per-game gain, direction correction
and GUI settings. This is a reference implementation; our runtime continues to
use its built-in SDL path. [Release notes](https://github.com/Endprodukt/FFBPluginRacerMAME/releases/tag/1.996).

Pinned source: `7e95f65cab18109cda6b6d0da8ab4c210f3c9c12`.
The Exotica handler accepts `wheel` or `wheel_motor`, interprets the signed byte,
treats -128 as neutral, applies configurable gain, clamps to ±127 and reverses
direction for its recommended cabinet configuration. Its 400% default differs
from our 800% adapter gain. This is motor-signal processing, not new collision
telemetry. [Game handler](https://github.com/Endprodukt/FFBPluginRacerMAME/blob/7e95f65cab18109cda6b6d0da8ab4c210f3c9c12/Game%20Files/MAMESupermodel.cpp),
[direction fix](https://github.com/Endprodukt/FFBPluginRacerMAME/commit/c3f2ea699d8cd097a0fb1b414ba9486fac863eb6).

Its persistent constant-effect helper updates parameters while running and only
starts when its running flag is false; it stops on near-zero input. Our
`mvffb::apply` currently updates and issues RunEffect on each nonzero application.
That difference is worth testing for output continuity and device compatibility;
it is not yet evidence of a defect or a fix for oscillation. Audit return codes,
reconnect and stop/restart behavior before adopting it.
[Effect helper](https://github.com/Endprodukt/FFBPluginRacerMAME/blob/7e95f65cab18109cda6b6d0da8ab4c210f3c9c12/DllMain.cpp).

## Comparison with this project

Our `native/motor_signal.h` already handles neutral before gain and separates
Exotica's active-low cabinet polarity from device inversion. Preserve that
DIP-aware behavior rather than copying a fixed sign reversal. The Exotica gain
in `harness/run_rig.py` is 800; it was increased when an earlier per-game strength
setting was removed. The recorded Amazon session requested strength 80 and used
64 after the current Exotica trim. These are distinct stages.

The current shared profile is `cruisn-vunit@2`. The launcher percentage is
converted to the toolkit's different strength scale before conditioning. Any
normalization work must trace effective values through those stages and verify
that strength is applied once. The historical comments describe a tuning choice,
not a measured four-game calibration.

## Initial measured clipping

The new native-lifetime Amazon control provides 7,476 exactly paired source/gate
events. All observed adapted values match the current 800% integer-gain/clamp
formula. Restricting to the trace's enabled driving gate gives 5,160 events,
including 4,162 nonzero commands:

| Adapter gain | Clipped nonzero events | Fraction | Distinct nonzero adapted values |
|---|---:|---:|---:|
| Current 800% | 1,885 / 4,162 | 45.29% | 32 |
| Offline 400% counterfactual | 1,103 / 4,162 | 26.50% | 64 |

At 800%, a raw magnitude of 16 already clips; at 400%, 32 clips. A later reduction
in wheel strength scales these flattened commands but cannot recover their
differences. This is a concrete reason to investigate where normalization gain
belongs and whether a wider intermediate representation is needed.

These are **event-weighted command statistics**, not time at full wheel torque.
The 400% row is an offline counterfactual before strength, filtering and device
delivery, not an accepted replacement tune. No contacts are labeled here. Our
enhanced impact path observes raw motor data separately, so this finding applies
directly to constant-force detail and does not prove that clipping caused every
weak collision report. Gate classification is specific to this recorded Exotica
configuration; World's passthrough cannot be classified the same way.

Local receipt: `results/diagnostics/exotica-amazon-20260909/ffb-upstream-gain-analysis.json`.
Source trace SHA256 `6bfbdf05d16252bb655a39259429225828993b3fc5b73d054b63086f83636336`;
gate SHA256 `10bc08c39d30e4e147e5f91686495b8d507ac92b3a0e80774dc6fe00f31374bb`.
Raw traces remain local. Public statistics are a receipt of that analysis, not
an independently rerunnable claim without those traces.

## Next

An initial offline sweep now executes 20 cases: four game traces at nominal
0/25/50/80/100. Exotica's current trim is applied explicitly (nominal50 becomes
effective40); other games use effective50. Zero strength produces zero output
and every case stays within its effective strength ceiling. The USA input comes
from the accepted current-candidate replay of `my-drive`, World and Off Road
from their human recordings, and Exotica from the current Amazon control.
Thus source builds are not yet common across all four.

A subsequent **common-candidate renewal is complete**: USA, Germany, El Paso
and Amazon all supply accepted source traces from native795fc with physical FFB
off. The fresh El Paso replay preserves all9,644 input frames/native pixels;
Germany's separate retry preserves9,269. All20 offline strength cases pass again,
with source CSVs and all five output-stage files per game byte-identical to the
initial baseline. Different courses and unlabeled situations still prevent a
cross-game normalization claim.

These runs include menus/boot and simulate the shaper without the full game
gate, worker timeout or device. They are algorithm baselines, not normalized
wheel-force acceptance. Between the first and last captured Exotica writes,
the held adapted command is at magnitude127 for23.77% of elapsed emulated time.
That whole-trace time statistic has a different denominator from the earlier
driving-event45.29%; neither measures time at physical full force. The other
traces reach no magnitude127, but can reach the output ceiling at126, so this
comparison alone does not establish their headroom.

Local command/receipt:
`results/diagnostics/exotica-amazon-20260909/ffb-four-game-baseline.py` and
`ffb-four-game-baseline/report.json`. The latter explicitly marks normalization
and matched-segment/common-source acceptance false. Raw stage traces stay local.

The renewal is `ffb-four-game-current-baseline/report.json`, generated with
`--current`. It marks common native source true, matched segments and normalization
false. [Public receipts](../../results/proof/2026-09-10-ffb-baseline/README.md)
verify hashes/consistency only. Game/device polarity is also outside the offline
shaper simulation; use the separate polarity checks before accepting signed force.

The sweep preparation also exposed an offline-analyzer compatibility bug:
`wheel_motor` rows were ignored while the older `wheel` name worked. The new
native regression fails on the previous executable and passes after accepting
both names, with identical output stages and reserved-neutral behavior. Existing
raw-versus-adapted impact tests still pass. This changes analysis only, not the
game or SDL output.

Use the completed common-candidate baseline to compare matched segments at
nominal strength 50. The [new interval analysis](2026-09-10-ffb-condition-coverage.md)
identifies OCR speed and sparse turn coverage that must be resolved first.
Retain source, adapter,
shaper and output metrics separately; label actual contacts and measure recovery.
Choose a versioned per-game calibration from those results and validate it with
attended wheel checks. Keep menu-policy changes and persistent-effect experiments
separate so each can be evaluated and backed out independently.
