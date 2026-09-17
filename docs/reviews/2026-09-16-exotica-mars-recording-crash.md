# Exotica Mars attended recording crash

The restarted attended drive genuinely failed. Native07e exited with code3 at
frame8088, scene6655, after approximately141seconds of emulated play. This was
an active-margin geometry rejection, not the recording timeout. The user also
reported intermittent stutter and loss of steering response before the exit.

The original case remains **failed**. Its8090 complete INP rows,8089 frame-trace
rows, logs, snapshots and sealed failure operands are preserved under
`results/diagnostics/drive-exotica-mars-3x-20260916-retry2`. The earlier attempt
is separately retained, with the user's restart request recorded in its attempt
note. Neither attempt is a completed two-race acceptance recording.

## Cause and correction

The active assembler rejected ordinary list `0xbbb8`, slot `0x1c426`, whose model
word was `0x09c63832`. Two other selected slots held `0x08c5e992`. These are
current animated objects retaining their initialization tag in the high byte.
The TMS320C32 program bus is24bits (`tms320c3x.cpp` program configuration and
`tms320c3x.h` memory accessor). The original CPU consequently reads model
`0xc63832`, whereas our host bounds check rejected the full32bit value.

The active-scene entry point now translates root and selected alternate model
pointers to24bit addresses **at dereference**, before the existing mapped-span
checks. Captured object words remain unchanged for ownership and resource lease
checks. Future-source admission remains strict: this does not enable future
animated scenery or invent its phase. Invalid mapped regions, command-ring
descriptors and overflowing descriptor spans still reject.

Native `dd60206a0ee` contains the correction. It is an isolated candidate;
the personal Stream Deck executable and publicv0.5.0 are unchanged. Its264patch
export is attested in `tagged-pointer-native-export.json` beside the failed case.
The export script has already run and must not be rerun against its appended
baseline.

## Saved-scene verification

The original helper reproduces the rejection offline at its descriptor guard.
The corrected helper assembles all21 independently reselected margin candidates:
21instances,176quads,160viewport-intersecting quads. A separate Python geometry
implementation matches all instance and quad bytes exactly. All16632 requested
model bytes match the scene-end WaveRAM lease image. Three selected objects have
tagged pointers. The failure dumps do not include the original submitted-slot
exclusion set, so this offline census is not a claim that every reconstructed
candidate reached the live margin submission.

The focused native scene test covers tagged root and alternate pointers,
unchanged caller operands, identical untagged geometry, invalid masked addresses,
and continued rejection by the future-source path. It passes. No broad suite
was run. The active-capture ownership and scene-endpoint integrity tests also pass.

Local scripts and receipts are retained as `diagnose.py`, `diagnose_fixed.py`,
`verify_saved_failure.py`, `failure-analysis/`, and `failure-analysis-fixed/`.
The initial rejected assembly remains separate from the corrected result.

## Stutter evidence and limits

The recording's frame callback intervals have median17.49ms and95th percentile
18.36ms. Seven intervals exceed35ms; three exceed50ms. The largest are92.86ms
at1387,76.37ms at2849, and55.36ms at7681. Two of the seven occur immediately
after a60frame native snapshot. Snapshot-aligned intervals average18.03ms versus
17.52ms for the others. That does not establish snapshots as the sole cause.

The continuous renderer reports no GL readback/file/stall calls; its largest
swap was16ms. Average emulation speed99.84% does not exclude these brief stalls.
These measurements cannot separate device polling, game-thread computation,
presentation cadence, or other host scheduling. There is no device-disconnection
proof. Physical FFB was deliberately disabled for this diagnostic recording;
steering input was enabled. The stutter/steering symptom is still unresolved.

## Bounded runtime regression

One isolated replay passed through the original failure point with the
same8089 recorded input frames and an explicitly labeled120frame neutral
scripted continuation. The original case is not being relabeled as successful.
The run requests completed4K frames8088,8090,8092,8094, preserves the original
configuration/ROM identity, and kept physical force disabled.

All8089 original frame inputs/emulated times match. All8090 original INP rows
match except host-speed metadata, including analog interpolation fields. All134
original native snapshots are byte-identical; these are not proof of Zeus GL
output. The candidate completes8209recorded frames,6739scenes,23549endpoints,
zero endpoint rejection and no degraded fallback. CPU/GPU queues drain all
12,659,551,200bytes, workers join and the process exits normally.

All four requested GL frames completed at3840x2160 with zero dropped messages.
Frame8094 was visually inspected: game elapsed1:29.38,90MPH,4AUTO, gameplay
continues beyond the old failure. There is no prior completed GL comparison at
that point, so this is not exact-pixel or broad visual acceptance. The120frame
continuation is explicitly synthetic and does not complete the requested drive.
`fixed-replay/report.json` contains the qualification and `replay_failure.py`
retains the recovery procedure. No second drive was run for analyzer adjustments.

The replay also repeats the attended drive's cluster of27–35ms frame intervals
at7810,7811,7813–7815,7817,7818 and7820. This is before the new GL captures and
occurs without live wheel input or the external clock. It supports investigating
scene-dependent workload, rather than attributing every pause to live input or
the clock. It is not a controlled performance benchmark: host conditions and
recording mode differ. The next useful diagnostic is CPU scene-phase timing on
this saved route, not another attended drive or a broad regression suite.
