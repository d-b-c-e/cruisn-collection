# World: active road coverage in widescreen margins

The Germany black wedge near game elapsed 1:37 has a specific source: an
existing active road object rejected by the game's approximate horizontal
bounding-sphere test. Increasing the far plane cannot fix this nearby object.
The new recovery passes the targeted live Germany comparison. It remains a
diagnostic experiment; broader-track and release acceptance are still open.

## Evidence and the framebuffer timing correction

One recorded control runs through input7342 with physical FFB disabled. Camera
samples5542 and actual ADC reads16626 match the earlier Germany control exactly.
Two scene-entry snapshots at native7337/7339 reproduce all2521/2479 host quads
and their ordered fingerprints. Original draw provenance matches1971 native DMA
commands. The ordinary framebuffer reconstruction matches all204800 pixels.

That ordinary comparison concerns the **draw page**, not necessarily the page
on the monitor. At completed7340, the monitor shows page0's scene7337; the normal
offline preview selects the later page1 draw. Its elapsed1:36.81 therefore cannot
diagnose the visible elapsed1:36.78 wedge. The matched live7340 screenshot is
pixel-identical to the earlier fade trial. Original-only GPU mirror buffers show
the same wedge, excluding the new far scenery as its cause.

Selecting actual scene7337 reproduces the visible geometry. Its original-only
offline index buffer differs from the live original mirror by505 pixels
(history/overlay/fill differences remain); it is not claimed byte-identical.
The sampled2446 black wedge pixels have no current original polygon coverage.

The road's center depth is approximately2827 and its radius2461. The original
screen-space sphere ends at x=-131.36, beyond even the expanded left edge -86.
Its actual nearest-right vertex reaches x=-60.65. All18 vertices have positive
depth1915..3733. An independently reconstructed road uses the existing vertices,
materials and UVs and covers the entire sampled wedge.

In the actual original painter order, restoring this road after the five
background commands and before ordinary geometry changes2415 RGB pixels, covers
all2446 target pixels, adds no black pixels and leaves the native4:3 region
unchanged. The image was inspected. This is an offline finding, not yet a live
or temporal acceptance claim.

## Gated implementation

`--world-host-active-roads margins` requires an explicit candidate, future draw,
stock road detail, both auxiliary layers and physical FFB0. It is not exposed
as a shipping setting. Both World2.4 and2.5 layouts are explicit and guarded.

The collector walks the actual current render lists on each scene. It bounds
all pointers and traversal, detects cycles and duplicate membership, preserves
the real active flags and does not cache allocation membership. Only ordinary
active roads with qualified material values are eligible. Unsupported objects
receive no permission. No guest state, allocation or hardware DMA is changed.

The decoder considers roads rejected by the original horizontal sphere test,
requires every actual vertex to remain within the accepted positive-depth
interval, and retains only polygons wholly outside the native4:3 region. It
does not stretch textures, generate terrain, change the near plane or make
clipped polygons safe by clamping them. Original geometry draws afterwards.

Germany7337 produces46 extra polygons from four roads, independently exact in
Python and C++. Only one road's10 polygons have sampled visible coverage; the
other roads are outside that view. All2521 previous host polygons stay exact.
The adjacent7339 scene retains2479 originals and adds46; saved World2.5 Hawaii5900
retains5922 and adds zero. Two native tests and13 focused Python tests pass.

The first local qualifier incorrectly expected only the visible road, despite
its full native/reference equality passing. That failed expectation is retained;
the corrected qualifier explicitly accounts for all46 polygons.

## Live transition guard correction

The first candidate `2e0466f84e0` stopped at native1884. A bounded baseline capture
of that exact scene proves valid topology:472 objects in one render list and a
separate effect object with flags0x3020. The initial collector wrongly required
every traversed object to have ordinary-active flags before excluding non-roads.

The successor excludes non-road/non-active objects without granting permission;
malformed topology and code mismatches still reject the collection. A test uses
the captured effect flags. The initial failed run is retained.

## Live successor result

Frozen native `62f2d62a42f` passes7342 recorded inputs, all original native-image
checks,5542 camera samples and16626 actual ADC reads. Both scene-entry RAM/FAST,
texture/palette resources and all original command-provenance bytes are exactly
the control. The entire original DMA journal and captured framebuffer/material
files at7340 also match exactly. Live host scenes2567/2525 quads reproduce the
canonical saved-scene fingerprints, including the46 added margin polygons.

All five completed3824x2073 CRT images (frames7336..7340 on the4K monitor) change
only at the left margin. The counts are21093,10604,10604,3152,3152 RGB pixels;
none becomes newly black. The fixed interior is exact. The final image was
inspected: the black wedge is gone and the existing road texture continues to
the edge. This demonstrates a useful repair in the sampled transition, not
elimination of every black margin or pop-in across World tracks.

The build is separately frozen with SHA256
`4c714cb027359a15985edaad07d85197fa9074e31362a8a38295de57bb1cc4e3`.
The229-patch export reconstructs native tree
`0bf1885e46bb7b9e4700e41d39db060ca6f0a9bc`.

Local evidence lives under `results/diagnostics/world25-roads-20260914/`:
`germany-road-resources`, `germany-road-qualified`, `germany-active-roads` (initial
guard failure), `germany-active-roads-v2`, `germany-active-roads-v2-qualified.json`,
and `world-active-membership-control`. Raw game resources remain
local. Personal/Stream Deck installation and publicv0.5.0 remain unchanged.
