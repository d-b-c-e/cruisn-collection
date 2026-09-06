# Session Notes
<!-- Written by /wrapup. Overwritten each session; history preserved in git. -->

- **Date:** 2026-09-06
- **Branch:** codex/world-geometry-and-textures; fast-forward master after final CI.
- **Primary handoff:** docs/reviews/2026-09-06-world-rendering-and-replay.md, RESULTS.md tail.

## What Was Done
- Native dd12bed67f0 exact endpoint reciprocals; f40c28f8e0a tagged enhanced dither resolve.
  Root vunit.exe SHA256 4553e2afb939e4fea88238b62c1180b9c2e3dcc9bee58c102fed49c878237893.
- Off Road sky patch 0b48f3d extends one flat backdrop, no extra instructions/draws.
  Full 6000 inputs/100 native/9 GL captures pass. World/USA exact 100.0000%; GPU 20 checks.
- World route tools: lua/world_motion_trace.lua, harness/compare_world_motion.py,
  derive_case.py (repeatability ONLY). 59 Python tests. Original Germany unchanged.
- Final Germany world-final-faithful-germany: 9269 inputs/154 native pass;
  faithful-motion.json: 7401 camera samples/22203 ADC reads including exact times match.
- World visibility works geometrically but DEMOTED by 3d9d8a9. Normal 2.4/2.5
  defaults restored. Proof in results/proof/2026-09-06-world-visibility/.
- Bounded World lifecycle, DMA, transmission and projection probes committed.
  Native export 108 patches reconstructs tree 79f28f8dc867012d19be9807d4a3df7980c12372.
  Native helpers/generated shaders match; toolkit v0.11.1 unchanged.

## Decisions Made
- Extra admitted World guest geometry changes route. Both left-only/right-only
  first camera diff 2732; 4503 actual ADC values/PCs equal. Read time diff 1802/40ns.
  Original-bounds helper passes; original/derived INP yield same divergent route.
  Exact timing/state cause OPEN. Do not alter inputs or silently bless a new baseline.
- Do not re-enable experimental World B9/C0/108..10D in defaults. No fresh drive needed.
- D/A atlas reused early: BCC100..BD08FF, loader B25/B27 at 1282..1286, panels
  drawn through 1358. Hold-control restores D/A; header still corrupt. No frame hacks.
- Far 80k->100k needs reciprocal LUT extension. world_projection_distance.lua adds
  guarded reads 5000..6250/five clamp pairs; 2651 hits, earlier mountain visible.
  MUTATING diagnostic only. Guest-work/route and mountain-base appearance remain open.

## Open Items
- [ ] World route producer dependency, then safe margin geometry and draw distance.
- [ ] Black left wedge at GAME ELAPSED ~1:37 (external frames 7320..7360). Final GL
  7340 shows 1:36.78; offline 7340 differs slightly in scene time. Align exact scene.
- [ ] Semantic transmission asset lifetime fix, including title header atlas.
- [ ] No-pop-in goal all games: safe projection, residency, background/LOD transitions.
- [ ] Physical crash feel/labels and per-wheel tests; other games' numeric telemetry.
- [ ] Prior Exotica unexplained abrupt exit (next-exotica-fenced-gameplay) if recurring.

## Next Steps / Context
1. Read full new review; retain failed experiments and immutable original cases.
2. Prioritize guest drawing work versus simulation timing before more World admissions.
3. Current normal build preserves original Germany route. Extra real routes useful later.
4. Final suite world-final-remaining-suite: USA original/wide, World 2.4/2.5, Exotica.
   Off Road/Germany have separate full final runs; see final verification proof.
Native branch poc/quadlog: push ONLY fork. Never touch deployed racing mame.exe.
Never force-enable automated replay; use clean WM_CLOSE, not hard kill with live FFB.
Stream Deck uses this checkout and E:/Source/mame-src/vunit.exe. MSYS2 E:/msys64;
build with OS=Windows_NT exported INSIDE shell and both midvunit/midzeus sources.
