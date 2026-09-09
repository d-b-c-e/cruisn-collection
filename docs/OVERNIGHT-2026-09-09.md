# Overnight queue: consistent 3x scenery — September 9, 2026

The maintainer requests concentration on robust 3x draw distance equally across
USA, World, Off Road and Exotica, followed by removal of confusing or redundant
graphical experiments **if the replacement succeeds**. Work is authorized through
the morning checkpoint at 08:00 America/Chicago on September 9. The existing
`cruisn-overnight-cheats-and-distance` heartbeat is reactivated with this scope and
the display name **Cruisn overnight 3x scenery**. The September 8 queue is historical.

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
| World 2.4 | Host pending scenery preserves full Germany inputs/camera/ADC and guest resources; 2x visibly helps, 3x adds a brief mountain gain. Future sections are not decoded yet. | Finish host-owned future-section placement/material binding, broaden yaw/offset checks, split preparation/logging/submission cost, then test occlusion and handover. |
| World 2.5 | Guest far/lookahead trials repeat against themselves but diverge from the original route; no extra 3x visibility established. | Verify its section/object/material layout before adapting the host path; keep its own scene oracle and full replay. |
| USA 4.5 | Far-only gains are tiny; guest residency changes route. | Verify static section/admission and material layouts for a host adapter that leaves guest activation unchanged. |
| Off Road 1.25 | Coherent far/clip/reciprocal extension is implemented; modest sampled gain, no extra 3x pixels, strict timing/one-quad differences remain. | Identify the remaining scenery residency or submission limit and map eligible static data to host drawing; retain the stock timing/geometry failures. |
| Exotica 2.4 | Far-only extra geometry is occluded; earlier admission changes active depth bias/order and loses original geometry matches. | Trace register 0x15 provenance and isolate state/order effects; establish a Zeus static geometry/material adapter before claiming robust distance. |

Start with [World's host-scenery evidence](reviews/2026-09-08-world-host-scenery.md)
and the canonical `native/world_host_scenery.h`/`native/scenery_c31.h`. The existing
section capture verified only two angles and no flag-8 placement offsets. Broaden
that evidence before extrapolating. Do not discard the successful original-route
and resource equality to obtain more admitted scenery.

## Ordered implementation checklist

- [ ] Split World host preparation, logging and GPU submission timings; allow
  expensive per-quad tracing to be disabled while retaining cheap scene counters.
  Measure uncaptured gameplay intervals at the actual 4K display size. Attribute
  the prior 120 ms outlier before claiming smooth performance.
- [ ] Broaden section placement/yaw/offset and palette/texture binding evidence.
  Reconstruct eligible future static objects in PC-owned storage with bounded
  caches and checked ROM reads, without invoking guest object initialization.
- [ ] Draw the future scenery at 3x, preserving original submissions and materials.
  Verify near/side clipping, transparent shadows, roads/sky, occlusion, cache
  invalidation and exactly-once handover as the original renderer takes over.
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

## Morning handoff

At or after 08:00 local, stop starting long tests, safely finish/checkpoint the
current operation, commit/push completed work, record findings and pause the
heartbeat. Report implemented versus diagnostic-only versus deployed behavior,
per-game evidence, retained failures, menu removals/migrations and precise remaining
work. Do not create a new public release from this overnight authorization.
