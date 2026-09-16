# Cruis'n Collection — agent instructions

## Current work: release parity, September 16

Latest: read docs/reviews/2026-09-16-exotica-pre-device-reset.md.
Native083ceb32407 frozen262patches/attested;
SHA50779072342fb6046eb579e05a31e550b7526af87beab7805ffe467ca197f6d9.
Fixedrealresetordering: rootdevice_reset BEFOREchildren, prior machine_reset
guard sawZeusFIFOalreadycleared. Existingstrictquiescence unchanged.
Actual7500MarsresetPASSpre-deviceFIFOempty5559/scene4161/gen12372, newpool6944.
Allinputs/nativeimages5691camera12921ADCexact;12completed4KCRTframes5200..7400
byteexactprioraccepted3x.4679scenes2734357696bytesdrain/join.3focusedtestsPASS.
InitialaggregateoldreportmissingnewattestationKeyErrorretained; correctedv2
hashesoldreport,NOgamerun. LOCALrace-transitions-20260916/exotica-active-reset/
pre-device-3x and pre-device-qualified-v2.json.
Interrupted/bootstrap/degradedresetremainstrict; no blindqueuedownerclears.
PriorUSA/Offroadopacityobservers qualified; USAvisible41partialpixels, Offroad0.
NEXT Offroadstaticbillboard sources: read2026-09-16-offroad-billboard-foundation.md.
StandalonePython/C++505actualmatrices2020vertices/13modelsEXACT;2Python1nativePASS.
2524originalinputs/nativeimages723camera2892ADC andcompleted2520CRTpriorcontrol
exact. Captured10basisvariants. Source1BDD..1BF7preparebasisBEFOREhost1BF8.
TwoLOCALprobeFAILswrongreadspanthenaddress809C00identified; correctedv3PASS.
CanonicalboundedLua added, fixedcaptureequivalentparameterizationnotnewgamerun.
HelpersNOTMAMElinked/synced. LOCALW/offroad-billboard-original-v3,
offroad-billboard-original-qualified.json,offroad-billboard-transparent.json.
337actualflags00800804+60flags00000804/hitbitsclear;108dynamic04004004excluded.
NEXT bindstaticactualrecords toROMdescriptors/currenthitstate, thenpolygon/DMA/
materials beforeearlierdrawing. No blindordinaryrelabeling. Native083unchanged.
Priorfade2520/3360no visibleenvelope;8760noneingeometry. Don'trepeatthosewindows.

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


Current frozen native: `569549d9aee75a78c004c3ad78f99e68080229fd`,
`build/candidates/569549d9aee/vunit.exe`, SHA256
`e9c477fa7c575bf77e8c6d42f1a246e817fb03300744cf37e8cec28ee9227fb1`.
255 patches reconstruct `dd5e248097adfd6aea546517d4ed0e3f48de865e`.
`late-retirement-native-export.json` under
`results/diagnostics/world25-roads-20260914` is the current export receipt.
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

- No deployment, release publication, hosted CI, physical FFB, or menu removal
  during this parity work. The personal Stream Deck copy and publicv0.5.0 remain
  unchanged. Personal `E:/Source/mame-src/vunit.exe` SHA256 is
  `87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8`.
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
- Current monitor selection is DISPLAY2,3840×2160 primary; DISPLAY1,3440×1440
  secondary. Verify actual completed dimensions. V-Unit maximized client is
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
