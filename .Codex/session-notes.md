# Session Notes
<!-- Overwritten each session; history preserved in git. -->

- **Date:** 2026-09-06
- **Branch:** codex/world-distance-impact-analysis; fast-forward master after CI.
- **Review:** docs/reviews/2026-09-06-world-distance-and-impacts.md.

## What Was Done
- New attended World2.4 case results/diagnostics/world-germany-extended-20260906:
 8783 frames,146 native snapshots, terrain ON, FFB80. Full identity/lifecycle pass.
- User still reports heavy pop-in and weak crashes at80%. No claim those are fixed.
- Per-game Impact Cues submenu exposes existing optional torque mix, defaultOFF.
 force_options.py resolves exactROM (includingOFF), family, global; World writes24.
- Widescreen Terrain is renamed Terrain Visibility; same INI key, no distance claim.
- analyze_ffb --frames anchors force-source candidates to frame CSV. Reject host
 clock labels/anchors.65 Python tests and actual offscreen menu previews pass.
- Archived force profile matches toolkit.8317 raw/adapted writes identical;
 6621 accepted updates,26 rumble successes. Standard peak.7998/RMS.3286; optional
 mix peak.7076/RMS.2464. Firstcandidate45.076s/GL2612 coincides hill crest/jump.
 No collision labels inferred. Dense first-candidate replay prefix2704 passes.
- Lifecycle94 resident objects beyond80k within160k. Probe far parameter added.
 Control/100k/160k GL2000..2200 each101 images; candidate inputs/time match but
 4 native image differences retained as expected FAIL.160k~80% emulation inclLua.
- No native/shader/toolkit/profile changes. Native2bf1048a/root vunit SHA256:
 7eaf9ce8888190a5a6b8c30dd698fb57175c644779d4c65bf52cc083c74263fb.

## Decisions / Open Items
- [ ] Physical World Impact Cues OFF/ON, same strength/profile, deliberate car and
 wall hits plus clean steering/bumps. Existing detector only infers force spikes.
 Optional user question asked for a weak collision timestamp; no reply yet.
- [ ] Actual distance: identify first visible mountain geometry, then projection,
 LOD, per-face culling/residency. Do not promote bounded Lua tap to product.
 Largeobject13E40/modelCB1A8B/radius26031 crossesfar80k atframe2027.
- [ ] Cheats submenu: archive C:/Users/antho/Downloads/cheat0279/cheat/ has arcade
 XMLs inclcrusnwld24. Native cheat manager API in frontend/mame/cheat.h.
 World24 TimeEBE4/placeEBC0;World25 TimeEBDE/placeEBBA. Not installed or enabled.
- User accepts useful extra drawing and new attended baselines; preserve parents.
 New recording is trustworthy. Old Germany still preserved; no new recording needed
 merely to continue analysis of this case.

## Context
Proof results/proof/2026-09-06-world-distance-impacts/; large diagnostics gitignored.
Stream Deck uses checkout/root vunit. Reopen launcher for Python menu changes.
All automated replays FFB OFF. Native poc/quadlog pushes fork ONLY, never origin.
Toolkit remainsv0.11.1. Previous native/UI-road review remains important context.
