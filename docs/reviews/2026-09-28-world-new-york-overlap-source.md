# New York frame-3600 overlap source check — September 28

The World 2.4 New York opt-in active non-road margin candidate repaired nearly
all of the measured right black wedge at completed frame 3600, but it also
changed 25,631 pixels that the game had already drawn. This check identifies
which source-time objects and native packets produced that overlap. It does
not promote the candidate to the personal build or release.

The existing 3,602-input control and candidate replays were retained. A new
bounded read-only Lua source tap at preparation frame 3596 ran on the same
frozen `03123d5b272` control binary, physical 2560×1440 primary display and
literal FFB0. Its recorded inputs, native images, completed frame 3600 and all
eight original/extended indexed mirror planes are byte-identical to the saved
control. The tap also captured program RAM, C31 internal RAM, texture and
palette at the actual scene read. The source-time RAM and C31 hashes differ
from the end-of-frame RAM dump, confirming why the latter is a poor camera
oracle. Source texture/palette are byte-identical to the completed capture.

The first offline active-object projection report is preserved as **FAIL**:
the previous reciprocal-table capture window began at index -80, while two
near-plane objects read -95 and -87. Extending only the read-only table window
to -128 resolves those capture errors. The second report passes its baseline:
1,029 of 1,874 projected quads match original DMA exactly, with zero projection
errors and zero accidental host-packet matches. This is a broad baseline, not
exact reconstruction of every active object. Its one source-qualified absent
quad in the selected right ROI is indeed among the new native packets, but
its isolated coverage touches **none** of the changed pixels. Broad projected
boxes alone would have misattributed the repair.

The independent standalone native helper was then run cold and warm on the
source-time RAM/C31/ROM. Its control and opt-in scenes contain 2,452 and
3,263 quads. Every 16-word quad matches the corresponding *live* fade packet
in order on both paths: zero count or word mismatches. The prior 2,452 packets
remain an exact ordered subsequence of the opt-in run. The 811 new policy-2
packets all belong to current active `0x1000` objects. Thus the measured
overlap is from a current-list margin policy, not an untracked future-section
addition or a changed original DMA stream.

An isolated GPU raster of those exact 811 new packets using the saved
source-time texture RAM covers **all 50,390 changed indexed pixels**, with the
same index value as the live candidate at every changed pixel. These consist
of 24,759 newly owned gap pixels and 25,631 previously game-owned pixels.
Debug quad IDs assign the changed pixels to 180 visible new packets across
39 active objects. The largest object contributes 7,161 pixels; no single
quad or track ID is responsible for the whole wall/shoulder extension. The
original-only indexed planes and complete 4:3 indexed center stay exact.
The remaining ten unowned pixels form a short diagonal at fine coordinates
`(2615,695)` through `(2607,699)`. They are a residual edge, not grounds for
claiming 100% repair.

**September 28 ownership correction:** the earlier v1–v5 report treated every
nonzero control mask as host ownership. The shader's tag bit 2 distinguishes
host geometry: control tag `1` is an ordinary game pixel, while the new
candidate's tag `5` is host geometry. Source-hashed v8 reanalysis of the same
saved planes finds control tags `0` for 24,759 changed pixels and `1` for
25,631; **zero** changed pixels were previously host-owned. All 25,631 tag-1
pixels have exactly the same index and tag in the original-only mirror. An
isolated raster of all 1,237 current original DMA quads also reproduces every
one of those indices and attributes **all 25,631 to original quad 3**, a wide
top-of-view strip at native `x=502..758, y=-17..208`. Its shape and its place
among five contiguous first commands identify it as the game's backdrop
strip in this scene. The candidate replaces that backdrop with additional
scenery, rather than overwriting existing road or prior host geometry here.
This narrows this frame's apparent occlusion risk, but does not prove the same
for another scene or course. The original-only planes remain intact. The
v1–v7 raw reports remain locally preserved as evolving checks, including the
ownership error in v1–v5.

This is an **attribution and material check of one completed scene**. The
isolated raster does not reproduce the full ordered mixing of old host,
original geometry, subsequent palette changes or temporal appearance. The
saved completed image looks coherent, but a denser matched sequence around
frame 3600 is still needed to screen popping, overlays and changing seams.
The New York 6000 result and Germany/Hawaii sparse cross-course checks remain
separate evidence; none establishes release parity or solves distant pop-in.

Large local evidence is under
`results/diagnostics/world-new-york-20260927-live-1`:
`source-3596-run/report.json`, raw failed
`source-3596-active-projection-v1.json`, corrected v2, native scene text
`native-source-3596-{control,nonroads}.txt`, and the final source-hashed
`active-nonroads-3600-overlap-v8.json`. Earlier overlap v1–v7 reports are
retained as evolving checks; v5 additionally verifies policy-2 packet identity
and exact native scene/live order, v7 corrects mask ownership, and v8
attributes game-owned changes to current original DMA. No native code, binary, release export or
personal installation changed in this check.
