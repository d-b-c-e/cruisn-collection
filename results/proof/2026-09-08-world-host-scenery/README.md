# World host scenery evidence

Read [the assessment](../../../docs/reviews/2026-09-08-world-host-scenery.md) for
the results and their limits. This archive contains 279 derived evidence files,
with SHA256 hashes in `manifest.json`. No ROMs, packed models, texture RAM or
emulator binaries are included. Local raw captures remain under
`results/diagnostics/world-host-transform-20260908`.

Run from the repository:

```text
python results/proof/2026-09-08-world-host-scenery/verify_archive.py
```

The verifier requires Pillow, already included in the testing requirements. It
recomputes original inputs and emulated times, host scene/quad counts, camera and
actual ADC equality, the 3× ordered insertion, selected full-resolution image
hashes, section placement/yaw, actual outgoing telemetry versus memory, and force
polarity/passthrough. It checks both platform source identities and the precise
diagnostic-only source changes after the default suite. Those suite results keep
their original identity; they are not relabeled as observations on later code.

Model reconstruction and unarchived image/resource comparisons remain hash-bound
receipts. The archived images show selected changes; they do not certify all
occlusion, handover, tracks or presentation latency. Per-quad logging and GL
submission are included in the current host timing counter; the long outliers
are unresolved. Physical force, other wheels and attended handling were not tested.

The failed expectation that 3× would change the sparse 31-image sample is retained.
A later dense 21-image interval finds six changes; both observations are valid.
The display-transition run and rejected preflight/control attempts are retained
separately. The published v0.4.0 package and personal settings are unchanged.
