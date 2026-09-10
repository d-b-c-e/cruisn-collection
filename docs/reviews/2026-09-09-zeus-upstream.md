# Zeus upstream review — September 9, 2026

MAME's current development branch is named `master`. This review checked
`17d29108c100ff26bf9f9bbe21553ab9034bd8d7` and all **291 open pull requests**,
including every page of changed filenames. Four open PRs touch Zeus paths.
This is a source review, not evidence that an upstream change fixes Amazon.
The personal v0.5.0 executable and published releases remain unchanged.

## Isolated candidate checkpoint

Native `9136388a026` adds diagnostic policy bits; `edb517392f82b14646736c47f12519bf28900b9c`
separately clarifies the DIP label. Both are pushed to our fork. The separately
built candidate is `build/candidates/edb517392f8/vunit.exe`, SHA256
`cb65a78766284fd839965f363e5173056e15a3a8664fcbdd65e435d9dd6179bb`.
All 149 exported patches reconstruct tree `0f37e795158c8792ba000c7e3228035c3dec2808`.
The root personal executable remains SHA87d04de4.

`--zeus-upstream legacy|depth|alpha|blend|all` selects the trial explicitly.
Absent options preserve frozen recordings. Nonlegacy trials require an explicit
candidate and actual native acknowledgment; native diagnostic force must be zero.
The model journal records a versioned policy, rejects mixed policies and validates
the requested mode. Legacy captures retain version 1 and identical bytes.

Local checks pass 273 Python tests without skips, 29 native programs, 32 existing
GPU checks and 25 new Zeus pixel cases across 81 commands. The same 25 pixel cases
also pass against the actual generated native shader. Source identity (409 files):
`ad11a87d8f9def7406d807c25d606b513671938bbc9bb3881e8b1c9b720b2336`.

The first full Amazon legacy run preserves all 8,860 inputs, 7,051 camera samples,
21,153 ADC reads/times and **all 59 original 4K images**. All ten captured original
model/resource files at frame 7200 are byte-identical to the earlier candidate.
The combined trial preserves the same motion and original model/device/resource
data; both independent geometry oracles match all 3,380 ordered quads from 223
models. Only the selected depth/blend/source-alpha fields differ. Its images
change in 33/59 samples. The car-selection reflection is restored in the inspected
frame, while damaged description text and the 1:12 artifact remain. Changed pixel
counts are not a visual acceptance verdict.

The individual trials and combined repeat now finish the full drive with the same
inputs, camera and ADC timing. Their frame7200 model/geometry/resource checks all
pass. The combined repeat matches all59 completed4K images exactly.

| Selected policy | Amazon images changed from legacy | Observation |
|---|---:|---|
| Depth floor | 33/59 | Changes depth/overlap decisions; not a whole-track visual acceptance verdict. |
| Alpha depth | 0/59 | No visible benefit in this sample; synthetic foreground/behind-surface GPU tests exercise it. |
| Blend fields | 4/59 | Changes frames2520/2640/2760/2880, restoring car-selection floor reflections. |
| All three | 33/59 | Includes the reflection improvement; all59 images repeat exactly. |

Two additional headless CPU runs preserve the original3650-frame input prefix and
1850camera/5550actual ADC samples. At frame3600, the independent CPU rasterizer
matches **all1,048,576 RGB24 and depth entries exactly**, under both legacy and
combined semantics. Both native/Python model oracles also match414models and
3488ordered quads. The headless replay's comparison against the original GL-only
CPU snapshots deliberately fails; those retained reports are not overall passes.
The CPU-buffer results are separate, explicit evidence. WaveRAM is a final
snapshot, so these checks do not establish write/upload ordering generally.

The damaged car-description text also appears in the headless CPU image at2520.
That defect is not explained solely by the enhanced GL renderer. The marked
Amazon1:12 artifact is unchanged by the combined trial at7200. All seven default
cases now pass on this exact candidate, including actual UDP/memory telemetry,
four software force-policy/polarity checks and Exotica's21 completed4K images.
The enabled-policy Hong Kong trial also completes6000frames and preserves
4191camera/12573actual ADC samples. Native/Python match316models and2570ordered
quads; original model/device/resource bytes are unchanged after only the declared
policy fields are normalized. Of its21 completed4K gameplay images,19 are exact
and frames5417/5418 each change just two pixels. This is narrow sampled coverage,
not whole-track visual acceptance. Do not deploy or make this the default.

Public proof is in `results/proof/2026-09-09-zeus-upstream`. Its verifier
recomputes six full Amazon input/motion traces, two headless prefixes and the
selected4K car-selection/1:12 windows, using lossless image bases/deltas. Full
geometry/resources, all59GL, CPU/GPU/build, Hong Kong and seven-default checks
remain hash-bound receipts. Raw game operands stay local.

## Separate palette-lifetime investigation

The native GL consumer uses256 palette rows. Queued vertices retain their row
number, but an upload can wrap around and replace that row before those vertices
are drawn. Its batch boundaries depend on when the consumer reads the ring, so
this is a concrete route to host-timing-dependent material corruption.

A synthetic GPU reproduction produces different colors for the same geometry
and palette loads when the draw is delayed. Flushing before overwriting a row
still used by pending geometry preserves its intended color. The actual Amazon
frame3600 capture contains288 palette loads between its clear and final draw.
Replaying those captured commands/resources with the CPU oracle produces29,968
wrong full-buffer pixels under the delayed256-row policy; an early draw or one
guarded flush restores exact native CPU pixels. Those differences are outside
the currently displayed page in that capture. This demonstrates susceptibility
in real captured data, but **does not yet reproduce the specific displayed
black-sky failure** in the earlier repeat. Native consumer event tracing and a
guarded A/B trial are next. Keep the earlier frame3600 failure as unresolved.

## Relevant changes

| Upstream work | Local status | Action |
|---|---|---|
| [Open #16094: depth and blending](https://github.com/mamedev/mame/pull/16094), head `54b7ec0720e1d3a3d26a2e881b06628f78732837` | Added to a separate, default-off diagnostic candidate | Isolated A/B trials against Amazon and Hong Kong; CPU, GPU and independent oracles carry matching selectable semantics. |
| [Merged #16058: dot clock, X offset and vertical counter](https://github.com/mamedev/mame/pull/16058), `5fdbebde74ce2cb4db89ae615860c51a1bbf1f38` | Missing | Separate integration. Latch framebuffer origin and stride per deferred primitive; extend capture metadata if required. |
| [Merged #16046: Exotica timer and depth clear](https://github.com/mamedev/mame/pull/16046), `64ee7b37da03ae9b195c3cd4adacf45f5bc6b582` | Already backported in native `9f8397cf6ea` | Retain existing timer and SGRAM decoding; not a new fix to apply. |
| [Merged #16057: DIP label](https://github.com/mamedev/mame/pull/16057), `ee608cbb9d2c` | Clearer label in the separate candidate | Defaults, saved mask/value, and steering/force behavior are preserved. |
| [Earlier rendering work #15719](https://github.com/mamedev/mame/pull/15719) and [#15723](https://github.com/mamedev/mame/pull/15723) | Backports `d5f9f613a33` and `40c0fd8efb3` | Preserve existing fixes; compare source behavior, not just Git ancestry. |

#16094 treats register `0x15` as a depth floor rather than an additive bias,
keeps register `0x14` depth testing/writing for alpha textures, and decodes blend
fields rather than recognizing only two complete register values. A source
factor of `0x04` selects unity. The PR reports improvements to The Grid and
Exotica's car-selection reflections. It remains open; the author's observations
do not establish correctness on our renderer, tracks or extra scenery.

This is relevant to the inherited `0x15` state found in our Exotica probes.
Reproducing original command words does not prove that our interpretation of
those words is correct. Keep those two tests separate.

#16058 also latches framebuffer location/stride for deferred rendering. Our
captured Hong Kong state has a clock divider of six, no vertical scale and zero
X offset: the old and new clock formulas agree for that sample. That observation
does not establish timing compatibility for every track. Renew original
input/ADC timing after any clock change.

Follow-up snapshots at Amazon3600/4200/7200 and HongKong4700 cover1,365 model
contexts and19,972 submitted polygons, including all in-model register writes.
Every draw retains X offset0; all contexts use yScale0 and divider field5.
No in-model write changes either render-window offset. This narrows the likely
benefit for these scenes but does not cover unjournaled CPU register changes or
deferred CPU ordering. The independently reconstructed7200 CPU page also shows
the silver checkpoint structure visible in the4K image. Its later clipped edge
still needs a matched capture; it is not explained by a nonzero X offset here.

## Other open PRs

- [#16021](https://github.com/mamedev/mame/pull/16021) adds motor output naming
  while addressing Driver's Edge. Our Exotica driver already exposes
  `wheel_motor`; it is not a new graphics fix.
- [#13138](https://github.com/mamedev/mame/pull/13138) changes The Grid DIP label
  strings to standard definitions. Its Zeus delta is not rendering work.
- [#6515](https://github.com/mamedev/mame/pull/6515) changes embedded layout
  references. Its Zeus delta is not a graphics algorithm change.

The review includes Zeus2 device files and the Zeus1 `midzeus_v.cpp` path, plus
driver/header history. A filename scan can miss indirect shared-subsystem
changes; this is not an audit of every MAME change. Local API receipts are under
`results/diagnostics/exotica-amazon-20260909/upstream/`.

## Acceptance before adoption

1. Preserve original recordings and legacy rendering controls. Test the three
   #16094 changes separately, then together. A shader-only implementation would
   leave CPU output and diagnostic oracles inconsistent.
2. Inspect dense Amazon windows at **game elapsed** 0:35, 0:45, 0:57 and 1:12,
   plus car selection, shadows, transparent effects and the finish. Menu time
   offsets the external clock; these values are not replay seconds.
3. Check original command/resources, camera/actual ADC times, completed 4K images,
   repeatability and uncaptured performance. Amazon's initial repeat differs at
   frame 3600 despite matching motion; retain and diagnose that failure.
4. Renew all seven default cases on any changed native candidate. Then evaluate
   future scenery against the corrected baseline. Neither this review nor extra
   submissions establish four-game 3x acceptance.
