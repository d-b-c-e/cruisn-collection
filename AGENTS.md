# Cruis'n Collection — agent instructions

## Current work: frontend UX deployment and rendering parity, September 19

Read docs/reviews/2026-09-23-rendering-parity-checkpoint.md for the compact
four-game status, remaining evidence gates and next efficient sequence.

September23 Hawaii offline skirt trial REJECTED: single-edge extension makes a
narrow hanging strip; seven-edge continuation makes a rectangular wall and
1,092 new near-black pixels in saved World2.5 scene5900. The authored gap is
not fixed by more distance or a generic skirt. Read
docs/reviews/2026-09-23-world-hawaii-skirt-trial.md before revisiting. No
native build, live game or deployment resulted.

Completed-frame `gl_frames.py --details` now emits near-black and 3×3 spatial
review hints. Existing Exotica Mars, World Hawaii and Off-Road El Paso saved
pairs were reanalyzed without gameplay; intended changes still fail exact
equality. Read docs/reviews/2026-09-23-completed-frame-triage.md. Dark pixels
in added scenery are not automatically a texture defect or a parity pass.

Off-Road El Paso attended frame3120 sharp turn exposes a blue far-left ground
opening in both ordinary and3x 4K saved images. New bounded physical1440 replay
passes3200inputs/native/one completed image and verified mirror;3x host contributes
32066 visible-page pixels on the left, but opening persists. Initial preset+
mirror run FAILED immediately because quiet journals exclude mirror. Preflight
now rejects the combination; explicit capture-mode run passes. Read
docs/reviews/2026-09-23-offroad-left-margin-gap.md before proposing a fix.

Matched source3116/display3120 confirms Off-Road gap is ordinary sky between
3x auxiliary terrain and near ground at fine(60,960), with no projected host
quad bounds at native(-71,158..161) after accounting for the86-coarse margin.
The initial x15 coverage report is superseded, preserved locally.
First wrong-source3118 raw run FAILS;
corrected run passes3200 inputs,708 packets and page join. The continuous
metadata verifier now bounds all scene rows by runtime stop while keeping
exact capture-window and packet checks. Read
docs/reviews/2026-09-23-offroad-left-margin-source.md before future work.
Subsequent same-source RAM/resource and original DMA captures PASS3200-input
prefixes. Original completed3120 pixels and8indexed planes are exact to the
matched run;499 page1 original commands span3116..3117. At native(-71,158..161)
only backdrop command1 intersects; nearest original ground starts y163, host
masked-texture quad470 ends y156. Combined source report is
left-gap-source-analysis-v5.json; neighboring host470 and original ground66
are each two native units from the sample but use different palettes/textures;
no renderer fix or general gap policy qualified.
The source-backed Margin Fill screen predicts ground-column smearing, not
geometric repair: row960 has194 sky pixels from x0 with ground pen27207 at
boundary x344. Keep retired global Margin Fill off; no live on/off image was
run. Read the source review for seven-row evidence.
Reusable V-Unit sky-gap triage now screens10 saved indexed gameplay captures:
Off-Road3120 has one5841-pixel host-bounded region and915 connected ordinary
sky pixels (6756-pixel envelope ending x228); four other Off-Road plus two World and
two USA captures have zero by this narrow predicate; later Off-Road3136 is
positive at the32-coarse default. Duplicated views are not
independent routes. No fill enabled. Read
docs/reviews/2026-09-23-vunit-sky-gap-screen.md and preserve source-hashed
local vunit-sky-gap-screen-v5.json; v2/v3 remain narrow predecessors.

Offline palette reconstruction of the saved Off-Road3120 frame is near but not
byte-exact (121/3,442,032 pixels differ by >1 channel unit). Four targeted
pen-copy fills produce visible repeated bands/cutoffs and leave the wedge tip.
All rejected; no runtime fix. Read
docs/reviews/2026-09-23-offroad-gap-fill-screen.md before revisiting.
Saved3116 Off-Road billboard screen independently reconstructs all708 existing
host packets byte-exact;469 eligible static future sources yield46 material-
valid projected extras, none intersect the left gap (nearest103 native units).
This rules out only that undamaged static class in this scene, not custom or
dynamic geometry. Read the billboard section in the margin-source review.
One bounded Off-Road El Paso temporal replay PASS3200inputs/native/11 completed
2544×1353 views at3100..3140 every4, stable physical1440 display, literalFFB0
and owned stop. Frame3120 is byte-exact to prior source-joined capture. Blue
opening visibly shifts/widens across the turn; paired CRT-color counts are
heuristic, not exact sky area. Read
docs/reviews/2026-09-23-offroad-margin-temporal.md; source-hashed v2 report and
contact sheet are local. The first preset prepare-only plan ended host drawing
at2250, and an attempted override rejected; neither launched MAME.
Matched no-host replay also PASS3200 inputs/native and11 completed images.
Source-hashed temporal-screen-v4 reports3x changes529..37898 completed pixels
per frame and reduces sky-like left-ROI counts by3..3377 paired pixels in all11;
the lower blue wedge still visibly persists. These are heuristic color counts,
not exact geometry area. Paired contact image is local. No product promotion.
Second source-joined Off-Road3132/display3136 PASS3138 inputs and completed BMP
byte-exact to temporal capture;689 host packets, sampled native(-71,156..158)
remains original sky with no host bounds. Sky-gap screen default now32 coarse:
strict7438 and connected11649 pixels at3136; former16 default missed it.
Read2026-09-23-offroad-margin-temporal.md. First source-prepare rawFAIL from
host-last3150 beyond drain3136 retained; corrected last3136 passed.

September23 owner resumed autonomous overnight work. Three2560×1440 panels
are attached and Windows currently enumerates three separate monitors with
DISPLAY1 primary. Earlier it alternated a7680×1440 merged monitor and one
2560×1440 monitor. No 4K display is connected; the frozen4K Mars comparison
remains pending. Native4df profiling found14
completion bursts/1236callbacks; native54df isolated tap removal at99.4126%
of their cost. Opt-in nativebbcb fixed opcode hook preserves all8209 Mars inputs,
six completed1440 images and lifetime counts while reducing completion time
209.3094->0.5454ms; next callback intervals>25ms fall14->1. Six other long
intervals remain. Its Amazon11260-input run preserves input/native and6/7
completed images exact but raw report FAILS one7680×1440 capture at6300.
Do not recast that failure as a pass.

Native4c6 opt-in single-panel geometry selects center2560 from merged7680;
compiled geometry and17Python contracts PASS. Subsequent merged-mode native
replays FAIL owned queue timeouts before full qualification. Native64e opt-in
128MiB ring reaches4700 with three byte-exact2560 images, then fills/stalls;
do not make128MiB default. Nativee468 copied-byte cursor trial also FAILS at
frame17. Stage diagnostics locate repeated frame17 stalls in GL presentation
setup, and after uniform caching in SwapBuffers. Source does not establish a
specific faulty GL call or driver. Native006 restores default batch-end cursor
publication and is built/exported as279patches. Preserve raw failures.

On stable physical DISPLAY1 at2560×1440, native006 now PASSes a bounded5700-input
Mars replay: six completed captures exact to the prior1440 opcode control,
input/native comparisons exact,64MiB ring drained and GPU joined. A full11260-
input Amazon/name-entry replay also PASSes; seven completed2560×1440 images,
including frame6300, are byte-exact to the saved slot-hook control and shutdown
is quiescent. Earlier merged-display failures remain failures. These runs qualify
the optional opcode hook on two routes at1440p, not merged-mode stability,4K,
interrupted-work reset, physical FFB or product promotion. Pristine startup and
quiescent active Exotica resets already qualify on separate recorded routes,
including a pre-device FIFO check; consult the September16 reset reviews before
new work. NEXT investigate genuinely interrupted work or another independent
parity issue; avoid more repeated full drives without a changed hypothesis.
Personal UX707, publicv0.5.0 and force settings are unchanged; all diagnostic
runs use literal MIDV_FFB=0. Read
docs/reviews/2026-09-23-exotica-lifetime-stutter.md for exact local evidence.
The replay harness also has opt-in --display-watch topology polling. Ten focused
display/watch contracts and one short180-frame ordinary Exotica replay pass
with FFB0, stable physical1440 preflight and zero observed layout changes;
that smoke has no extended-renderer or long-drive claim.
Merged-display replay preflight now rejects old Zeus binaries without the
single-panel capability; bbcb fails prepare-only,006 prepares, no game run.
Merged-center selection requires explicit --zeus-merged-panel; without it,
a7680 desktop fails a requested2560 display before launch.
The previous global desktop pause is superseded by the owner's September23
explicit autonomous continuation; serialize shared rig and keep FFB0.

Owner authorizes local UX deployment through coordinator
01a07ac3-e639-7762-a698-5365d447ee7e. Personal Stream Deck source target is this
checkout E:/Source/cruisn-collection. UX sourceb8d2c49 is deployed through master753b2de with
reviewed native707fd6a8f0a (accepted4ac renderer lineage,142patches). No unrelated
4df renderer changes are deployed. Exact package and closed-target backups are
under results/diagnostics/ux-20260919-deployment-v2; verified.json PASS:43settings/wrapper/profiles unchanged.
Prior frontend79a192b/eb78f4f deployment remains documented in
docs/UX-OVERNIGHT-2026-09-16.md. Publicv0.5.0 unchanged; no unattended torque.

Native707 SHA f1f908e66784b657d892e651850693c99e606ffcf093397f9a994975f1c51c01.
091/33/e5/707 exports ALREADY RAN; never re-export their appended baselines.
e5 is rejected for persistence before actuator stop;707 attempts all stops
before filesystem persistence. Actual-function blocked-flush/failed-stop fixture
and independent review pass. Read2026-09-19-output-disconnect-ordering.md.
One earlier091 device-free stop replay passes3300inputs/55nativeimages exact,
324zero worker ticks despite227nonzero requests; no physical/live-key claim.
Native57 calibration goldens and actual backend/core fixtures pass. Strict
identity has no name-only migration: legacy owners confirm an output device once.
Unresolved saved-On gets Configure / Continue without FFB / Cancel; override
is launch-only, saved strength/tunes retained. World force exception unchanged.
Read2026-09-19-control-launch-transport.md and2026-09-19-control-setup-ui.md.

Integrated UI29/settings7/common-launch7 tests pass. Final local package
CruisnCollection-dev-20260919-162140.zip includes native707 with exact capability
and142patch source receipt. Frozen launcher SHA
10058cc02de6b2e78a95511a582a1a01f43754e6c381b1c7930ef296df6aae21 passes
fresh/legacy/saved-Off configuration checks without changing fixture bytes.
Model24/control-launch8/reader4/session12 focused contracts already pass.
Thirty-two720p/4K CPU layouts pass. Frozen6c4407e actual4K frontend passed
warning/cancel, pointer navigation, F6 modal cancel, F8 Off/strength retention
and focus recovery. Empty inventory prevented real axis preview/calibration;
no physical wheel/force or in-game key acceptance. Finalb8 wording removes the
misleading capability-only Ready label; no native change or repeat live test.
verified-wording.json PASS:26source blobs/43settings/wrapper/runtime preserved.
The September19 global desktop pause was in force until the owner resumed
autonomous work September23; retain its historical evidence below.
Shared UX guidance94dc3a1 read. No new rendering scope or public release.

## Rendering checkpoint

Dated findings below retain the personal87d baseline at the time of those runs.
Current personal native is the reviewed UX707 described above; the rendering
source and candidates remain separate. September19 lifetime prepare-only PASS
at results/diagnostics/exotica-mars-timing-20260916/lifetime-prepared-20260919.
No replay executed; wait for an explicit coordinated slot.


Latest: docs/reviews/2026-09-16-exotica-lifetime-timing.md.
One remaining-profile replay8209inputs/136native/4completed4K images exact.
Source/stage/queue phases do not explain remaining30-35ms pauses. New bounded
lifetime callback timers native4df727db105 built/frozen/attested268patches;
Python3/native1 PASS, live timing qualification awaiting coordinated rig slot.
September19: coordinator explicitly says old quiet-slot hold expired and new
request is NOT granted. Do not launch pending lifetime-profile until a fresh
slot grant. Native/frontend candidates untouched. Offline cadence analyzer
and3focusedtests PASS: existing3700..5690 has17>25ms intervals, none of33
immediately after acknowledged screenshots (max19.362ms). This rules out an
immediate screenshot stall for those17, not delayed I/O or other host costs.
Evidence remaining-cadence-20260919.json; no extra replay. Current monitor is
DISPLAY1 primary3840x2160 only; --compare-gl selects it from reference size.
Shared diagnostic execution now requires literal MIDV_FFB=0 even when callers
omit the key, and rejects conflicting Windows case aliases or force tests
before launch. Six focused runner tests PASS; no game/device run. See
docs/reviews/2026-09-19-diagnostic-force-guard.md.
Previous qualified native1fccd423f39 below. Shared UX rollout also authorized
by owner through coordinator task01a07ac3-e639-7762-a698-5365d447ee7e; read five
CONSUMER UX documents in dbce-wheel-mod-toolkit, preserve rendering scope.
Details of previous improvement: docs/reviews/2026-09-16-exotica-mars-phase-timing.md.
Existing Mars recording sufficient; no redo needed. Profiling window7780..7840
found future graphics-queue submission blocking emulation up to20.824ms.
Native1fccd423f39 skips ONLY disabled per-scene diagnostic hashes on CPU/GPU;
material/lease/ownership/capture checks unchanged, V-Unit rollinghash untouched.
One matched candidate8209frame replay PASS input/time,136nativeimages,4completed
4KGL images EXACT100.0000%. Queue max20.824->0.187ms;62frame window >25ms 6->0,
max35.683->18.850ms. Broader >25ms 61->44 but maximum66ms remains; no claim all
stutters fixed or physical wheel acceptance. Continuous receipts/drained/joined.
LOCAL results/diagnostics/exotica-mars-timing-20260916/quiet-hash-profile,
timing-before-after-qualified.json. 267patches exported/attested; all three
export scripts ALREADY RUN. Timing native/Python contracts andjournal testPASS.
Crash fix dd60206a0ee retained; original failedretry2 intact. No newattendedrun.
NEXT use this recovered route for remaining scene/performance/margin work;
remaining isolated pauses and broader route/FFB gates still open. No repeat
broad suite or extra drive merely for the already-fixed pointer/queue issue.
Overnight continuation authorized; recovery heartbeat ACTIVE, not a work cadence.
Investigating remaining repeatable Mars pauses;personal87d/publicv0.5.0unchanged.


Latest: read docs/reviews/2026-09-16-matched-host-capture.md.
Native07e9eb25de5 frozen263patches/attested;
SHA1adac2fd14f4443b0c41366bfd8be144abfe42320c2ae539d50ec963488e830e.
--vunit-host-metadata-frame S separatesoperands frommirrorP; explicitmatchrequired.
ActualOffroad2528inputs/nativeimages727camera2908ADCexact. S2520/P2524visiblepage1
1482quadsexact; originalDMA931from2520..2521. ROM/RAM/textures/palettes/metadata2520
byteexactprior083; sharedGL2520exact. New2524GL4KCRTviewed,0:02.96/49MPH/2AUTO.
Bothpagesopacityall1;nowvisiblepagealigned. Noactualfade/newbillboardsenabled.
11focusedmirror+4completiontestsPASS. No broadsuite.
LOCALW/offroad-matched2520(-qualified),metadata-presentation-native-export.json.
Matchedbillboardscreencomplete: read2026-09-16-offroad-billboard-visibility.md.
Existing1482host+931originalcommands reproduceALL4388544completedindicesexact.
Added205futurebillboards changeZERO afteroriginalforeground. No runtimepromote.
Saved8760 existing516hostDMAexact;31billboards with449originalcommands change10
indices in4x3region, NOTmatchedcompletedacceptance. 3360isolatedonly.
LOCALW/offroad-billboard-completed2524,offroad-billboard-ordered8760.
Standalonehelpers a7e64cc397sources/DMAexact remainuseful, damaged/dynamicexcluded.
Fresh attended Exotica input now received; crash/replay results are above.
Another attended launch still needs the user; wheel/FFBacceptance also needs
maintainer. Do not repeat currenthiddenviews seekingpositivecounts.
Recoveryheartbeat ACTIVE; no paritycompletionclaim.
Unresolved: broadercourses,visibleouterhandover,FFBnormalization/finalpackage;
Exotica interrupted/degradedreset remainsstrict,notuniversallyaccepted.
Personal87d/publicv0.5.0unchanged.

No game/build/test active. Personal87d/publicv0.5.0unchanged.
No deploy/release/physicalFFB/hostedCI. Continue directly whileparityremains.

Continue autonomously through useful parity work. Commit completed changes
separately and start the next item; do not stop at a milestone or wait for the
heartbeat. Stop only for a real user-dependent roadblock or a user pause.
The recovery heartbeat is a backup, not the work cadence.

Read these current references first:

- [Remaining release work](docs/reviews/2026-09-15-parity-remaining-work.md)
- [USA race transition](docs/reviews/2026-09-16-usa-race-transition.md)
- [Continuous3x preset](docs/reviews/2026-09-16-scenery-presets.md)
- [Optional Exotica endpoint capture](docs/reviews/2026-09-16-exotica-optional-endpoint-capture.md)
- [Quiet continuous V-Unit](docs/reviews/2026-09-16-vunit-quiet-runtime.md)
- [Off-Road 3x race transition](docs/reviews/2026-09-16-offroad-race-transition.md)
- [World 3x race transition](docs/reviews/2026-09-16-world-race-transition.md)
- [Exotica 3x race transition](docs/reviews/2026-09-16-exotica-race-transition.md)
- [Scripted recording continuations](docs/reviews/2026-09-16-scripted-recording-continuations.md)

**Current checkpoint:** World2.4 and Off-Road continuous quiet3x race/menu
continuations qualify, alongside Exotica. World12,669 inputs; Off-Road13,044;
original motion and owned shutdown exact. Both add distant terrain after menus.
Off-Road initially compared inherited401-line control against400-line candidate;
that raw comparison is NOT visual acceptance. A matching400-line control passes,
with10/14 images exact and4 changing only distant geometry above y838. The
candidate was not rerun. See their dated reviews for actual course/scope limits.

**Current checkpoint:** Exotica snapshot0 under explicit continuous quiet mode
passes one5300-input check.170 prior non-endpoint files and4 completed4K images
are exact, original input/camera/ADC unchanged,9842 endpoints prepared/0reject,
joined shutdown. Initial checker failed on scheduling-dependent depth batch count;
source-guided qualified-v2 preserves vertices/resources/pixels and separates that
count. No game rerun. Native first-rejection selection remains tested and lazy
operand capture retained. Read the optional endpoint capture review below.
USA also now passes12,212 inputs,10,412 camera/31,236 ADC,6,336 scenes,
14,903,983 quads and joined shutdown. Continue8400/startGoldenGate9000/bridge12000
at0:54.41 observed.2/13 menu images exact,11 gameplay changes all above y1142;
start-letter gap detail retained, not blanket overlay acceptance. No full second
race claim. The reusable recording command ran live and preserves all5012 source
inputs; probe/CRT/height controls are explicit.

The new diagnostic --scenery-preset continuous-3x centralizes all5 ROM profiles.
Three targeted parser/conflict tests PASS; saved controls match executed plans
(Exotica only changes snapshot5219->0, separately qualified). No redundant game
replay for argument spelling. The preset now ran live in one normal WM_CLOSE
trial per engine: Exotica4012/USA4019 original inputs and66 native images exact,
2200camera/6600ADC prefix exact, all queued bytes drained and graphics workers
joined. Full replay FAILs intentionally retained because both stopped early;
separate qualified reports PASS. Read docs/reviews/2026-09-16-normal-close.md.
V-Unit independent shutdown reporting now precedes full-input comparison.
No game/build/test active. New replay --prepare-only and record_prepared.py
freeze exact continuous3x live cases with FFB0 and the external clock. Read
2026-09-16-prepared-candidate-recording.md. All5 ROM plans validate;4 actual-input
families freeze live cases. SyntheticWorld25 correctly rejects disabled devices.
Initial inherited-GL-capture failure retained; explicit clearing fixes schedule,
not disabled bindings. No attended game launched. Ready Exotica plan is LOCAL
race-transitions-20260916/exotica-recording-plan-v3; use a NEW output when user
is ready. Three focused tests and saved Exo/USA native receipt checks PASS.
Product FFB, machine reset, broader courses and useful outer distance remain.
Continue independent work; don't launch an attended recording without a reply.
Read docs/reviews/2026-09-16-exotica-continuous-retirement.md. One5400-input
fault/control pair qualifies Exotica continuous recovery: failure5300/retire5301,
3852scenes,9854endpoints,0reject,fulloriginalinputs and3600camera/10800ADC exact,
GL5299/5300different and5301..5304exactoriginal, joined quiescent5.576GBdrain.
RawdegradedFAIL retained; initialcheckerFAIL wrongnonempty-patch assumption,
qualified-v2PASSfromsamefiles. No replay for analyzer. Preset now Exo failureoriginal.
Prepared recorder rejects fault/stall inheritance and degraded-native acceptance.
Native/runtime3Python +3preset+3recorder testsPASS. No currentgame/build/test.
Startup recovery now separately qualifies2000inputs/33nativeimages,200camera/
600ADC and3ordinary4Ktrack-menu images1945..1947. Failure1385scene2,retireGPU1385,
present1386,1scene,0endpointcommits,2emptyadmissionpackets,125867456bytesdrained.
Rawquiet-workloadFAIL remains: nativecomplete requirespositiveendpointcoverage.
No verifier relaxation. Saved recoveryPASS explicitly workloadFALSE. Read
2026-09-16-exotica-startup-retirement.md. Replay now retains independent retirement
and continues input/pixel checks after a journal error, still finalFAIL. No rerun
for this analyzer change.

Read docs/reviews/2026-09-16-exotica-mars-distance.md. Native5c unchanged. Scripted
half-wheel selection confirms Mars by displayed name. One5500input scout plus
matched2x/3x pair; allinputstime exact,20saved originalRAM/resources/quad/target
files exact,4064scenes2580marked0reject,joinedshutdown.13current4KCRT images:
only5200changes509pixels atfarleft(35,1066)-(127,1115),nonewblack,carROIexact.
5200has2286thirdbandquads/319instances;4800none. Completeddepthscreen680pixels.
Newexotica_fragment_sources.py auxiliaryintegerattachment reproduces fullsaved
insertioncolor/depthexact andidentical680mask;19sources,8blendedlast-fragmentpixels.
Two focusednegative/ownershiptestsPASS;7syntheticinputtestsPASS. Sparsecaptures/
record-onlyscouts now reusable. Rawsetup/cadence/dimension/bounded64removal failures
retained; no game reruns forcheckers. LOCALexotica-open-course-20260916 contains
allplans,scout,pair,qualification,canonicalfragmentreceipt. NEXT inspectbriefactual
appearance intervalaround5200 andsourcehandover. No fullcourse/per-framecamera/
physicalFFB/performance claim. Follow-up appearancepair5500inputs3700camera/
11100ADC exact,30savedoriginalfilesexact.15GL5060..5340every20:5200/5240/5260/5280
change509/314/146/16pixels,nonewblack,carROIexact;other11EXACTincluding5220.
5300has1961thirdbandquadsbutcompleteddepthscreen0visible;no fadefailureclaim.
All4064scenes2580marked0reject/ownedshutdown. LOCALmars-appearance-qualified.json
andmars5300-fragments. Fulltrackenumerationalreadyconfirmed, no shortlookaheadfix.
Read2026-09-16-exotica-animation-sequencing.md. Census: Mars125animationtags plus
138customclasses;Amazon21tags plus65classes. Matchedhandlersaredynamic, no useful
future no-op omission. Newstandaloneanimationhelper/analyzer NOTMAMElinked/synced.
Amazon7220inputoriginalreplayPASS,246actualupdates/sixowners/78modelchanges/sixwraps
exactindependentPython+compiledC++;3focusedPython+nativeboundarytestPASS.
FirsttwoinstrumentationFAILsretained: program-spaceinstructionfetchE8CC mistaken
forcountdownread; exactfetchfilterfixesit. LOCALexotica-open-course-20260916/
animation-qualified/actual-updates.json andamazon-animation-updates-v3.
Standaloneanimation_source now28initialfields/35actualallocations/tags7..12 exact
Python;compiled32wordreconstructionexact. Nodepointerisobservedinput, notallocation
proof; result remainsfutureunsupported. ClassA/B/C/F rejected. Amazonoldallocation
captureonlytaggedcustomhandler, emptycoverageFAILretained.4Python/nativeboundary
checksPASS and246updatesstillmatchcombinedanalyzer. No MAMElink/sync/build.
Savedinitial-modelscreen Mars1/125futuretaggedinrange149viewportquads,Amazon10/20
27viewportquads;both0coloredpixelsagainstcompleteddepth. Originalfullinsertion
color/depthexact andCPU/GPUWaveexact, newpalettesfromsameWave. LOCALanimation-
completed-depth.json. No positivevisibilityclaim or liveanimationpromotion.
NEXT Exotica machine-reset contract (currentlyexplicitfatalaftertracking);
inspectorderedretirement/CPU-GPUresetownershipbeforechangingit. No game/test.
Continue directly.

Read2026-09-16-exotica-late-retirement.md. SourceauditfoundCPU/GPUretirementstill
capped16000evencontinuous. Native569549d9aee nowuses sharedruntimeframepolicy,
capture1..16000unchanged/continuous1..UINT32_MAX; injectionstill16000. Nativeboundary
and4focusedPythonfailuretestsPASS, localbuild/export255patchesPASS. No newgame
or livepost16000/rebootclaim. Lastlivecandidate5c retained. Machine-reset remains
open: pendingCPUscene/cuesneedexplicitcancellation plusorderedGPUboundary, cannot
justclearfatalguards. Luaactualsoft_reset confirmedsource;screenframecontinues.
Read2026-09-16-session-soft-reset.md. session.lua nowidempotentacrossautobootreset;
oldscriptreproducesnonconsecutivetrace, newrecord+identity180frames/6nativeimages
exactwithactualreset90. Ordinaryheadlessboot, notextendedrenderer. LOCALrace-
transitions-20260916/session-soft-reset/qualified-v2.json; initialimportFAILand
rawconversioncheckerFAILretained, no rerunforchecker. NEXT boundedrecordedreset
schedule/completionreceipt nowimplemented (max16,FFB0, frozenmetadata+loader).
Normalheadlessreplay resets60/120 PASS180inputs/times+6nativeimages+actualcompletion
receipthashes.14focusedPythonchecksPASS. LOCALscheduled-soft-reset/{case,identity}.
Continuation/derivation inheritactions. Completecasesonly; shorterprefixbeforea
laterscheduledactionrejects. NEXT Exoticamachine-reset CPU/GPUownership usingnew
fixturemechanism; notyetextendedrenderresetacceptance. No activegame/build/test.


Current frozen native: `1fccd423f3930d1919137ee37feb61045dba21df`,
`build/candidates/1fccd423f39/vunit.exe`, SHA256
`5e56d183e2e59b79c0cb352fc8d260ddc7a1ed6a6a706a028b76e52ff30f2755`.
267 patches reconstruct `3abf205db375d9a16d72b6578cc2fe6fe087f705`.
`quiet-hash-native-export.json` under
`results/diagnostics/exotica-mars-timing-20260916` is the current export receipt.
**All existing export scripts have already run. Never rerun an export against
its appended patch baseline.** Create a new export for a new native commit.

Recent verified results:

- V-Unit scene bootstrap, continuous operation and owned GPU shutdown qualify
  USA, World2.4/2.5 and Off-Road. Quiet journals qualify USA/World2.5/Off-Road;
  World2.4 retains a matching capture-mode regression. Recorded inputs, motion,
  geometry and actual post-reference-end4K images match retained controls.
- Exotica continuous3x completes Amazon plus scripted name entry/loading/new
  race start:11,260 inputs,9,460 camera records,28,380 ADC reads,9,734 scenes,
  ten native pool epochs,32,221 marked commands with zero rejection, and joined
  quiescent shutdown. Eight menu/loading images are exact. Frame11100 changes
  only far-right foliage;941 new dark pixels there are retained, foreground
  rectangle exact. Not a complete second race or proof of outer3x visibility.
- `harness/extend_input.py` preserves the entire recorded INP prefix and joins
  a labeled scripted tail with correct analog interpolation. New stimuli must
  pass through MAME's writer and actual prefix checks before use as new cases.

Exotica's first transition plan failed **before launch** because the endpoint
snapshot is mandatory. Corrected `exotica-menu-tail-3x-v2` retains5219 and passes;
keep the original failure. Earlier USA/World analyzer corrections and Off-Road
bootstrap receipt failures remain documented. Never turn old failed reports
into successes or rerun games merely to fix an analyzer.

Open work includes broader track/temporal quality, World Hawaii's authored
terrain gap, New York's artifacts/crash, useful outer Exotica distance/fade
coverage, remaining performance and final product gates. Prior World custom
handlers/no-op and adjacent terrain searches are already completed: consult
their reviews rather than reopening obsolete NEXT instructions. A two-race,
open-course Exotica recording was requested; availability is unanswered. Do not
start an attended recording without a reply. Independent work still remains.

## Constraints and efficient validation

- No renderer deployment, release publication, hosted CI, physical FFB, or menu removal
  during this parity work. The separately authorized controls/FFB UX deployment
  above is complete. Publicv0.5.0 remains unchanged. Current personal
  `E:/Source/mame-src/vunit.exe` is UX707, SHA256
  `f1f908e66784b657d892e651850693c99e606ffcf093397f9a994975f1c51c01`.
  Original87d is backed up in ux-20260919-deployment-v2/backup/runtime.
  Native source HEAD4df is NOT the installed binary's source lineage.
- Serialize the rig, GPU and builds. No builds, patch exports or broad scans
  during a timed game. Use exact known result directories; the full diagnostics
  tree is enormous. Use `rg --files --no-ignore` for ignored case artifacts.
  Do not guess case or capture filenames: manifests are usually `case.json`
  and completed capture indexes `captures.csv`.
- Use existing evidence before new gameplay. Run targeted checks for changed
  behavior. Do not repeat full drives for favorable timing or broad suites by
  habit. The previous seven-case default suite passed; repeat only for a new
  shared risk. Performance comparisons need matched conditions and clear scope.
- Preserve original cases, failed reports, source/ROM/settings identity and
  exact frozen binaries. Save substantive diagnostic scripts. Python text I/O
  must specify `encoding='utf-8'`; Windows default encoding previously corrupted
  a source comment. Keep corrected analysis in new reports.
- Separate input identity, camera/ADC equality, scene/resource/ownership proof,
  completed pixels, timing and attended feel. None alone proves a good game.
  Zeus GL skips CPU polygons: matching black native images do not validate
  its visible output. Attract mode does not substitute for gameplay.
- Exact renderer claims require zero differing pixels (100.0000%, four decimal
  places). Never assume a scene occurs on every frame or is always nonempty.
  Do not accept missing requested work just because native execution returned0.
- September19 monitor inventory is DISPLAY1,3840×2160 primary only (previous
  runs used DISPLAY2). Verify actual completed dimensions. V-Unit maximized client is
 3824×2073; Zeus covers3840×2160. Do not describe older3440 tests as final4K.

## Source, build and export

The collection is `E:/Source/cruisn-collection`, branch `master`, remote `origin`.
Native MAME is `E:/Source/mame-src`, branch `poc/quadlog`, remote `fork`, based on
MAME0.286. Commit/push them separately and keep the complete exported patch
series in sync, including the DIJOYSTATE2 base patch from `mame0286`.

Canonical C++ helpers live in `native/`; check/sync with
`python harness/sync_native.py [--write]`. The toolkit pin is
`lib/toolkit/VERSION` (v0.11.1); `harness/sync_toolkit.py` checks consumers.
Shader source is `gpu/renderer.py`; regenerate with `harness/gen_shaders.py`.
Never hand-edit generated `midvunit_gl_shaders.h` or introduce raw C++ shader
strings that MAME's source scanner cannot parse.

Build locally with MSYS2 at `E:/msys64`, not C:. Export `OS=Windows_NT` inside
the login shell because its profile clears the inherited value:

```powershell
$env:MSYSTEM='MINGW64'
& E:/msys64/usr/bin/bash.exe -lc 'export OS=Windows_NT; cd /e/Source/mame-src && make SUBTARGET=vunit SOURCES=src/mame/midway/midvunit.cpp,src/mame/midway/midzeus.cpp NOWERROR=1 TOOLS=0 SEPARATE_BIN=1 -j18'
```

The isolated output is `build/mingw-gcc/bin/x64/Release/vunit.exe` in mame-src.
Freeze it under collection `build/candidates/<commit>/` with profile and SHA
receipts. Never overwrite the personal root `vunit.exe` during candidate work.
Never touch `Launchbox-Racing/Emulators/mame286/mame.exe`; only read its ROMs,
controller inputs and fixtures as needed. Add REGENIE only for relevant build
project changes. Use `git -c core.safecrlf=false` for native commits/exports.

Export once per committed native successor. Verify prior patch SHA, clean native
HEAD, expected commit count, actual built binary age, reconstructed Git tree,
profile SHA and unchanged personal binary before appending. Preserve patch
bytes; do not rely on PowerShell text redirection for a binary-safe export.

## Architecture and product boundaries

This is still emulated game code with replacement renderers and host scenery,
not a native port. Never reuse unverified memory addresses across ROM revisions.
Explicit MIDV_PATCH overrides normal selection; conflicting experiments must
fail. The launcher menus still use older guest-distance experiments; the new
continuous host prototypes are explicit CLI candidates, not shipped features.

| Path | Responsibility |
| --- | --- |
| `harness/collection.py`, `run_rig.py` | Launcher, saved rig preferences, common launch/input path |
| `harness/record_drive.py`, `replay.py`, `derive_case.py`, `extend_input.py` | Attended recordings, isolated replay, derived cases and scripted continuation |
| `harness/local_checks.py`, `release_gate.py`, `promote_release.py` | Local evidence and exact accepted ZIP promotion |
| `harness/cheats.py`, `lua/cheats.lua` | Exact-revision cheat import and live bridge |
| `native/`, `gpu/`, `lua/` | Canonical C++ helpers, renderer/shaders and read-only probes |
| `tests/`, `fixtures/` | Focused contracts, native tests, scenarios and calibrated NVRAM |
| `patch/`, `lib/toolkit/`, `profiles/` | Native patch series, pinned reusable wheel code and profiles |
| `docs/`, `results/` | Current guides, dated evidence, ignored large diagnostics |
| `rig/`, `build/`, `media/`, `third_party/` | Personal state/candidates, menu assets and notices |

Release preparation is local; workflows are disabled and tag pushes do not
authorize publication. Follow `docs/LOCAL-BUILDS.md` and the full release checklist
only when publication is authorized. Keep personal preferences separate from
fresh-install defaults. Defaults include CRT on,4x, full widescreen and free play.
Launcher-path tests remain necessary before release; replay success does not
prove the shell launches correctly.

## Rendering, controls and FFB facts

- V-Unit page_control bit2 selects render target, bit0 the visible page. Pages
  persist; native cracks may expose prior-frame content. Margin ownership,
  painter/depth order and intrinsic transparency must remain correct.
- After shader/pipeline changes, preserve exact-mode reference output with
  `python gpu/renderer.py results/capture-8000`; original native captures require
  seeded NVRAM. Use completed GL fences for displayed scenes, not quad-count
  thresholds or legacy asynchronous external-viewer captures.
- GL uses an owned top-level popup, not a child window. Keep input focus on MAME;
  never activate the overlay or use SwitchToThisWindow. GDI captures can show GL
  as black; prefer native completed-frame captures. Rawinput may reject injected
  keyboard events. Normal Esc opens the in-game menu; F9 CRT, F12 exits game,
  Shift+F12 exits both game and launcher. See INSTALL for bindings/calibration.
- FFB is built into MAME through SDL2 and the pinned toolkit; retired input/FFB
  plugins must not return. Preserve World's user-requested menu/race-end pass
  through; no unattended strength retuning or restoration of its rejected gate.
  Motor polarity, input direction, native source, conditioning and wheel torque
  are distinct. Full normalization and physical feel remain unaccepted.
- Never hard-kill with physical FFB active: stranded constant torque is possible.
  Use normal exit/WM_CLOSE; the Stream Deck Stop FFB control is available for a
  stuck wheel. Unattended runs require literal MIDV_FFB=0 and no actuator tests.
  FFB time joins require force-source/emulated clocks, not an assumed wall clock.
- User-observed defects and complete gameplay recordings are valuable evidence.
  Do not call crashes harmless based on old teardown hypotheses; preserve logs
  and distinguish guest, renderer and shutdown failures.

## Documentation maintenance

Update this current checkpoint in place. Do not prepend another full history.
Put detailed outcomes in dated reviews and link them here. Keep `results/RESULTS.md`
append-only and original failures intact. The previous361KB AGENTS file is
preserved verbatim in
[the checkpoint archive](docs/reviews/archive/2026-09-16-agent-checkpoints.md).
It contains obsolete NEXT tasks, old private-repository status, superseded RPM
claims and unsafe-for-current-work build destinations. It is historical evidence,
not active instructions; read only a relevant dated section when needed.
