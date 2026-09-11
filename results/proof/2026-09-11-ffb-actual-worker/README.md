# Actual force-worker receipts

Run `python results/proof/2026-09-11-ffb-actual-worker/verify.py` to check source
hashes and aggregate consistency for the separately built native worker observer.
The four complete recordings use one candidate and nominal strength50, with
Exotica's existing explicit 0.8 trim. Every actual observed force-processing stage
was replayed independently using its recorded inputs and clocks. Original source,
gate, speed and drivetrain traces remain unchanged.

The compact receipts also cover ordinary disabled observation, zero strength
with nonzero game requests, and an enhanced-impact drive. Exotica's 21 sampled
4K/CRT frames match their control. Native images have a different scope: CPU
polygons are disabled in Exotica's live GL path.

This public verifier does not load raw game recordings, compile or execute MAME,
replay the worker journals, render GPU images or test a physical wheel. Those
results are execution receipts. It does not establish mailbox causality,
unperturbed host performance, matched contact/cornering coverage or accepted
four-game normalization. Software sink acceptance is not physical delivery.

LOCAL evidence is under `results/diagnostics/exotica-amazon-20260909/` in
`ffb-worker-{usa50,world50,offroad50,exotica50,disabled,zero,enhanced}` and the
separate native/Python check directories. Failed test-expectation and initial
file-versus-pixel-hash comparisons are retained there.

See [the review and next calibration steps](../../../docs/reviews/2026-09-11-ffb-actual-worker.md).
