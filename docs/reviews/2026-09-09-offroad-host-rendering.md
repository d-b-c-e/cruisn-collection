# Off Road host rendering — September 9, 2026

The first integrated Off Road host renderer is built separately as native
`4a507c5f3724704b000a52a33a07756cf015202d`, SHA256
`c88ae4f260d663734bf9f582a90ca4488cfac154c90be9290bbb08e20b368d8d`.
It uses the independently verified Off Road model, transform and future-section
helpers. The original game continues to own simulation, allocations and hardware
DMA. This is an explicitly selected diagnostic candidate, not a deployed feature.

## Controls and boundaries

`harness/replay.py` accepts `--offroad-host-scenery observe|draw|off`, bounded
`--offroad-host-first`/`--offroad-host-last`, `--offroad-host-distance 1|2|3`,
`--offroad-host-source pending|future`, summary/detailed logging and the existing
auxiliary-layer choices. Absent options install nothing and preserve old
recordings. Explicit settings are frozen into derived replay manifests. Combining
host drawing with the guest distance experiment is rejected.

The scene hook reads111F4 atPC1BF9, after the background tiles and before ordinary
objects. Main RAM is read directly; bounded ROM reads disable side effects.
Every callback asserts zero change in emulated CPU cycles. Game revision,
frontier, queue/busy state, material bounds, model bounds and projection limits
are checked. Immutable section/model caches refresh live material bindings;
palette colors are never cached. No original hardware DMA is added or modified.

## Current evidence

The full6000-input observation pass completes1978 scene callbacks, including
52 pretrack and7 partial-frontier states. It preserves4191 camera samples and
16764 actual ADC reads/timestamps, matching the original Off Road recording.
Five independent Python snapshots at4000/4500/5000/5500/5900 match7402 ordered
host quads plus admission, transform, LOD, projection, material and radial-order
decisions. Each matches the exact native frame, emulated time and page.
Native frames are one lower than these Lua snapshot frame labels.

The control run completes40 GL captures at3824x2073, frames4000..5950 every50.
Its three overlapping frames equal the prior cf58 candidate. The initial attempt
to compare a40-frame set with a3-frame set correctly failed the strict capture
reader; the final overlap check validates both complete sets before selecting
those three frames. It does not silently drop missing captures.

Future1x changes29/40 images over control. Future2x changes40/40 over1x and shows
additional mountains and terrain ahead, including210925 changed pixels at4600.
Three-times adds six more changed images over2x, at4000..4250;4250 changes25409
pixels. All preserve the complete input sequence and camera/ADC timing. The first
3x callback p99/max is4.303/7.488ms. Extra pixels are not a full visual acceptance
verdict. Repeat pixels, original resources and seven-default acceptance are being
checked separately.

The first repeat completed but encountered11.34s and5.81s frame intervals while
a broad disk search was also running. Its largest host callback was6.30ms, so
those long delays were outside this callback. A further repeat without competing
disk search completes in103.55s host time, like the initial3x run. The stalled
run is retained; this correlation alone is not a complete root-cause diagnosis.

Material bounds reject272979 object candidates across476 early scenes2354..3609.
The five gameplay snapshots have no material rejection. This is a conservative
exclusion, not proof that every future material is available throughout menus,
loading and gameplay. The bounded source/cache/helper implementation and earlier
live material investigation are described in
[the foundation review](2026-09-09-offroad-host-foundation.md).

This recording covers the beginning of El Paso and includes a long period near
one hillside with the car nearly stopped. It is useful for distant geometry and
reproducibility, but is not a complete-track, tunnel, finish-line or broad handover
acceptance drive. Existing ground/geometry gaps remain visible in the control.

## Build and remaining gates

The146-patch export reconstructs native tree
`06563dddcaa8c48572d05792c284df88e3e49894` exactly. The frozen candidate is
`build/candidates/4a507c5f372/vunit.exe`. Raw diagnostic evidence is local under
`results/diagnostics/offroad-host-20260909`; no raw game resources are published.

Pending: repeat pixel comparison, original DMA/VRAM/material equality,
4K timing analysis, all-seven default regression renewal and final local checks.
Broader clipping, foreground occlusion, material lifetime and handover remain
open even if those bounded checks pass. USA performance, World2.5 roads and the
Zeus adapter remain separate unfinished work.

Personal Stream Deck remains v0.5.0/SHA87d04de4. No release, deployment, hosted
workflow, physical force, World force tuning or menu removal occurred. Continue
directly into useful implementation and validation; the one-minute heartbeat is
recovery only.
