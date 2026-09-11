# Four-game force condition coverage receipts

This archive verifies source hashes and consistency of the recorded coverage
results. It **does not independently rerun the raw traces, games, force worker,
physical wheel or tests**. No normalization or physical-force acceptance is claimed.
See [the review](../../../docs/reviews/2026-09-10-ffb-condition-coverage.md).

Run `python results/proof/2026-09-10-ffb-condition-coverage/verify.py` from the
repository root. The source hashes bind `harness/force_segments.py` and its tests
to this checkpoint. `python-checks.json` retains the complete 368-test Python
receipt; it is not a new native/GPU or release acceptance report.

`strict.json` excludes OCR speed. `exploratory-ocr.json` permits it with the same
100 ms sample-age limit and exposes only two shared condition bins. Both retain
source/gate/input/speed/invocation/replay-report hashes and interval-file hashes.
Raw interval files and game traces remain LOCAL under
`results/diagnostics/exotica-amazon-20260909/ffb-condition-final` and
`ffb-condition-final-ocr`.

Selected durations are evidence coverage, not reviewed contact-free driving.
Requested force is measured before the shaper/worker and does not include gate
transitions between writes, device rumble or damping. Steering bins use recorded
game ports, not physical angle or actual per-conversion ADC values.
