# Live waiting observation receipts

Run `python results/proof/2026-09-10-exotica-waiting-observation/verify.py` from
the repository root. This verifies source hashes and consistency of the recorded
results. **It does not rerun native/game/GPU execution, raw geometry, pixels or
tests, and it does not certify waiting drawing or fade/handover.**

The [review](../../../docs/reviews/2026-09-10-exotica-waiting-observation.md)
explains the explicit observer, full Amazon/repeat/disabled controls and measured
same-scene first-submission overlap. The old original target stays displayed;
waiting geometry is proposed and logged only. Personal v0.5.0 is unchanged.

- `runs.json`: accepted replay/input/motion/21 completed original4K receipts.
- `independent.json`: actual handles/order and Python geometry comparisons.
- `repeat.json`: byte-exact waiting/lifetime trace and snapshot pairs.
- `handover.json`: five sampled admission intervals; ten overlaps at5072.
- `checks.json`: complete 375-Python/50-native/142-command local-check receipt.
- `native.json`: separately built native9ad, patch tree reconstruction and hashes.
- `source.json`: canonical source bindings for this checkpoint.

Raw inputs/resources/geometry/images remain LOCAL under
`results/diagnostics/exotica-amazon-20260909/waiting-observer-*`.
