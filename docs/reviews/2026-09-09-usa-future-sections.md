# USA future sections and material ownership — September 9, 2026

USA's next loading boundary is now decoded and independently checked. Source
commit9058093 adds a standalone native section decoder, Python reference and
bounded Lua probes. It does **not** yet connect future descriptors to MAME's
renderer. The previously integrated pending adapter remains the only USA host
drawing path in candidate4e565. No release, deployment or default change occurred.

The maintainer asked why work was waiting30 minutes. Active work now continues
directly between implementation and verification steps. The existing heartbeat
was also shortened to a **one-minute recovery interval**, with no cutoff, so an
ended turn does not intentionally wait for the old half-hour cadence. It remains
the same task and automation, with quiet non-actionable checks.

## What is now verified

USA's section header has six base words, an optional second list, optional four
placement operands and an optional third list. The third list clears the offset
flag and may use the offset heading. Treating it as World's fixed three-list
layout would produce wrong placement. Allocation also has distinct palette,
flags, road-tag and object-field rules.

The final-allocation probe captures the ordinary descriptor after class-specific
processing, before the next allocation or list-stage transition. All1,700 ordinary
allocations pass position, heading, matrix, cached depth, active/pending membership,
ready/final flags and kind checks. This includes1,504 direct palette bindings,
20 sections,10 headings and413 offset placements. Twenty-four custom-handler
allocations are recorded but excluded from the descriptor assertion.

The independent ROM-list reader matches all1,724 captured source definitions,
stages, effective flags and headings. Five snapshots contain26,992 upcoming
definitions. The standalone native decoder matches Python for26,807 ordinary
descriptors;185 custom cases remain explicitly unsupported. This comparison
checks all34 constructed words, including deliberate zero values for fields the
host does not initialize. It is not an assertion that every guest physics field
should be zero.

Across those snapshots,3,525 predicted descriptors match later actual allocations,
including3,104 already-bound direct palette mappings. The last snapshot4901 has
no subsequent allocations within this recording and contributes **no** later
allocation coverage. Its descriptor comparison is Python/native only.

The current scene samples include1,770 matching loader frontiers. E4A5 points at
the next section; E49D catches up after the current section finishes. The decoder
checks their relationship against the track start and section number. A current
partial section is deliberately excluded; no guest AR5 cursor is guessed. No
partial state occurred in these1,770 scenes. Synthetic tests cover that boundary,
but live partial-section coverage remains open.

## Textures and live palettes

All five8MB texture-atlas snapshots are byte-identical. Future supported models
use74–80 bounded UV rectangles in these samples. Every referenced palette has a
nonzero binding, a valid slot/refcount and the matching reverse owner record.
There are no unbound ordinary future references in these particular snapshots.

The first material checker required every palette bank to stay byte-identical
and failed. That failure is retained. Bank0x4300 changes only color entries251–255;
its palette index46, binding and reverse owner remain identical throughout. The
values cycle among black and colored entries, consistent with color animation.
The material's identity is established; the specific in-game animation has not
been visually identified.

The corrected contract checks slot ownership and reports color changes, allowing
the renderer to use the game's **live palette**. It must not cache those colors
as immutable future-section data. A separate `--require-static` check still
rejects this material. The native decoder now rejects mismatched reverse owners
and zero reference counts instead of trusting a nonzero pointer alone.

This establishes sampled continuity, not full material lifetime. Queued palette
uploads, changes between samples and new tracks still need coverage. No
per-model or per-palette allowlist was introduced.

## Validation and next implementation

Three new5012-input diagnostic replays (final allocations, future sections and
future materials) preserve3,211 camera records and9,633 actualADC values/timestamps.
Allthree late3824x2073 GL images per replay match the existing control. Raw
memory/resource capture costs are diagnostic overhead and are not host-rendering
performance measurements.

Local checks pass223 Python tests with no skips,19 native helpers,10,081 C31/137 yaw
vectors and32 GPU checks over53 commands. All339 source files match identity
`db1c5e42696f8ef8891ca6bd52baba167a649a52fdade9f2c0d3c8c32bcd67e3`.
The final native oracle uses the analyzer from that exact check run.

Native candidate4e565/SHA248aef7c and its142-patch export are unchanged. Its previous
seven-default acceptance remains the last full game regression gate; this
standalone decoder milestone does not renew that gate. Stream Deck remains
v0.5.0/SHA87d04de4. No physical force, World force tuning or hosted build occurred.

Continue with a bounded cached USA future source in the host renderer, exposing
an explicit CLI choice that preserves absent/old recording behavior. Refresh
palette ownership and upload readiness each scene. Preserve direct RAM reads,
zero guest CPU-cycle changes, original DMA/resources and exact input timing.
Then compare1x/2x/3x and repeats with visible4K scenery, sky/occlusion, host-to-guest
handover and callback-cost checks. Renew the seven defaults after integration.
World2.5 roads/ground and Off Road/Zeus adapters remain separate active follow-ups.

Raw operands stay local under `results/diagnostics/usa-host-scenes-20260909`.
[Public proof](../../results/proof/2026-09-09-usa-future-sections/README.md)
recomputes declared route/pixel/frontier/scalar evidence and distinguishes it
from raw-descriptor/material/native/GPU receipts. Future drawing and cross-game
3x feature parity remain unfinished.
