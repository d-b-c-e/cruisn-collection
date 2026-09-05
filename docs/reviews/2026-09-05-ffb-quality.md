**Force-feedback quality and distinguishable collisions — review proposal, 5 September 2026**

The user's inability to distinguish crashes and contact with other cars should not be treated only as a matter of taste. The current integration contains objective defects and information loss that can weaken or confuse those cues. Repair and measure those first; then use controlled driving comparisons to choose the preferred response.

This document proposes future work. No force was sent to hardware during the review. Source references and scope are recorded in the [main assessment](E:/Source/cruisn-collection/docs/reviews/2026-09-05-assessment.md).

**What the current system actually does**

| Stage | Current behavior | Consequence |
|---|---|---|
| Game output | Original signed motor byte, with driver-side gain/slew/clamp where configured | A motor command is not a semantic collision event |
| Exotica adapter | Launcher defaults to 800% gain; driver clips back to ±127 | Early saturation destroys distinctions between commands |
| Normalization | `midv_ffb_write` maps magnitude against 126 to ±32767; applies direction | Global strength is deliberately absent at this stage after the toolkit migration |
| Transport | Atomic latest value plus notification; worker reads the latest command | Intermediate commands may be coalesced if the worker falls behind |
| Main force | Shared `Shaper::shape(input, 0, dt, false)` | Uses conditioning only; no shared force-model collision logic or explicit event flag |
| Extra cue | Changed-force history detects a high recent rise and calls generic SDL rumble | Heuristic depends on motor history, gain assumptions, and device rumble implementation |
| Device output | Infinite constant effect, optional condition effects, update/run calls | Requested values alone do not establish accepted effects or delivered torque |

The shared toolkit extraction is useful. The defects cluster at the boundaries between the remaining local detector/worker and the new shaper. The [worker and detector](E:/Source/mame-src/src/mame/midway/midvunit_v.cpp:2133) are the primary integration point to review.

**Confirmed problems in the supplementary collision cue**

1. The detector normalizes against `32767 × global strength`, although its input now uses the full unscaled ±32767 range. At strength 80%, the nominal 80% arrival and 40% rise thresholds become 64% arrival and 32% rise in raw normalized input. At strength 40%, they become 32% and 16%. Changing volume changes what qualifies as a collision.
2. Its history records changed, nonzero values only. Zero does not become a baseline sample; an unchanged low force is not refreshed. After the earlier history expires, an isolated jump to a high value can insert only that new high value. The computed rise is then zero and the extra cue is missed.
3. Rumble amplitude is `min(1, arrived) × rumble setting`. It does not pass through the shared global-strength scaling. The native constant effect and supplementary cue therefore do not obey one strength contract. The launcher's “FFB off” gating is a separate mechanism; this finding does not claim that normal off selection necessarily leaves rumble enabled.
4. A motor stop immediately calls rumble stop. A short motor pulse can terminate the intended 120 ms cue early. The 250 ms cooldown can also suppress closely spaced contacts; that may be desirable debouncing or a missed second collision, depending on the event.
5. The return value from `SDL_HapticRumblePlay` is ignored. Initialization success does not establish that every later burst was accepted. SDL documents a negative return on failure in [SDL_HapticRumblePlay](https://wiki.libsdl.org/SDL2/SDL_HapticRumblePlay).

The following were evaluated with an in-memory transcription of the current branch logic, not a physical wheel or the compiled worker. Values are normalized motor magnitudes. Rumble setting is assumed to be 100%.

| Input case | Strength 40% | Strength 80% | Strength 100% |
|---|---|---|---|
| Zero, then isolated full-scale step after expired history | No supplementary cue | No supplementary cue | No supplementary cue |
| Rise from 0.10 to 0.40 in 17 ms | Full-amplitude supplementary cue | No cue | No cue |
| Documented 25, 40, 67, 80, 103, 113, 126 byte ramp, 17 ms samples | Cue at +34 ms, amplitude 1.0 | Cue at +68 ms, amplitude 1.0 | Cue at +68 ms, amplitude about 0.818 |

These cases establish gain dependence and a missing baseline. They do not establish that the entire force disappears: the main constant-force path continues to receive the motor signal.

**The generic SDL rumble helper is a questionable wheel-impact primitive.**

The local DLL reports version 2.32.10. In the matching [SDL source](https://github.com/libsdl-org/SDL/blob/release-2.32.10/src/haptic/SDL_haptic.c), the generic helper chooses a sine effect when supported, sets a 1,000 ms period, and uses Cartesian direction. This project requests 120 ms of that effect. That is 0.12 of a cycle, rather than a deliberately specified sharp wheel transient. Devices using SDL's left/right fallback have a different effect again.

This source behavior is established; the actual effect accepted by this wheel and its perceived contribution were not measured. Log the selected effect type, direction, duration, period, capabilities and API result. If an enhanced collision cue is wanted, explicitly define its wheel-axis waveform or mix a controlled transient into the main force, with a common output budget. Do not rely on the word “rumble” to imply a consistent mechanical sensation across devices.

**Exotica loses headroom upstream.**

The current [driver multiplication](E:/Source/mame-src/src/mame/midway/midzeus.cpp:739) yields:

| Raw byte magnitude | After ×8 and byte clamp |
|---:|---:|
| 10 | 80 |
| 15 | 120 |
| 16 | 127 |
| 30 | 127 |
| 46 | 127 |

An ordinary spring response and an impact can become indistinguishable before the shared shaper sees them. Downstream gain does not undo clipping. Record the original byte, move calibration into a higher-precision signal stage where feasible, and quantify how often each stage saturates. Preserve enough output range for a contact onset to differ from sustained cornering resistance. Do not merely boost every force until it is noticeable.

**Event preservation and scheduling are incomplete.**

The shared shaper has an input-jump bypass, but the documented collision ramp comprises several smaller changes. A bypass threshold of 0.6 per update will not classify that ramp the same way as the 250 ms rise detector. The integration always passes `is_event=false`; the detector's decision never informs the shared shaper. Profile fields belonging to the shared force model do not affect this call path at all.

The worker's timeout still depends on legacy `s_smooth_ms`: 4 ms when nonzero, otherwise 20 ms. Smoothing loaded from a profile can be nonzero while that variable stays zero. Normal motor writes wake the worker at roughly game cadence, so this is not a claim that every update waits 20 ms. It is a mismatch between the configured chain, scheduler, and fixed-cadence conformance assumptions. Measure actual wake intervals and input age, then specify a deliberate output clock using the resolved profile. Exercise irregular intervals in replay.

For short transients, retain input sequence numbers and timestamps, or a separate event queue. A latest-value mailbox is reasonable for some continuous signals but cannot promise to preserve every event during a stall.

**What “good” should mean**

Use three separately reported categories. There is no credible universal score that collapses them into one number.

| Category | Questions that can be answered | Acceptance approach |
|---|---|---|
| Signal and integration correctness | Correct sign? Correct scaling? Events preserved? Valid timing? Stop confirmed? | Deterministic checks with exact expected behavior or declared numerical tolerance |
| Event usefulness | Can we detect a contact onset and distinguish it from ordinary driving? | Labelled driving cases, detection errors, onset latency and output headroom |
| Driver preference and device response | Is it informative, comfortable, controllable and enjoyable on this wheel? | Repeatable supervised drives and blinded preset comparisons, recorded by device |

For this arcade collection, “good” need not mean synthesizing a modern simulation's aligning torque. Preserve a documented baseline interpretation of the cabinet motor signal, and make enhanced impact cues an explicit product choice with its own acceptance evidence.

**Measurements to collect**

Every output trace should correlate emulated frame/time with host monotonic time and include raw motor, adapter result, normalized input, event decision/reason, pre/post smoothing, pre/post limiting, final requested force, API result, selected device/effect, and any output drop/retry. Record condition effects and supplemental cues too; the constant-force value alone is not total requested feedback.

Track these metrics per scenario and wheel setup:

- Event precision/recall against labelled contacts, including false cues during normal steering. Allow a declared timing tolerance for human labels.
- Delay from contact evidence to event decision and to successful device submission; report percentiles and worst cases separately from physical response latency.
- Peak force, clipping occupancy, limiter activity, rise time and settling time at each processing stage.
- Output update interval, stale-input age, coalesced samples, effect errors, and time to acknowledged stop.
- Oscillation during specific controlled conditions such as stationary hands-off or steady hold; do not classify every sign reversal during ordinary steering as instability.
- Subjective recognition of car hit, wall impact, wall scrape, rough surface and sustained cornering, plus comfort and controllability.

An API acknowledgment proves a software operation succeeded, not that a particular torque was delivered. Wheel position likewise does not measure torque. Where the device offers suitable telemetry, include it with its limitations. Otherwise describe traces as requested/accepted force and use controlled human observations for mechanical behavior.

**Build a collision corpus instead of tuning to one trace.**

Record isolated low-speed car contact, high-speed contact, left/right glancing hits, a sustained wall scrape, rapid successive hits, landing after a jump, ordinary hard steering without contact, and stopping after each. Include contacts during both low and already high baseline force. Use multiple tracks and all four games, and retain a held-out set of drives so thresholds are not merely fitted to the examples used to choose them.

A marker button should retain several seconds before and after the observation. A human “hit here” marker is useful evidence, but button reaction delay makes it an approximate label. Correlate it with video and any verified game collision flags or impulses.

Investigate real game event sources before relying indefinitely on motor magnitude: collision handlers, contact flags, damage/state changes, or verified physical impulses. If a game exposes no reliable source yet, keep a clearly identified heuristic with a confidence/reason field. A hard turn and a crash can produce overlapping motor values; no clever scalar threshold can always separate them.

**Suggested signal architecture**

Maintain the original motor signal as a named channel. A game adapter may additionally emit a verified event with type, onset, severity and direction when known. A device-independent stage conditions sustained force and constructs optional event envelopes. A mixer allocates headroom and applies common user gain/limits. The backend owns device capability selection, output scheduling, acknowledgment, recovery and stopping.

An impact should preserve a clear onset; a sustained scrape should not repeatedly restart a full collision burst on every write. If ordinary steering and the event exceed the output budget, define the prioritization explicitly and log limiting. Consider a single composed steering-axis signal for backends where combining independent effects has unpredictable clipping, while retaining native effects when capability tests support them.

Separate profile responsibilities:

| Profile layer | Examples |
|---|---|
| Game interpretation | Motor encoding, known event source, calibrated spring/motor relationship |
| Device calibration | Direction, usable range, rotation, available effect types, stable device identity |
| User preference | Overall strength, road detail, optional impact emphasis, comfort limits |

Record toolkit implementation revision as well as profile ID and resolved contents. A profile with the same name can behave differently when gain order, bypass semantics, or scheduling changes.

**Cross-wheel evaluation**

Begin with the user's Moza setup, then deliberately cover at least a gear-driven, a belt-driven and a direct-drive wheel when hardware is available. Record model, firmware, vendor settings, rotation, rim/inertia where relevant, game steering curve, backend and resolved profile. Equal percentages do not mean equal torque or equal bandwidth.

Choose a stable baseline for each setup. Compare a small number of clearly different candidates, preferably with preset identities hidden during the drive. Ask for event recognition and control quality before overall preference. Change one signal decision at a time and retain both traces. User preference can choose the final response, while the objective gates prevent a preferred preset from silently breaking stop behavior, scaling or event preservation.

No automated graphics replay should move the wheel. Input playback reproduces the game-visible steering trajectory; it does not reproduce the driver's closed feedback loop under a new force profile. Recorded signals can evaluate force algorithms without hardware. Supervised wheel evaluation remains a separate activity.

**Implementation order and gates**

| Step | Completion evidence |
|---|---|
| Repair cleanup ABI and stop accounting | Fake-backend failure cases pass; supervised lifecycle checks distinguish release success/failure |
| Preserve raw input and force-stage diagnostics | One run explains every transformed value, cue decision and output result |
| Repair history and gain contract | Silence-to-hit, long steady baseline, repeated hit and strength-sweep cases behave as specified |
| Specify supplemental effect | Actual effect parameters and capability path are visible; all force channels obey the output budget |
| Remove avoidable early saturation | Exotica raw distinctions survive until an explicit final limiter; clipping is quantified |
| Connect reliable events to shaping | Verified collisions retain onset through smoothing; ordinary driving does not falsely become an event |
| Evaluate devices and preferences | Held-out drives and supervised comparisons support the chosen defaults |

Do not declare the issue resolved because a trace contains large force values or because one driver reports “stronger.” Resolution requires distinguishable events during repeatable driving, without excessive false cues or degraded steering control.
