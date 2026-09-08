# Exotica visibility evidence

Run `python results/proof/2026-09-08-exotica-visibility/verify_archive.py` from a
checkout. The standard-library verifier uses the separately committed
`2026-09-08-exotica-frustum/derived-evidence.zip` baseline to reconstruct the
unchanged stock trace, avoiding another copy of the same observations.

`lua-traces.zip` retains the three full intervention traces. `derived-evidence.zip`
contains source snapshots, native counters, frame inputs, capture hashes, ordered
submission/palette signatures, comparison reports, CI receipts and menu images.
Every archive entry and archive itself is SHA256-bound by the manifest. Duplicate
repeat traces are represented by their independently recorded matching hashes.

The verifier recomputes all sphere decisions and pose-comparison failures, native
counter summaries, input comparisons, candidate repeats and ordered submission
hash comparisons. Actual completed-GL pixels, texture memory and ROM/program
dumps remain local under `results/diagnostics/exotica-visibility-20260908`; their
comparisons are bound receipts, not independently rerendered here. Regression and
CI reports are likewise receipts; this archive does not replay games without ROMs.

Retained limits: projection/both changes later poses and existing submissions;
the strict combined-scene geometry comparison fails. The margin-only matched
scene preserves originals and adds one actual textured edge polygon. Neither
candidate establishes pop-in elimination, original-route fidelity or attended
wheel/handling acceptance. All emulated runs disable physical FFB.
