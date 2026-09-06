# Session Notes
<!-- Overwritten each session; history preserved in git. -->

- **Date:** 2026-09-06
- **Branch:** codex/world-rendering-followup; fast-forward master after final CI.
- **Primary handoff:** docs/reviews/2026-09-06-world-assets-and-road.md, RESULTS.md tail.

## What Was Done
- Native 2bf1048a1cf retains World 2.4 outgoing D/A and header atlas in GL uploads
  while actual UI models remain linked. No guest-memory change or frame gate.
  Helper native/retained_texture.h; scale >1; revision/model guards; reset/load releases.
- Root E:/Source/mame-src/vunit.exe SHA256:
  7eaf9ce8888190a5a6b8c30dd698fb57175c644779d4c65bf52cc083c74263fb.
- Full original Germany passes 9269 inputs/154 native images; 7401 camera samples
  and 22203 ADC reads including exact times match. All 21 completed GL transition
  frames equal semantic texture-hold control. On/off differs only at 1280..1370.
- Probe load/callback errors stop cleanly; evidence rejects Lua/snapshot errors
  even on exit0. Two actual failure controls exit cleanly and fail without timeout.
- Black road: dump7338 matches completedGL7340/HUD1:36.78. Native(-82,355) has
  no owner. Object117A4/modelCA06A9/radius2461/depth2827 is wrongly rejected.
- Conservative projected radius1.25 plus X-86..598 restores the wedge with77
  added quads, all966 originals/order/resources/native pixels preserved in matched scene.
  Full X bypass adds145 and remains diagnostic; old +86 helper alone leaves the hole.
- World Terrain Visibility is an optional reversible launcher setting, verified
  World2.4/2.5 in widescreen only. No far-distance increase.
- Full derived Germany + identity replay match9269/154, around100% emulation.
  World2.5 headless candidate pairs match6000/100. Parent differences retained.
- Native export109 patches reconstructs tree1dc9cd3cb86a8599321a71286c8924906d6890bd.
  Toolkitv0.11.1 unchanged. 61 Python tests,20 GPU fixtures,atlas native unit pass;
  exact USA/World captures100.0000%. Final cross-game evidence is appended below.

## Decisions Made
- User accepts extra drawing and a NEW attended recording for a better experience.
  Old-route equality is diagnostic, not an absolute veto. Preserve original Germany.
  Require repeatability/performance plus human handling evaluation.
- Derived cases do not establish attended acceptance. Candidate changes117 sampled
  Germany images and29 World2.5 images versus parents; those failures are retained.
- Keep UI fix display-only, Margin Fill retired, and avoid filling a road hole
  with crack filler. MIDV_GL_UI_ASSETS=0 / replay --no-ui-assets is the UI control.

## Open Items / Next Steps
1. Fresh attended Germany drive with Terrain Visibility Extended: inspect handling,
   collisions, road margins and moving scenery. Use a new recording name.
2. Understand why extra drawing changes route; internal timer/state dependency open.
3. Distance: valid reciprocal projection beyond80k, residency and stable mountains.
4. More real World/Off Road/Exotica routes; physical crash feel and telemetry.

## Context
Stream Deck uses this checkout and root native exe. Native poc/quadlog pushes ONLY
fork, never origin mamedev. Never touch racing mame.exe. All replays have FFB off.
Proof: results/proof/2026-09-06-world-assets-road/. Full/failed diagnostics retained.
