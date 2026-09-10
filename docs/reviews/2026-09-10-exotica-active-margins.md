# Exotica active objects and missing margins — September 10, 2026

The Amazon black-ground investigation now has a direct CPU visibility oracle.
Some missing ground is already loaded and active, but the game rejects it at
the original horizontal screen boundaries. Future-section rendering alone does
not address this case. A general rule over current active objects can cover it
without maintaining a list of models or tracks.

This remains diagnostic work. No extra geometry is drawn in the live emulator,
and the personal Stream Deck installation remains v0.5.0/SHA87d04de4.

## Observed behavior

Seven earlier snapshots cover Hong Kong and Amazon: 2,275 ordinary-list members,
1,180 supported stock preparations and 195 additional horizontal-margin
candidates. The local native/Python geometry prototype agrees on 189 instances
and 1,238 ordered quads after conservative bounds rejection. All sampled added
vertex depths fit the existing D24 range. This does not establish the range for
other scenes, nor solve the general future-distance depth problem.

A bounded read-only journal now follows 13 consecutive Amazon game scenes
(native frames 5070–5082), capturing list membership, current render fields,
actual culling operands, admission, preparation and standard model emission.
The actual command-ring write at PC6970 distinguishes emission from preparation;
the earlier preparation callback can also execute during special delayed branches.

All 4,591 current object visibility decisions match an independent C31 reference.
There are 4,019 actual depth/translation/factor checks, 2,316 admissions and 2,238
standard emissions; 143 special-path objects are counted separately. All 2,206
ROM descriptor/LOD selections match. Iteration order and list membership match
at each list's start and end. During the scene, only scratch depth word20 changes
4,318 times and auxiliary word31 changes once. Membership does change between
scenes, so snapshots must not become a persistent historical-object cache.

The 5072 scene contains 67 ordinary margin candidates. The four earlier ground
examples are active but horizontally rejected. Two begin normal submission at
5073 and5076; the other two remain unsubmitted through5082. Earlier suggestions
that all four had later actual-use coverage were too broad.

## Scene insertion constraint

All 201 standard emissions in the complete5080 game scene join uniquely and in
order to actual Zeus model records. The final model arrives after CPU ordinary-end.
The earlier5072 snapshot likewise had two late models. CPU ordinary-end therefore
cannot serve as a completed device or GL fence.

The intended next diagnostic will own its scene request at CPU end, then enqueue
it only after the last matching original model's polygons have entered the GL
queue. It must handle models already completed before CPU end and reject ambiguous
joins. Waiting in the GL consumer for work queued behind that wait could deadlock;
producer-side bookkeeping is needed.

## Material evidence and limits

58 of the67 margin candidates have actual later uses in the captured5080 scene.
Their selected descriptors, complete model bytes, palette bindings and palette
colors match the earlier5072 values. Nine candidates lack later-use coverage.
Conservative texture footprints for all522 early margin quads cover463,610 unique
bytes, including bilinear neighbors and two texels of padding. None of those
bytes changes between5072 and5080, although1,338 other WaveRAM bytes do change.
Endpoint equality does not rule out transient writes between those samples.

A broader current-object geometry check deliberately remains a FAIL:198 of201
objects reproduce exactly. Two rejected objects have centers behind the near
plane, which the existing future assembler excludes even though part of each
object is visible. The third reuses the preceding object's matrix; recomputing
its rotation yields four slightly different float coefficients and changes23
projected quads. All three lie outside the58 later-used margin candidates.
Fresh geometry and original matrix reuse need an explicit handover policy;
these observations do not establish all-object equivalence.

## Replay controls

Both6000-frame runs use the separately frozen native7b432/SHAd16e8b7a candidate,
cache/depth on, checked written material pages, bounds on, and the earlier Amazon
page-clear/sky/palette fixes. Physical FFB remains0. They preserve4,191 camera
samples and12,573 actual ADC reads, all ordered scene/material identities,
sampled host/GPU bytes and the ten original capture resources. All25 paired
completed3840×2160 images match. The new control also matches all17 shared images
from the prior accepted capture. Both5072/5080 independent scene oracles pass;
original device-context coverage is required at5080.

Two diagnostic failures are retained. The initial image comparison expected17
frames from a25-frame capture; the corrected post-check explicitly validates
both complete intervals and compares their shared17 frames. The first device
join attempted the next game scene merely because it began in refresh5081;
the model capture closes before that scene. The final oracle requires the fully
captured5080 game scene, while retaining CPU checks across all13 scenes.

All raw resources, object operands and images remain local under
`results/diagnostics/exotica-amazon-20260909`. Public proof contains sanitized
counts, ordered CPU/device timestamps and hash-bound receipts; it cannot
independently reconstruct raw culling, materials or pixels.

## Next implementation

The distinct current-object source type and bounded horizontal-culling adapter
are now implemented in `native/exotica_active.h`, with a separate `build_active`
entry point. The existing future-ROM overload still rejects RAM identities.
Duplicated slots across lists, malformed pointers/cycles, invalid culling inputs,
far multipliers and forced fade completion are rejected by the active path.
Current offsets0..30 are copied; the common32-word geometry DTO's final word is
zero padding, so it does not borrow a neighboring allocation's first word.

The canonical helper matches all4,591 live decisions/52lists/814margin candidates.
At seven snapshots it reproduces2,275 decisions and189instances/1,238quads; the
same refactored assembler preserves all22,670 existing future quads. Native
`analyze_exotica_scene` accepts the explicit `active-margins` offline mode, and
`analyze_exotica_active` checks bounded active-list operand streams. All321Python
tests/no skips,42native tests and118local commands pass at source identity
`d641c801c076ef54fa70d811474be603f6fff7defde61ad794813122a7cd45ee`.
Proof lives in `results/proof/2026-09-10-exotica-active-helper`. These changes have
not been synced into a new live MAME build; last live acceptance remains7b432.

Next implement the completion fence and a private copy of original depth, drawing only margin
rectangles. Original center pixels and original depth/resources must remain exact.
Unknown coordinate/material paths remain explicit unsupported classes. General
3x future scenery, far depth, foreground occlusion and fade handover remain
separate unfinished work. No release, deployment or menu removal is authorized
by this diagnostic checkpoint.

A more general fence is now being considered: the game drains its command ring
at B684/B685 into Zeus register8, then commits the consumer pointer at B686.
The ordinary-end producer pointer names an exact command boundary. A callback
after Zeus processes that final FIFO word could certify completion for standard
and special model commands alike, without relying on matching the final model.
This is a code-derived design, not a tested implementation. Ring wrap, already
drained targets, partial commands and reset handling need explicit verification.
