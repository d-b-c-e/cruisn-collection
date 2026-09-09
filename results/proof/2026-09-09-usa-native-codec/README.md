# USA native codec checkpoint

Implementation: collection `b0d18ca`. The native USA helper is compiled offline;
MAME remains candidate `5a5e11d9ab7` and personal Stream Deck remains v0.5.0.

Run `python results/proof/2026-09-09-usa-native-codec/verify_archive.py`.
Requires Pillow. The archive contains no ROM/model/material/program dumps.

The verifier recomputes five complete5,012 input/time traces against the original
recording,3,211 camera and9,633 actual ADC samples/timestamps per run, and all
fifteen completed3824x2073 images. Identical BMPs use content-addressed storage;
each run retains its capture clock, size, drop count and exact file digest.

The18,903 projection/transform and111,498 original DMA comparisons remain
hash-bound receipts because their raw game operands are local. Native/GPU
build/test results and the prior seven-game baseline are not newly recomputed by
this archive. The source and synthetic native test are included for inspection;
`python harness/local_checks.py` rebuilds and checks the current repository.
The32 signed-depth reference failures are retained alongside corrected verdicts.

See [the review](../../../docs/reviews/2026-09-09-usa-native-codec.md) for scope,
diagnostic logging cost and remaining scene/residency/material work. This is not
a visible USA draw-distance improvement or a deployment acceptance report.
