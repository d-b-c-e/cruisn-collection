# Overnight queue: consistent 3x scenery — September 9, 2026

**ACTIVE: explicitly resumed by the maintainer after the morning checkpoint.**
The expired 08:00 cutoff has been removed. Continue toward feature parity across
all four games; [the morning handoff](OVERNIGHT-RESULTS-2026-09-09.md) records the
starting evidence and limitations, rather than a current stop instruction.

The maintainer requests concentration on robust 3x draw distance equally across
USA, World, Off Road and Exotica, followed by removal of confusing or redundant
graphical experiments **if the replacement succeeds**. The existing
`cruisn-overnight-cheats-and-distance` heartbeat is active with this scope and
the display name **Cruisn extended scenery parity**, every one minute without a
new time cutoff. The September 8 queue and September 9 morning stop are historical.

**Continuous active work:** the maintainer objected to30-minute gaps; the recovery
wakeup is now one minute. Do not stop at a milestone to wait for the next trigger.
Continue implementation and verification directly; use independent offline work
during builds/replays or while the personal rig is occupied.

Latest: [USA future rendering](reviews/2026-09-09-usa-future-rendering.md) is
integrated in a separate native candidate with live material checks. 3x adds
small visible changes beyond2x and repeats its original route and images.
Performance remains below full speed after model/reciprocal caching. Final
resource/default gates pass. [Off Road's standalone codec](reviews/2026-09-09-offroad-model-codec.md)
now passes independent/live projection and ordered-DMA checks. Its
[transform/LOD reconstruction](reviews/2026-09-09-offroad-transform-and-lod.md)
also passes. Its [future-section source](reviews/2026-09-09-offroad-future-sections.md)
now matches actual loaded/later objects and seven partial loader boundaries.
Its [integrated host candidate](reviews/2026-09-09-offroad-host-rendering.md) now
passes bounded4K/repeat/original-resource/default gates, with broader visual
acceptance still open. [Exotica transforms](reviews/2026-09-09-exotica-transforms.md)
now match40093 calls and39541 ordinary emissions; independent Zeus model geometry,
material state and future-section host integration are next. Stream Deck is unchanged.

v0.5.0 is the published and deployed baseline. The repository is now public.
Preserve released tags/ZIPs, personal settings, original recordings and default
behavior. Build native candidates separately using the local build targets.
Do not run physical FFB unattended, tune World's force response, enable hosted
workflows or publish another release. Commit and push completed milestones
separately, including native patch exports when applicable. Keep ROMs, raw resource
dumps and personal state out of the public repository.

## What success means

Three times the normal distance must produce earlier **visible** static scenery
with sound materials, occlusion and handover to normal game drawing. A larger far
constant, additional submitted polygons or a menu labeled 3x is insufficient.
The same user-facing setting should have comparable meaning across games, with
separately verified implementations and revision guards. World 2.4 and 2.5 both
need coverage; do not silently treat one revision's success as both.

Zero pop-in everywhere is the stretch goal, not an established property of 3x.
Report measured gains and the limits of the recorded routes. Keep unsupported
codecs, dynamic objects and unknown material paths explicit. Avoid per-model or
per-level allowlists and changes to guest simulation solely to draw more scenery.

## Starting evidence and next work

| Game | Current evidence | Next implementation target |
|---|---|---|
| World 2.4 | Host future sections now produce a visible 3x gain over 2x in 16/31 completed Germany images; the 3x repeat preserves all inputs/camera/ADC and 31 images. Final descriptors/frontiers are checked. Opt-in host roads now fill the missing uphill section, repeat21 current4K captures and preserve full input/camera/ADC timing. | Finish resource/occlusion/handover acceptance, decode the separate road path, then carry verified scene contracts to the other adapters. |
| World 2.5 | Integrated CLI host adapter now completes control/1x/2x/3x/repeat.3x changes10/30 current4K captures over2x and repeats all30 with identical camera/ADC timing. Eleven snapshot/frontier oracles pass. Disconnected distant ground remains. | Verify its road/ground path, material lifetime and occlusion while advancing USA/Off Road/Zeus adapters; no menu promotion yet. |
| USA 4.5 | Host pending/future scenery is integrated separately;2x adds13/16 current4K images over1x,3x adds three smaller changes. Original route/resources/defaults pass. | Improve3x performance (currently97–98%), clipping/material lifetime, foreground occlusion and handover; no promotion yet. |
| Off Road 1.63 | Host pending/future renderer is integrated separately.2x adds40/40 current4K images over1x;3x adds six further changes.40GL/ordered geometry repeat, original53.8MB resources and all7defaults pass; clean3x~100% speed. | Broaden El Paso/full-track coverage, clipping, material lifetime, foreground occlusion and handover. Preserve the stalled diagnostic repeat; no menu promotion yet. |
| Exotica 2.4 | Far-only extra geometry is occluded; earlier admission changes active depth bias/order and loses original geometry matches. | Trace register 0x15 provenance and isolate state/order effects; establish a Zeus static geometry/material adapter before claiming robust distance. |

Start with [World's host-scenery evidence](reviews/2026-09-08-world-host-scenery.md)
and the canonical `native/world_host_scenery.h`/`native/scenery_c31.h`. The existing
section capture originally verified only two angles and no flag-8 placement offsets.
The [September 9 milestone](reviews/2026-09-09-world-host-cost-and-sections.md) now
checks 8,222 placements, 46 section angles, 970 offsets and both initial material
lookups for every object. Special class handling and future resource residency
remain unverified. Do not discard the successful original-route
and resource equality to obtain more admitted scenery.

## Ordered implementation checklist

- [x] Split World host preparation, logging and GPU submission timings; allow
  expensive per-quad tracing to be disabled while retaining cheap scene counters.
  Measure uncaptured gameplay intervals at the actual 4K display size. Attribute
  new 16.127-second outlier to polygon logging; summary controls stay below 0.9 ms
  with identical geometry fingerprints and completed images. The older 120 ms
  cause and whole-game smoothness remain unproven.
- [x] Broaden section placement/yaw/offset and initial palette/texture evidence.
  Corrected full-drive probe verifies 16,444 initial writes and 410 later writes;
  preserve the first two probes' incomplete allocator coverage.
- [x] Verify final metadata overrides and reconstruct eligible packed future
  objects in PC-owned storage with bounded caches and checked ROM reads. All
  6,823 ordinary descriptors and 166 partial frontiers pass; 5,405 allocations fit
  this codec. Custom and road-chain classes stay excluded. See the
  [future-section milestone](reviews/2026-09-09-world-future-sections.md).
- [ ] Complete future GPU resource-lifetime and static-class coverage across tracks.
  Initial binding/descriptor equality alone does not establish these properties.
- [ ] Draw the future scenery at 3x, preserving original submissions and materials.
  Verify near/side clipping, transparent shadows, roads/sky, occlusion, cache
  invalidation and exactly-once handover as the original renderer takes over.
  **Implemented for World 2.4 packed scenery, acceptance incomplete:** 3x now
  visibly adds terrain/buildings over 2x and repeats at full speed; distant road
  gaps and other codecs prevent promoting it as the complete replacement.
- [ ] Carry the shared math, scene contract and verification harness to the other
  game/revision adapters above. If one decoder is blocked, make useful progress on
  another adapter or its independent acceptance rather than retuning unrelated FFB.
- [ ] Exercise all supported games with disabled/default controls, candidate
  self-replay and completed gameplay captures. Diagnose any World New York crash
  evidence available; request its attended recording when the maintainer returns.
- [ ] Consolidate menus only for replacements that pass the acceptance below.
  Preserve diagnostics through clearly separate developer controls as needed.
- [ ] Run appropriate local checks and cross-game regressions on the final native
  candidate; refresh exported patches and document exactly which candidate passed.
  Deploy with the Personal target only after acceptance and when no personal game
  is running. Otherwise leave Stream Deck on v0.5.0 and explain the remaining gap.

## Acceptance harness

Keep these outcomes separate; never convert a failure into a pass by dropping an
identity check or resizing/replacing original reference images:

1. Original route: inputs, camera poses and actual ADC values **and timestamps**.
2. Candidate repeatability: effective options, source/native identity, input events,
   native counters and completed 4K GL captures against the same candidate.
3. Rendering integrity: original geometry/order and texture/palette/VRAM resources,
   intended added scenery, correct foreground occlusion and no handover duplicate.
4. Visible distance benefit: time of first appearance for distant scenery, compared
   at matched poses with stock/2x/3x; dense samples around transitions. Additional
   admissions alone do not clear this check. Record the measured draw extent.
5. Presentation cost: separate preparation/logging/submission and capture overhead;
   report percentiles/outliers and whether a long trace actually reproduces them.
6. Cross-game baseline: the existing seven default drives, telemetry/force policy,
   fresh configuration and menu option composition as relevant. Physical force
   remains disabled; these are not tactile observations.

Use available human recordings first. Short synthetic drives are useful controls,
but cannot establish whole-track quality. The morning handoff should identify
specific useful new drives, particularly World New York, a longer Off Road route
and an open Exotica course, without blocking independent overnight work.

## Conditional menu cleanup

The intended player experience is one clear distance control per applicable game,
with common Off/2x/3x semantics only where each mode is implemented and validated.
Do not expose a nominal 3x mode that changes no earlier visible scenery.

Inventory current global far, lookahead, selective scenery and margin controls.
For each proposed removal, record the replacement and an A/B demonstration that
its useful behavior is covered. Keep complementary widescreen, seam and shadow
corrections unless evidence establishes redundancy. Preserve saved preferences
through an explicit migration and keep old recording options interpretable.
If comparable cross-game behavior remains incomplete, keep the existing menu and
document the gaps instead of presenting a cosmetic unification as completion.

## Continuing checkpoints

Commit and push completed milestones separately. Keep the next concrete task and
its evidence in the handoff so scheduled continuations can resume useful work.
Continue until the parity objective succeeds, newer steering changes the scope,
or a concrete blocker requires maintainer input. Report implemented versus
diagnostic-only versus deployed behavior, per-game evidence and retained failures.
Do not create a new public release from this authorization.
