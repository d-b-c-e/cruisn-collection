# World 3x experiment evidence

Read [the assessment](../../../docs/reviews/2026-09-07-world-3x-and-release.md).
Physical force was disabled throughout. These are diagnostic comparisons, not
attended handling/FFB acceptance or proof that all textures are correct.

- `matrix.json`, `summary.json`, `full-drive-traces.zip`: five full Germany
  runs, with distance and lookahead varied independently at normal CPU speed.
- `2x-vs-3x-*`: lead-8 camera equality and five small-output image differences.
- `paired-assessment.json`, `bounded-report.json`, `bounded-traces.zip`, Lua
  sources and `run_windows.py`: bounded comparisons, 201 completed images per run.
  All 2x/3x images match at either lead. Earlier lead-12 submissions are not first
  visible pixels; camera/traffic changes prevent claiming a clean visual win.
- `fullsize-comparison.json`, lossless `*-6040.png`, `fullsize-traces.zip`:
  eight completed near-4K images match exactly at lead 8. **The failed first
  3x attempt is retained in the ZIP**: renderer stream loss, zero GL captures.
  A logged retry passed capture completeness; it does not fix the startup issue.
- `repeatability.json`, `repeat-traces.zip`: the 3x/8 native run repeats all
  8783 frames, 146 native images, 321 completed GL images, and camera/ADC data.
- `previous-2x-identity.json`: new build preserves the earlier 2x/8 run exactly.
- `patch-verification.json`: 115 exported patches reconstruct the native tree.
- `provenance.json`, `archive-verification.json`: every raw ZIP entry verified;
  all five full motion/distance reports recomputed; two PNGs preserve BMP pixels.

Original recordings remain in `results/diagnostics/`. No ROMs, emulator binaries,
or full program-RAM dumps are included. Copy the bounded runner and Lua files to
a fresh directory under `results/diagnostics/` before rerunning them. Its paths
assume that depth; do not use the committed proof directory as a run output.
