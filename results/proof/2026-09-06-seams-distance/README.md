# Evidence guide

The corresponding review is `docs/reviews/2026-09-06-seams-distance.md`.
Full recordings, binary dependencies, raw images and traces remain local under
`results/diagnostics/next-*`. Reports preserve their original absolute paths.

- `rpm-wire.json`: actual local UDP JSON/Forza observations; no physical force.
- `next-quality.json`: retained failing pre-fix GPU control. `next-quality-fixed`
  and the two native capture reports pass after the fine-coverage correction.
- `terrain-pixel-*`, `terrain-alignment`, `quality-capture-deltas`, and the seam
  crops: actual Off Road5518 geometry, UVs and owner transitions; optional alignment.
- `six-game-regression`: full local suite, measured timing windows and explicit
  per-game coverage. Exotica uses actual completed GL pixels, not native black.
- `exotica-abrupt-failure`: unexplained early process exit, retained as a failure.
  `exotica-visible-repeat`: successful21-frame GL replay after that failed run.
- `exotica-dual-control`: expected native-image FAIL because CPU rendering is
  enabled; its GL comparison passes. Native and GL screenshots are illustrative
  views, not a same-frame native/GL exactness comparison.
- `exotica-fallback`: injected consumer exit recovers CPU rendering, clean process
  exit, and correct diagnostic rejection. This is not an overflow stress test.
- `next-distance-existing` vs `distance-full-drive`: short vs extended object
  trace windows. `far-candidates`: the15 samples just beyond the original limit.
- `far-effective-replay`: guarded late patch and matching native replay.
  `far-matched-extension`: expected FAIL for the margin-only acceptance contract,
  because89 of97 added draws intersect native X. All original geometry/resources
  remain unchanged. `far-visible-delta`: ZERO visible4x benefit in this capture.
- `lod-full-replay`: expected native-image differences with detail thresholds
  changed; `lod-timing` and `lod-workload` quantify the full remaining-drive cost.
- `guest-state-probe-results`: unchanged baseline vs changed widescreen histories,
  not proof of the original upstream cause. Probe scripts/hashes remain retained.
- `patch-reconstruction`: full105-commit export reproduces the committed MAME
  tree from mame0286 using an isolated Git index.

No report here certifies all routes, all visual artifacts, subjective collision
feel or every wheel. Failed controls are deliberately retained.
