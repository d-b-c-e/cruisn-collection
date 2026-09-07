# Global World distance trial evidence

Read the [assessment](../../../docs/reviews/2026-09-06-global-distance-trial.md).
This is an experimental candidate, not a claim that all rendering is fixed.

- `full-drive-summary.json`: six complete Germany runs, far/lookahead axes separated.
- `full-drive-traces.zip`: original raw CSV logs, invocations, checked patches and replay reports.
- `bounded-*-assessment.json`, `bounded-*.lua`, `bounded-traces.zip`: changes begin at frame5900; camera words match through6183, traffic/render phase can differ earlier.
- `bounded-scenery-comparison.mp4` and `.png`: overview of original,1.25×/lead4,2×/lead8. Video is lossy, images are the comparison evidence.
- `fullsize-*-6040.png`, `fullsize-comparison.json`, `fullsize-traces.zip`:8 completed frames per run at3824×2073; selected frame6040 retained losslessly as PNG.
- `cpu125-assessment.json`, `cpu125-traces.zip`: clock-only and extended-distance controls at125% CPU. No overclock recommendation.
- `derived-repeatability.json`, `derived-case.json`: separately archived2×/lead8 case repeats8783 frames/146 native images; it is not the original attended route.
- `patch-verification.json`: the114-patch export reconstructs the native source tree.
- `default-regressions.json`, `default-comparisons.json`: all seven cases pass with the experiment disabled; Exotica's visible oracle is its21 completed GL images.
- `archive-verification.json`:184 raw archive entries checked; all six full-drive camera and native-counter summaries recomputed exactly.
- `provenance.json`: executable/source identity, raw archive-entry SHA256 values and selected image provenance.

All physical force was disabled. A recorded camera match is not an assertion of
identical vehicles, traffic, physics, or the transform used by a completed GL
scene. Gate counts and submitted quads are not visible-pixel measurements.
No ROMs, emulator binaries or program-RAM dumps are included here.

ZIP entries preserve original trace bytes. After extraction, the existing
`compare_world_motion.py` and `analyze_world_distance.py` tools can recheck them.
The full local case/capture directories remain under `results/diagnostics/`.
