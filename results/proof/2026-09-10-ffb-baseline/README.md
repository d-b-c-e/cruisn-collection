# Preliminary four-game FFB baseline

Twenty offline algorithm runs use source traces from the same795fc native
candidate. Every replay passed its recorded input/native-pixel checks; physical
FFB was off. This is not matched driving/contact coverage or accepted force
normalization. See [the plan](../../../docs/FFB-NORMALIZATION.md).

`python results/proof/2026-09-10-ffb-baseline/verify.py` checks current source
and artifact hashes and receipt consistency. It does not rerun native algorithms,
raw traces, replays or wheel tests. Raw CSV/stage data remains local. The analyzer
simulates the shaper, not game/device polarity or full gating/worker behavior.
Local reproduction script: `results/diagnostics/exotica-amazon-20260909/ffb-four-game-baseline.py --current`.
