# Preserve recording evidence across emulator reset

MAME reruns its autoboot chunk after a soft reset while existing Lua frame
callbacks remain registered. `session.lua` previously reopened its log in write
mode and registered another callback. The resulting trace was truncated and had
nonconsecutive frame numbers, making reset recordings unusable.

The script now initializes once within its retained Lua environment. Subsequent
autoboot invocations preserve the existing recorder closure, frame counter and
open log, and emit a resume receipt. New emulator processes still initialize a
fresh recorder. Ordinary sessions gain no extra snapshots or input changes.

A short headless Exotica check schedules an actual soft reset at90 and stops
at180. The old script fails with a nonconsecutive trace. The fixed recording and
identity replay both retain180frames with zero input/time differences and six
identical native snapshots. Each requests one reset and resumes once at90.
This tests recorder behavior during boot, not gameplay or the extended renderer.

The first local runner failed before launch because it imported `tree_hashes`
from the wrong module. The actual identity check initially omitted raw-to-PNG
conversion and failed its snapshot manifest check. Converting the already saved
captures yields `qualified-v2.json`; no game was rerun for that correction.
All failures remain in `results/diagnostics/race-transitions-20260916/session-soft-reset`
and its adjacent runner scripts.

The current check supplies the same explicit reset probe to record and replay.
An INP file alone does not encode this emulator action. Next retain a bounded
reset schedule and actual completion receipts as part of the case, so later reset
tests can use the normal replay workflow without an out-of-band mutating probe.
Exotica's extended-renderer reset ownership problem remains open.

## Scheduled actions now travel with a case

The recorder can now freeze up to16explicit `soft_reset` actions, with a
validated frame schedule, owned Lua loader and request/completion log. The normal
replayer runs those actions automatically; comparisons require exact receipt
hashes, including emulated completion timing. The completion notifier confirms
the emulator actually reset. Force-enabled recordings cannot schedule these
diagnostic actions. Continuation and derivation preserve existing schedules.

An ordinary headless Exotica case with resets60/120 passes normal `replay.py`:
all180inputs/times and six native images match; both request/completion pairs
are exact. No external probe is used. Fourteen focused Python tests covering
actions, recording continuations and existing session behavior pass. Evidence:
`race-transitions-20260916/scheduled-soft-reset/{case,identity}`. This is a brief
recorder integration check, not extended-renderer reset or gameplay acceptance.
Scheduled cases currently require their complete schedule; shortened-prefix
replay before a later scheduled action is rejected rather than silently dropped.
