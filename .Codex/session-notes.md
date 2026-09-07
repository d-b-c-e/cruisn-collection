# Session Notes

Date: 2026-09-06. Branch: codex/world-scenery-activation. User authorized ongoing
fixes until they return, with separate commits/pushes. No return yet. Automated
physical FFB OFF. Native pushes fork/poc/quadlog only, never mamedev/origin.

## Built and deployed

Native e8b8fc3be9c, root vunit.exe SHA256
 d520c414c8bae335abe316695f78ff4794513e97313b000b10b28ff24dfcec47.
Distant Scenery remains OFF by default, World2.4/widescreen/scale>1 only.
Five mountains, four small tree cards, forest strip CB2375. Mountains/forest now
activate up to8 track sections earlier via PC7B69 pending section comparison.
MIDV_SCENERY_LEAD=0 reproduces prior expanded-scenery case (8783/146 PASS).
No hook writes guest RAM; guest transfers lists/flags. Small-tree activation
unchanged. Exact model/radius/flags/program guards; direct backing RAM in taps.
Native/world_scenery.h is canonical. Full113patches reconstruct native tree
0c8391ca7c8749bef3da2d2d8458d422fad11474. Prior checkpoint master/origin14702,
native abe4b98aa38, archived55578f8a at germany-expanded-scenery-native/case/binary.

## Evidence

Review docs/reviews/2026-09-06-background-activation.md and proof same suffix.
Full derived germany-background-activation-native/case and replay8783/146 PASS;
parent12images differ, no original route equivalence claim. Driving~100.005%,
callbackp99~25.6ms; GPU latency/physical feel unmeasured. Both1049mountain/3964tree/
355forest admissions,31712reciprocal reads,max8120;12earlier activations at
5991/6003/7585/7599,3each. All7background-activation-default-regressions PASS.
72Python tests/native unit PASS; CI34073144803 atb06c26b all4jobs PASS.
DenseGL5940..6280 every1:341completed,100changed6023..6122,max6839pixels6093;
all158images6123..6280match. Geometry adds2578, original coords/texture preserved,
but orderFAIL3scenes6077/6093/6119; last has49possiblyoverlapping pairs. Never
mark that strict check PASS. New object sortkey seeds80000 vs earlier object's
updated depth is a hypothesis, not fully established cause. Read-only assignment
probe finds CB1A8B/11A7C allocated5985,pending->active6091,firstdraw6093 inside80k.
Single-model lead8 activates5991/draw5993; visible6041..6094,max4289px.
Video results/diagnostics/mountain-return-comparison.mp4 shows that probe.

## Running / next

LateGL121images3824x2073 complete;11change7694..7714,max107075px7712;
all7716..7780sampledmatch. Initial100/102of121 attempts failed; explicit stop8000
let captures finish. Harness e7e82b6/CI34074373829 PASS,74Python tests.
Bounded global pending lookahead experiment:
lua/world_pending_distance.lua intercepts D58C atPC7B51, returns11+lead0..8,
all pending models, NOT production. Prepared pending-global-control/lead8.lua
provenance wrappers5900..6140 completed, noerror/inputtimemismatch;global8
adds unverified geometry and changes native images. Individualtreecards pending
2008 appear here; selective native currently only2000. Require --scenery-lead0.
Compare geometry/models/completedGL before promoting anything. One emulator at a time.
New explicit WATCH_EXISTING mode in world_scenery_activation.lua needs actual
control/candidate verification: mountain-sort-key-existing.lua targets11C04/
CB2314,5990..6230. Default still requires assignment. Prior narrower traces
missed allocation and correctly failed; don't call those complete probes.

## Context

Original attended world-germany-extended-20260906 immutable. No fresh recording
needed now. compare_scenery --alignment scene/--order-details retains failures;
gl_frames --frames/--every/--details/--contact-sheet validates completed frames.
Earlier CCF288 activation has only22visiblepixels and orderfailure, not promoted.
World24 runtime disassembly: scenery-activation/run/program.asm. Pendinglist61EC,
activeD50B, playerEE0E+50->+1B; threshold D58C=11, cachedD584; transfer7B5E.
Object+12 is depth sortkey, drawing writes atPC93; factory625C..626D seeds80000.
Continue graphics, then cross-game adapters, weakWorldimpacts (ImpactCues OFF
pending physical acceptance), Cheats submenu. Toolkitv0.11.1 unchanged.
No racing mame.exe; don't rebuild root binary while emulator uses it.
