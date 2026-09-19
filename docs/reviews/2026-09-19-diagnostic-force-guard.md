# Require an explicit force disable before timeout-capable execution

`diagnostic_runtime.execute` previously treated a missing `MIDV_FFB` key as `0`.
That did not enforce the project's requirement for a literal force-disable
setting before a diagnostic process that may be terminated on timeout. Existing
callers using `diagnostic_env` already received an explicit `0`; this is a guard
gap, not evidence that the recorded parity runs enabled physical force.

The execution boundary now rejects missing, empty or nonzero force settings,
nonempty force-test settings, and conflicting case aliases of either key.
Windows environment variable names are case insensitive. Rejection happens
before creating the run directory or launching a process.

Six focused runner tests pass. The new negative cases mock process creation
and verify that no process or output directory exists. The existing timeout
test runs only a sleeping Python child with `diagnostic_env`, verifies retained
partial output, and confirms timeout reporting. The printed capture/oracle
FAIL messages are expected negative tests, not game regressions.

No emulator, GPU, wheel test, native build or deployment was performed. Game FFB
strength, menu behavior, product preferences and the frozen parity candidate
remain unchanged.
