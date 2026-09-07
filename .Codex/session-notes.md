# Session Notes

- Date:2026-09-06. Branch codex/world-scenery-distance; user authorized ongoing
  autonomous fixes until return, separate commits/pushes. No physical automated FFB.
- Native5ca501570a5 pushed fork/poc/quadlog. Deployed rootvunit hash
  2e3ac3f32e791516a7b0f8d0339cf7cf98c120e90a02b14b94ce0f34acc09f56.
- Latest review docs/reviews/2026-09-06-scenery-coverage.md; previous native-scenery.md
  records first3mountain/conifer build. Default option OFF, World24 only.
- Four treesCA57F3/CA5833/CA5863/CA5896, exact flags/radii, virtualreciprocal5000..10000.
  No guestRAM writes. Direct backingRAM inside taps avoids nestedread corruption.
- Fourtree fullGermany8783/146identityPASS, parent10images differ; ~100.005% driving.
  371mountain/3964tree admissions,31712reads,max8120. All7defaultcasesPASS.
  Dense trees-onlyGL201images vsOFF:109changes,max49pixels. Small visual gain.
- Long LuaGL timedout2252/164images; not accepted. Native201completed, shared164match.
- scenery-events fullread-only8783/146PASS,3584runs,16323events. Ranking proposes
  windows; bounds not visibility, reusedslot notLOD, firstgate notcreation.
- Active: scenery-second-control/candidate2000..2200 (Lua selectedCB2314/CB21A2/
  CB2375 admission-only160k). Strictframecompare FAIL:2HUDquads shift2171->2172.
  CompletedscenecomparePASS, originals retained/order unchanged. Keeptimingdifference.
  DenseGL1980..2240 runs started; inspect reporterror/completed counts before claims.
- Activation: scenery-activation-fields PASS3042. ModelCCF288 slot12668 assigned2991
  byPC6261; stack7B9C/7CA3. Flags2000->1000 byPC7B5E at3017, firstfar/draw3019
  alreadyinside80k. Pendinglist at61EC, activeD50B, activationcompares object+1B
  segment low16 to playersegment+wordD58C; read runtimeasm around7B4C..7B69.
  lua/world_scenery_activation.lua traces fields and CPUinternalRAMstack809800..809FFF.
  Runtimeasm results/diagnostics/scenery-activation/run/program.asm.
- Original attended world-germany-extended-20260906 immutable. No freshrecord needed.
- Remaining: bigger scenery/activation then cross-gameadapters, weakWorldimpacts
  (optionalImpactCuesOFF, physicalacceptancepending), MAME XMLCheats submenu stretch.
  Toolkitv0.11.1 unchanged. Latest CI atfc586ed all4PASS; finalhead stillneedspush/CI.
- Pushnative tofork only. Export FULLmame0286..HEAD111patches after nativecommit.
  Collection/master ff only afterfinalCI. Neverracingmame.exe. No emulatorbuildwhile
  rootexeisused. AutomatedreplayFFBOFF. Keepmeaningfulupdates <=60sec.
