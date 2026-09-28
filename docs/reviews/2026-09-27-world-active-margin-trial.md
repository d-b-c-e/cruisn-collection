# World active non-road margin trial — September 27

The attended World 2.4 New York drive supplied two distinct, source-joined black
margin gaps. The opt-in native candidate `f762e01d63b` recovers the active
non-road geometry that the guest's original horizontal sphere test rejected.
It draws only in the widescreen margins and does not change the game image's
original indexed planes or the 4:3 center. This is a **diagnostic candidate**;
the personal Stream Deck installation, public v0.5.0 and tracked release patch
remain unchanged. Every live comparison used the physical 2560×1440 primary
display and literal `MIDV_FFB=0`.

## Why this candidate

At source 5997/display 6000, the source-time RAM/ROM/resource reconstruction
matches 2,030 of 2,144 original active-object quads. Ten additional quads in
three active objects are absent from both original DMA and existing host
packets, intersect both measured unowned components, and independently fail
the stock horizontal sphere test. The isolated raster covered 8,117/8,117
left and 11,651/11,651 right component pixels. These are source-qualified
objects, not hand-picked New York object IDs. The prior offline preview was
not a native ordered draw, so it could not establish finished-frame behavior.

`world_active_roads::collect` now has a separately gated ordinary `0x1000`
non-road path. It validates the current camera/table, limits membership to
static resource-bound objects with stock horizontal rejection, and leaves the
existing road-only call unchanged. The native margin compositor accepts this
class behind `MIDV_WORLD_HOST_ACTIVE_NONROADS=1`; fade policy 2 encodes its
permission separately from the existing authored-road policy 1. The replay
CLI requires candidate, active-road margin settings and FFB0. The normal
product path is off. World 2.5 uses the same guarded code; its subsequent
single-frame Hawaii check is reported below.

The standalone source scene qualifies first: all 10,555 old host quads and
their order are preserved; 58 non-road quads from 11 active objects are added,
including all ten source-qualified gap quads. The initial standalone version
admitted all 323 active non-road objects and **failed** its guard; the narrowed
static/horizontally rejected collector passed. `native-source-5997-qualified-v1.json`
records that bounded result.

## Live results

The first candidate `456e143` **failed** the first live mirror with “Invalid
emitted host fade metadata.” The new packet class needed a separate gated fade
policy. Candidate `f762e01` fixes the native decoder. Its first 6,002-input
replay then **failed only in the Python mirror reader**, which still rejected
policy 2; emulator exit was zero and the full prefix ran. The raw failed
reports are retained. After a gated reader fix, the same raw files were
requalified without rerunning the game in
`active-nonroads-fade-qualified-v1.json`.

That source5997/display6000 trial preserves all recorded inputs and times,
native images, original indexed planes and the full 4:3 indexed center.
20,954 margin indexed pixels change, all newly owned and none previously
owned. The measured left and right unowned components become 8,117/8,117 and
11,651/11,651 owned, with zero residual. The correct completed frame 6000
changes 14,626 RGB pixels within the two margins; the repaired image was
visually inspected. Shutdown drained and joined its worker. A separate matched
nine-frame sequence at completed frames 5960..6040 passes both replays and
changes eight frames (42,053 total RGB pixels), with zero changes in the
middle third. The ninth is exact. The added geometry follows the moving scene
in this sparse interval; a 76-pixel newly near-black color hint at 5990 appears
on an overpass underside in the paired image. That color heuristic cannot
establish a new texture defect.

The independent earlier New York source3596/display3600 right wedge also
passes a 3,602-input candidate replay. The matched indexed component acquires
host ownership at **24,759 of 24,769** pixels; ten isolated pixels remain.
The original indexed planes and 4:3 center are exact. Unlike frame6000, this
scene changes 25,631 previously host-owned margin pixels as new geometry
overlays existing host scenery; the finished image was visually inspected and
the right wall/shoulder looks continuous. This is a larger overlap and needs
more temporal/course scrutiny before product promotion. It is not a proof
that every missing texture or distant pop-in is fixed.

The paired screenshot comparator's initial `active-nonroads-6000-paired-v1.json`
was **invalid for RGB evidence**: it joined frame6000 indexed planes to the
first screenshot (5960). Its indexed ownership counts remain valid. The
comparator now uses the completed-frame receipt and validates decoded-pixel
hashes; `active-nonroads-6000-paired-v2.json` carries the corrected RGB result.
`active-nonroads-3600-paired-v1.json` used a single screenshot and was already
correct; v2 also validates its completed-frame receipt. Raw temporal image
comparison v1/v2 invocation failures and v3's
expected pixel-difference FAIL are preserved; the explicit
`active-nonroads-temporal-qualified-v1.json` checks matched inputs, original
planes, center and completed-frame deltas without redefining changed pixels
as exact equality.

## Evidence and next gate

All large files are local under
`results/diagnostics/world-new-york-20260927-live-1`. The native binary SHA-256
is `db019f5c62fd75bccfc451bb85b0da14344a0492b6b6167a8bd6a1082e8704d7`.
Its one-time 283-patch export passed, and the accepted 281-patch release export
was not modified. Focused native projection/fade fixtures pass; 26 Python
tests plus compilation of four new evidence tools pass. A bounded build linked
the candidate; no fresh clean worktree build or public package was made.

One World 2.5 Hawaii cross-revision check has now run on the same candidate.
Matched control/non-road 6,000-input replays both pass recorded input/native
comparisons, stable physical1440 display and owned worker stop. The option
submits 108,249 more host quads across the same 1,967 scenes, yet their one
completed frame at 5900 is **byte-exact**. The conspicuous dark rectangle in
the distance is present in both images. This proves execution/preservation at
that sparse point, not a visual repair or broad World 2.5 acceptance. The
initial prepare-only attempt with stop6002 failed because the recording ends
at6000; corrected stop6000 prepared and both live replays passed. Local raw
reports are `world25-{control,nonroads}-run/report.json`, with the source-hashed
pair in `world25-nonroads-paired-v3.json` (v1 preceded an explicit
display-target equality check; v2 preceded a center-third damage gate). The reusable
`harness/compare_world_nonroad_course.py` enforces binary, controls, FFB0,
input/native, display, shutdown, completed-image receipt and unchanged
center-third gates.

A second World 2.4 course check reuses the saved Germany race without a new
attended drive. A control/non-road pair passes 7,350 recorded inputs on the
same frozen binary and stable physical1440 display with FFB0 and owned
shutdown. The candidate submits 144,797 extra host quads across the same
2,837 scenes; four completed images at 7280, 7300, 7320 and 7340 were compared.
Only 7280 changes: 13,727 RGB pixels in the far-left margin, image bounds
`(68,455)..(299,637)`, revealing a small distant building. The other three
are byte-exact. The center third is exact in all four. The paired image was
inspected; 53 newly near-black pixels are within added building details and
are a color hint, not a proven defect. Local evidence is
`germany-{control,nonroads}-run/report.json` and
`germany-nonroads-paired-v2.json` (v1 before the center-third gate). This is a bounded cross-course preservation
and visibility check, not a full-race geometry/transition verdict.

Next, inspect a denser World 2.5 interval or a World 2.4 transition where
newly admitted objects can overlap prior host scenery. 4K and physical-wheel
acceptance remain open.
The New York result addresses **black widescreen coverage gaps**, not the
distance at which mountains/trees enter the guest's scene list; global pop-in
remains a separate problem. Off-Road Pike's Peak's saved ten-frame resident
trial was pixel-exact to control, so that candidate has no demonstrated
benefit on that course. Do not promote either renderer path or overwrite the
personal executable from this evidence.
