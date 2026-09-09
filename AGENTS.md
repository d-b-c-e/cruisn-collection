# Cruis'n POC — Codex Agent Instructions

## Normal launcher fix and public-doc preparation (2026-09-08, evening)

Read `docs/reviews/2026-09-08-launch-environment.md`. User reproduced unbound
`env` while launching USA with Always in 1st Place. Recording-only assignment
inside nested start() shadowed the enclosing environment and broke normal
launches, including cheats off. Each start now owns launch_env; no native rebuild.
Tests reach Popen for all5 ROMs, cheats on/off, plus ordinary/explicit-trial
recordings (30 paths); no emulator/physical force.187Python/native/24GPU pass.
Replay tools use another path; older replay passes did not certify normal launch.
Source launcher must be reopened after this fix. User is actively testing;
do not start competing automated games. Public docs are being refreshed; current
guide index is docs/README.md, readiness is docs/PUBLIC-READINESS.md. Repository
remains private; "go public soon" is preparation, not a visibility-change command.

## Local build/check/release policy (2026-09-08)

GitHub Actions minutes are exhausted. Both collection workflows are disabled
in GitHub, and diagnostic checks now have a manual-only trigger. Do not enable
or dispatch hosted workflows without a newer user request. No hosted CI is
required for subsequent work: run the equivalent checks locally and preserve
their reports/source identities. Previous CI PASS statements below are historical.
Use `python harness/local_checks.py` for the full ROM-free Python/native/GPU
inventory; see `docs/LOCAL-BUILDS.md`. Release gate and promotion now require
`--checks` pointing to its complete Windows report and intact evidence files.
Subset/Linux runs cannot clear release coverage. Retain the legacy shared/ci
ledger key but attach local evidence; this automated gate cannot be waived.
Build MAME on this PC when native code changes; assemble releases locally with
make_release.ps1 and promote the exact tested ZIP with promote_release.py.
Do not publish a release merely because the build policy changed. Keep v0.4.0,
its ZIP/tag, personal settings and existing physical-FFB restrictions intact.

## World host-scenery checkpoint (2026-09-08, later authorized work)

Read `docs/reviews/2026-09-08-world-host-scenery.md` and current ROADMAP first.
This supersedes the morning native/source baseline below; the old heartbeat stays
PAUSED. Native `d52b8f95d92` is built/pushed; root vunit SHA256
`e0cf8a8b498d4499f81228b2fbb3e40367d29fd25e1c86edb9c95ee500c689d1`.
133-patch export reconstructs tree `8502d3368438573facb5fb8edaaa5d487fe074df`.
World2.4 now has CLI-only host pending scenery: `--world-host-scenery observe|draw`
plus bounded first/last and `--world-host-far 80000|160000|240000`. No menu/default
change, guest activation/CPU/RAM/VRAM/hardware DMA change, or per-model allowlist.
Native canonical `world_host_scenery.h` uses shared C31 math and checked ROM spans.
All7 defaults pass on final native: actual UDP/memory, World passthrough, Exotica
polarity and21 completed4KGL. Default source identity411697739e64f832 is retained;
later changes affect ONLY the section/yaw diagnostic and numerical tests (four
files enumerated/rechecked in proof), not default probes or product/native code.
Final180tests/all4CI34286683257 pass; local/Linux/Windows agree on all287 source
hashes, identity89efc97dcda1a5f2a14f73ddca5a4d4475511866ce2c588ae809e75cb6438203.
Full Germany9269/154 remains exact, including camera and actual ADC timestamps.
At3824x2073 on restored4K monitor, host80 changes18/31GL; host160 changes20/31
further and repeats all31 plus662946 host quads. Host240 adds132 quads with no
old loss/order change; sparse31GL equal but targeted21GL finds6 mountain changes.
Final2x oracle reconstructs13215 host quads/61scenes; original DMA/VRAM/textures/
palettes byte-equal. Do not call occlusion, stutter or zero-pop-in solved. Host
callback p99~1.54ms but120ms outlier; split preparation/logging/submission and test
without per-quad CSV before promotion. Old ultrawide run marked display-transition.
Read-only section probes preserve inputs/camera/ADC:180 XYZ/heading matches and
180 object/section yaw matches from actual7 constants; ONLY2 distinct angles and
no flag8 offset coverage. Next: broader angles/offsets, palette/texture binding,
PC-owned future-section decoder, occlusion/handover tests, then other-game adapters.
Proof: `results/proof/2026-09-08-world-host-scenery`; numerical verifier uses no ROMs.
Model/resource/uncaptured GPU checks remain hashed receipts. Keep original drives,
v0.4.0 tag/ZIP and personal settings. Stream Deck still uses source/root binary.
No physical FFB; World normalization remains deferred. No emulator/build running
at handoff. No new release or resumed overnight automation.

## Final overnight handoff (2026-09-08, 08:00 local)

The overnight heartbeat `cruisn-overnight-cheats-and-distance` is PAUSED at the
scheduled morning checkpoint. Do not resume it without a newer user instruction.
Read `docs/OVERNIGHT-RESULTS-2026-09-08.md` and the refreshed `ROADMAP.md` first.
Cheats and top-level Experiments are complete in the source launcher; World 2.5
and Off Road have optional global distance controls. Exotica's menu fixes margin
visibility only; its far/admission trials remain diagnostic. USA global distance
also remains CLI-only. All new per-game trials default off; settings preserved.
Native `12e9ea6a374` is built/pushed, with its 129-patch export; vunit SHA256
`9936c7160ddb708949d9e776c9197d833e868ffc921fd679153a72ab99735275`.
Seven default regressions pass on that binary. All 168 tests and four CI jobs
34228828289 pass; Windows/Linux/local match all 268 source hashes, identity
`8c20a78779c02b150e4aa3f6a18181a6199a862d736fe9fd24211530e51d9c13`.
Proof/images/deployment checks: `results/proof/2026-09-08-overnight-checkpoint`.
Exotica follow-up: all 814 matched depth-bias changes are 2047 -> 0, at unique
geometry and with the bias branch used. Trace register 0x15 command provenance
next; both strict scene/frame FAILs remain. No native admission promotion.
No emulator/build is running. Stream Deck still uses this source/root binary.
Published v0.4.0 tag/ZIP, original recordings and personal settings are preserved.
No physical FFB was tested; World force normalization remains deferred.
Earlier active-overnight and pending-release statements below are historical.

## Exotica admission checkpoint (2026-09-08, 07:35 local)

Read docs/reviews/2026-09-08-exotica-admission.md. Tools4c47b67 pushed; native12e
and release remain unchanged. Streaming589 is adaptive: Timer0-based updates,
normal60000..130000 clamp, initial90000; a separate conditional47500 cap exists.
Read-only control6000/21originalGL PASS:132624 admissiontests,96016rejects atdepth
90111..168375, observedlimit90000..130000. Loader usesupper+12, observedlead45.
Four6000 bounded4500..5990 trials hold coherentprojection/widebounds fixed and
replace ONLYtwo admissionlimitreads with160000/190000. No guestwrites/far change.
160k repeatsbothfulltraces/15GL.190k samefrustum/15GL as160k. Latecontrol9890rejects
become0;24345passes become24361; sphereadmissions387144->396867.12/15GLchange,
but late camera/routeidentity is unproven. Do not call allchangedpixels newscenery.
4Kmatched4700:367/374changedpixels in4699/4700nearhorizon; resources equal.
Bothframe/scene strictFAIL:2831->2972records;2612->2753quads;2560geometrymatches
as multiset,2409ordered.52oldquads lackexactgeometry. Alpha changesmostlyinactive
but814active-depth-biaschanges anddraworderremain. No nativeadmission/menu promotion.
168tests/all4CI34225451570,268sourcehashes local/Linux/Windows match8c20a78779c02b150e4aa3f6a18181a6199a862d736fe9fd24211530e51d9c13.
83entry proof results/proof/2026-09-08-exotica-admission uses previousfararchive
as a hashed companion; recomputes numericalchecks, GPU evidence remainsreceipts.
Next: isolate depthstate/order effects orhoststaticdraw preservingoriginals;
freshopenExotica/longerOffRoad/WorldNY drives useful. No physicalFFB/Worldtuning.
Stop at08:00local; recordhandoff and pauseovernightheartbeat.

## Exotica far-distance checkpoint (2026-09-08, 07:05 local)

Read docs/reviews/2026-09-08-exotica-far-distance.md. Tools dc1f07d are pushed;
native12e9ea6a374/SHA9936c716 remains deployed. No new native far option or shader.
Five6000 Lua trials4500..5990 complete: coherent stockfar204800 vs2x409600/3x614400
matches515968 poses;3035 additional admissions, no losses,15/15 GL1920x1080equal.
2x trace/images repeat exactly. Far rejects are allBBB7; do not call them proven
mountains/trees. Generic and vehicle LOD branches are separate.
Matched4864:199 extra quads+8palettes, resources equal. StrictgeometryFAIL retained
because438 original quads shift4863->4864; explicit --alignment scene preserves
all2606 original ordered records/effectivepalettes,207insertions. It excludes ONLY
quad frame stamps. Two completed GLimages equal. Offline query extra199quads:
0visible/173depth-disabledsamples atscale4; doubling depthrange remains0/173.
Captured-resource snapshot and conservative farthest initialdepth are diagnostic
limitations; no whole-frame/native/tactile acceptance implied.
166tests/all4CI34223306424 PASS; local/Linux/Windows sourceidentity54c2b421df9a39bc29c94bf493f2b2805dd8d3a5336d8cd47f0848bb87a10b4b.
80entry LZMA proof results/proof/2026-09-08-exotica-far-distance recomputes CPU
branches/poses/inputs/timing; GPU images/resources/query remain hash-bound receipts.
Next: read-only Exotica streamer investigation. Static code identifies separate
589 admission initialization90000 andB7B9..B7BC loader upper+12. These require
runtime evidence before any mutation. PhysicalFFB stays0; Worldtuning deferred;
v0.4.0tag/ZIP and personalsettings preserved. Heartbeat stops08:00local.

## Off Road native checkpoint (2026-09-08, 06:25 local)

Read docs/reviews/2026-09-08-offroad-native-distance.md. Collection2669afe/ba3364c
are pushed. Native12e9ea6a3742643f5bbc57e7dc07073177594cd6 is built/pushed to fork;
root vunit.exe SHA9936c7160ddb708949d9e776c9197d833e868ffc921fd679153a72ab99735275.
129-patch export exactly reconstructs tree85f158eccb5f11308144513e77b8678f45a0317b.
Settings -> Experiments -> Off Road Challenge -> Off Road Draw Distance offers
Off/2x/3x, defaultOFF, enhanced widescreen/scale>1 only. No personal settings changed.
MIDV_OFFROAD_DISTANCE=0/unset installs no hooks;1 observes stock;2/3 extend far,
clip and reciprocal ceiling together. Header native/offroad_distance.h is canonical.
Only verified read consumers receive substitutions; stored limits/initializers
and ROM resources stay intact. All59 projection signatures plus AR0/signedIR0/
actual-address checks guard the tail. Stale AR0 resource PC1EA8 must stay excluded.
All67776 original table entries reproduce exactly; integer eight-decimal half-even
rounding, not naive binary round. Initial native781af835091 duplicated startup
frame822 in CSV and is retained as a rejected diagnostic log;12e fixes it.

Native matrix4x6000: stock exact;2x/3x changes5/42 small-windowGL;2xvs3x all42equal.
2x repeat has identical counters/4191camera samples/actualADC events and42GL.
Independent derived2x repeats6000inputs/native/counters and13GL3824x2073.
Camera/ADCvalues equal stock over1800..5990, ADCtimes strictFAIL with added work.
Frame4400:715common quads ordered,1oldquad changescoordinates+23new. Texture/palette
equal;target386changedVRAMwords covered,otherpage384historychanges. Strictgeometry
FAIL retained. Very modest gain; syntheticElPaso driveslow/offcourse, no attended
handling/long-track/pop-in-elimination claim. replay/derive --display-size W:H
select actual monitor; client capture can exclude borders. Original cases untouched.

All7defaults actualUDP/memory/Worldpassthrough/Exo21GL PASS,163tests/all4CI34219090827.
All262sourcehashes local/Linux/Windows agree333901cdae9af35e404fc256ebc27170589c99927ceeb116024e081d00e4244b.
190-entry proof results/proof/2026-09-08-offroad-native-distance recomputes native,
input/motion and7telemetry/4force results; rawGL/resources remain hash-bound receipts.
StreamDeck source deployed; v0.4.0tag/ZIP preserved. No physicalFFB or Worldtuning.
NEXT: Exotica late far rejects4686..5986; coherent far/reciprocal trial, current
MIDZ_VISIBILITY still preserves204800. Continue authorized overnight work until
08:00 local Sep8; then checkpoint and pause heartbeat cruisn-overnight-cheats-and-distance.

## Exotica visibility checkpoint (2026-09-08, 05:30 local)

Read docs/reviews/2026-09-08-exotica-visibility-trials.md. Native6a2b7ae93fa is built
and pushed; vunit.exe SHAcec6d98afc732b7e1a268deb763a7afeab112c66e32a4a5ed643817f1f3fdc5a.
127-patch export reconstructs tree6d2e8a22e8641bbf6709eb2f1d5a5092c6bd0dcc.
Collectiondc1f5af adds guarded CPU visibility and Zeus capture checks;0e758f3 adds
Settings -> Experiments -> Exotica -> Widescreen Scenery, defaultOFF. Shared/game
filtering and top-level placement remain. It selects margins only, enhanced wide
scale>1; fallback suppresses the saved option. Explicit developer/recording mode wins.

MIDZ_VISIBILITY=stock|projection|margins|both|off is Exotica2.4-only. No guest writes,
model allowlist or far-plane increase. Canonical native/exotica_visibility.h guards
code/table,PC/registers,pointer/depth/radius; direct backing RAM avoids recursive taps.
No transient object cache; counters reset/load. Buffered exotica-visibility.csv.
replay/derive/record_drive accept --exotica-visibility; derive --keep-patch preserves
absence and rebinds frozen patch/cheat paths. --zeus-capture-frame validates actual
Zeus submissions/resources; V-Unit --capture-state explicitly rejects Exotica.

Five bounded Lua trials and five full-boot native trials6000 complete. Native stock
matches all21 original completed4KGL; each intervention matches19 Lua images.
Margins and both separately record/replay6000 inputs/counter rows and35 completed
1920x1080GL2500..5900. Both native full6000 counters also repeat exactly. Not original
route/attended acceptance: strict pose comparisons fail; combined scene changes42
original records. Margin-only3500 scene preserves3691 records/3532quads and effective
palettes in order, same texture RAM; adds one palette load/one real right-edge quad.
No claim that projection eliminates pop-in; margins vs both diverge markedly after5300.
Native stock finds3669 actual far rejects4686..5986, absent in early2500..4300window.
Next Exotica distance target is that late interval, with coherent reciprocal range.

All7 disabled defaults pass actual telemetry/memory/force controls and Exotica21GL.
157Python tests/all4CI34213524599 pass. Local/Linux/Windows all255 source hashes agree:
fa5809b1880d4373652c68e2e034afa992c97d15a29b8f4698ba4cf3a0a121a3. ROM-free proof under
results/proof/2026-09-08-exotica-visibility contains170 derived files and3full traces;
verifier reconstructs stock from the prior frustum archive, recomputes decisions,
pose failures,counters,inputs,ordered hashes; GL/resource/CI results are bound receipts.
StreamDeck source updated; saved config and v0.4.0 tag/ZIP unchanged. No physicalFFB
or World force tuning. No emulator/helper left. Continue overnight through08:00local:
Off Road native adapter/cost/repeatability next, then later Exotica global far trials.

## Off Road / Exotica diagnostic checkpoint (2026-09-08, 04:25 local)

Read docs/reviews/2026-09-08-offroad-global-distance.md and
2026-09-08-exotica-frustum.md. Collection commits5937063/410ad43 add diagnostics,
not native/launcher distance options. Native8b151aa9c2f/SHA638c74ff unchanged;
v0.4.0 ZIP SHAfd292b0d unchanged. No personal settings or physical FFB touched.

Off Road1.25 far-only adds15 pixels in3/42 completed512x451 samples. Bounded2x/3x
extend far/clip/table coherently using five guarded words (including initializers)
and a ROM-preserving virtual tail. Full6000-frame trials keep4191camera samples
and actual ADC frame/value/PC equal; ADC times and original pixel comparisons FAIL.
2x/3x both change220 pixels in5/42 samples, identical to each other; no3x gain.
Maximum indices95085/95782, well below configured127359/191039. Probe costs54%/53%
emulation, control94%; not native-performance acceptance. Atframe4400 textures/
palette match,715 original quads keep order, one changes three coordinates,23 added.
Strict geometryFAIL remains: altered original/history;386 target-page changedwords
covered,384 other-page changes outside current-page scope. Syntheticdrive is short
and goes off-course. No launcher promotion or fullcandidate/attended acceptance.

Exotica read-only6000/21completed4KGL passes. All339018 CPU sphere decisions match
captured pose/operands and independent acceptance;85350projection clamps,0far
rejects204800. Predicted true reciprocal adds4051instances/no losses;88px margins
alone21717,combined28610. These are CPU predictions, not pixels. Acceptance marker
MUST be instruction68A3/PC68A4;689D is inside final reject delay slots. Original
incorrect probe's replayPASS did not validate interpretation; negative sample kept.
Next: bounded stock/true-reciprocal/margin/both GL matrix. Onlymainculler688B/PC688C;
cache depth outside tabletap; keep C371/C375 helper and far204800 unchanged.

147 Python tests/all4CI34209001116 at410ad43 PASS. Off Road92file ROM-free proof
and Exotica15file proof recompute counters/motion/branch decisions; raw RAM/GL
comparisons are hashed receipts, not independently rerendered. Both native/release
hashes rechecked. No emulator/helper running at checkpoint. Heartbeat remains active
to08:00local; next useful work is the Exotica GPU matrix, then low-overhead native
adapters only if visible gain and resource/repeatability checks justify promotion.

## USA distance checkpoint (2026-09-08)

Read docs/reviews/2026-09-08-usa-global-distance.md and the updated
2026-09-08-distance-next-adapters.md. Native8b151aa9c2f is built/pushed; sourcevunit
SHA638c74ff4227532d0ff42be4cd46cb8a358a1a343549abb107bb56050e91bd74.126patch export
exacttree5e10f68c9badba2385d38d6178eaae1be02d48b6. USA4.5 global projection/residency
is CLI-ONLY in9e70f6a, defaultunset. --usa-far80000/100000/160000/240000 and
--usa-residency0/1; no permodel/level allowlist. Checked far/clamps plus hosttable;
75k admission/80k removal extended through guarded reads, no guest objectRAM writes.
All projection paths include277/278 dynamic clamp andA728 attachedobject consumer;
823E explicit screen-extremum reject remains stock. A728 extra reads were zero.

Five full5012frame USA trials complete at99.9900..100.0013% emulation. Original1x
control passes. Projection2x-only changes3native images/3pixels in1of19GL samples;
one camera sample differs3012, ADCvalues equal but timestamps differ. Residency
changes route substantially from2222 with interpolatedADC differences, retainedFAIL.
2x/3x first camera difference3902; no extra visible3x scenery established. Candidate
2x repeats5012inputs/83native/19completedGL at1904x993; matrixGL was512x451, not4K.
No launcher promotion or geometry/order/resource/attended acceptance yet. Derive
now --gl-capture/--gl-every plus --compare-gl identity check. World2.5 explicit
attendedrecording guard fixed separately in92b6659; source menu already has Cheats
and top-level Experiments beside Display. No personal preferences edited.

All7default regressions pass with actualtelemetry/independentmemory and existing
Worldpassthrough/Exoticaforce checks, physicaloutputOFF. Exotica21completed4KGL match.
139Python tests/all4CI34202538087 PASS at3628c96. All237sourcehashes matchlocal/Linux/
Windows identity946fc6523f110ddc2d91e5a481b4a6cbdd0cc067d73452cc3ab923e42023974c.
107file proof results/proof/2026-09-08-usa-global-distance recomputes inputs/motion/
distance withoutROMs. v0.4.0 ZIP/tag unchanged. No newrelease. No emulator remains.

NEXT OffRoad: all67776 reciprocal entries now match an exact rational eight-decimal
half-even reconstruction: index<503 =>2-(index+1)/504, else504/(index+1), thenfloat32
andC31. NaivePythonround(float,8) fails2ties (20479/61439); preserve failedcontrol.
Still need vertex/clipping/residency analysis. B725=63680 is a separate geometry
boundary;1.25far47296->59120 may retain it,2x cannot blindly reuseWorldtable.
Exotica: mainculler688B has80kclamp, unused204800far. Probe actual CPUfrustum
operands before intervention, caching object/XYZ at67DAfar tap to avoid recursive
reads in overlappingtable/objectRAM. C371/C375 helper already limited100..30000;
6B99 restores mainculler base. See next-adapters for exact consumers/probe outline.
Continue overnight queue to08:00local; no physicalFFB or deferredWorldforce tuning.

## World 2.5 distance checkpoint (2026-09-08, 02:40)

Read docs/reviews/2026-09-08-world25-distance.md and
docs/reviews/2026-09-08-distance-next-adapters.md. Native dae2569f793 is built/pushed;
source vunit.exe SHA f06a160b57c72737e89aedcc159f87cbe173c82620722ea109e84dcdffe70252.
125patch export reconstructs tree2f4f89c388ba380aa578036143049a723dcad00c. World2.5
now supports guarded shared Off/2x/3x and+0/8/12 menu/CLI trials; defaultOFF, same
exclusions. Source117e8fb; separate USA read-only residency commitb720b98. All7default
regressions/actualtelemetry+memory+Worldpassthrough/Exotica21GL PASS. 132tests/all4CI
34199270158 PASS; all229 source hashes match local/Linux/Windows, identity85ad5a175.
ExistingWorld2.4global2xGermany8783/146 PASS. World2.5original+2x/+8+3x/+8 full6000
trials complete ~100% speed; extended trials FAIL original-route equality, retained.
2x candidate repeats6000/100native/11GL. 2x/3x match100native+42GL images, but33camera
samples/ADCtimes differ; keep stricter motionFAIL. No3x visual gain proven, no2.5
geometry/order/resource acceptance or full attended race, +12 not newly tested.
Proof results/proof/2026-09-08-world25-distance (67derivedfiles) recomputes counters.
Publishedv0.4.0ZIP/tag untouched; no newpackage. No emulator remains running.

NEXT USA global admission+projection: residency trace finds22713 pending visits
within2x75k, maxdepth-minus-radius117026. Guard75k727D/80k727E windows and enumerate
ALLreciprocal paths: extra277/278 clamp +27C/27F dynamic-model reads were found;
823E/8240 andA727 need attribution. No USA intervention built yet. OffRoad float
far47296/ROMtable63679 are separate; tail resembles504/(index+1), NOT World512
generator, unverified beyond4samples. Exotica far204800 has no sampled rejects;
investigate80k CPUculler clamp/frustum and pending lists, not just raisefar.
Follow overnight queue through08:00. No physicalFFB, Worldtuning remains deferred.

## Cross-game distance capability checkpoint (2026-09-08, 02:05)

Read docs/reviews/2026-09-08-distance-capabilities.md. Bounded read-only gameplay
probes cover all5 revisions; native44c3494d6af remains unchanged. Four4305-frame
V-Unit controls pass; fullExotica6000/21GL passes and matches its headless distance
trace. Initial Exotica headless48native-image FAIL is preserved, not a GL oracle.
131tests pass. ROM-free35file proof recomputes all counters. USA has only3 plausible
far rejects within3x plus900 INT_MAX-like visits: admission75k/removal80k must be
investigated. Both World revisions have substantial80k..160k rejection; 2.5 table
B665/pendingD586 are separately mapped. OffRoad uses DP1 float1B724=47296 and ROM
tableCB0FC8 with63679 clamp, not World addresses. Exotica far204800 rejects nothing
in this sample despite85388 reciprocal clamps. Do not sell a larger far multiplier
as a fix without earlier visible scenery. NEXT guarded World2.5 adapter, USA
admission+projection, separate OffRoad/Exotica paths. No product defaults/FFB change.

## Overnight Cheats and Experiments checkpoint (2026-09-08, 01:40)

Read docs/reviews/2026-09-08-cheats-and-experiments.md. Cheats menu is implemented
for imported exact-revision continuous toggles/choices; all off by default. The
user archive is imported into rig/cheats, with no active selections. One-shots and
off-script/code-restoring cheats remain unavailable pending live activation.
MAME engine bridge native44c3494d6af is built/pushed; source vunit SHA
eb2db42a90288bf37ac0dcce9b9ce2106c136fad198c52320ee2b3af3c435a97. Full124patch
export reconstructs tree f7af3475d0ce0b6347e2be669338283437a81447. Never translate
cheat expressions into a second interpreter or substitute parent-ROM addresses.

Experiments now sits beside Display, preserving Shared/game contexts and keys;
Back returns to Settings. Shared Crack Fill retains its existing ON default;
per-game distance trials remain OFF by default. Current source commits eea6ef5
(cheats), e6154e1 (menu move), f8a804f (frozen checks), 1baa99a (capture targeting).
128tests/all4CI34195061384 pass. Seven binary-bound default controls pass as six
initial passes plus an Exotica rerun; initial aggregate FAIL is retained. Zeus
had chosen secondary1080p vs4Kreference. --compare-gl now selects a matching monitor;
all21completed4K images match. Do not resize references to fake equality.
Five4000-frame cheat-on replays and five timer on/off memory probes pass; this
does not certify rank/nitro/one-shot effects or physical feel. No physical FFB.

DevZIP f8a804f SHA f7a5a641affe81d7e44102d86cc9a6fa19411820a8b9d76607a99e7d08ecfdf5
passes9pages,4defaultboots/12GL,1cheatWorldboot/3GL,import/setup/support;1649files.
Proof results/proof/2026-09-08-cheats-and-experiments (75derivedfiles), verifier
checksbytes/nativebindings and recomputes5timer effects withoutROMs. These are
component checks, not a new release gate. Published v0.4.0 ZIP/tag untouched.
NEXT: global distance capability matrix and guarded trials across ALL4games,
WorldNewYork artifacts/crash. No new distance behavior was added in this checkpoint.
Heartbeat remains active to08:00local; follow docs/OVERNIGHT-2026-09-08.md.

## Release authorization and overnight queue (2026-09-08)

v0.4.0 is PUBLISHED at c098290aeaa1f19ca37d7bee56c747cbf51350b5, exact ZIP SHA
fd292b0d4ba4d2a97147c6ffc1fb95407e3891495dfb68fada2f899e3c31ba4a. Download verified.
Native97600e9597e unchanged. All7 current regressions/5 fresh boots/4 frozen launches,
117tests/all4CI34189532162, GPU exact/quality and3 pause menus pass. 1637-file upgrade
rehearsal preserves user-state fixtures. 217-file source identity4c9dd0a3 matches
local/Linux/Windows. Proof: results/proof/2026-09-08-v0.4.0-release (61 derived files).
41 human-check waivers are explicit; do not call them observed PASS results.
Heartbeat cruisn-overnight-cheats-and-distance is active through the morning checkpoint.

User explicitly signs off current state and authorizes v0.4.0 release. This
supersedes older pending-approval statements below. Read
docs/releases/v0.4.0-approval.md and docs/release-notes/v0.4.0.md.
Do not invent attended observations: release_gate supports explicit enumerated
maintainer waivers, bound to candidate/source and hashed approval evidence, while
all automated gates remain mandatory. Exact ZIP promotion still never rebuilds.
Repository visibility remains private; no visibility change authorized.
Post-release order is docs/OVERNIGHT-2026-09-08.md: Cheats first, Experiments as a
top-level sibling of Display second, global distance trials across all four games
third. Separate commits; preserve v0.4.0 tag/package and baseline defaults.
No physical FFB unattended. World force normalization remains deferred.

## Exotica force polarity correction (2026-09-07)

User reports anti-centering with Wheel Invert On, ADC mirror0 and shared force
invert0. Native97600e9597e now normalizes Exotica's active-low DIP0x0800 motor sign,
independent of steering and device inversion. Do not restore ADC mirroring or
change the global wheel direction to compensate. Strength/gain and World unchanged.
Read docs/reviews/2026-09-07-exotica-force-polarity.md. Native SHA256
b5ba0021a51a1f9ec50e105dde9c8112cb3c7e4ce71009ce4294841296383ee2, built in mame-src.
123patch export; canonical motor_signal.h. force-gate.csv adds game_invert/device_invert;
analyzer --check-polarity compares adapted source and recorded DIP inputs.
115Python/native vectors/all4CI34187080921 PASS. FullExotica6000/21GL PASS:2082nonzero
requests reverse exactly, magnitude/raw/adapted source unchanged. World2.5 control
6000/100 and all5534force requests unchanged. First replay ended early1052, retained
FAIL/incomplete; completed rerun passes. Physical centering acceptance still needed.
No gain/normalization tuning or new release ZIP; prior rc2 remains superseded.

## World FFB rollback supersedes the gate below (2026-09-07)

User reported World gate as a regression and explicitly deferred further tuning.
Read docs/reviews/2026-09-07-world-ffb-rollback.md. World2.4/2.5 driving-state gate
calls removed; game-menu/race-end motor feedback restored. NO10%boost and NO World
strength reduction: user superseded the boost request. Exotica trim/gate unchanged.
Native b9bef299f6d / SHA093abbeb01ac779dbc81b734bea609a9a358eebc17a7cfbf2ad6002e017135af,
built at mame-src/vunit.exe;122patch export refreshed. 114tests and both World
headless full replays pass: Germany9269/154 and2.5 6000/100, actual UDP/memory and
ungated force traces. Raw/adapted source CSVs exactly match prior verified runs.
Normal suite now explicitly requires World passthrough; Exotica still driving-gated.
Mark oscillation and cross-game80% strength normalization KNOWN ISSUES for later,
not a new autonomous tuning task. Previous rc2 ZIP contains rejected World gate;
source is newer and needs a replacement package/release gate before publication.

## Latest release-feedback fixes (2026-09-07)

Read `docs/reviews/2026-09-07-release-feedback.md` first; older telemetry/force
descriptions below are historical. Native f2e5b63dd72 on poc/quadlog, pushed fork;
source vunit.exe SHA25680688f753070bffe5e55654fed1fd7ffdbd1158acd978e44c9a2a660b40fba57.
All four games now have guarded actual player gear/rev producers in canonical
`native/hud_drivetrain.h`, mapped to the user-approved estimated900..8000RPM scale.
World2.4/2.5 have separately checked layouts. Off Road uses DP=1 globals and player
strideBC; speed comes from its HUD formatter. Exotica uses its own speed producer
and screen callback to emit UDP; previously it emitted no Forza packets at all.
World speed remains OCR, cleared outside its verified HUD states. E632 is never RPM.

World and Exotica now gate force on verified driving flags, independently of draw
distance/speed. Inactive transitions release constant force, impact state, rumble
and condition effects. `MIDV_FFB_GAME_GATE=0` is a developer control. Raw source
telemetry remains unchanged; separate force-gate.csv records requested host levels.
Exotica defaults MIDZ_WHEEL_INVERT=0: force/shifter DIP does not prove ADC inversion.
`force_options.apply_game_defaults` trims effective Exotica force20% after byte
conditioning; saved global strength is unchanged (80 becomes64). No physical-force
acceptance yet. Never test a wheel unattended.

All7 final-build replays pass actual UDP/independent memory checks plus original
inputs/images, including Exotica21 completed GL images; timing99.9735..100.0070%.
World/Exotica gate decisions match independent game-state probes. All5 fresh-save
boot/replay persistence checks pass. 113 Python tests/native helpers/all4 CI jobs
pass; CI34164817060 Windows/Linux/local agree on all217 source hashes, identity
9eeaefe1defee4ac06ea198a1ea192499ab6785abe0c684774a9b504f642d7cd.
The121-patch export exactly reconstructs native tree26264b1217f62b08aaab544658cda7a8e9128746.

Clean bb62a22 package: build/CruisnCollection-v0.4.0-rc2-20260907-170505.zip,
SHAe8847b70fc9436a23aa38ffdb2f2756009c040c6acbaf7bff577a42a947224f8.
1632 file hashes, actual frozen CRT-on/full-wide/scale4 defaults, four frozen boots,
12 completed GL images, eight menu pages/setup/support pass. Proof directory
results/proof/2026-09-07-release-feedback contains160 archived derived files and
verify_archive.py; seven telemetry/four force verdicts recompute exactly without ROMs.
No personal settings changed; old recordings/ZIPs preserved. Stream Deck still uses
source checkout/root mame-src binary. Later docs-only commits keep product identity.

All43 attended/shared release checks remain pending. Next: four-game automatic/manual
gear/tach and tactile acceptance (Off Road/Exotica synthetic cases cover first gear
only), Exotica startup/steering/20%trim, World finish/impact feel, package/second-wheel
acceptance. World legitimately has some countdown/rapid upshifts without rev drops;
do not fake drops to satisfy the strict optional analyzer. User's New York3x/+12
launch has a confirmed guest-fatal Unimplemented op at3EF9C170; cause unresolved.
Default-distance Germany also sends nonzero motor commands after finish, now gated;
this does not prove the lost original oscillation trace's sole cause. Distance stays
off for release. New York graphics/crash recording, cheats and other-game distance
work are postrelease priorities. No public tag/release/visibility change authorized.

## Latest source launcher update (2026-09-07)

Read `docs/reviews/2026-09-07-graphics-menu.md`. Crack Fill moved to Graphics
Experiments as a shared setting; its preference/default remain unchanged. World
2.4 now exposes Off/2x/3x and independent +0/+8/+12 lookahead, widescreen/scale>1
only, normal CPU. Global distance and selective Distant Scenery are exclusive;
Widescreen Terrain may compose. Explicit MIDV_PATCH wins; recording CLI distance
overrides saved distance. Source commits c753f4b/9ae9231, native unchanged 5bb9657.
104 Python tests pass; a separate 3x/+8 2404-frame recording/replay matches inputs,
40 native images and three completed GL images. This is short integration evidence,
not a new full release gate or original-route/attended acceptance. The overnight
050908 ZIP below is preserved and does NOT contain this menu change; package a new
candidate before releasing it. No saved personal preferences were edited.

## Current verified release baseline (2026-09-07)

Read `docs/reviews/2026-09-07-release-hardening.md`, `docs/RELEASE-MORNING.md`
and `docs/RELEASE-CHECKLIST.md`. Automated preparation is complete; public delivery
and human acceptance remain pending. No local emulator, build or helper is running.
Native `5bb965763b1` on poc/quadlog is pushed to fork. Root vunit.exe SHA256:
`9d8a8c14998777a15190ca76edd318380baec05e6dac6086d54929dcd2c62a86`.
The117-patch export reconstructs tree `a611778155bbaef209f5523bb711ba8b1f127cb6`.

Final clean ZIP: build/CruisnCollection-v0.4.0-rc1-20260907-050908.zip
SHA256 `eaa8520998e8fc76d5fecdbbda86311455d96ee129ac783892a54962a765a139`.
Packaged commit be87237; code correction7cb6751; later docs/proof commits preserve
source identity `e728e2463bc64d0695433007ec905f56ad93bf7966a791a9845412bf74d56921`.
100 Python tests and all4 CI jobs pass. CI34109534667/34109710043 verifies Windows,
Linux and local agreement for every201 source input hash. Known text line endings
normalize; binary NVRAM bytes remain exact. Raw package/file hashes stay exact.

Final source-bound checks PASS: all7 driving regressions (original Germany9269/154,
Exotica21 completed GL), all5 fresh boot/replay free-play persistence checks,
3 VUnit pause menus,24 GPU fixtures, both exact captures100.0000%, four frozen
launches/eight UI pages/setup/support, and actual-ZIP upgrade with1617 matching files.
Configured timing intervals99.9290..100.0040% emulation; worst callback44.7ms is not
presentation latency. Source/native/ZIP unchanged throughout. Evidence:
`results/proof/2026-09-07-release-hardening/release-final` (221 runtime entries).
The earlier native9D8 vs aa920 full-drive comparison preserves174 completed GL
frames across USA/Germany/Off Road (401 rows). It remains binary-bound component
proof; no renderer/shader/profile/options changed with the identity correction.
Traces remain in release-3720 (288 entries,33 proof files checked from Git blobs).

Startup CPU framebuffer writes use masked GPU copies preserving holes and order;
MIDV_GL_BATCH_VRAM=0 is an explicit control. Twelve C925 full-window starts pass;
long injected stalls still fail as intended, watchdog unchanged. Both driver
families normalize reserved motor-128 before gain/slew/clamp and reset driver slew
history. Ordinary command vectors unchanged; no physical-feel/polarity acceptance.
Known historical dinput8 proxies move to backups on upgrade/first launch; unknown
DLLs remain intact and block the operation. Never execute old proxies in automation.

Stream Deck still opens this checkout and E:/Source/mame-src/vunit.exe. Saved user
preferences/NVRAM are preserved. Fresh defaults are widescreen/CRT/scale4/World2.4,
force50 and default profile; experiments/impact cues off. Off Road DOES checksum
operator settings: use cmos_settings.py, never restore lone-byte free-play edits.
World3x/lead12 stays diagnostic; no extra mountain visibility proven over2x at equal
lookahead. Next engine milestone is host drawing of future/static scenery independent
of guest simulation, not more model allowlists. Margin Fill remains retired.

The repository is PRIVATE and the anonymous update endpoint returns404. Public
hosting needs a maintainer decision; no visibility change, token distribution or
public tag/release was performed. All39 human/shared checks remain pending; the
prepared ledger attaches automated receipts without fabricating human approval.
Use new attended manual drives, wheel/FFB checks and the clean-profile/soak protocol
next. All automated physical FFB remains OFF; original recordings are immutable.

## Latest verified update (2026-09-07)

Read `docs/reviews/2026-09-07-usa-drivetrain-and-startup.md`. USA v4.5 now has
validated player-state gear and rev producers: E8A8 pointer, +38 gear, +39 C31
rev, traced from HUD consumers 9D86/9E53. `native/hud_drivetrain.h` guards exact
opcodes, pointer/range and fresh HUD lifetime; backing-RAM reads only. The
900..8000 RPM scale is explicitly estimated from that real game rev signal.
Automatic gear1..4 works; E632 remains speed text, never RPM. Other games need
their own producers. Nativebf8821358d4 / SHA4d63433b45f492ae7dd6f982c0aca92afdf7d12283d19ee194bf5ec95e55fee4.
Full118patch export verified. `replay.py --telemetry-loopback` captures real
Forza/JSON on private localhost ports; `analyze_drivetrain.py` validates samples,
shift drops and optional independent RAM probe. `--no-arcade-rpm` is the control.
Lua tap exceptions may be swallowed by MAME: explicitly propagate them to the
frame callback. A replay PASS alone does not certify arbitrary probe contents.
Experiments are filtered by Shared/game/revision. World reported fallback was
not reproduced; screen-only fallback and bounded launch history/GL logs are
mitigations/evidence, not a proven scale-init fix. No renderer/force algorithm
change. Original recordings and old release ZIPs remain unchanged.

## Current verified handoff (2026-09-06)

Latest: `docs/reviews/2026-09-06-global-distance-trial.md`. Native `9ea71f601b3`,
root vunit.exe SHA256 `050cf6ea393f1d44a1662ad191a5fc6d38be3084f49603ce8d7de2b379f736ce`.
The shared World 2.4 distance experiment is built: `MIDV_WORLD_FAR`80000/100000/160000,
`MIDV_WORLD_LEAD`0..8, optional diagnostic CPU percent100/125/150/200. Canonical
`native/world_distance.h`; matching checked far/clamp patch is mandatory. Host
reciprocals preserve adjacent guest RAM. No per-model/level allowlist. All native
hooks remain disabled when FAR is unset; never combine with selective scenery.
Replay, derive_case and record_drive accept `--world-far/--world-lead/--world-cpu`.
`run_world_distance_trials.py` serializes an explicit controlled matrix; its
completion verdict is not visual acceptance. `analyze_world_distance.py` validates
the buffered native CSV. Normal launcher preferences remain unchanged.
Six full Germany trials hold ~100% emulation speed; zero extension matches all
8783 frames/146 native images. Full2x/lead8 repeats against itself but changes the
old route. Bounded camera equality through6183 is not traffic/render-phase identity.
Actual ADC interpolation can change a wheel sample despite equal frame inputs;
motion reports now retain that distinction and matching camera intervals.
2x/lead8 at normal CPU is the attended-trial candidate: the mountain is visibly
present earlier in completed GL, also verified at3824x2073. No pop-in-elimination
claim; fresh Germany/second-level drives still needed before launcher promotion.
The next engine milestone is a host static-transform oracle and pending/future
scenery draw path independent of guest simulation. Research/context:
`docs/reviews/2026-09-06-global-distance-and-native-port.md`. Stop growing model
allowlists as the main strategy. The archived draft patches are historical inputs,
superseded by this built implementation, not instructions to reapply them.
All seven default regression cases PASS with the experiment disabled, including
21 completed GL images for Exotica. 79 Python tests and native helper tests PASS;
CI34080307060 at42f1635 passes all four jobs. Proof ZIP hashes were verified and
all six full-trial camera/native-counter summaries recomputed exactly.

Newest distance evidence: `docs/reviews/2026-09-06-background-activation.md`.
Native e8b8fc3be9c / SHA256 d520c414 adds opt-in `MIDV_SCENERY=mountains|trees|all|off`,
World2.4 only. Canonical `native/world_scenery.h` syncs to MAME. Five identified
mountains use earlier admission with ORIGINAL far-clamped perspective; trees
CA57F3/CA5833/CA5863/CA5896 use valid virtual reciprocals only for rejected instances.
Forest strip CB2375 uses original clamped projection, never the small-tree fast
path; it follows Trees mode with its own forest_admissions counter.
The five mountains/forest also activate up to8 track sections earlier, via their
pending-list section read atPC7B69. MIDV_SCENERY_LEAD=0 disables activation only;
default8 when scenery is enabled. Guest performs transfer; hooks don't write RAM.
Only pendingflags2000, exactmodels/radii and verified activation code qualify.
Small-tree activation is unchanged. Replay/derive --scenery-lead archives0..8.
No guest RAM writes. Exact model/radius/flags and projection instructions guard
it; don't copy addresses into other revisions/games. Reset clears active tree;
state saves preserve it. MIDV_SCENERY_LOG=1 -> per-frame scenery.csv.
Shell Distant Scenery is defaultOFF, World2.4/widescreen/scale>1 only. Terrain
visibility remains separate. Full candidate8783/146 repeats, ~100.005% driving
speed; twelve parent native images differ. Lead0 repeats the previous expanded
case exactly. Dense GL5940..6280 completes341 images:100change,max6839pixels;
all6123..6280match. Geometry keeps originals but orderFAILs three scenes;6119 has
49potentially overlapping pairs. Don't call that check PASS. All7defaultcases
pass separately. Later-margin evidence and broader activation remain tracked
in the review/session notes. Admissions aren't visible pixels.
`compare_scenery.py` requires explicit allowed additions, keeps duplicate quads
and original order, and can bound added quad extent. Pair it with completed GL.
Optional --alignment scene checks completed page-control runs; preserve stricter
frame timing differences. --order-details describes inversions, not acceptance.
gl_frames.py --every N --details --contact-sheet PNG
validates sparse global-frame captures and locates changed pixels.
Avoid nested address-space reads inside reciprocal taps: selected-model RAM
lies in the observed range. A failed Lua prototype caused giant trees this way;
its negative-control evidence is retained. Native reads backing RAM directly.

Latest: `docs/reviews/2026-09-06-world-assets-and-road.md`. Enhanced World 2.4
retains the outgoing transmission atlas in the GL upload only while its actual
UI models remain linked. CPU memory/native rendering stay unchanged. The helper
`native/retained_texture.h` is synced by `harness/sync_native.py`; gate is GL
scale >1, verified World 2.4 instructions/models. `MIDV_GL_UI_ASSETS=0` or replay
`--no-ui-assets` provides a control. Reset/post-load discards the retained atlas.
Do not replace this with a timed freeze or deferred writes into guest RAM.
`world_asset_jobs.lua` and `world_ui_models.lua` are bounded read-only probes.
Session probe errors stop playback; evidence rejects Lua errors even on exit 0.
Germany's black wedge: dump 7338 matches completed GL 7340 (HUD 1:36.78).
No current polygon owns native (-82,355); bypassing C0/C4 restores a real road
quad. The bounded +86 extension does not. Full X bypass is DIAGNOSTIC ONLY.
`crusnwld-terrain-visibility-experimental.txt` adds a conservative 1.25 projected
radius factor plus wide bounds and DOES restore that wedge (+77 draws, originals
and native/resources unchanged in the matched scene). Exposed as World Terrain
Visibility, widescreen only. User explicitly accepts a new recording for improved
rendering: old-route mismatch is diagnostic, not an absolute veto. Preserve the
original, require candidate repeatability/performance, and obtain a fresh attended
drive for handling/route acceptance. Derived replay is not attended acceptance.

Previous: `docs/reviews/2026-09-06-world-rendering-and-replay.md`. Native executable
f40c28f8e0a fixes two exact endpoint samples and resolves enhanced tagged dither
before display scaling. Exact USA/World captures are 100.0000%; real opaque
checkerboard art is preserved. Off Road's flat sky rectangle now spans the wide
canvas without extra guest instructions/draw calls; 6000-frame replay passes.
World object visibility is EXPERIMENTAL ONLY: do not put the B9/C0/108..10D group
back into normal 2.4/2.5 patches. It adds correct margin geometry but changes the
route at frame2732 with identical actual ADC values. Original-bounds helper
control passes; extra admitted geometry is the trigger, exact dependency open.
Final original Germany replay matches 9269 inputs/154 native images plus 7401
camera samples/22203 ADC reads and exact times. No fresh recording is needed.
`lua/world_motion_trace.lua` + `harness/compare_world_motion.py` validate route
traces; `derive_case.py` proves repeatability only, never original route fidelity.
`lua/world_object_lifecycle.lua`, `world_texture_transition.lua`, `dma_window.lua`
are bounded read-only probes. `world_projection_distance.lua` is a guarded,
bounded MUTATING World2.4 diagnostic, never a product patch. Do not ship its
frame-number window or a guest-memory transmission atlas-hold experiment. World distance
needs a safe reciprocal-table extension and route validation; D/A corruption
is premature atlas reuse, also reproduced by official MAME controls.

Previous: `docs/reviews/2026-09-06-germany-level.md`. V-Unit pause UI must present
without a new emulation fence; pausing blocks that fence. `check_menu.py` tests
the real key-handler menu states with physical force disabled; its menu BMPs
are separate from completed gameplay captures. Germany Level is a complete human
World 2.4 race (9,269 frames / 154 native images), now the seventh local case.
`record_drive.py` preserves shell settings and shows a passive external clock by
default. Physical FFB needs explicit `--with-ffb`; replay always disables it.
`replay.py --clock` opts into the current Lua script and six-frame log flushes,
hashing that override. Never rewrite an original recording to add clock support.

Read `docs/reviews/2026-09-06-seams-distance.md` and `.Codex/session-notes.md` for
current limits; older artifact-free/general speed claims below are historical.
Broad `MIDV_GL_MARGINFILL` is OFF by default after gameplay proved it destroyed
World/Off Road sky detail. It is retired from the launcher; legacy INI values
are ignored/reset on save. `=1` restores that explicit developer experiment. Local crack
fill is separate. V-Unit GL captures have completed-frame fences; legacy external
viewer captures are not an oracle. USA numeric displayed speed is guarded to
v4.5 and actual HUD submissions, with OCR fallback; other games need their own
producers. Force impacts and attended recording are opt-in, never run unattended.
Toolkit pin is v0.11.1. Keep the new LOD patch experimental, not a default.
Quality rendering now retains fine samples in native-empty spans. Geometry
T-junction alignment is opt-in (`MIDV_GL_TJUNCTIONS=1`), never native-exact mode.
Zeus now has completed-frame captures and a 6,000-frame driving case with 21
actual GL reference images. Its live path skips CPU polygons: old matching black
native images were NOT a gameplay oracle, and headless/live differences did not
establish nondeterminism. Use `replay.py --compare-gl`; `--zeus-native` is a slow
double-rasterization diagnostic. `run_regressions.py` runs seven local cases with
explicit coverage and timing gates. RPM is unavailable; never restore the old
E632 mapping, which interpreted packed speed text as engine RPM.

Launcher Settings -> Display -> Graphics Experiments now exposes per-game seam
alignment and USA v4.5-only detail/draw limits, all off by default. Shared resolution
and patch composition live in `harness/graphics_options.py`. Full widescreen and
selected distance patches compose with expected-word guards; explicit MIDV_PATCH
still wins. Do not apply USA addresses to clones or other games.

Read `docs/reviews/2026-09-06-exotica-polarity.md` before any Exotica FFB change.
Endprodukt's open PR16057 identifies Wheel Invert as force/shifter polarity.
The old log inferred steering inversion from motor polarity alone; this does not
prove vehicle steering direction. Current input compensation remains unchanged
pending a no-force replay matrix. Sit Down is currently conditional on complete
shifter/paddle bindings; existing Kit DIP survives. No physical Fanatec retest yet.

## What this is

Working proof-of-concept for a **native PC port of the Midway Cruis'n
games** (Cruis'n USA, Cruis'n World, Off Road Challenge — V-Unit hardware,
renderer-replaced and verified bit-exact — plus **Cruis'n Exotica**, Zeus2
hardware, with a live Zeus GL replacement and a MAME-renderer fallback;
upstream emulation limitations remain). Built as a
renderer-replacement over MAME, the same architecture as wanszai's arcade
ports. As of 2026-09-05 the collection launches all four games with scaled
widescreen rendering and built-in SDL force feedback, conditioned by the
vendored wheel-toolkit shaper. Gameplay rendering artifacts, collision feel,
and telemetry coverage remain open. USA's measured GDI selection slowdown is fixed
with an underlying D3D window; native exactness
on archived captures must not be described as proof of artifact-free gameplay.

Current assessment: `docs/reviews/2026-09-05-assessment.md`, with dedicated
widescreen/distance, replay/testing, FFB and telemetry companion reports.
The user authorized implementation after committing/pushing this assessment
baseline. Prioritize diagnostic evidence and real gameplay input replay;
automated graphics runs must disable physical wheel output. Preserve the
review reports as a dated baseline and record fixes separately.

Implemented workflow: `docs/DIAGNOSTIC-REPLAY.md`; results and remaining work:
`docs/reviews/2026-09-05-implementation.md`. Record with `run_rig.py --record-case`;
replay with `harness/replay.py`. Force defaults off; only explicitly attended
recording may retain it. Real USA synthetic
gameplay has matched 6,000 input frames and 100 native snapshots on replay.
The user's LA Freeway recording and a separate improved-build candidate each
replay 5,012 frames / 83 native images exactly. This does not establish other
games or GL pixel equality. Preserve `results/diagnostics/my-drive` unchanged.
See `docs/reviews/2026-09-05-recorded-drive-findings.md` for the UV atlas-bleed
fix, USA object-visibility patch and crack-filler reassessment. A full-run game
patch changes later native frames; use late matched-state tests for causal
graphics comparisons and a separate candidate case for new-build determinism.
New recordings defer PNG encoding until exit (`raw-snap/` retained and hashed).
`replay.py --patch --patch-at-frame --capture-state` checks effective program
words; `verify_scene_extension.py` checks preserved draw order and native RAM.
`verify_quality.py` runs ROM-free GPU fixtures locally and under Mesa in CI.
Run `python -m unittest discover -s tests -v` for hardware-free harness checks.
Toolkit source is pinned to v0.11.1: `harness/sync_toolkit.py --ref v0.11.1`
checks both consumers; `--write` updates. The OCR filter's canonical source is
`native/hud_speed_filter.h`; reset-time patch preflight is in `native/checked_patch.h`.
`harness/sync_native.py` checks both MAME copies. Patch installation validates
the entire file before writing; the legacy per-frame self-healer remains per-word.
Configured game experiments compose with widescreen defaults; conflicts fail.
An explicit `MIDV_PATCH` environment setting replaces all defaults.

**Read these two documents before doing anything:**

1. `results/RESULTS.md` — the complete chronological engineering log. Every
   phase, every bug, every number, current staging state. This is the primary
   handoff document.
2. `E:\Source\launchbox\Launchbox-Racing\docs\cruisn-usa-port-feasibility.md`
   — strategy, product roadmap, feature wishlist, collection framing, legal
   posture (WB owns a live brand: no ROMs shipped, no binaries hosted, GPL
   obligations from deriving from MAME).

`.Codex/session-notes.md` has the immediate open items and a complete
self-sufficient handoff (written for context-loss resilience).

**GitHub:** `d-b-c-e/cruisn-collection` (private; renamed from cruisn-poc
2026-08-20 — old URL redirects). Releases publish via tag push
(`.github/workflows/release.yml`); see CHANGELOG.md for releases. Local folder renamed
to `E:\Source\cruisn-collection` 2026-08-20 (matches the repo name).

## Repo map

```
cruisn-collection/
├── harness/
│   ├── collection.py     ← THE product entry: fullscreen game-select shell
│   │                     (Stream Deck button opens this; config rig/collection.ini)
│   ├── run_rig.py        single-game launcher (in-process GL, sound, wheel);
│   │                     importable: collection.py calls launch_game()
│   ├── run_oracle.py     determinism oracle (2 cleanroom runs, pixel diff)
│   ├── run_capture.py    instrumented capture (quads + state dumps)
│   ├── rasterize.py      CPU reference rasterizer (bit-exact vs MAME)
│   ├── widescreen.py     16:9 margin analysis/render
│   └── record_diag.py    60fps desktop capture + frame-diff (flashing detector)
├── gpu/
│   ├── renderer.py       verified GPU pipeline (moderngl). THE SHADER SOURCE OF
│   │                     TRUTH — midvunit_gl_shaders.h is generated from it
│   └── live_viewer.py    out-of-process viewer (debug/reference path, MIDV_LIVE)
├── lua/snap.lua          frame-scheduled snapshots (SNAP_FRAMES env)
├── fixtures/nvram-crusnusa/  calibrated NVRAM (skips CALIBRATE CONTROLS boot)
├── patch/vunit-poc-patches.patch  FULL series vs mame-src base 6f55ed93
├── results/              RESULTS.md + proof images + flash-evidence
└── rig/                  gitignored per-user runtime (ini/nvram/cfg)
```

## The mame-src relationship (critical)

- The emulator half lives in **`E:\Source\mame-src`**, branch **`poc/quadlog`**
  (MAME 0.286 + our DIJOYSTATE2 base patch `6f55ed93` + the POC series).
  POC code: **`src/mame/midway/midvunit_v.cpp`** (env-gated, zero cost when
  unset) + `midvunit.h` (visibility + `mvgl_exit` teardown hook) + one
  7-line env-gated block in `src/frontend/mame/ui/ui.cpp`
  (`MIDV_SKIP_STARTUP_SCREENS` — BAD_DUMP warning screens refuse
  skip_warnings by design and block launcher boots).
- Build product is **`E:\Source\mame-src\vunit.exe`** (subtarget build —
  physically cannot clobber `mame.exe`). Since 2026-08-20 the subtarget
  includes **midzeus** (Cruis'n Exotica): build with
  `SOURCES=src/mame/midway/midvunit.cpp,src/mame/midway/midzeus.cpp`.
- **`midvunit_gl_shaders.h` is GENERATED — never hand-edit.** Regenerate
  after any shader change in `gpu/renderer.py`:
  **`python harness/gen_shaders.py`** (emits escaped C strings — genie's
  REGENIE source scanner cannot tokenize raw strings and dies with
  "unterminated character literal").
- **Force feedback is built into vunit.exe** (2026-09-03, `mvffb` in
  `midvunit_v.cpp`, replaces the FFB Arcade Plugin on Endprodukt's advice):
  the drivers hand the signed motor byte to `midv_ffb_write()` (V-Unit
  WHLCTLZ, Exotica LED-board offset 0, after gain/slew/clamp) and a worker
  thread drives ONE signed constant force on the wheel's steering axis
  through SDL2 haptics (Cannonball DX / Flycast model: STEERING_AXIS,
  infinite length, update + run per write). **`SDL2.dll` (MSYS2
  `/mingw64/bin`, 2.32) sits UNTRACKED beside vunit.exe** and is loaded at
  run time - no import, no build-time link; without it FFB is off and
  `midv_ffb.log` says so. Byte interpretation = the plugin's Cruis'n
  handler (0 stop, |v|/126). Sign: a positive byte pushes RIGHT (Exotica
  spring measurement) and a positive SDL level turns the Moza LEFT, so the
  level is `-sign(byte)`; `MIDV_FFB_INVERT` / SETTINGS FFB DIRECTION flips
  it. The game writes the motor every frame (~17 ms), so the 500 ms hold
  watchdog only fires on pause/exit. The old plugin files are parked in
  `mame-src/_plugin-backup-*` (never copy them back: its dinput8.dll hooks
  the process).
- Known-cosmetic: vunit exits sometimes logged a post-exit ACCESS VIOLATION
  (Event Log; also fired headless with our GL thread not running — it was
  attributed to the plugin's teardown; re-observe now that it is gone).
  Our GL and FFB threads stop cleanly via machine-exit notifiers.
  WER minidumps land in `rig/crashdumps/` for future forensics.
- After committing in mame-src, refresh the exported series (FULL series
  from the upstream tag — CI and INSTALL.md apply it onto a clean mame0286
  clone, so the DIJOYSTATE2 base commit must be included):
  `git format-patch --stdout mame0286..HEAD > E:/Source/cruisn-collection/patch/vunit-poc-patches.patch`
- ⚠️ **NEVER touch the racing build's deployed
  `Launchbox-Racing\Emulators\mame286\mame.exe`.** The POC only reads its
  `roms/`, `ctrlr/`, and nvram fixtures.

## Build environment

- **MSYS2 at `E:\msys64`** (NOT C:\ — that died in the C: wipe), GCC 16.2.0.
- Build (incremental ≈1 min; from Git Bash):
  ```
  env MSYSTEM=MINGW64 /e/msys64/usr/bin/bash.exe -lc "export OS=Windows_NT; \
    cd /e/Source/mame-src && make SUBTARGET=vunit \
    SOURCES=src/mame/midway/midvunit.cpp,src/mame/midway/midzeus.cpp \
    NOWERROR=1 TOOLS=0 -j18"
  ```
- ⚠️ `OS=Windows_NT` must be exported **inside** the MSYS2 login shell — its
  profile clears the inherited value and MAME's makefile then fails OS
  detection. Add `REGENIE=1` only on first build / project changes.
- Python side: system Python 3.14 with numpy, pillow, moderngl, glfw
  (pygame has no 3.14 wheels — don't try).

## Env vars (all read by vunit.exe, all inert when unset)

| var | effect |
|---|---|
| `MIDV_GL=1` | **in-process GL renderer** (the product path) |
| `MIDV_GL_SCALE` | internal scale (default 3; rig uses 4) |
| `MIDV_GL_CRT=1` | CRT pass on at boot (mask+scanlines+curvature); **F9** toggles live |
| `MIDV_GL_CRACKFILL=0` | disable crack fill (default ON: unwritten hardware quad-crack pixels get filled from axis-bounded neighbours in the palette pass; 3D scenes only; shell SETTINGS has the toggle) |
| `MIDV_SKIP_STARTUP_SCREENS=1` | boot straight past MAME warning/info screens (frontend gate) |
| `MIDV_TELEM_UDP=host:port` | mirror MAME outputs (wheel force, lamps) as JSON UDP datagrams (SimHub/Buttkicker); also via collection.ini `[telemetry] udp=` |
| `MIDV_FFB=1` | **built-in force feedback** (SDL2 haptics on the wheel's steering axis); `MIDV_FFB_STRENGTH` 0-100, `MIDV_FFB_DEVICE` name substring or vid:pid, `MIDV_FFB_INVERT=1`, `MIDV_FFB_HOLD_MS` (500), `MIDV_FFB_TEST=<pct>` (1.5 s level at start), `MIDV_FFB_LOG=2` (every write) → `midv_ffb.log` |
| `MIDV_FFB_SMOOTH` / `MIDV_FFB_DAMPER` / `MIDV_FFB_FRICTION` | low-pass time constant (ms) on the level; DirectInput damper / friction condition effects in % for the session (launcher: `[collection] ffb_smooth / ffb_damper / ffb_friction`) |
| `MIDV_FFB_CLAMP` / `MIDV_FFB_SLEW` | cap the motor byte at ±N / limit its change per write (driver side, before the FFB output and the trace) |
| `MIDV_FFB_TRACE=<csv>` | every output change + `wheelpos` rows (the FFB diagnostics trace) |
| `MIDZ_FFB_GAIN` | Exotica spring gain percent (launcher passes 400) |
| `MIDV_GL_SNAP=<dir>` | backbuffer BMP every ~150 presents (unattended verify) |
| `MIDV_GL_LOG=1` | diagnostics to `midv_gl.log` in cwd |
| `MIDV_LIVE=1` | shared-memory ring only (drive `gpu/live_viewer.py`) |
| `MIDZ_GL=1` | **live Zeus GL overlay** (Cruis'n Exotica renderer-replacement; default ON via run_rig, =0 falls back to MAME d3d/bgfx). MIDZ_GL_SCALE/CRT/SNAP/LOG/VSYNC variants |
| `MIDV_QUADLOG=<file>` | offline quad capture (38-byte records) |
| `MIDV_STATEDUMP_FRAME/DIR` | one-shot videoram/texram/palette dump |

## Verification workflow (the project's superpower)

Attract mode is a **bit-identical deterministic oracle** (seeded NVRAM
fixture required). The invariant to protect: `gpu/renderer.py` exact mode
(`--scale 1`) must stay **100.0000%** vs MAME's videoram on
`results/capture` and `results/capture-8000`. After any shader/pipeline
change: `python gpu/renderer.py results/capture-8000` and expect zero
differing pixels. Fresh captures: `run_capture.py <vunit> <frame>`.

Semantics that everything relies on (full detail in RESULTS.md):
- `page_control` bit 2 = render-target page, bit 0 = visible page; a run of
  consecutive same-pc quads = one **scene**; last COMPLETE scene =
  second-to-last run (never trust quad-count thresholds for this).
- Pages persist between scenes (hardware behavior — 3px cracks show prior
  frame); the 16:9 **margins are ours** and get scissor-cleared per scene
  with a 2px overscan inset.
- 2D screens are detected by **axis-aligned-rectangle dominance ≥70%** and
  crop to 4:3 (quad counts overlap between 2D ~160 and sparse 3D ~260).
- The in-process overlay is an **owned top-level popup**, NOT a child window
  — MAME's gdi caches its window DC so child-clipping can never work.
  V-Unit now runs with `video d3d` underneath; `CRUISN_VUNIT_VIDEO=gdi` is the
  compatibility fallback. NOACTIVATE/TRANSPARENT/DISABLED keep input on MAME.

## Rig facts

- Product entry: `python harness/collection.py` — fullscreen shell, all
  four games, menu music + blips (`rig/assets/`, regenerable via ffmpeg
  from LaunchBox video snaps); C toggles CRT per launch; **S = wheel-setup
  wizard** (press-to-bind → `[wheelmap]` in `rig/collection.ini`, applied
  by the ctrlr generator each launch; wins over EmuEz per-game sections).
  Config `rig/collection.ini`. Stream Deck entry: Elgato "Games" key [7,2]
  → `Launchbox-Racing\scripts\Launch-Cruisn.bat` opens the shell. Direct:
  `python harness/run_rig.py --rom crusnusa [--crt]`. Coin=**5**,
  Start=**1** keyboard, **Esc = in-game options menu** (Resume / CRT
  toggle / Exit to launcher — drawn by the GL overlay, physical-key
  polled), **F9** = CRT live toggle, **F12** = emergency instant quit
  (UI_CANCEL is remapped off Esc in the generated ctrlr). crusnwld needs ONE-TIME
  wheel calibration at first boot (persists; headless runs always
  re-demand it — no input devices — so captures must run in rig config).
- All three games verified **100.0000% bit-exact** vs MAME videoram
  (offroadc runs 512×**401** with visarea right edge 510 — renderer.py
  honors meta visarea in exact mode; the launcher passes MIDV_GL_HEIGHT=401
  to the C++ overlay for Off Road).
- Wheel buttons 33-48 = MAME tokens `ADDSW1-16` (not BUTTON33+; 49+ are
  unaddressable OTHER_SWITCH). winhybrid (default provider) needed the
  DIJoystick2 fix (mame-src 3cac3d67) — without it every wheel caps at 32
  buttons (this also silently afflicted the racing build).
- run_rig makes MAME's window **borderless-fullscreen** post-boot
  (`--windowed` opts out) and **enforces fg+focus on MAME's window** —
  keyboard and foreground-mode DirectInput FFB die without it. Never
  activate the overlay (owner's last-active-popup redirection eats keys;
  SwitchToThisWindow is banned).
- ⚠️ **Never hard-kill with FFB active** — stranded constant-force torque on
  the Moza; Esc out normally; Stream Deck "Stop FFB" key clears a stuck
  wheel. Remote/automation quit: WM_CLOSE on MAME's window is clean.
- run_rig still relaunches once when no responsive window shows in 20 s
  (a plugin-era safety net; harmless).
- If the wheel steers but FFB is silent: read `midv_ffb.log` beside
  vunit.exe (device list, which one was taken, "no constant-force device",
  strength 0). The wizard's steering device name is what
  `MIDV_FFB_DEVICE` gets.
- Known: `JOYCODE_1_BUTTON33+` tokens are dropped by the token parser AND
  invalidate the whole seq (killed keyboard Start). run_rig writes a
  sanitized EmuEzRacing copy to `rig/ctrlr/` (never edits the racing
  build's). Root cause vs the 128-button DIJOYSTATE2 patch: **deferred by
  user decision (2026-08-18) into the collection shell's wheel-mapping
  frontend** — keyboard 5/1 is the accepted interim for coin/start.
- Probe facts: GDI screen capture shows the GL overlay as pure black — use
  `MIDV_GL_SNAP` for ground truth; keybd_event-injected keys never reach
  MAME's rawinput — keyboard verification needs physical keys.
- The user's live observations at the screen are the best debugger this
  project has — four artifact root-causes came from them. Describe-what-you-
  see beats instrumentation; `record_diag.py` catches what screenshots can't.

## Working style

- Latest attended case: `results/diagnostics/world-germany-extended-20260906`
  (8783 frames, terrain option ON, FFB80); full identity matches 8783/146.
  `docs/reviews/2026-09-06-world-distance-and-impacts.md` records distance/FFB evidence.
  Widescreen Terrain is the renamed Terrain Visibility option, not far distance.
- `harness/force_options.py` resolves impact cues consistently in shell/launcher:
  explicit ROM revision (including OFF), then family, then global. Shell World
  saves the selected revision. No physical-feel acceptance yet; defaults stay OFF.
- `analyze_ffb.py --frames CASE/record/frames.csv` anchors candidates to completed
  frames; emulated-time labels/anchors require `force-source.csv`, not wall time.
- `lua/world_projection_distance.lua` accepts bounded `CRUISN_DISTANCE_FAR`
  (80016..160000, multiple of16) plus FIRST/LAST; diagnostic World2.4 only.
  160k used ~80% emulation in the instrumented window and changed silhouettes.
  Do not deploy this read-tap experiment as a product distance fix.

- RESULTS.md is append-only chronology: add dated sections, never rewrite
  history. Keep proof images in `results/proof/` (capture dirs are regenerated
  and gitignored).
- Commit mame-src and cruisn-collection separately; refresh the patch series after
  mame-src commits.
- Bit-exactness claims require four decimal places — "100.00%" once hid a
  99.9985 that cost an hour.
