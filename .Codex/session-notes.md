# Session Notes
<!-- Written by wrapup; previous history is in git. -->

- **Date:** 2026-09-09
- **Branch:** master

## What Was Done
- **2026-09-09 Off Road future sources:** standalone native/Python descriptors match46,133loaded/future records across12snapshots,2,424actualordinaryobjects and703laterallocations/bindings. Two6000headless probes preserve4,191camera/16,764actualADCtimes;1,978frontiers include7realpartialstates missedbyoldsnapshots. Initial7frontierFAILs retained; conservativewhole-section exclusion qualifiesall7partials. Initialallocation29dynamicmodelFAILs retained/excluded;1,380staticinitialdescriptorsPASS.239Python/no skips,22native,32GPU/61commandsPASS,358sourceidentityc3c81d2a. No MAMEintegration/build/default/GPUrenewal. Continue scene/material/upload guards and hostprojection directly; see docs/reviews/2026-09-09-offroad-future-sections.md. Personalv0.5.0 unchanged.
- **2026-09-09 Off Road transform/LOD:** native/Python prepared oracle matches1399 matrices and selectedLODs plus9602orderedDMA;301 initial yaw rounding FAILs retained, store/reload fixed. Three further6000probes and1scene snapshot preserve4191camera/16764actualADCtimes/all3completed4KGL. Localpending lists86–124objects suggest additional2x geometry;3x remainsloadinglimited in5offline snapshots.235Python/no skips,21native,32GPU/58commands PASS,351file identityddf24a4d. Standalone only, no nativebuild/deploy/default renewal. Continue descriptor allocation/material/scene mapping directly; localallocationtrial may still run. See docs/reviews/2026-09-09-offroad-transform-and-lod.md.
- **2026-09-09 Off Road native model codec:** native/offroad_model.h and independentPython/Lua now qualify1399 projections/9602 orderedDMA commands over3windows, plus463/3309 canonicalrepeat. Four6000 visible replays preserve4191camera/16764actualADCtimes and3completed4KGL each. Initial two-word-stride and raw-page-verifier FAILs retained. 232Python/no skips,20native,32GPU/56commands PASS;348-file identitydf90e420. No MAME integration/build/default renewal; cf58 retains prior7defaultpasses, personalv0.5.0 unchanged. Next transforms/LOD, section/material contracts, hostfuture adapter; continue directly, heartbeat recovery only. See docs/reviews/2026-09-09-offroad-model-codec.md.
- **2026-09-09 USA future renderer and continuous work:** collection39750ad/dd803a0/0672222 and nativeeee9/439c/cf58 are pushed in separate commits. Finalcf58/SHA37c0a4ce is a separate candidate;145 patches reconstruct9befa7f. Future2x adds13/16 images over1x;3x adds3/16 small changes.17 USA runs preserve inputs/camera/ADC;16GL and6,445,085 ordered quads/750 scenes repeat across model/reciprocal caching. Original153,833,626 bytes match both initial/final candidates. Four live and five old scene oracles pass. Final7defaults/UDP-memory/4softwareforce/Exo21GL and227Python/19native/32GPU/53commands pass at341-file identityb04de1be. PERFORMANCE remains OPEN:3x improved95.2% to97.6% (repeat97.0%), still below full speed. Material upload/partial transitions lack live coverage; sky/occlusion/handover remain. Public proof under2026-09-09-usa-future-rendering; raw resources local. Off Road ownDP1/LOD/float-vertex probe and independent draft decoders prepared underresults/diagnostics/offroad-model-20260909 and first control/probe now running serially. No deploy/release/hostedFFB/Worldtuning; personalv0.5/SHA87d04de4 unchanged. One-minute heartbeat is recovery only; continue directly.
- **2026-09-09 USA future descriptors, ACTIVE continuous work:** source9058093; see docs/reviews/2026-09-09-usa-future-sections.md/topAGENTS. Standalone native future decoder, bounded finalallocation/frontier/material probes.26,807Python/native/3,525lateractualdescriptors/3,104bindings pass;1,770frontiers/1,724sources;1,700finalordinaryallocations. Three5012replays preserve3211camera/9633ADCtimes/3late4KGL.8MBatlas equal5samples; initialstaticpaletteFAIL retained, bank4300's sameowner cycles5colors; use livebinding/colors, queueduploads/lifetime open.223Python/19native/32GPU/53commands,339-file identitydb1c5e42 pass. Future not linked;4e565/nativeexport/sevendefaultlastgate/personalv0.5 unchanged. NEXT cachedUSA future rendering and upload readiness, originalroute/resources/4K/defaultgates, thenOffRoad/Zeus alongsideWorld25roads. Existing heartbeat shortened toONEminute recovery; do not pause activework betweenmilestones. No cutoff/release/deploy/hostedFFB/Worldtuning.
- **2026-09-09 USA host pending integration, ACTIVE continuous work:** read docs/reviews/2026-09-09-usa-host-scenery.md and top AGENTS. Collection492bf48/native4e565971954 pushed; separate candidate248aef7c,142patches.2x adds12/16 current4K frames over1x,3x equals2x;755scenes/168874quads repeat, original5012/camera/ADC exact.153833626 original resource bytes exact.217Python/18native/32GPU/50commands and all7defaults/4softwareforce/Exo21GL PASS. Personal87d04de4 unchanged. Current next work is USA future-section placement/material capture; local prototype383/383 oldsnapshot matches.30minutes is recovery ONLY; continue directly between useful steps, no cutoff. Prior PAUSED/cutoff statements below are historical.
- **2026-09-09 morning checkpoint, PAUSED:** read docs/OVERNIGHT-RESULTS-2026-09-09.md and host-layers-and-roads review. Collection1f07de0/544ec63/eb16977/87d5131 implement gated host coverage, capture drain request, reusable road oracle and138-patch export. Native94368ee939e is built separately/pushed, SHA2099a187; personal87d04de4 unchanged. Prior layer5214/5fbf candidate has51 completed4K legacy/coverage/both controls; coverage removes tunnel green line3079->139pixels, no newly different region, coverage/both byteequal; original4502inputs/camera/ADC/resources exact. Initial boot timeout and split41/51,50/51 capture FAILs retained. Final drain candidate small4502/51 captures and300-frame32ms boundary wait pass; final4K run blocked by unavailable4K display. Seven defaults not renewed since de1. Local203Python/15native/32GPU/42commands at388cb344 identity pass. Road oracles23589projections/17821far/21123unclippedDMA;2466clipped excluded. Final8155 descriptors including1332roads pass afterbit24tag correction; no integrated road drawing. Uncompiled native draft saved only under results/diagnostics/world-host-layers-20260909/unfinished-road-draft. Public106-file proof recomputes selectedpixels/routes/scalars, raw geometry/materials/builds remain receipts. Queue is PAUSED; no automatic resumption, deployment, menu cleanup, release or physicalFFB. Cross-game3x incomplete; next road integration then guardedWorld2.5 and other adapters.
- **2026-09-09 World future-section milestone:** collection66ed6ab/d427029/43d462d and native de1d6333cd9 are pushed; candidate0f947fd5 is separate, StreamDeck87d04de4 unchanged. World2.4 future sections give visible3x-over2x mountains/buildings in16/31 completed4K samples; full Germany9269/154 and camera/ADC remain exact,3x repeats31GL/fingerprints,~100% speed/max6.608ms callback. Dense51GL original82.6MB hardware stream/frame4500 geometry/resources equal, BUT new green line across tunnel road at4408 is a VISUAL FAIL. Keep candidate undeployed, no menu cleanup. Roads excluded;416 late unbound descriptors/118scenes. Final6823 descriptors/166frontiers/four native-Python snapshot oracles pass;202Python/15native/24GPU/42commands and7defaults/actualUDP+memory/4force/Exo21GL all PASS at308-file b317fd06. New proof/review under2026-09-09-world-future-sections retain visual and initialWorld2.5 failures. Local next probes: road2308vertex/matrix/center and2140unclippedDMA calls match (1802far-template); World2.5v2 proves modeEBDD/limitD57E predicts2296pending+390active, all2686ordinarydescriptors match; originalpending-only390flagFAIL retained. No host road or native2.5future implementation yet. Other game mapping snapshots pass. Read latest AGENTS for addresses/local draft recipes. Overnight remains ACTIVE to08:00, physicalFFB0; no release/deployment.
- **2026-09-09 02:50 World foundation:** nativec1ef52c2dcc candidateSHA41b0fdf3 built separately/pushed;135exactpatches. RootStreamDeck remainsv0.5.0/87d04de4. FullGermany5runs keep9269inputs/154native/camera/actualADCtimes; summarytracing removes measured16.127secondpolygonlogstall (detailed88.633%FAIL retained), callbacks<0.9ms and>99%intervalspeed,31GL/fingerprints unchanged. No newfuturegeometry. Fullsection8222objects/46angles/970offsets and137mathvectors; correctedv3 captures16444initialmateriallookups+410laterwrites, previousv1/v2initialcoverage explicitlyincomplete. InitialownerAR0, notAR4; tables4151/4150 indexedmodel[-2]/[-1]. Nextmetadataoverride/staticclasses/futureresidency andhostsectiondecoder; specialtype0xB continuespastcaptureboundary. Seven defaults/actualtelemetry+fourforce PASS candidate41b; final199Python/14native/24GPU/39localcommands,299sourcehashesd4237a33. Defaultsacf7 source differs onlythree later allocationdiagnosticfiles, boundinproof. 145-file ROM-freeproof independentlyrecomputes timing/fingerprints/motion/yaw/scalarbindings/7telemetry/4force; fullgeometry/resources/GL/build stayreceipts. No game/buildrunning, physicalFFB0. Overnight queue ACTIVEto08:00; no release/deployment/menu cleanup yet. Review: docs/reviews/2026-09-09-world-host-cost-and-sections.md.
- **2026-09-09 overnight queue ACTIVE:** maintainer prioritizes robust comparable 3x draw distance across all four games and conditional removal of superseded experiments. Reactivated the existing heartbeat with the September 9 work order and an 08:00 America/Chicago stop. See docs/OVERNIGHT-2026-09-09.md for per-game targets, independent acceptance checks, conditional menu migration and candidate/deployment rules. No new implementation or distance acceptance is claimed by this scheduling checkpoint.
- **2026-09-09 public access:** made d-b-c-e/cruisn-collection public at the user's explicit request. Anonymous source, latest-release lookup and updater download pass; v0.5.0 ZIP matches SHA25620d1cf67cc7db82fa6cebf494369117e25bf5cf6eae0e8b7d717a55c830d3734. Updated visibility guidance. Hosted workflows remain disabled, heartbeat paused, releases and personal installation unchanged. This did not complete the remaining history/licence/assets or human-coverage reviews.
- **FINAL v0.5.0:** user accepted watched Cheats tests and explicitly requested release. Published96006e7/ZIP221432/SHA20d1cf67; downloaded exact bytes/tag verified. RootStreamDecknative4ac/SHA87d04de4 deployed with d52backup;26personal files unchanged. Five4Kmenu/replays,7defaults/actualUDP+memory/4forcechecks,5freshboots,196Python/14native/24GPU/10081math pass. Sourcef4d17d05,297files. Frozen1726files/defaults/9pages/6launches18GL/liveEsc/import/setup/support PASS; actual upgrade/rollback/re-upgrade preserve7fixtures. Forty-one human coverage waivers remain explicit. Proof2026-09-08-v0.5.0-release recomputes7telemetry/4force. No game/helper running; user may test Stream Deck. v0.4.0/private visibility/preferences preserved; hosted workflows disabled/heartbeatPAUSED. Earlier pending deployment/release statements below are historical.
- **Latest live Cheats/build targets:** native4ac6a84b51b pushed, separate candidateSHA87d04de4; NOT deployed to Stream Deck (rootd52/SHAe0cf8a8b preserved). Exotica-only Menu Force Feedback source experiment is ready, defaultOff keeps game gate. Other-game equivalents explicitly postrelease, World untouched. Separate Release/Personal targets preserve rig. Five real timer and five restoration/finish probes pass headless/FFB0;196Python/14native/24GPU/10081math pass locally. Clean245b318devZIP220014 has1724files/frozen factory defaultsPASS, SHA0a45aec9. See newest AGENTS and docs/reviews/2026-09-08-live-cheats-and-build-targets.md. Visible menu/replay and7default regressions are pending user testing availability; no game running. Proof recomputes memory/actions, other verdicts hash-bound receipts. v0.4.0/settings preserved, no hosted jobs/new release. Equalizer popup is its independent scheduled updater. Scenery fading is a roadmap item.
- **Evening normal-launch correction:**41a8ba9 fixes unbound env in nested start(); user hit it with USA Always in 1st Place. Added30 Popen-boundary cases across five ROMs/cheats/recording overrides;187Python/native/24GPU pass locally. No new native build or automated game launch. Source launcher must be reopened. User is actively testing through Stream Deck; do not compete with automated games.
- **Public documentation refresh:** current guide index docs/README.md; public readiness docs/PUBLIC-READINESS.md. Correct source-versus-v0.4.0 features, menu paths, Exotica shifting, shared FFB strength/CRISP default, retired Peak Limit, telemetry setup and old rc2 guidance. Native/ZIP preserved; original-code licensing and tracked menu art/music provenance are explicit remaining public decisions. Repository stays private and hosted workflows disabled.
- **Local build policy after Actions quota exhaustion:** both collection workflows disabled remotely; checks now manual-only. No Actions jobs on pushes/PRs/tags. MAME fork has no workflows. Use `python harness/local_checks.py` and `docs/LOCAL-BUILDS.md`; release gate/promotion require `--checks` with full Windows evidence. Do not re-enable hosted workflows without a new request. Local run passes185Python/no skips, native helpers/C31 math and24GPU checks; negative missing-compiler and incomplete-release gates fail correctly. Product/native/release/settings unchanged. Historical CI statements below apply only to their original revisions.
- **Later user-authorized host scenery work:** read `docs/reviews/2026-09-08-world-host-scenery.md` and the new top AGENTS checkpoint. Native `d52b8f95d92` / root SHA `e0cf8a8b498d4499f81228b2fbb3e40367d29fd25e1c86edb9c95ee500c689d1`, 133 exact patches. World2.4 CLI host drawing adds scenery without changing guest activation, CPU, RAM, VRAM or DMA. All7 default regressions pass; no physical force.180tests/all4CI34286683257 pass;287 local/Linux/Windows hashes match89efc97d. Default suite retains41169773 identity; only later read-only section/yaw diagnostics/tests differ, explicitly bound in proof.
- Host160 full Germany9269/154 keeps exact camera/ADC timestamps and repeats31 completed3824x2073 GL images and662946 host quads. 20/31 images change beyondhost80; visible hills/buildings/trees. Host240 adds132quads; sparse31GL equal but dense21GL finds6 brief mountain changes. Original-order/resource checks and13,215-quad independent oracle pass. User restored4K; earlier ultrawide run is marked possibly affected by transition.
- Section probes reproduce180 XYZ/heading/object yaw/section matrices; only2 distinct angles and no flag8 offset sections. C31 polynomial uses7 captured constants. Next future-section palette/texture binding and broader transforms; host occlusion/handover and timing phases remain open. p99host1.54ms but120ms outlier is not screenshot-aligned. No host menu promotion, new release or changes to saved settings/World force tuning. Old heartbeat remains paused. Proof verifier in `results/proof/2026-09-08-world-host-scenery` distinguishes recomputed numerical results from model/resource/GPU receipts.
- **Final 08:00 local checkpoint:** overnight heartbeat `cruisn-overnight-cheats-and-distance` paused through the app at 13:00:37 UTC. No emulator/build active. Source/native pushed; final changes only document the checkpoint. Read `docs/OVERNIGHT-RESULTS-2026-09-08.md` and refreshed ROADMAP next. Do not resume the schedule without a newer instruction.
- All four CI34228828289 jobs pass at8157c3a; both downloaded platform artifacts exactly match all268 local source hashes, unchanged8c20a787. Final native/rig/StreamDeck/v0.4.0ZIP hashes pass; source/menu/CI/deployment receipts are archived in `results/proof/2026-09-08-overnight-checkpoint`. Seven default binary regressions and168tests remain the automated baseline; no new attended acceptance.
- Morning follow-up: all 814 Exotica changed depth biases are 2047 -> 0 at unique matched geometry, with the bias branch used in both captures. Standalone `results/proof/2026-09-08-exotica-admission/analyze_state_bias.py --check` recomputes the separate receipt. Trace render register 0x15 provenance next; this does not waive scene/frame FAILs or prove the visible cause.
- Final source offscreen Settings/Off Road/Exotica pages were rendered and visually inspected. Three images and a source/config-bound receipt are in `results/proof/2026-09-08-overnight-checkpoint`. Saved settings remain intact. ROADMAP now links the preserved historical checkpoint and lists current work, removing obsolete active RPM/checksum/plugin assumptions.
- Latest07:35: global Exotica admission tools4c47b67 pushed. Native12e/release/settings unchanged. Read-only6000/21originalGL passes; actual589 adaptive90000..130000 rejects96016/132624tests within168375depth. Timer0normalclamp60000..130000; distinctspecial47500case unobserved.
- Four6000coherent/admit160/admit190/repeat trials4500..5990.160 repeatsbothtraces/15GL;190samefrustum/GL.12imageschangebutonly52pixelsat4700and2at5100; laterroute/cameraidentityunproven. CandidatephysicalFFB0.
- 4Kpaired4700:367/374changedpixels nearhorizon; resources equal. BOTHstrictframe/sceneFAIL:2560/2612originalquadgeometrymultiset,2409ordered,52unmatched;814activedepthbiaschanges. Mostalpha differencesinactive. No nativeadmission/menu promotion; needstate/order isolation orhostdrawing.
- 168tests/4CI34225451570 PASS;268sourcehashes same8c20a78779c02b150e4aa3f6a18181a6199a862d736fe9fd24211530e51d9c13.83entry admissionproof21,687,380bytes SHA37aa0c0e953c145a0a4d7bcd17348c80cb5c15d9b8723fd77deb2837ae53a3d8. Verifier reuses the hashed companion far archive and passes both working-copy and staged Git-blob checks.
- No emulator/build active. Finishmorninghandoff andpauseheartbeat at08:00local. Keepforce/Worldnormalizationdeferred andv0.4.0baselineimmutable.
- Latest07:05: Exotica true far trials complete; toolsdc1f07d pushed, native12e unchanged. Coherent204800 vs2x/3x:515968equalposes/3035extraadmissions/no losses,15GLsame;2x rawtrace repeats.
- Matched4864:199addedquads+8palettes;438originalquads shiftframe only, strictFAIL retained. New explicitZeus --alignment scene matches2606orderedoriginals/effectivepalettes/resources. BothcompletedGLsame.
- GPUocclusionquery0visible/173withoutdepth; doubleddepthrange remains0/173. No newExotica far menu/native/shader. Need upstreamloader/activation, not another advertisedmultiplier. Probe limitations inreview.
- 166tests/all4CI34223306424; local/Linux/Windows identity54c2b421df9a39bc29c94bf493f2b2805dd8d3a5336d8cd47f0848bb87a10b4b. 80entry ROM-free proof49MB, archiveac473773075631e6ecafe7e587f171aa8f6386a77c4cd80c414bff9e5c43f0b9. Archive verifier passes both working-copy and staged Git-blob checks.
- NEXT read-only Exotica streamer probe: staticB710..B712 stores90000at589; B7B9..B7BC comparesupper+12 tocurs598. Do not mutate without runtime evidence. lua/exotica_streaming.lua currently uncommitted. Read-only control matches6000inputs/21originalGL; actual589 varies90000..130000,96016rejects/132624tests. Bounded160k/190k coherent trials active underresults/diagnostics/exotica-streaming-20260908. NoFFB, preservedrelease/settings, stop08:00local.
- Latest06:25: OffRoad native12e9ea6a374/SHA9936c716 built/pushed;129patch exacttree85f158ec. Core2669afe/menu ba3364c pushed; proof/docs follow.
- DefaultOFF OffRoad Draw Distance0/2/3 in its top-level Experiments context. Canonicaloffroad_distance.h: no guest writes; guarded far/clip/ceiling and59 projection consumers. Stock1 is CLI observer;0/unset nohooks.
- run_offroad_native_trials.py is the NEW native runner; old run_offroad_distance_trials.py remains the bounded Lua runner. replay/derive/attendedrecorder --offroad-distance; replay/derive --display-size W:H select actual display.
- Four6000 matrixtrials: stock exact;2x/3x5of42GLchange,2xvs3x42identical. 2x counters/camera/ADCevents/42GL repeat. Derived2x6000/13GL3824x2073 repeats.
- Strictoldroute ADCtimesFAIL butcamera/actualADCvalues equal1800..5990. Frame4400:715commonordered+1oldcoordinatechange+23new; texture/paletteequal. StrictgeometryFAIL retained. Target386VRAMwords covered;384otherpagehistorychanges.
- Nativeinitial781af835091 duplicateCSVframe822 rejected;12e correctsperframeemit. Full67776 reciprocalROMentries match measured rational8decimalhalf-even generator.
- All7defaults actualtelemetry/memory/Worldpassthrough/Exo21GL PASS;163tests/4CI34219090827,262sourcehashes same333901cdae9af35e404fc256ebc27170589c99927ceeb116024e081d00e4244b.
- 190entry ROM-free proof recomputes7telemetry/4force results, input/motion/nativecounters; GL/resources hashboundreceipts. ZIP077b1aee432ddc754c7b7897cceef876732ba0ad48baae4ae0f27318d04638c6. NoFFB/Worldtuning or personalconfigchanges; releasedv0.4.0ZIP/tag intact.
- NEXT autonomous: Exotica coherent true far-plane trial targeting4686..5986. Current nativevisibilityonly changesCPUprojection/margins and keepsfar204800. Need extend reciprocal capacity beyond12800 for2x/3x; existingworldhelpercaps15000. Do not assume faradmissions are drawn or resident. No newExotica edits/trials in06:25checkpoint yet. Heartbeatactiveuntil08:00local, then pause.
- Latest05:30: Exotica native6a2b7ae/SHAcec6d98a built/pushed;127patch exacttree6d2e8a22. Collectiondc1f5af/0e758f3.
- Exotica Widescreen Scenery optional menu now restores real edge geometry. Explicit CPU projection/margins/both controls leave far204800 unchanged.
- Matched3500 margin scene preserves3691 ordered records/3532quads/effectivepalettes and texture RAM;1palette+1quad added. Combined42originalchanges remains strictFAIL.
- Lua5x6000 andnative5x6000; all19 Lua/native images match bymode. Both6000countertrace/19GL repeats. Separate margins/both cases each6000/35GL repeat.
- Later margins/both pictures diverge after5300; no originalroute or farbenefit claim. Actualfarrejects3669 at4686..5986 give next Exotica target.
- All7defaults actualtelemetry/memory/Worldpassthrough/Exo21GL pass.157tests/all4CI34213524599;255sourcehashes same onlocal/Linux/Windows, identityfa5809b1.
- Proof170derived+3fulltraces recomputes decisions/counters/inputs/posefailures/geometryhashes; stock reconstructed frompriorarchivedbaseline. GL/resource checks remain boundreceipts.
- SourceStreamDeckhasnewmenu/native; savedsettings andpublishedv0.4.0ZIP/tag unchanged. No physicalFFB/Worldtuning, no emulator/helper left.
- Next: OffRoad coherent native adapter/cost/repeatability; thenExotica laterfar-limit trial. Heartbeat active until08:00local.
- Latest04:25: Off Road/Exotica diagnostics5937063/410ad43; native8b/SHA638 unchanged, v0.4.0 ZIP rehashed unchanged.
- Exotica339018 validated CPU sphere samples: true reciprocal predicts4051 extra/no losses;88px margins21717;both28610.6000inputs/21completed4KGL exact.
- Exo acceptance marker68A3/PC68A4; earlier689D lies inside branchdelay and was rejected by analyzer.15file ROM-free proof, verified from Git blobs.
- Off Road full2x/3x6000 controls: camera/ADCvalues equal,220 pixels in5/42GL512x451;2xvs3x identical. Initializer reset and unrelated ROM-read failures retained/fixed in diagnostic.
- Off Road trace costs54%/53% emulation (control94%); no product promotion. At4400 texture/palette equal,715common quads ordered,1coordchange+23new. Strict geometryFAIL retained.
- All147Python tests/4CI34209001116 pass at410ad43.92file Off Road ROM-free proof; no physicalFFB or Worldtuning.
- Next bounded Exotica stock/true-reciprocal/margins/both GL matrix; then native low-overhead adapters if justified. No emulator/helper running; heartbeat continues to08:00local.
- Latest USA: native8b151aa9c2f/638c74ff built/pushed,126patch exacttree5e10f68c9badba2385d38d6178eaae1be02d48b6.
- USA CLI global adapter9e70f6a: five5012frame controls;1x exact, residency altersoldroute.2x repeats5012/83native/19GL1904x993.
- All7currentdefaults actualtelemetry/memory/Worldpassthrough/Exo21GL pass.139tests/all4CI34202538087.
- All237sourcehashes local/Linux/Windows match946fc6523f110ddc2d91e5a481b4a6cbdd0cc067d73452cc3ab923e42023974c.
- 107file ROM-free proof recomputes USA distance/input/motion; archived receipts retained for oldrouteFAIL and GL repeat.
- Off Road all67776 table entries exactly reconstructed with rational eight-decimal half-even rounding; naivePythonround2tiesFAIL retained.
- USA no menu promotion/geometry/order/resource/attended acceptance. Next OffRoad floatclipping/vertex path and Exotica frustum probe.
- v0.4.0 tag/ZIP unchanged, no furtherrelease or Worldtuning. No emulator/helper remains running at checkpoint.
- Overnight02:40: World2.5 global Off/2x/3x +0/8/12 adapter/menu in117e8fb; native dae2569f793 built/pushed.
- Sourcevunit SHA f06a160b57c72737e89aedcc159f87cbe173c82620722ea109e84dcdffe70252;125patch exacttree2f4f89c388ba380aa578036143049a723dcad00c.
- All7defaultcases actualtelemetry/memory/Worldpassthrough/Exo21GL pass; existingWorld2.4global2x8783/146 passes.
- World25 original/2x+8/3x+8 full6000 trials complete at~100%; extended trials change original route (retainedFAIL).
- Separate2xcase repeats6000/100native/11GL. 2xvs3x match100native+42GL but33camera samples/ADCtimes differ.
- 132tests/all4CI34199270158; local/Linux/Windows all229sourcehashes match identity85ad5a17558ffc18d7f3d8eac431151e6c7582ba6359bd3b8ad3392e573ee152.
- 67file ROM-free proof archived under results/proof/2026-09-08-world25-distance, counters recompute.
- USA residency b720b98 read-onlyprobe matches4305;22713 pending visits within2x75k, max117026.
- Overnight02:05: all5revision distance capability matrix now measured. Native44c3494d6af unchanged.
- Four4305frame V-Unit probes pass; Exotica6000/21GL passes with identical distance trace to headless.
- 131tests pass;35file ROM-free proof recomputes counters. See docs/reviews/2026-09-08-distance-capabilities.md.
- Overnight01:40: Cheats menu + top-level Experiments implemented/pushed in separate commits.
- Native44c3494d6af bridge uses MAME engine; built eb2db42a90288bf37ac0dcce9b9ce2106c136fad198c52320ee2b3af3c435a97.
- Full124patch export tree f7af3475d0ce0b6347e2be669338283437a81447 verified; source Stream Deck uses new native.
- 128Python/4CI34195061384 pass; seven default binary controls pass (six initial + Exotica4K rerun).
- Fixed Zeus monitor selection for exact replay: secondary1080p mismatched4Kreferences. All21GL now match.
- Five4000frame cheat-on replays against final binary and five real timer on/off memory probes pass.
- Frozen devZIP f8a804f passes9pages/4defaultboots+1Worldcheatboot/15GL/import/setup/support,1649files.
- 75derivedfiles archived in results/proof/2026-09-08-cheats-and-experiments; ROM-free verifier passes.
- Published v0.4.0 at c098290aeaa1f19ca37d7bee56c747cbf51350b5; tag and downloaded ZIP verified.
- ZIP build/CruisnCollection-v0.4.0-20260908-000947.zip SHA fd292b0d4ba4d2a97147c6ffc1fb95407e3891495dfb68fada2f899e3c31ba4a.
- All117Python/4CI34189532162,7replays,5freshboots,4frozenlaunches/12GL,24GPUfixtures/3menus pass.
- Actual ZIP upgrade preserves user-state fixtures and all1637files; both exact comparisons100.0000%.
- 61derived receipts in results/proof/2026-09-08-v0.4.0-release; verify_archive.py checks bytes/identity.
- Recorded explicit maintainer sign-off with41human waivers, not fabricated PASS observations.
- Created active heartbeat cruisn-overnight-cheats-and-distance, every30minutes, morning08:00local checkpoint.
- User archive now imported into rig/cheats; all selections remain OFF. Continuous toggles/choices supported.

## Decisions Made
- Repository remains private; anonymous updater remains unavailable. Release exact ZIP, no rebuild on promotion.
- CRT on/full-wide/scale4/freeplay defaults verified; experiments remain off; personal settings untouched.
- Preserve released v0.4.0 tag/package while implementing postrelease improvements in separate commits.
- World FFB passthrough restored; no strength tuning/normalization overnight. Exotica DIP motor polarity corrected.

## Open Items
- [x] Initial Cheats submenu and top-level Experiments. See docs/reviews/2026-09-08-cheats-and-experiments.md.
- [x] Global distance capability matrix across all4games, including World2.4/2.5; no native changes yet.
- [x] Guarded World2.5 global adapter, optional/defaultOFF; no attended/geometry/order acceptance yet.
- [x] USA global projection/admission CLI trial; no launcher promotion. Five5012frame trials complete;
      residency changes originalroute. Separate2x repeats5012/83native/19GL at1904x993, not4Kacceptance.
- [ ] USA geometry/order/resource validation and fresh attended/second-level recording remain open.
- [ ] NEXT OffRoad own floatfar47296/clipping63680/ROMtable path; Exotica guarded CPUfrustum probe.
      Full OffRoad table reconstruction now exact across67776 entries. Read distance-next-adapters.md.
- [ ] Live cheat activation for one-shot/code-restoring actions; individual rank/nitro/custom-choice validation.
- [ ] Physical second-wheel/manual/soak and wider track coverage remain unperformed alpha limitations.
- [ ] World oscillation/normalization, New York black flashing and3x/+12crash remain known issues.

## Next Steps
1. Follow section3 of docs/OVERNIGHT-2026-09-08.md. Cheats initial milestone and Experiments move are done.
2. Continue Off Road culler/vertex/clipping and Exotica CPU-frustum trials. The capability matrix,
   World2.5 adapter and USA CLI adapter are implemented; inspect their acceptance limits.
3. Downloaded XMLs are in ignored build/overnight-cheat-inventory; archive C:/Users/antho/Downloads/cheat0279.zip.
4. Preserve ROM revision checks, cheat-off defaults/replay identity; keep physical force off in all automation.
5. At08:00America/Chicago Sep8 checkpoint and pause heartbeat; no additional release/visibility change authorized.

## Context for Next Session
Native E:/Source/mame-src/vunit.exe remains8b151aa9c2f on poc/quadlog, pushed fork,
SHA638c74ff4227532d0ff42be4cd46cb8a358a1a343549abb107bb56050e91bd74.126patch export
exacttree5e10f68c9badba2385d38d6178eaae1be02d48b6. Stream Deck uses source launcher
and this binary. Cheats and top-level Experiments are complete; USA global CLI only.
Publishedv0.4.0 ZIP/tag are immutable, rehashed unchanged04:22. No newrelease.

Read docs/reviews/2026-09-08-exotica-frustum.md and offroad-global-distance.md first.
Collection5937063/410ad43 diagnostics are committed/pushed,147tests/all4CI34209001116
pass. Raw evidence results/diagnostics/{exotica-frustum,offroad-global}-20260908;
proof folders same datednames under results/proof, ROM-free verifiers included.

NEXT: Exotica CPU sphere counterfactual now validated. True reciprocal mainculler
predicts4051extra admissions, horizontal88margin21717, combined28610; no visible
change yet. Build bounded four-way Lua GPU trial first, retaining stock control.
Only replace clamped readPC688C using depth cached atfar tapPC6888; preserve RAM,
short-rangeC371/C375 helper and unusedfar204800. CPU horizontal center read67D0 at
PC6898 can become344, upperplane67CE atPC689C can become687 for88px margins;
other consumers MUST stay original. These precise values are a proposed trial,
not implemented. Record effectivefactor/margin in observer; its current analyzer
assumes stockreads. Independent accept marker68A3/PC68A4, not delay-slot689D.
Run completedGL during2500..4300 plus candidate repeatability and resources. No
newnative adapter until useful visible evidence; do not equate admissions to pixels.

Off Road diagnostic2x/3x completes6000, camera/actualADCvalues equal to original,
ADCschedule and originalpixels differ.2x/3x42GL equal,220pixel gain vs original.
Fivewords include11221/11223 initializers; game resetsactive1B724/5 fourtimes.
Virtualtail must check PC+AR0+actualindexedaddress; resourcePC1EA8 has staleAR0base.
Large Lua ROMtap costs~half emulation speed, not product acceptance. At4400 texture/
palette same;715original quads ordered,1changes3coords,23new. GeometrystrictFAIL
preserved;386targetpage changes covered,384otherpage outside that narrow scope.
Fullcandidate repeat, nativecost and attendeddrive remain open. SyntheticElPaso
sample goes offcourse/slows; no broadlevel acceptance. Do not promote to menu yet.

Native/guest changes can alter actual ADC interpolation/routes. Preserve originals;
require repeatability and freshattended acceptance for handling. No physical FFB
unattended. World normalization/oscillation tuning remains explicitly deferred.
No emulator/helper remains. Heartbeat cruisn-overnight-cheats-and-distance stays
active until08:00America/Chicago September8; finish safecheckpoint and pause then.
