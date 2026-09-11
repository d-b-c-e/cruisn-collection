# Four-game force-feedback normalization

Status: **near-term priority**, requested September 10, 2026. This supersedes
the earlier decision to defer cross-game tuning. Measurement and candidate work
are authorized; the current deployed tune remains the reference.

The goal is that **FFB STRENGTH 50 feels roughly equally strong in USA, World,
Off Road and Exotica on the same wheel and driver settings**. Normal cornering
should have comparable weight, with stronger, distinguishable collision cues.
The games can retain different textures and force character.

## Delivery checklist

- [x] Reopen B4 as near-term work and define the comparison criteria.
- [x] Audit the new Endprodukt Exotica plugin and our existing gain/polarity path.
- [x] Identify recordings for all four games and the gaps in their force evidence.
- [x] Run a preliminary offline algorithm sweep at 0, 25, 50, 80 and 100 with
  physical output disabled; retain its different-source/whole-drive limitations.
- [ ] Produce a reproducible baseline with explicit time windows and data-quality
  flags for each game, using the same candidate, profile and nominal strength.
- [ ] Label steady driving, left/right turns, car contacts, wall contacts and
  race-end/menu transitions; reuse existing footage where the event is visible.
- [ ] Compare candidate per-game gain/curves offline at 0, 25, 50, 80 and 100.
  Preserve raw signal detail before filtering and leave room for impacts.
- [ ] Add regression bounds for neutral, polarity, clipping, monotonic strength,
  effect lifetime and contact contrast, including malformed/stale trace rejection.
- [ ] Validate the candidate with short attended drives on the same wheel, then
  at least one different wheel family. Record wheel firmware/driver settings.
- [ ] Publish versioned game calibration and the evidence behind each value;
  carry reusable analysis/conditioning through `dbce-wheel-mod-toolkit` and its
  consumer checks. Promote a tested package separately from personal settings.

## What to compare

Use matched situations rather than averaging whole races. A rough Off Road
track and a straight USA section should not receive the same tune merely to
make their whole-drive RMS equal. Compare similar steering angles, steering
velocity, speed bands and contact classes. Keep vehicle, transmission, cabinet
DIPs, wheel range, profile, game revision and effective options in each receipt.

| Measurement | Purpose |
|---|---|
| Raw motor, post-adapter motor, shaped constant and final mixed output | Identify the stage that changes strength or discards detail |
| Time-weighted absolute-force percentiles and RMS in matched segments | Compare sustained steering weight without bias from write frequency |
| Time at the adapter/output ceiling and longest saturated interval | Detect flattened forces and long full-force pulls |
| Left/right force versus steering angle and velocity | Separate centering/damping strength from polarity errors |
| Contact peak, impulse area, rise time and recovery relative to nearby driving | Keep crashes distinguishable from ordinary turns |
| Zero/stop delivery, sign reversals and race-end dwell | Detect stuck output and characterize the reported oscillation |
| SDL submission success and physical wheel settings | Distinguish requested output from force actually delivered |

Use emulated time for deterministic game events and host time for the output
worker. Join them through explicit anchors; never silently treat the clocks as
interchangeable. Integrate irregular motor writes as held commands over known
intervals. Exclude unknown starts/ends, report coverage, and account for the
worker's hold/timeout and game gate when reconstructing final output.

The first proposed acceptance band is **within 15% of an agreed reference** for
median and upper-percentile sustained output in adequately covered matched
segments at strength 50. This is a provisional engineering target, to be checked
against attended feel, not an already measured result. Require both directions,
document sparse bins, and report disagreement rather than tuning to one aggregate.
Impact acceptance needs labeled contacts and a separate contrast check; a force
spike alone is not proof of a collision.

A percentage cannot guarantee equal torque across unrelated wheel bases. First
normalize the games on one fixed setup; keep device calibration separate so the
relative result carries to other bases. Do not infer Newton-metres from a product's
advertised peak torque without a suitable physical measurement.

## Implementation boundaries

Prefer explicit, immutable per-game calibration versions ahead of the common
strength control and shared conditioning. Keep calibration gain distinct from
device polarity, cabinet polarity, menu policy and the user's strength preference.
Do not rewrite existing profile versions or silently reset saved preferences.
Avoid automatic per-race gain that makes the same contact change strength as a
drive progresses.

Preserve World's current passthrough while measuring it; normalization does not
authorize silently reintroducing menu suppression. Keep Exotica's DIP-aware
polarity correction. A late strength multiplier cannot recover details already
lost to its early signed-byte clamp. Test an alternative mapping with sufficient
intermediate precision before selecting a new calibration. The impact detector's
raw input is separate from the constant-force path and needs separate evaluation.

Automated replays and algorithm comparisons use physical FFB off. Attended wheel
checks are necessary to accept feel and stability; software output alone cannot
close those items.

## Existing evidence and next measurement

| Recording | Available evidence | Gap |
|---|---|---|
| USA `my-drive` | Human inputs and host-time output trace; current 795fc default replay now supplies an emulated-time source trace with original input/pixel acceptance | No attended force acceptance in the original recording |
| World Germany, September 6 | Human drive, emulated raw/adapted trace, host output, strength 80 | Older candidate; no current gate trace; requires current replay and independent state labels |
| Off Road El Paso, September 10 | Human drive, source/gate/host output, strength 80 | Contacts and matched driving segments not labeled |
| Exotica Amazon, September 9 | Human drive, source/gate/host output; requested 80, effective 64, gain 800 | Contacts not labeled; current gain clips much of the motor range |

The existing `harness/analyze_ffb.py` executes the actual vendored shaper and
impact algorithms offline. It is a useful starting point, but its whole-trace
summary does not establish cross-game normalization or reproduce the full device
worker/gating contract. The analyzer now accepts both `wheel` and `wheel_motor`
host-output names; the two produce identical tested stages, including neutral.
Extend that evidence with segmentation, source identity,
time weighting and explicit coverage before choosing defaults. Legacy
`ffb_compare.py` is a USA/plugin transfer comparison with permissive parsing;
it is not a four-game acceptance gate.

See the [upstream audit and initial clipping measurement](reviews/2026-09-10-ffb-plugin-and-normalization.md).
