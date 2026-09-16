# Exotica: rearm after a quiescent machine reset

The continuous candidate previously stopped immediately on any machine reset
after lifetime tracking began. A scheduled reset at frame4000 reproduced that
failure even though all CPU phases and the GPU queue were drained. The original
recording completes5460inputs. Its title calls this a mid-race case, but it has
no nonempty future geometry or marked endpoints before reset; do not treat it
as an extended-scenery workload test.

Native `e65c6270d42` permits a reset only after verified startup and completion
of every pending CPU phase. It checks matching scene/fence/waiting/active counts,
empty command ownership, and the device FIFO before queuing a separate
GPU boundary. The GPU independently checks the scene, material generation/hash,
completed endpoint order and monotonically increasing reset identity.

At that ordered boundary, a shader copies ordinary color into the private target
and converts ordinary D24 depth into the private D32F representation. All
16,777,216 depth codes and color pixels pass an exhaustive synthetic GPU check;
ordinary color/depth remain exact. This avoids a depth blit between incompatible
formats. The shader is created only when reset is actually requested.

CPU reset invalidates old allocation/admission identities, clears retained source
selections and invalidates the ROM-source cache. Material generations and total
scene/endpoint counters remain continuous. Fresh pool and first-scene proofs are
required before extended rendering resumes. Each reset saves separate proof
files; original startup evidence is preserved and exit notifiers are registered
only once. Ordinary emulator reset still performs its own register/RAM changes.

The same5460-input case now completes. Initial startup is1385; reset boundary3999;
fresh startup5384, with scene2615 followed by2616. All inputs/times and native
snapshots match the ordinary recording. Seven completed4K CRT images4200..5400
are byte exact. CPU/GPU reset material receipts match,2683 scenes finish, and
615,743,800 queued bytes drain with joined shutdown. Nine focused Python tests
and the native reset-boundary test pass.

The raw replay remains **FAIL** because this early case contains zero marked
endpoint workload. `quiescent-qualified.json` accepts only the explicitly checked
reset/reboot behavior. The original fatal run is retained; no workload verifier
was relaxed. Next test a reset after actual nonempty extended scenery and source
admissions. Reset during unfinished work, reset before initial startup, another
reset while rebooting, and reset after degraded retirement remain strict/open.

Local evidence: `results/diagnostics/race-transitions-20260916/exotica-mid-race-reset`,
`exotica-reset-seed.json`; export receipt and build log under
`world25-roads-20260914/quiescent-reset-*`.256 patches reconstruct native tree
`9230c1757f47947579bcb6957b7a2a825729a4db`; frozen candidate SHA256
`d5fb48024f5a243d823a087df0cd1e149b88bc5f16d6463046a75dff07d1c41b`.
Personal Stream Deck binary and publicv0.5.0 remain unchanged. No deployment,
physical FFB or general reset/release acceptance is implied.

## Reset after actual extended scenery

A second case preserves all5500Mars inputs, appends an explicit neutral tail,
and schedules reset5560. Its ordinary recording and continuous3x replay both
complete7500inputs. The normal replay report now passes all workload checks:
4679scenes,2,993,770futurequads,2598marked endpoints prepared with0reject,13,689GPU
pairs,488lifetime bindings and12epochs. CPU/GPU reset receipts agree at5559
(scene4161,material generation12372); fresh pool/scene activation occurs6944
(scene4162). All2,734,357,696queued bytes drain and workers join.

All7500original inputs/times/native snapshots,5691camera rows and12,921actual ADC
rows match. Twelve completed4K CRT images cover5200..7400. Both pre-reset images
are byte exact the retained prior3x candidate; all ten post-reset images are byte
exact the ordinary control. The355near-black pixels differing from ordinary at
5200 are already present in that prior3x image, not a reset regression.

Evidence under race-transitions-20260916/exotica-active-reset:
report.json, host3x/report.json, qualified.json and prior-3x-prefix.json.
This closes the sampled quiescent reset with actual prior scenery ownership.
No repeated full drive, new build or verifier relaxation was needed. The
interrupted-work/pre-startup/repeated-during-reboot cases listed above remain
separate limitations. V-Unit reset cache lifetime is the next source audit.

The later [pre-device reset correction](2026-09-16-exotica-pre-device-reset.md) fixes an ordering flaw: this original hook checked FIFO after Zeus had cleared it. The corrected root hook proves emptiness before child reset and preserves the actual7500-input reset and all twelve completed images.
