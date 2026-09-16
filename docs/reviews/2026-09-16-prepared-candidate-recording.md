# Fresh recordings using the exact host candidate

The recorder can now use the same qualified continuous3x preset as replay.
Previously, attended recording exposed the older guest-distance experiments;
this gap made it difficult to obtain a useful new course recording with the
actual host scenery enabled.

`replay.py --prepare-only` validates the existing case, frozen inputs and ROMs,
all option guards, display selection and candidate files, then saves a hashed
launch plan. It starts no emulator. Its report remains unexecuted and not passed.
`--no-inherited-gl-captures` explicitly removes old screenshot schedules before
applying any new requested capture interval.

`record_prepared.py` checks that plan and its unchanged initial state, ROMs,
candidate and adjacent dependencies. It freezes a separate live-input case,
removes playback and finite-stop arguments, preserves recorded bindings and
starts an external emulation clock. Physical FFB and external telemetry stay off.
The plan cannot silently bring along an old capture schedule, probe or disabled
input devices. Neither source recording nor personal launcher configuration is
modified. A prepared recording performs only the read-only `-listxml` query;
gameplay starts only without its `--prepare-only` option.

After a live drive, recording validity and native runtime qualification are
reported separately. The latter uses the actual recorded extent and the existing
strict bootstrap, shutdown, quiet journal and failure checks. It never calls the
new route a deterministic replay or a visual pass.

Three focused tests pass: removal of all playback/stop arguments with retained
bindings; changed dependencies, unsafe force/telemetry/capture plans and disabled
devices reject; preparation freezes a live case without starting gameplay or the
clock. Syntax checks pass. The receipt helper independently reproduces the saved
Exotica and USA normal-close qualification, without replaying either game.

Actual preparation reaches all five ROM profiles. USA, World2.4, Off-Road and
Exotica also freeze live cases with `-record`, no `-playback`, SNAP_STOP0, clock
flush6 and FFB0. **No attended drive was launched.** The existing World2.5 source
is synthetic with input devices disabled, so it correctly rejects live recording.
A real World2.5 input configuration is required for that particular parent.

The first matrix attempt is retained as FAIL: the World2.5 source also inherited
a5480..5490 screenshot schedule. Explicitly clearing that schedule exposed its
disabled-device condition; neither guard was relaxed. The corrected matrix
reports five valid plans, four live-recordable cases and the explicit World2.5
restriction. It is not a five-gameplay-run pass.

Local evidence is under `results/diagnostics/race-transitions-20260916`:
`all-recording-plans-qualified.json` (initial FAIL),
`all-recording-plans-qualified-v2.json`, `*-recording-plan-v2` and
`*-live-recording-preflight-v2`. The Exotica plan is ready for a contrasting
open-course drive when the user returns; no new recording has been claimed.

Native remains f0b4db1f25d; personal87d/publicv0.5.0 are unchanged. This closes a
diagnostic recording usability gap, not product FFB, machine-reset, visible outer
distance or release acceptance. The command examples are in
[Diagnostic replay](../DIAGNOSTIC-REPLAY.md#record-a-fresh-drive-with-the-host-candidate).
