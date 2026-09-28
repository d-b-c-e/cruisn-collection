# New York frame-3600 overlap source check — September 28

The World 2.4 New York opt-in active non-road margin candidate repaired nearly
all of the measured right black wedge at completed frame 3600, but it also
changed 25,631 pixels that already had host ownership. This check identifies
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
of 24,759 newly owned gap pixels and 25,631 previously host-owned pixels.
Debug quad IDs assign the changed pixels to 180 visible new packets across
39 active objects. The largest object contributes 7,161 pixels; no single
quad or track ID is responsible for the whole wall/shoulder extension. The
original-only indexed planes and complete 4:3 indexed center stay exact.
The remaining ten unowned pixels form a short diagonal at fine coordinates
`(2615,695)` through `(2607,699)`. They are a residual edge, not grounds for
claiming 100% repair.

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
`active-nonroads-3600-overlap-v5.json`. Earlier overlap v1–v4 reports are
retained as evolving checks; v5 additionally verifies policy-2 packet identity
and exact native scene/live order. No native code, binary, release export or
personal installation changed in this check.
