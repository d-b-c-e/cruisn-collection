# Session Notes
<!-- Overwritten each session; history preserved in git. -->

- **Date:** 2026-09-06
- **Branch:** codex/world-scenery-provenance; fast-forward master after CI.
- **Latest:** docs/reviews/2026-09-06-selective-scenery.md.

## What Was Done
- User asked how to keep pushing mountains/trees. Concrete selective mountain
 prototype plus future implementation order documented; no product distance fix.
- lua/world_scenery_provenance.lua joins same-frame admission to DMA. World2.4
 only, bounded240frame interval; slow-path333 savedAR0 supported, unknowns explicit.
 Control2042frames/34nativeimages pass.1998..2040 has36395matched/1158unmatched.
- Mountain object13E40/modelCB1A8B: first15quads2027, bounds167..274/95..198,
 far test80019->79839; no LOD change. Isolated atlas render confirms mountain.
- Global100k projection shrinks mountain87x82 vs107x103. Selective earlier
 admission preserves original size and original far-clamped projection.
- lua/world_scenery_admission.lua: bounded PCA1 far-read override for selected
 model(s), defaultCB1A8B/160k/frames1800..2200. A8/A9 and projection unchanged.
 Late1998 trace adds15mountain quads1999..2025,zero originals removed/changed;
 no differences2027..2039. Archive scripts in diagnostics bake combined probes.
- Live GL2000..2200 every2:15earlier images differ in mountain region; all86
 images2030..2200 identical. Timing100.03%; inputs/time equal. Native strict FAIL
 on3earlier screenshots expected/retained. This is NOT full-route acceptance.
- TreeCA57F3 texture11066/palette18176/U3..83/V0..88 identified. Object14118
 resident atdepth99830, draws5x11 in100k projection. Tree fix still open.

## Next Steps
1. Catalogue Germany mountains/tree groups and precise pop events from provenance.
2. Native guarded selective scenery candidate: mountains continuity; trees valid
 far perspective limited to distant instances. Preserve normal-range geometry.
3. Full-route repeatability/timing, old54s divergence window and earliest admission
 boundary. User accepts extra drawing/new baseline if useful; preserve parents.
4. Only then expose validated per-game distance controls. Consider deliberate
 distant transitions/background models if admission still abrupt; no pixel smear.

## Other Open Work / Context
- CASE results/diagnostics/world-germany-extended-20260906 remains valid8783/146.
 FFB80 weak impacts; per-game Impact Cues menu is available/defaultOFF. Need
 controlled car/wall hits vsbumps and physical OFF/ON comparison atsameprofile.
- Cheats XMLs C:/Users/antho/Downloads/cheat0279/cheat/ includeWorld24/allfour.
 MAME cheat manager integration/recording provenance pending, none enabled.
- Native2bf1048a, rootvunit SHA2567eaf9ce8888190a5a6b8c30dd698fb57175c644779d4c65bf52cc083c74263fb;
 toolkitv0.11.1 unchanged. Native pushes fork ONLY. Replays physicalFFB OFF.
- Proof results/proof/2026-09-06-selective-scenery/. LargeCSV/captures ignored.
 Prior review2026-09-06-world-distance-and-impacts.md retains FFB/distance context.
