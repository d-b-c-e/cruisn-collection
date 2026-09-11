# Exotica allocation is earlier than drawing admission

The current future-only renderer stops selecting a source after its section is
allocated. The new Amazon trace shows that the original game often waits several
seconds after allocation before submitting that object. Continuing eligible
objects through that interval is a more useful next step than merely increasing
the far multiplier again.

An offline test at game time 0:34.96 adds a visible row of distant trees by
including allocated objects that have not yet submitted. It preserves the
original foreground in that sample and introduces no newly black pixels. This
is a promising geometry-selection correction, not a deployed fix or proof that
pop-in is eliminated.

## Complete-drive first submissions

A read-only probe observes all 1,010,130 standard model commits in the capture
window. It records the first commit for each section allocation, commits carrying
the temporal-fade flag, and the first subsequent commit without that flag. The
pool generation and source annotations are independently checked against the
actual allocator and section traces. A repeated drive produces the same results.

Of 3,932 ordinary section allocations, 3,487 eventually submit in the captured
interval; 445 never submit. Of the first submissions, 1,115 carry the temporal
fade flag and 2,372 do not. Model submission is still not the same as visible
pixels: clipping, transparency and nearer geometry can hide a submitted object.

| Allocation to first model submission | Measured delay |
|---|---:|
| Minimum | 1 frame / 0.016 seconds |
| Median | 238 frames / 4.162 seconds |
| 90th percentile | 540 frames / 9.448 seconds |
| Maximum | 726 frames / 12.704 seconds |

There are 2,801 ordinary objects with a delay exceeding 60 frames. Every one of
the 33,876 recorded model commits has a verified live generation and section
owner. All 30,308 fading commits reproduce the earlier fade-only trace exactly.
The ordinary objects' position, rotation, model, initial bindings, radius and
progress match their independently reconstructed source definitions.

Each full drive preserves all 8,860 inputs, 7,060 camera samples and 21,180 ADC
reads and emulated timestamps. The 21 completed 3840×2160/CRT captures match the
original control. Those captures cover one bounded window, not every frame of
the drive. No automated physical force feedback is used.

## Fade handling must remain material-aware

The ordinary fading commits include 24,525 uses of the fade setup branch and
5,308 uses of the light branch. In 832 fade-branch commits the source value is
8 and the destination value is 240, rather than a complementary sum of 256.
Simply drawing an opaque host copy behind the original can therefore produce a
small brightness dip. Treating every object carrying the fade flag as an
ordinary alpha blend would also mishandle the light branch.

These are object setup operands. A model can subsequently override material
state, so they do not establish the final alpha of every polygon. A correct
transition must distinguish the temporary scenery fade from intrinsic
translucency, texture alpha, shadows and material-specific commands.

## Allocated waiting geometry

Five retained device-boundary snapshots are joined to the live pool and actual
first-submission history. All selected objects are ordinary, still live, not yet
submitted at that boundary, and excluded by the existing future-only predicate.
Their immutable render operands match the source definitions exactly.

| Native scene frame | Waiting objects | Projected instances at 3× | Quads at 3× |
|---|---:|---:|---:|
| 3900 | 252 | 249 | 1,690 |
| 5072 | 155 | 149 | 949 |
| 5644 | 298 | 298 | 1,906 |
| 6330 | 52 | 35 | 338 |
| 7187 | 1 | 1 | 18 |

The local C++ adapter and independent Python assembler match every ordered
instance and polygon in 30 comparisons: five snapshots, 1×/2×/3×, and current
versus completed temporal fade. Nine malformed selection inputs are rejected.
Completing a fade here is an explicit diagnostic comparison, not an approved
policy for all materials. Polygon counts alone are not a visual success test.

The frame-5072 resources, RAM and context match the earlier exact command-stream
join byte-for-byte. The original GPU interval completes at frame 5073. Fresh
original and wider-depth replay reproduce all original color/depth bytes. New
waiting geometry is then inserted at the verified command boundary, before the
original models. All original commands, uploads and foreground rendering follow.

At 3× the current-fade version changes 118,226 RGB pixels relative to the earlier
future-only result; the completed-fade diagnostic changes 118,409. Visual
inspection confirms additional trees along the distant road and left side. The
original vehicles, dinosaurs and foreground remain in front in this sample.
Both comparisons introduce zero newly black pixels. The existing black ground
wedge at the left margin remains a separate defect in this older control.

Both fade variants are tested at 1×/2×/3× and repeated at 3×. Other framebuffer
pages remain exact, depth remains finite and bounded, and the repeats match.
These are completed internal 2736×1600 page images from a 2736×4096 target, not
new live 4K/CRT playback acceptance. Ordering through an entire drive, resource
changes and the actual transition into original drawing remain open.

## Reusable lifetime tracking

`native/scenery_lifetimes.h` is a standalone host component for identifying reused
guest slots. Source keys include a track/bank realm, section and source. Handles
also carry an allocation generation and reset epoch. It tracks observed model
submissions without deciding visibility, opacity or rendering eligibility.

The real trace rejected the first contiguous-pool assumption: 174 transitions
use addresses outside the main rebuilt pool. The original allocator accepts
externally created objects into its free list. That failed trace preparation is
retained. The revised component stores a bounded set of addresses within an
adapter-supplied domain, retains removal history to reject double frees, and
invalidates handles on reuse and reset. It does not contain game-specific
addresses or per-model allowlists.

The canonical native component matches an independent fold of 86,376 actual
events: initialization, 48,481 pool transitions, 4,018 source bindings and 33,876
model submissions. All 26 pre-window removals are explicitly identified. A
separate text-output comparison initially failed on Windows CRLF versus LF;
only that text transport difference is normalized, with raw hashes retained.
Stale handles, source collisions, cross-realm identity, reset, address bounds,
bounded history and 10,000 reuse cycles are tested. The analyzer rejects 17
malformed or inconsistent input scenarios.

The component and analyzer are not linked into MAME yet. Exotica-specific hooks
must still verify the original pool transactions, source allocation and exact
scene/device boundaries. Other games can reuse the identity component with their
own verified adapters; this does not establish identical game lifecycle behavior.

## Next implementation

Connect the lifetime observer to a separately built native diagnostic candidate
and compare it against these exact read-only traces. Then include eligible
allocated-but-not-yet-drawn scenery in the private extended pass, with current
render operands and owned materials. Capture the transition into the first
original submission and fade completion before deciding when to retire a host
copy. Preserve original command order and intrinsic transparency.

The complete local check run passes 352 Python tests without skips, 49 native
test programs and 140 commands, including GPU checks. Its 514-file source identity
is `786f6abd57be9f1a479331267b334260956c67b2b2b827d08d3e39b820824c95`.
The [public checkpoint](../../results/proof/2026-09-10-exotica-drawing-admission/README.md)
recomputes source/file identity, delay statistics, stored hash equality and scalar
receipt consistency. Raw native execution, game traces, geometry and GPU pixels
remain receipts; the archive does not rerun those operations.

The personal Stream Deck build and public v0.5.0 remain unchanged. Raw game data,
the comparison images and local prototype scripts remain in
`results/diagnostics/exotica-amazon-20260909`. No deployment, release, all-track,
whole-drive handover or physical-wheel acceptance is claimed.
