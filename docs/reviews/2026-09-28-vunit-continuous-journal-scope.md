# Continuous V-Unit detailed-journal scope

The USA packet attribution replay exposed a harness trap: under V-Unit
continuous bootstrap, `--usa-host-first 10450` did **not** start quad logging
at frame 10450. Bootstrap admitted the first actual guarded scene and the
continuous runtime kept detailed logging through owned shutdown, producing a
1.5 GB quad CSV for that 10,480-input replay. The run itself passed and its
evidence was used; the attempted short-log assumption was wrong.

The replay harness now emits a preflight **NOTICE** when continuous V-Unit
runtime and detailed quad logging are selected together. It explains that
the host `first/last` values are finite capture references, not the effective
detailed-journal window. The same notice is saved in `report.json` and in
`launch-plan.json` for prepare-only runs. This changes diagnostic guidance,
not emulator execution or renderer output. The focused V-Unit runtime tests
pass (6 tests). A real prepare-only USA plan printed the notice and stored
identical text in both files; it launched no game.

Local evidence:
`results/diagnostics/race-transitions-20260916/usa-quadlog-scope-prepared`.
The original full trace and source/packet/pixel findings are documented in
the [USA bridge attribution](2026-09-28-usa-bridge-pixel-source.md). Avoid
another full detailed replay merely to obtain a short interval; use saved
source logs and bounded summaries first.
