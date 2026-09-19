# Native FFB stop: isolated implementation and validation plan

The accepted personal native binary remains SHA256
`87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8`.
Its source is `4ac6a84b51b4ae549399c81ffe1b9346e2c04758`. The separate
`E:/Source/mame-ux` branch `codex/ux-native` adds the existing device-free worker
observer and the new user-controlled stop. It does not include the undeployed
extended-rendering lineage from `E:/Source/mame-src`.

Native `0913925c858` built successfully locally with eight jobs. No native successor
has been deployed or runtime-qualified. Source commits are pushed separately.
The frontend stop-marker changes are also staged, not yet deployed; the previous
Simple/Advanced frontend79a192b rollout remains the installed frontend baseline.

## Implemented behavior

- F8 and the new Esc-menu Stop FFB action latch this game process off. The worker
  also polls F8 while the game's process owns foreground focus, independently
  of rendering cadence. Existing Cheats and Exit indices remain unchanged.
- Stop acceptance and output updates are serialized. The worker cancels pending
  conditioning/impact history, stops all SDL effects and rumble, and retries
  failed cancellation. Future game motor writes cannot clear the latch.
- A durable marker requests Off on subsequent launches. Only explicit On in
  launcher settings removes it after the settings save succeeds. Failure to
  persist is reported separately from the current game's stop.
- Both native renderer menus show the stop state. The launcher provides fixed
  Close and Stop FFB controls on all settings pages. Recording/replay markers
  are private to their runs and cannot mutate the owner's saved preference.
- Strengths, force profiles and World menu/race-end pass-through are unchanged.

## Device-free proof being prepared

The previous observer skipped condition effects and actual rumble requests.
Its successor routes constant, spring, damper, friction and rumble through
logical sinks without loading SDL haptics. A bounded output journal records
accepted requests, latch and stop acknowledgment. Shutdown requires all logical
outputs cleared. These are software requests, never physical delivery receipts.

`--ffb-worker-stop-frame` explicitly configures a device-free test with positive
strength, legacy rumble, three20% conditions and40% rumble. Inherited stop
schedules and insufficient post-stop replay intervals are rejected. The ordinary
conditioning verifier remains in place; `verify_ffb_stop.py` adds independent
checks for all families active at stop, cancellation, nonzero subsequent game
requests, continued zero worker output, private persistence and journal identity.
An expired rumble request does not count as active-stop coverage.

Seven observer-policy tests, four stop-verifier tests (including corrupt evidence
and missing coverage), and eleven session-isolation tests pass. These do not
substitute for the pending native execution. Existing USA data locates the first
rumble candidate around frame3067; a prefix through3300 with stop3070 should
provide bounded positive and post-stop coverage, subject to actual journal checks.
No game slot is currently granted. Native build completion, binary/patch
attestation and a coordinated output-free runtime check precede rollout.

Build and attestation are now complete: candidate
`build/candidates/ux-0913925c858/vunit.exe` SHA256
`69bf482f396b13687541b564076d9fe9313469f7ec262afdb2979dcba37e414b`.
All137 patches in `patch/ux/0913925c858.patch` reconstruct source tree
`e5374f0cbdad80d2e678414911a0aedf4c5afe83` exactly frommame0286, including
the original DIJOYSTATE2 change. Personal87d and the separate renderer patch
series are unchanged. Local receipt is
`results/diagnostics/ux-20260919/native-build/0913925c858-export.json`.
The new freeze tool requires successful matching build status and rejects
overwriting an existing candidate/patch/receipt. **This export already ran.**
The3300-frame/stop3070 headless plan validates with literalFFB0 and a private
marker; it has not executed. Requested coordinated runtime slot remains pending.

Remaining acceptance includes live F8/menu delivery, persistence across the
actual launcher route and attended physical wheel behavior. Stable device
selection and ordinary calibration are separate open consumer UX requirements.
