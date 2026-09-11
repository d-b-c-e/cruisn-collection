# Exotica pool lifetime checkpoint

The bounded read-only experiment tracks allocation, removal and one post-race
pool rebuild, and joins scenery/fade observations to live allocation generations.
The initial event-budget and unmapped-reset failures are retained separately.
See the [review](../../../docs/reviews/2026-09-10-exotica-pool-lifetimes.md).

At the recorded source checkpoint, run
`python results/proof/2026-09-10-exotica-pool-lifetimes/verify.py`.
The verifier recomputes source/file identity, captured-frame coverage and saved
hash equality, then checks consistency of scalar receipts. It does not rerun
MAME, parse the original pool trace, reconstruct game operands or compare raw
pixels. Raw game data stays local. No host fade/drawing, material lifetime,
broader-track, deployment, default-game or physical-wheel acceptance is implied.
