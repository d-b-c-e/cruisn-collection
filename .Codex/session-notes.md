# Session Notes

Date: 2026-09-06. Branch: codex/world-global-distance. User returned, asking for
global distance approaches, external precedents and fresh native-port feasibility.
Continue authorized improvements with separate commits/pushes. Automated
physical FFB OFF. Native pushes fork/poc/quadlog only, never mamedev/origin.

## New direction and research

Read docs/reviews/2026-09-06-global-distance-and-native-port.md first.
Stop growing per-model allowlists as the main strategy. Recommended next:
map shared section/activation/projection routines and prototype host-side drawing
of pending static scenery without guest list transfer, then decode future sections.
The USA original source documents group loading and active/inactive lists.
Jeff Harris's actual incomplete USA native C/SDL2 port was found and inspected:
https://github.com/jeff-1amstudios/cruisin-usa, commit5eeeb65f0c716aa20435286f7d39ea0a99dbc17c.
Source/ROM walker aligns4.4source with4.5binary, customC3xfloat, MAME assertions.
Not built/play-tested locally, not fully playable, don't imply source availability
forWorld/OffRoad/Exotica. Exotica CPU isC32, V-UnitC31; Zeus2graphics differs.
OutRun2006 shared section+culling-node union/dedup, OpenMW distant object paging,
RT64 earlier geometry capture, N64Recomp literal translation inform the proposal.
Clones ignored under results/diagnostics/research; no third-party code imported.
Unbuilt native globalfar draft archived in docs/experiments/world-global-distance,
with native/collection patches checked for applicability. No active source changes
or new binary. Missing tick wiring, checkedpatch generation, harness integration,
unit/runtime tests listed there. Do not treat it as a tested feature.

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

## Completed probes / next

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
Explicit WATCH_EXISTING mode verified: mountain-sort-key-existing.lua targets11C04/
CB2314,5990..6230. Lead0control189writes,activation6117,depth6119=81722;
lead8candidate575writes,activation6003,depth6005~109k. WrongmodelCB2315 fails as
required. These runs complete without diagnostic errors but original-attended
image identity FAILs due existing scenery changes; do not label fullreportsPASS.
Default still requires assignment. Prior narrower probes missed allocation.

global-motion-control/lead8: sceneryOFF,lead0 native, boundedglobalpending0/8,
stop6304,smallwindowGL5900..6300every2,201completedimages each. Controlmatches
attendedprefix.421camera samples5880..6300,firstdifference6184.1263actualADCreads
each,frame/value/PCsame,timestampsdifferfirstindex81. Latercapturesdrivingstate
differs. MotioncomparisonFAIL, no purevisualclaim. Proof2026-09-06-global-distance
includes reports, hashes, baked scripts and contact sheet (viewed).
pending-global geometry counts61615added/41264removed-or-changed,order116fails;
firstchangedoriginaltwoHUDquadsspill5907->5908, so classify timing instead of
assuming allunknownmodelsarebad. Selectivefourtrees probe72early,1374added,
zerochanged/removed butorderfails; archiveonly, userwantsglobaldirection.

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
