# World future sections: visible 3x scenery, September 9

World 2.4 now has a CLI-only renderer for scenery in upcoming track sections.
Unlike the older guest lookahead experiments, it constructs the extra objects in
PC-owned storage and leaves the game’s loader, simulation, inputs and hardware
draw stream alone. On the original Germany drive, 3x produces additional visible
mountains, trees and a building compared with 2x. This is a useful implementation
milestone, **not yet a first-class distance setting or a cross-game result**.

**Visual acceptance currently fails:** dense tunnel testing reveals a new thin
green line across the road at frame 4408. The remaining distant road/ground gaps
are also conspicuous. Road-chain objects and
custom allocation classes are deliberately outside this first codec. Foreground
occlusion, texture lifetime and handover need broader validation. No existing
experiment has been removed, no personal preferences changed, and Stream Deck
still uses the accepted v0.5.0 native binary. There is no new release.

## What changed

`native/world_future_sections.h` reads a bounded window of up to 64 upcoming
sections, including all three object lists and the optional placement offset.
It uses the actual loader stage and next-definition cursor to exclude objects
already allocated in the current partial section. The section end marker stops
decoding. Immutable placements are cached; palette and texture bindings are read
again for each scene. Old sections are discarded as the frontier advances.

The existing pending-object renderer accepts these additional descriptors without
writing fake objects into guest RAM. Both paths share checked C31 arithmetic,
projection, material decoding and far-to-near submission. Exact revision/code,
pointer, list-length, resource-index and frame-bound guards remain mandatory.
Unsupported classes are determined by the game’s representation; there is no
model-name, model-address or level allowlist.

The explicit diagnostic invocation adds `--world-host-source future` to the
existing `--world-host-scenery draw` controls, with `--world-host-far 160000` or
`240000`, bounded first/last frames and `--world-host-log summary`. The pending
source remains the default for existing recordings and commands. Live GL is
required for drawing. Guest far/lookahead experiments cannot be combined with it.
This is still World **2.4 only**; 2.5 is being mapped independently.

## Independent reconstruction

The allocation probe now observes the final boundary after special handlers.
All 8,222 Germany allocations are retained. For 6,823 ordinary allocations, the
independent Python reconstruction exactly matches fields 1–17, heading and
section tag. Of these, 5,405 fit the current packed geometry path. Class A has
67 custom allocations; class B has 1,332 road-chain allocations and changes flags,
metadata, links and other fields after the earlier “ready” boundary.

The frontier comparison covers all 166 captured partial-section states: 52 in
list stage 1 and 114 in stage 2. Predicted remaining definition identities equal
the independently observed later allocations. The frame callback occurs before
allocations stamped with that same frame, which matters at the boundary.

At frames 3000, 4500, 6000 and 8500, native and Python future decoders agree on
3,631, 3,962, 3,119 and 966 eligible descriptors respectively. There are no
already-allocated entries or mismatches against later allocations. Independent
Python projection matches all future quads at 80k, 160k and 240k in these four
snapshots. The old pending oracle still reproduces 13,215 quads in 61 scenes.
The shared native math check includes 10,081 C31 vectors and 137 captured yaw
vectors. These checks do not establish every material’s GPU lifetime or every
later animation path.

## Full-drive visibility and repeatability

All five native runs complete the original Germany recording: 9,269 input frames,
154 native snapshots and identical camera and actual ADC values **and timestamps**.
The new native with the future feature disabled also matches the preceding
candidate’s pending geometry fingerprints and all 31 completed 4K captures.

| Mode | Host quads over 3,731 scenes | Host callback p99 / maximum | Recorded interval speed |
|---|---:|---:|---:|
| Existing pending 3x | 663,078 | 0.310 / 0.523 ms | 99.787% |
| Future sections 2x | 4,639,772 | 3.891 / 6.010 ms | 100.005% |
| Future sections 3x | 8,774,663 | 5.709 / 6.315 ms | 100.005% |
| Future sections 3x repeat | 8,774,663 | 5.710 / 6.608 ms | 100.005% |

The 3x repeat matches all ordered scenery fingerprints, inputs, camera/ADC traces
and 31 completed 3824×2073 client images on the 3840×2160 display. An additional
headless observe run produces the same 3x geometry without submitting it to GL.
Its unthrottled speed is not a 4K presentation benchmark. Timings above measure
CPU callbacks and emulation progress, not completed GPU latency or absence of
all stutter.

Future 2x changes 24 of 31 images compared with the older pending 3x control.
At frame 2880, it fills a distant hillside that was previously sky. More
significantly, future **3x versus future 2x changes 16 of 31 images**. At frame
6720, 28,006 changed pixels show an additional wooded mountain and a half-timber
building beyond the foreground trees. These are completed images at matched
camera poses, not just admission counts. The archive includes both comparisons
at their original resolution.

Both 2x and 3x still show a large missing distant road/ground area in the frame
6720 view. The same short drive cannot certify all occlusion or handover behavior,
and sparse captures do not measure a scenery object’s precise first-appearance
time.

The dense frame 4400–4500 comparison completes 51 images per mode; 43 differ.
Both runs preserve the full 82,601,136-byte original hardware-quad stream, VRAM,
texture RAM, palette RAM and capture metadata byte-for-byte. At frame 4500, all
1,354 original quads and their order match, including previous-page history.
That integrity PASS is separate from the visible failure: at 4408, 3,079 changed
pixels include a new green horizontal line across the foreground tunnel road.
The archive retains both images. The exact primitive/renderer-stage cause remains
unattributed; do not describe correct foreground occlusion as established.

Full-drive counters also reveal 416 unbound descriptors in each of 118 late scenes,
frames 9025–9259. They are excluded rather than assigned guessed materials.
The four earlier snapshot oracles had none, so their resource results cannot be
generalized to late scene/asset transitions. This is another explicit lifecycle
case for the next adapter work.

## Build and acceptance status

Candidate native `de1d6333cd9918305d9b1d300c357d2dca5a3abf` is built separately:

```text
SHA256 0f947fd500385cbab10bd68a857703f2659d7dcdfc1b8334bcae52d5cdc4b0d1
```

Its 136-patch export reconstructs tree
`ef9e2f9741e766211669ede31874a7178489769f` from the documented base. The first build
attempt failed because the MSYS environment was not initialized; its log is
retained. The corrected local build passed. No hosted workflow was used.

Final local checks pass 202 Python tests without skips, 15 native helper tests,
24 GPU fixtures and all 42 commands. The 308-file source identity is
`b317fd06db0015eb3d2ed322a81a1858e64fe4775121b1d4d83c4b15fe6b94fb`.
All seven default regressions pass at that same source identity and native hash,
including actual UDP versus memory, four force-policy/polarity checks and 21
completed Exotica GL images. The dense hardware-resource comparison passes as
described above; visual acceptance remains a retained failure. The
[ROM-free archive](../../results/proof/2026-09-09-world-future-sections/README.md)
recomputes route/timing/fingerprints, selected pixels, scalar descriptors/frontiers,
World 2.5 membership and telemetry/force checks. Full geometry/resources, placement,
remaining GL and build results are hash-bound receipts.

Personal native remains SHA256
`87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8`.
Published v0.5.0 and v0.4.0 tags/ZIPs are unchanged. Automated physical FFB is zero;
World force tuning remains deferred.

## Next adapters and road work

Read-only snapshots for World 2.5, USA, Off Road and Exotica all replay their
requested scopes successfully; Exotica also matches its 21 original GL images.
The first World 2.5 snapshot falls outside active track setup, so its zero frontier
is not evidence that no loader exists. Two later full 6000-frame read-only captures
complete and retain identical camera/ADC traces. The original pending-only
descriptor reference fails 390 allocation flags. A new capture of the real mode
word and activation limit predicts all 2,686 ordinary allocations correctly:
2,296 pending and 390 directly active. Other reconstructed fields/materials agree;
32 custom and 596 road-chain allocations remain excluded. Preserve the original
failure; do not mask the membership bits without checking their producer.

World 2.5 has the same broad section format and C31 math, but not one uniform
address relocation: its palette/texture tables, allocator, pending-list pointers,
loader and trig constants move by different amounts. Verify actual allocations
and resources before adapting the renderer. USA and Off Road need their own
submission/material layouts; Zeus additionally requires render-state ownership
and depth/order work.

World’s road path uses unpaired vertices and a separate distant polygon/material
template selected from metadata. The new read-only frame 4400–4500 probe completes
the 4502-frame prefix and independently reproduces 2,308 camera transforms,
matrices and projected vertex buffers, including 1,802 distant-template calls.
All 2,140 unclipped calls reproduce their original ordered DMA words; 168 clipped
calls remain excluded from that polygon check. No host road drawing is implemented
yet. Simply removing the packed decoder’s exclusion would misinterpret the distant
templates, which reside in checked main RAM rather than the ordinary ROM model
layout. Carry this verified representation into a bounded host road codec next.

The overnight queue remains active through 08:00 local. Keep each completed
adapter or correction in a separate commit. Consolidate the player-facing options
only after useful replacements pass the shared acceptance criteria.
