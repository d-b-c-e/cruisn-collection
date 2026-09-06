# Session Notes
<!-- Overwritten each session; history preserved in git. -->

- Date: 2026-09-06
- Branch: codex/world-scenery-distance (continue tree coverage; ff master after final CI).
- Latest: docs/reviews/2026-09-06-native-scenery.md.

## Completed baseline
- Native3dc426ec75d pushed fork/poc/quadlog; rootvunit075d16a7cc7648b3dd61b19fd2fda264cc476ebf48584c76256847371ddc5ffb.
- Canonical native/world_scenery.h syncs to MAME. World24 only opt-in
  MIDV_SCENERY=mountains/trees/all/off; log=1 ->scenery.csv. No guest RAM writes.
- Three mountainsCB15F8/CB171E/CB1A8B admitted160k with originalclampedperspective;
  CA57F3tree only originallyrejected instances get safe fastprojection and virtual
  reciprocals5000..10000. Model/flags/radius/code guards; reset/save context handled.
- Native tree prefix matches finalLua exactly.42addedquads/21drawframes,zero
  original changes/removals/reorder. Giant nested-read Lua prototype retained as
  negativecontrol; compare_scenery.py optionalextent32 rejects it. Read backingRAM
  directly in native callbacks, never nested address-space reads in same taprange.
- FullnewGermany8783/146repeatPASS; both100.005% driving speed. Parent6early
  nativeimages differ, later samplesmatch.371mountain/660tree admissions,5280reads,
  maximumindex7361. Admission is not proof of visible improvement.
- LiveGL201images1600..2400every4:103earlyimagesdiffer;93images2032..2400 identical.
  Mountain visible through garageexit/start, preserving laterlook.
- Launcher DistantScenery defaultOFF, World24/wide/scale>1; preference preserved
  but unavailableWorld25. Different fromWidescreenTerrain edgegeometry fix.
- All7defaultregressionsPASSED at075d16a7;67Python tests,20GPUfixtures,nativeunit,
  CI34067459020/96ea041all4passed.110exportpatches reconstructtreeb2b9bab9.

## Active work
- User said keep fixing/improving until they return. No physical automated FFB.
- Next trees identified:CA5833 mirroredconifer1950,CA5863 broadleaf818,
  CA5896 broadleaf1252. Actualobjectflags1008/highstatebit, notDMAflags900.
- lua/world_tree_distance.lua now accepts a verified-model list (defaultCA57F3).
  Baked four-model/provenance probe results/diagnostics/tree-four-models-probe.lua;
  run tree-four-provenance started. Compare against scenery-provenance-start,
  allowedfourmodels/extent32. Nativeallowlist still onlyCA57F3.
- 12originalcrossingevents at2031..2193 in tree-next-crossings.json. Next denseGL
  control/candidate2000..2400, then expandnative only if validated and fullrepeats.

## Remaining queue
- Continueother scenery/loading limits and per-gameadapters; no globalfar hack.
- World impacts stillweak at80; optionalImpactCues defaultsOFF, physicalacceptance
  pending. Toolkitv0.11.1 unchanged.
- CheatsXMLdownloadhasallgames; MAMEcheatmanager canapply existingXML, notLuaAPI.
  Submenu/provenance notimplemented. PreserveCheats asstretchaftergraphics.
- Originalattendedcase world-germany-extended-20260906 remainsimmutable/valid.
