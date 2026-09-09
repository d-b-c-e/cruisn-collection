# Local build migration evidence — 2026-09-08

Source commit `e0676d4`, identity
`9cfd7955efeb5ae52d761f4d6664f7553ffe7782d06dfdb60fc4e46ad2a2ff76`
(289 inputs). The 35 KB ZIP preserves 47 derived files, without ROMs or executables.

- Full Windows local runner: 37 successful commands, 185 Python tests/no skips,
  13 standalone native tests, 10,081 C31 math vectors, FFB/T-junction analyzers,
  24 actual GPU quality fixtures on the RTX 5080. Command time totals20.967s.
- Release gate accepts the new local report but correctly remains NOT READY
  without current replay/fresh-boot/attended evidence. No release was attempted.
- Missing compiler produces a failed report. Unit tests cover partial/stale
  reports, failed commands, skipped tests, damaged evidence and unsafe paths.
- GitHub API receipts show both workflows disabled and no run after the new
  commit. MAME fork has no workflows. Billing-block annotation and recent
  approximately50-minute hosted release runs are retained; this is not an account invoice.
- Native executable, v0.4.0 ZIP and personal settings retain their prior SHA256s.

Run `python results/proof/2026-09-08-local-builds/verify_archive.py` to check the
archive, internal evidence bindings and verdicts. GPU/compiler/GitHub/baseline
observations are receipts; the verifier does not rerun those environments.
