# Normal-launch environment regression — 2026-09-08

The maintainer selected USA's **Always in 1st Place** cheat and saw
`cannot access local variable 'env' where it is not associated with a value`.
The screenshot missed the transient error. The old `rig/launch.log` was still
from a prior session because failure occurred before the new log was opened.

`launch_game_async.start()` assigned `env = dict(env)` inside the later Off Road
and Exotica recording branches. Python therefore treated `env` as local across
the entire nested function. Both cheat-on assignment and cheat-off removal read
it before initialization. This affected ordinary launches for all games, not
the semantics of the selected cheat. Replay and memory-probe tools use separate
launch paths; their earlier PASS results did not catch this integration failure.

The start function now takes a fresh `launch_env` copy of its enclosing settings
on each attempt. Cheat selection, recording overrides, logs and process creation
all use that copy. No emulator rebuild, cheat selection, personal settings or
force policy change is required. Already-open source launchers must be reopened.

Validation reaches the actual `subprocess.Popen` boundary while replacing only
the process itself and unrelated device/window setup. The first test reproduces
the original exception in10 cases (five ROM revisions, cheats on/off), then passes
after the correction. Another20 cases cover ordinary recording and each game's
explicit distance/visibility recording override, with cheats on/off. All launch
requests retain physical FFB0. Recording freeze/path binding has separate tests.
This does not certify the behavior of Always in 1st Place while racing.

The complete local suite passes187 Python tests without skips, all native helpers,
10,081 C31 vectors and24 GPU quality fixtures. Evidence is in
`results/diagnostics/local-checks-20260908-launch-fix`; the initial failure log is
retained in `results/diagnostics/local-checks-20260908-first/launch-boundary-before.log`.
No automated game was opened while the maintainer was testing.

The [ROM-free proof archive](../../results/proof/2026-09-08-launch-environment/README.md)
preserves the failure and complete local check evidence with a standalone verifier.
