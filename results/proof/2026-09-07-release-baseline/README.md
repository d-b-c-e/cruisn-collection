# Release preparation baseline

Read [the assessment](../../../docs/reviews/2026-09-07-world-3x-and-release.md)
and [the maintained checklist](../../../docs/RELEASE-CHECKLIST.md).

`readiness.json` passes automated configuration, the complete seven-case replay
suite and all five fresh-seed boot/persistence checks. It deliberately remains
**NOT READY**, with 39 attended/package checks pending. `attended-pending.json`
is the frozen empty ledger for this build, not fabricated acceptance.

- `regressions.json`, `fresh-boots.json`, `runtime-checks.json`: final results.
- `runtime-traces.zip`, `runtime-trace-hashes.json`: 124 verified raw log/report
  entries. ROMs, binaries and personal runtime NVRAM are excluded.
- `menu-*.json`: real V-Unit menu-handler checks, separate from physical key tests.
- `ci.json`: all four jobs pass at collection commit `471ffd6`.
- `freeplay-seeds.json`: the initial seven setting-byte changes.
- `offroad-checksum.json`: the additional checksum correction. The old claim
  that settings have no checksum was wrong for Off Road 1.63.
- `initial-runtime-checks.json`: preserves the **failed Off Road persistence**
  result despite a passing replay. `initial-regressions.json` is the first suite.
- `offroad-checksum-traces.zip`, `offroad-trace-hashes.json`: read-only attribution
  probes and corrected replay evidence. The CMOS callback reports PC ED6F for
  the write at ED6E. Stack reads are outside the tapped CMOS range.
- `offroad-relaunch*.json`: a separate boot using the corrected run's saved NVRAM.
- `preflight-initial.json`: historical initial incomplete gate, before final checks.

The two Off Road attract images visibly show INSERT COINS after the invalid
checksum reset and FREE PLAY after correction. They are not matched camera scenes.
Neutral boot checks do not establish no-coin race start, manual shifting or FFB
feel. All automated physical force was disabled; originals remain immutable.
