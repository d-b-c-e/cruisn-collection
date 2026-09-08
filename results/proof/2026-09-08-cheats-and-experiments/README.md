# Cheats and Experiments evidence

Run `python verify_archive.py` here. It checks the ZIP and every member, native
binary bindings, five timer-effect conclusions recomputed from raw CSV using the
archived analyzer, and replay/frozen-check receipt consistency. It does not rerun
gameplay or recompute all original framebuffer/input comparisons without their
local recordings and ROMs.

The 75 derived files contain seven default controls (six first-run passes plus a
4K Exotica rerun), five 4,000-frame cheat-on replay comparisons, five real timer
on/off probes, source/frozen menu images, package/default checks, 128 Python tests
and CI 34195061384. The initial aggregate FAIL and Exotica's 1080p-vs-4K mismatch
are retained. Exact comparison was restored by selecting the matching monitor,
not by resizing reference images or accepting changed pixels.

The local development ZIP is built at `f8a804f`; the later `1baa99a` adds the
diagnostic display-target correction. These are component checks, not a new
release gate or attended/physical-force acceptance. Some source edits continued
during the original default regression, as detailed in the review. The published
v0.4.0 ZIP hash is verified unchanged in the manifest.

See [the review](../../../docs/reviews/2026-09-08-cheats-and-experiments.md) for
scope and remaining live-cheat and distance work. Raw local runs remain under
`results/diagnostics` with their original inputs and logs.
