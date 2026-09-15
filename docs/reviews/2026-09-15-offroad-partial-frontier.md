# Off-Road partial-frontier recovery: geometry restored, no visible gain in this view

The optional recovery candidate restores scenery lost during a conservative
one-scene loader guard. It preserves the original game state and passes the
targeted replay, but **all 11 completed screenshots match the control**. The
town scene does not demonstrate a visible improvement. Keep this diagnostic
gated; do not promote it as a fix for observed pop-in or black textures.

## What the saved drive exposed

The existing full El Paso trace contains 52 partial frontiers with another
section ahead. At 14 of them, ordinary sources in the excluded section are not
allocated until a later recorded frame. At other transitions, allocation timing
is earlier or within the same frame and does not establish current membership.
A blanket removal of the guard would therefore lack an ownership proof.

At native frame 5044 (replay frame 5045), the host submits 657 polygons between
neighboring scenes with 906 and 903. A new bounded capture saves actual RAM,
textures and palettes at 5042, 5044 and 5046. The partial scene has 51 ordinary
section-28 sources absent from the entire allocated object pool. Retaining them
adds 49 decoded objects and 235 polygons, bringing the scene to 892. All existing
ordered objects, geometry and materials remain exact; both neighbors are unchanged.

The initial isolated host render changes 14,458 pixels in a distant-town strip.
This justified the native comparison, but did not establish visibility through
the original foreground. Inspection of the completed control shows substantial
foreground buildings in that area.

## Implementation and limits

`offroad_partial_sections.h` checks the full bounded free list and collects the
verified section/ordinal tags of every allocated pool slot. Any matching tag
blocks recovery, regardless of its mutable fields. It adds only supported
ordinary sources from the uncertain next section. Existing material readiness,
near/far, projection and ordering guards continue to apply. Invalid lists or
frontiers fail before altering the result.

Membership is checked after cached immutable source collection on every affected
scene. It is never cached across allocations. The helper requires the qualified
ordinary scene boundary, outside an allocation. Its standalone tests exercise
allocation changes with the same frontier, tag exclusion, malformed free lists,
duplicate recovery, unsupported classes and settled/end-of-track behavior.

The scene analyzer and independent Python implementation reproduce both cold and
warm passes at all three saved snapshots, with recovery off/on. The native
runtime option is `--offroad-host-partial recover`; it requires an explicit
candidate, Off-Road 1.63, 3× future drawing and physical FFB disabled. The absent
option preserves the old behavior. Five option tests and two scene tests pass.

## Completed native comparison

Both control and candidate preserve all 5,060 recorded inputs and original native
images, 3,257 camera samples and 13,028 actual ADC samples/times. The original DMA
journal, captured framebuffer, texture RAM and palette RAM are byte-identical.
All three scene resource snapshots, including RAM and exact callback metadata,
also match. The native frame-5044 count and fingerprint match the independently
reconstructed 892-polygon proposal. All changed scene rows occur at partial
frontiers; 22 recovery receipts occur in this prefix.

All 11 completed CRT images at 5040–5050 are identical, at 3824×2073 on the current
3840×2160 monitor. The comparison records integrity PASS and visible-benefit FAIL.
No additional replay of this same window is justified. Other partial transitions
may have different foreground coverage; that remains untested.

Native `a035f824e3be8f111a0f117cfe285be3b406ad15` is frozen separately, SHA256
`35a135dff5544b9de0abae2864235dff554e824f27fb9fe237319dc8307aab33`.
The 227-patch export reconstructs `be17d6fdf3ec669831c28b9be67e766549c7dfcf`.
This also links the previously qualified optional Off-Road depth helpers, with
depth retention disabled in the live scene path. No launcher deployment, release,
hosted CI or physical FFB occurred. Personal87d/public v0.5.0 are unchanged.

Local evidence under `results/diagnostics/world25-roads-20260914/`:
`offroad-partial-allocation-audit.json`, `offroad-partial-resources`,
`offroad-partial-proposal`, `offroad-partial-qualified`, `offroad-partial-native`,
`offroad-partial-recovered`, `offroad-partial-live-qualified.json` and
`offroad-partial-native-export.json`. Raw game data remain local.
