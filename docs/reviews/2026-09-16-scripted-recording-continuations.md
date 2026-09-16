# Scripted continuations after a recorded drive

`harness/extend_input.py` appends scripted inputs to an existing supported MAME
INP without changing any original input row. It supports USA, both World
revisions, Off-Road and Exotica. This enables autonomous race/menu transition
testing after a useful human drive; it is not a replacement for an attended
recording of a new course or good driving through a visual defect.

The output is explicitly a stimulus with a recorded prefix and synthetic tail.
It must be recorded through MAME's own INP writer before becoming a new test
case. The original case is never overwritten. Provenance records source and
stimulus SHA256, the original decompressed input hash, row/frame counts and the
first synthetic row. A successful byte-generation check alone does not establish
successful menu navigation, a second race, replay determinism or visual quality.

The original header and every original decompressed row are retained exactly,
including recorded speed metadata. The tail uses the game's port layout and
last recorded defaults and analog sensitivity, releases digital buttons, and
requires explicit initial values for all pedal and wheel axes. Its first analog
interpolation starts from the actual last recorded accumulator. Later keyframes
retain normal MAME interpolation. Exotica's distinct first-refresh rounding is
preserved when generating the absolute continuation timestamps. Unsupported
layouts, incomplete rows, nonuniform recorded timing, ambiguous axes and invalid
tail ranges are rejected. Total length is bounded at36,000 frames.

Example, with paths chosen for the recording being tested:

```powershell
python harness/extend_input.py <case>/record/input/session.inp <tail-scenario.json> --output <new-stimulus-directory>
```

Scenarios use the existing synthetic-input schema. `frames`, button pulse ranges
and analog keyframes are relative to the first appended row. The output contains
`stimulus.inp`, the exact scenario and `provenance.json`.

Two focused tests cover all five supported layouts, exact original bytes,
first-tail and subsequent analog interpolation, final-row button pulses, invalid
axis/frame selections, incomplete data and a timing discontinuity after the seed
interval. Saved-recording preflight also preserves every byte of the actual
USA5,012, Germany9,269, World2.5 6,000, Off-Road9,644 and Amazon8,860-frame inputs
when appending2,400 scripted frames. Their source hashes match their manifests.

Local preflight: `results/diagnostics/world25-roads-20260914/input-extension-preflight`.
The first live experiment is an Amazon prefix followed by menu-selection pulses
and brief acceleration, under `results/diagnostics/race-transitions-20260916`.
MAME records all11,260 frames successfully, and every original effective input
and emulated timestamp through8,860 matches the parent. Completed4K CRT images
show name entry at9000/9900, a loading transition at10800, and a new race start
with Chinese flags at11100. This establishes useful navigation beyond the first
race, not a complete second race. The candidate3x continuous replay is being
qualified separately. Its first plan was rejected before emulator launch because
the endpoint snapshot is mandatory; the corrected plan retains snapshot5219.
The original failed report remains available. No physical FFB, deployment,
release or hosted CI is involved.

## Reusable recording command

`harness/record_continuation.py` now performs stimulus creation, source-case
validation, isolated MAME recording and complete original input/time-prefix
comparison. It preserves frozen game patches and recorded cheat actions, stores
the source/scenario hashes, requires a new destination and disables physical
FFB. Capture ranges are explicit for the new case; stale parent ranges are
cleared. An optional display selection and completed-GL capture range use the
existing verified harness helpers.

This command records once. Candidate replay and route/visual acceptance remain
separate, so it does not automatically spend another full drive on an identity
replay. Two focused tests cover changed controls/times, truncated tails, changed
columns, allowable host-speed differences and mocked command orchestration with
physical force disabled and exact source provenance. The underlying recorder
and extension codec have the actual Exotica/World/Off-Road transition evidence;
the new wrapper itself has not justified another full live recording.
