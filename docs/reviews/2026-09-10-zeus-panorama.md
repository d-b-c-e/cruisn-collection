# Zeus panorama continuation — September 10, 2026

The Amazon1:12 rectangle is stale widened-margin content. Page clearing removes
it, but exposes sky that the original panorama does not cover. A second isolated
candidate continues an existing repeated panorama tile into that gap. It retains
the tile's size, texture coordinates and material. No texture stretching, model
address allowlist, hardcoded track or fixed panorama period is used.

## Page-clear result and remaining gap

Three7290-frame Amazon replays on nativec527/SHA238a8798 preserve the original
route and actual ADC timing. All ten original resource/submission files at7216
are byte-identical, and the CPU oracle matches all1,048,576 color/depth entries.
The legacy control matches all31 previous GL frames7198–7228. Page clearing
changes all31, and its repeat matches all31 exactly. The old checkpoint remnant
is visibly gone, restoring the wall behind it. A small upper-right sky gap is
now black. Therefore **page clearing alone is not complete visual acceptance**.

The original sky consists of coplanar textured rectangles. At7216 the last tile
ends at projected X564.42, while this recording's86-column margins reach X598.
The local CPU coverage prototype deliberately uses88-column margins, reaching
X600; its35.58-column gap and pixel counts are a wider coverage experiment,
not an exact pixel oracle for the recorded GL view. Original submitted tiles
already demonstrate a repeating panorama:32 overlap comparisons agree on a
1536-column period in each of the four marked Amazon captures. Shorter apparent
periods fail material/UV comparisons and are rejected.

## Bounded structural continuation

The shared native helper recognizes8–64 contiguous background tiles on at most
four horizontal bands. It requires a known page/clip, finite coplanar rectangular
geometry, the background depth-clear policy and matching existing texture/UV
rectangles across the inferred period. Incomplete, inconsistent or unsupported
layouts produce no added tiles. Copies lie entirely outside the original512
columns and join the existing panorama edge. They use original tile geometry
at unchanged scale and preserve all non-X vertex parameters.

The GL consumer collects only the initial uninterrupted background span after a
clear. It finishes before foreground geometry, palette changes, WaveRAM uploads,
page changes or presentation. The64-tile limit discards an over-budget span.
Original guest execution, hardware submissions and recorded models are untouched.
The palette guard remains required so submitted copies retain their material.

`--zeus-sky off|repeat` is explicit and diagnostic-only. Repeat requires
`--zeus-palette guard --zeus-margin-clear page`, live Exotica GL and physical
force zero. Absent controls preserve old recordings. Native startup and completion
receipts report recognized groups, accepted groups, copies and budget rejections.

The independent Python and native plans agree on the four Amazon captures.
The offline CPU continuation adds one tile at7216, changing2,495 margin pixels
and filling the exposed sky. The other three center captures require no copy.
All four retain the entire native center's RGB24/depth exactly. Two actual shader
fixtures also preserve the center and other page and keep foreground geometry
in front of the continued panorama. These are controlled fixture/offline results;
native gameplay validation follows below.

Three native7290-frame trials now complete all31 real3840x2160 captures from
7198 through7228. Sky Off matches the parent page-clear candidate in all31.
Repeat changes all31, and a second enabled run repeats all31 exactly. The
inspected7215 image removes the checkpoint remnant, restores the wall and fills
the upper-right sky without stretching it. The central screen rectangle
X768..3071 is unchanged in every page-clear and panorama A/B image. All ten
original resource files at7216 remain exact; the actual CPU oracle matches all
1,048,576 color and depth entries, and original camera/ADC timing is preserved.
These CPU-instrumented runs do not measure normal GL-only performance.

The first full8860-frame Amazon run passes, including117 completed4K images,
original7200 resources and the original7051camera/21153ADC samples. It captures
nine additional late camera samples; comparison explicitly uses the older
reference's1800..8850 interval and retains the complete new trace for repetition.
Two local comparison failures are retained: the initial unequal trace lengths,
and a mistakenly selected3600 resource reference for a7200 capture. Comparing
the matching7200 reference verifies all ten files exactly.

The first full repeat fails at the renderer's consumer timeout near frame8460:
112/117 capture files are written;111 report no drops and the last records a
dropped state message. The
failure remains intact. Rendering and synchronous screenshot readback/file
writing share that consumer thread, but the current log cannot identify which
operation stalled. The fresh `sky-full-amazon-repeat-v2` succeeds: all117 images,
the full7060camera/21180ADC samples and the original resources match. Thus a
complete repeat pair passes, while the earlier timeout remains an open harness
failure, not a resolved or discarded result.

Enabled Hong Kong also completes6000 inputs, preserving the original shared
4191camera/12573ADC interval and all ten original4700 resource files. All21
completed4K images5400..5420 remain identical. The detector observes2480 groups
and accepts none, making no copies for the unsupported pattern. This is sampled
regression coverage, not proof of whole-track correctness.

Hong Kong snapshots3500/4700/5410 fail the current strict period condition.
Those failures are retained. The candidate therefore adds no inferred panorama
there. This is a coverage limitation, not evidence that Hong Kong is corrected.
Its periodic structure and broader track behavior still need examination.

## Build and checks

Native `2b55a1d7947e178406b02ed9b876f97073116b96` is separately built and pushed.
Candidate: `build/candidates/2b55a1d7947/vunit.exe`, SHA256
`e0ba3bf0c4da44b9c0f022cf547cbad34ab2dc0bf9fa4eb5de679503eb898eb1`.
All153 exported patches reconstruct tree
`6ee1a6085a58121b0848272d5e77ac83c886ab57`.

Full local checks pass281 Python tests without skips,32 native helpers,
10,081 C31/137 yaw vectors and the existing32 GPU cases plus25 policy,
three palette, four margin and two panorama cases across91 commands.
The428-file source identity is
`49343cca42e07c6683f2570e14cd4f6a2eab204eb5fe72210922ecbc8460a9f5`.
The three dense native Amazon7290/31GL/CPU7216 trials pass their separate oracles.
All seven default cases now pass on this exact candidate: actual UDP/memory
telemetry, four software force-policy/polarity checks and Exotica21GL included. Personal Stream Deck v0.5.0/SHA87d04de4 is unchanged.

## Other findings to carry into future scenery

Six snapshot audits match1,600 captured full palette tables against their final
WaveRAM source colors. Of1,686 captured models,1,680 match their final WaveRAM
bytes. Each snapshot contains one model whose source has changed by snapshot end;
the six retained mismatches involve the same reused source area. A final memory
snapshot is therefore not a general model/upload lifetime oracle. Capture at use
time or explicit ownership/versioning remains necessary for host geometry.

The [marked-window and depth study](2026-09-09-amazon-margin-depth.md) also
establishes that most sampled35/45s ground wedges lack submitted geometry.
Page/panorama clearing cannot supply that ground. The future-depth capacity study
uses the earlier Hong Kong section snapshots, separate from Amazon:1,425 eligible
future centers at3x exceed the current24-bit range in snapshot3500. Host depth,
future source readiness and extra geometry remain unfinished. A separate local
cross-capture study at Hong Kong3500 associates580 of2719 potential3x future
spheres with model/palette bindings already submitted in that snapshot. Their
captured model bytes match the final WaveRAM snapshot. The remaining2139 use
836 other bindings. This is catalog coverage, not proof those resources are
missing or ready: exact clock identity, ownership and queued upload completion
remain unverified. A per-model allowlist would leave most sources unaddressed.
The follow-up [future-material and fade study](2026-09-10-exotica-future-materials.md)
finds all970 selected model buffers parse and remain unchanged at later4700/5410
snapshots;401 later actual model submissions match their earlier bytes. It also
reconstructs486 original time-based fade-alpha/flag transitions, with three
low-word list-membership changes explicitly outside that render-only result.

The293-file [public proof](../../results/proof/2026-09-10-zeus-margins/README.md)
recomputes original routes and selected4K pixels. Full image sequences, hardware
resources, CPU/native/GPU/build and seven-default gates remain hash-bound
receipts. Its first verifier count error is retained locally:112 capture files
were written in the failed repeat,111 without drops and one with a dropped state
message. The corrected verifier checks those distinctions explicitly.

Raw evidence and local drafts remain in
`results/diagnostics/exotica-amazon-20260909`. No raw game resources are published.
No release, deployment, physical-force test, World tuning or menu removal follows
from this candidate. Continuous work proceeds into live validation and the
remaining material/ground/future-scenery contracts.
