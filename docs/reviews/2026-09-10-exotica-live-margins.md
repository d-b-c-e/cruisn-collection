# Exotica live margin candidate — September 10, 2026

**Current status:** full/repeat/Hong Kong/observe, seven defaults and final local
checks now pass on 50a. Read the [acceptance report](2026-09-10-exotica-margin-acceptance.md).
The chronological checkpoints below retain earlier pending and failed states;
they do not override that report. No personal deployment or farther drawing yet.

## Current extension status

The separate write-tracking optimization now passes the6,000-frame verification
run. **All2,457 CPU seals equal an independent full16MiB comparison.** It copies
11,499 pages in total, including4,096 at initialization; no later scene requires
more than four pages. All25 displayed frames, ordered geometry/counters and
85 files from five raw snapshots are byte-identical to d4d. Input/camera/ADC
timing and original rendering resources also match. Full written-mode, repeated,
Hong Kong, observe-only, seven-default and final local runs are now underway
serially; performance and complete acceptance remain pending.

The d4d full Amazon drive completes8,860 inputs,5,290 active scenes/970,889 quads,
57 camera advances and45 binding advances. All7,060 camera samples and21,180
actual ADC read times, plus ten original rendering resources, match the control.
All1174K frames complete;48 change. A full observe-only run matches all117
original images. Hong Kong's6,000-frame drive also passes route/resources and
21 completed images. Independent snapshots match there at5000 (4/9), and in
Amazon at6330 (24/165),7187 (0/0) and8760 (0/0). Inspected Amazon frames at game
44.89s and57.50s replace black edge ground with textured geometry.

Performance is still open: the fully instrumented Amazon run averages89.29%
emulation speed versus93.67% for the corresponding original control. Its full
16MiB scene-end texture copy is measurable. A separate candidate
`50a6eaa3d1f233f51d1c0174b6858a09487e9120` now gives CPU sealing an independent
write bitmap, copying only pages changed since the previous seal. GPU material
commits cannot consume that bitmap; first use and save-state restoration require
all pages. Verification mode compares the entire resulting image every scene,
and every raw snapshot always requests that comparison. The dual-reader fixture
passes1,000 writes/reset/independently scheduled commits.

This optimization is built/pushed/frozen, SHA256
`a4e4cd4dc060e068ae4e4f3c29f9c8abc853bdc28420958ee797f924742581de`, with176patches
reconstructing tree `0bf35ca188db56a9a90166f13763af39df28fbfd`. Its live full-image
verification is underway. The d4d results above are not automatically renewed
by this implementation change; repeat, default-game and final local checks remain.

The d4d **6,000-frame wider replay now passes**:2,457 completed active scenes,
547,883 quads,31 camera advances and eight binding advances. All4,191 camera
samples/12,573 actual ADC read times and ten original rendering-resource files
match the control. All25 requested4K images complete. Five sampled scenes
independently reconstruct, including frame5604 after its existing raster-policy
filter:23 instances/435 quads.

The generated descriptor's one quad is intentionally excluded by the current
private-pass contract because it lacks depth testing. There are55 excluded
instances across this run and **zero rendered RAM models**. The fix lets us
correctly decode and classify the source instead of aborting; it is not evidence
that this special primitive is now safely rendered. Its raw failure and decoded
state remain local for the later ordering/occlusion work.

Local checks pass **332 Python tests / no skips,46 native tests,127 commands**
at source identity `e012b5d525b3b67a32c690ee499b4b0b1294d30c4d9488ca994415c8706a7f9a`.
Excluding the five raw-snapshot scenes, the scene-end copy averages1.392ms
(p99 2.192ms); assembly averages0.196ms and material processing1.385ms in full
page-verification mode. The CPU byte checks average0.056ms. GPU callback mean
is0.451ms, p99 0.820ms, max16.800ms. These are instrumented callback timings,
not whole-game smoothness acceptance. Full Amazon, Hong Kong and seven-default
acceptance remain pending.

The frame5604 rejection is now isolated to a **generated RAM model descriptor**.
The current-object native builder inherited a ROM-only descriptor guard from
future scenery. An independent Python decoder reconstructs all28 candidates;
an instrumented native analyzer identifies the precise rejected span check.
The bounded failure capture is retained with exact scene-end and ready RAM/Wave.

Native `d4d696ed3612ba52ba4c2203427737718a9d5b5e` permits bounded six-word model
descriptors in the owned current-scene RAM image. It rejects command-ring spans,
out-of-range roots/alternates and leaves future scenery's ROM-only checks intact.
The former failed snapshot now matches independently:24 instances/436 ordered
quads. It is separately built/pushed/frozen, SHA256
`2a4faa534309c3763bb3e9269e340d61283a89906893b2d599a159e8aea8dfc3`;
175 patches reconstruct tree `0d700ae80750c6cf08b005c09fc331489ec627f8`.
This offline correction still needs the wider live replay and final acceptance.

The resource-lease candidate `b0e46125bfdb3f67b78e1cf5bfa6045239de9891`
seals WaveRAM at CPU scene end and compares the model spans, palettes and
conservative texture pages needed by the old scene at actual FIFO completion.
This permits normal animation-pointer advancement only when those resources
remain byte-identical. It is separately built/pushed/frozen, SHA256
`56c1121ac798354c6687e79547065bc4d7eae77c3319317d160d11639d1ad47b`;
173 exported patches reconstruct tree `d66336f1d1b705174dfe6e8813d7c838f7181cab`.

Its wider Amazon run completes **2,078 active scenes / 521,404 quads**, including
24 camera advances and eight binding advances, before a new geometry rejection
at frame5604. The completed prefix checks58,527 model spans and61,885 palettes.
Four exact sealed/ready snapshots independently pass resource, native/Python
geometry, original depth and outside-margin color checks:3510 (41/476),4131
(42/364),5072 (63/522),5080 (56/160), expressed as instances/quads. This is a
**partial-run result**, not full replay acceptance. The retained failure now
needs a bounded operand snapshot to identify the unsupported geometry case.

The standalone coverage helper passes1,688,400 synthetic texel addresses.
Independent brute-force UV/swizzle enumeration on1,158 actual quads covers
11,488,877 bounding texels; all required pages are present. The Python reference
uses row-block spans instead of the native rectangle span. Texture coverage is
conservative, including negative-coordinate clamping and bilinear padding;
these checks do not establish general GPU interpolation or occlusion correctness.
The16MiB scene-end copy and resource checks still need performance acceptance.
All seven defaults and the complete local suite have **not** been renewed on
this candidate. Personal v0.5.0 remains unchanged.

Short c998 drawing and repeat both complete6000 inputs,25 completed4K frames and
13 active scenes/4,435 ordered quads. All25 frames and both raw snapshots repeat
exactly. Compared with the no-draw control,13 displayed frames change; inspection
at5072 and5082 confirms textured ground replaces the black left wedge with CRT
enabled. Raw5072 repairs6,459 black pixels,5080 repairs4,231, with no newly black
pixels among the changes. Original depth, outside-margin color, route, ADC timing
and ten original rendering resources remain unchanged. This covers a short
window, not the full track or farther drawing distance.

The wider c998 run fails at scene3510 because camera memory advances during the
16.58ms old-command drain. A separate read-only3550-frame control captures four
scene-end/after-target pairs and2,817 FIFO events. One pair changes camera, view,
positions, animation and list links before the old target completes. Six of44
margin candidates change fade/link fields. All1,741 camera samples/5,223 actual
ADC read times match the original control. This is a legitimate game transition,
not playback drift; both the failure and raw diagnostic pairs remain local.

Native`b908fbd57d51ebab9f4b6fa5592d60f8a5843fbb` now seals the scene's main/internal
RAM and selected render operands at CPU ordinary_end. It uses those owned camera,
pose and state values after the original FIFO completes. The first affected scene
now reconstructs independently as41 instances/476 quads. Candidate SHA256 is
`bcd5aec8cf205e387ef0e3e58a5c96656f7f7c75bb93a4205a61626b8d5d90a2`, with172patches
reconstructing tree`043f3a5ff6e03a6d644cd1514e5458fa0d3cf16a`.

The wider b908 run then reaches a changed model pointer at scene4131 and stops
under the retained material-binding guard. Full acceptance is still **open**.
Next distinguish animation pointer advancement from actual model/texture/palette
reuse by checking the bytes needed by the owned old scene across the device
fence. Do not simply discard the binding guard or label this whole-track success.

The separate native candidate now connects the owned current-object capture to
the original command fence and a private depth buffer. This is a CLI-only
diagnostic. It keeps original far distance and does not change product defaults.
Live gameplay acceptance is in progress; the earlier offline repair does not
establish acceptance for this integration.

## First integration checks and retained failure

The disabled5ff control completes6000 recorded inputs and25 paired4K images,
matching accepted2eac. All4,191 camera samples,12,573 actual ADC read times, and
ten original command/model/material resources are identical.

The initial observe run fails the render watchdog at frame5080. Both captured
late scenes reconstruct independently:5072 has63 instances/522 quads;5080 has56
instances/160 quads. Their original color and depth remain unchanged, and the
complete camera/input-read trace matches. However, synchronous raw color/depth
file writes hold the GL consumer for1.274/1.487seconds. Only11 of13 scenes reach
the consumer; the harness correctly rejects the lost rendering state and missing
material generations. The failed run remains local and is not a visual pass.

Native`c9982f3e662b7932ff598741b797662faf4fa978` moves those owned snapshot bytes
to the existing bounded FIFO writer, with separate completion/failure receipts.
It uses at most512MiB/32 pending-or-in-flight requests. Only explicit offline
capture pacing can wait for capacity; no GL or game memory reaches the writer.
This is a separate native fix, frozen at`build/candidates/c9982f3e662/vunit.exe`,
SHA256`7bf0f3659ca4adc58d4d91914bec7e91710c141f5499c858ec68bde519297d40`.
The171-patch export reconstructs tree`ff66026f1203fb21df1b70ceb13a1d2e1cec6593`.

Its capture-only replay now completes all13 scenes/4,435 captured quads,26 owned
material generations and all requested files. The same25 images, route, actual
ADC times and ten original resources match2eac. Both late independent geometry
reconstructions pass again. Snapshot callbacks drop to139/130ms, including full
GPU readback and validation; this is diagnostic overhead, not ordinary drawing
cost. Drawing/repeat and broader acceptance are still in progress. The329-test
source identity below belongs to the pre-async checkpoint; final checks must be
renewed after this fix.

`--exotica-host-active off|observe|draw` requires an explicit candidate when
overridden, the bounded scene observer, private materials, and command-fence
observation. Absent settings preserve old recording behavior. Recorded settings
round-trip; disabling the parent observer removes the active setting as well.
All these runs require physical force output disabled.

At the four original list boundaries, the CPU owns each object's rendering
operands and culling inputs. At the actual original FIFO completion, it rechecks
membership, slot contents, camera, matrices, projection constants, programs and
default state. Actual original model submissions are excluded. Added geometry
uses current model bytes and owned palette colors. Unsupported D24/raster cases
exclude the whole instance and are counted explicitly.

A second, explicitly ordered material generation belongs to the same scene as
the earlier future-scene observation. Its owned XMD1 packet contains geometry
and material updates together. No queued work borrows guest RAM or live device
pointers. The same written-page image tracks both phases and can compare every
generation with a complete scan.

The GL consumer flushes original polygons, copies original D24 depth only in the
two margins, and draws through that private copy into the shared color texture.
The original depth remains untouched for subsequent original rendering. Original
shader material, blending and dither behavior are retained. Eight-vertex clipped
polygons produce complete triangle fans. Observe mode consumes the same captured
geometry and materials without drawing them.

Snapshot checks require byte-identical original depth, center, other-page and
outside-page color. Producer/consumer counts, generation order, palette ownership,
triangle fans and snapshot completion are independently checked in Python. A
separate snapshot reconstruction is still required to validate geometry itself;
these receipts alone cannot certify transparent foreground ordering or handover.

Native `5ff1f9f81329a2dabed6b454a74ebd90b94b0aec` is built separately and pushed.
Frozen `build/candidates/5ff1f9f8132/vunit.exe` has SHA256
`a88a0f8106e801e2440c117fcb07f3b2cd96ae7e3cc67563682d72ebe2211e00`.
The170-patch export reconstructs tree`9cffd3235432005bfebeeda47812cbb9ff84d468`.
The first compile failed on hexadecimal-address tokenization; that log is retained
and the arithmetic spacing is fixed in a separate native commit.

All329Python tests/no skips,45native tests and125local commands pass at source
identity`fa537af0216bc8e6bb6535b8e3ebe346e121616c251c4e9a2decc083c40aff0c`.
The next acceptance is disabled/observe/draw/repeat on the Amazon recording around
native5072/5080, followed by broader time/track coverage and seven default cases.
Compare the actual input sampling times and camera route, original command and
material resources, independent late geometry, and completed4K images.

No deployment or release. Native2eac retains the last seven-default acceptance;
the personal Stream Deck binary remains v0.5.0/SHA87d04de4. Raw model, texture,
RAM and image evidence stays local. General farther depth, alpha ordering and
the separate original texture-upload timing concern remain open.
