# USA global-distance checkpoint proof

107 derived files in `derived-evidence.zip`, SHA256
`725c393a7ae8257e5e3565534f65f5bfd12cfcb93adc57f2ff56465b05bc15fd`. Native8b151aa9c2f / SHA638c74ff4227532d0ff42be4cd46cb8a358a1a343549abb107bb56050e91bd74.

Run `python verify_archive.py`. It verifies archive bytes, native/source bindings,
five full distance/motion/frame-input comparisons, snapshot hash comparisons,
completed-GL repeatability receipts and all seven default regression receipts.
It runs without ROMs. Full BMPs and raw runtime telemetry remain local; their
original run receipts are not described as independently rerendered pixels.

The original1× control passes. Residency trials change the old route and retain
FAIL comparisons. The2× candidate repeats5012inputs/83native snapshots/19GL images
at1904×993. The matrix uses512×451 captures; Exotica's default control matches its
21completed4K references. No visible3× improvement, geometry/order/resource or
attended driving acceptance is claimed. No physical FFB was enabled.

The Off Road table appendix retains an exact rational reconstruction, a failed
naive decimal-rounding control and source hashes. Its optional `recompute.py`
requires the maintainer's own Off Road1.63 ROM ZIP and emits only a numerical
report. No ROM data, emulator binaries or original input recording is included.

Review: [USA global distance](../../../docs/reviews/2026-09-08-usa-global-distance.md).
The publishedv0.4.0 package is preserved; this is postrelease development evidence.
