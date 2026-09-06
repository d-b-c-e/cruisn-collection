# Session Notes
<!-- Written by /wrapup; overwritten each session, history retained in git. -->

- **Date:** 2026-09-05 (experiments extend into 6 September UTC)
- **Branch:** codex/recorded-drive-analysis, intended fast-forward to master after CI
- **Baseline:** collection d099c2f / assessment-2026-09-05; MAME 58203bb1;
  toolkit 4e99136 / assessment-2026-09-05. All were pushed before implementation.

## What Was Done
- Independent reviews in docs/reviews/; latest: 2026-09-05-recorded-drive-findings.md.
- 9451bb3 raw captures defer PNG encoding; 18200e5 D3D under GL fixes measured USA
  selection/race slowdown. Same human inputs now sustain approximately 100% speed.
- e1bef95 / MAME 45a05364e11 bound enhanced UV sampling; fixes distant road atlas
  bleed without changing native DDA. Six archived captures remain 100.0000%.
- fae3722 / MAME eb4db8fc706 validate whole patch files before initial writes.
- 0804eb8 and 9dc2723 add late/effective-RAM patch checks and compose experiments.
- 28738f9 widens USA object visibility: matched frames 3440/3800/4880 add 50/5/5
  margin-only quads, preserve original draw order and all native framebuffer/texture/palette RAM.
- 30 Python tests; native helpers; nine GPU fixtures (NVIDIA + Mesa CI); rebuilt
  full replay; World v2.4/Off Road launcher smokes. MAME series reconstructs 24 paths.
- Toolkit stays v0.10.1 / c9b76b7, canonical pre-gain force detector with 105 managed
  tests and native checks from the preceding milestone; consumers synced.

## Decisions Made
- Preserve results/diagnostics/my-drive unchanged: 5,012 human input frames / 83 images.
- UV-only rebuilt replay matches it. Full-boot USA game patch changes 32 native
  snapshots from frame 3120 and later trajectory; timing/state coupling remains unmapped.
- A separate usa-widescreen-candidate-case retains human INP provenance and passes
  5,012/83 identity replay (replay-20260906T030510Z-yydopnlr). No reference blessing.
- Crack filler remains a reversible cosmetic option, default/radius unchanged;
  it cannot fix covered atlas bleed or missing terrain. Margin fill is separate.
- Doubling USA far gate yields no extra geometry here; no new distance default.
- FFB is disabled in all automated recording/replay. No physical feel acceptance.

## Open Items / Next Steps
1. Investigate remaining thin source-geometry seams and ordered live resource/scene
   fences; asynchronous GL labels do not establish exact scene/pixel determinism.
2. Trace full-boot visibility patch execution coupling; record new human routes on
   the current build. Add World/Off Road/Exotica gameplay and black-sky cases.
3. Track a specific popping object through residency, node lifetime, LOD, depth
   rejection and reciprocal lookup before another draw-distance experiment.
4. Label actual collisions and test wheel variants; native speed/Off Road OCR,
   toolkit provenance/device selection/backend lifecycle remain open.

## Context for Next Session
MAME is E:/Source/mame-src, poc/quadlog at eb4db8fc706; push only fork, not mamedev
origin. Rebuilt vunit.exe is current; deployed racing mame.exe was untouched.
Full evidence is gitignored; tracked summary/proof crops:
results/proof/2026-09-05-recorded-drive-milestone.json. Use docs/DIAGNOSTIC-REPLAY.md
for commands and the recorded-drive findings for exact retained run paths.
