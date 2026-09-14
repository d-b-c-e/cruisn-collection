# Combining the Amazon ground repair with extended scenery

The reported black left margin on sharp turns remains an active release blocker.
The separate active-margin candidate repairs ground that the original horizontal
submission limits omit. The current future/waiting candidate presents a different
private target, so that earlier repair is not present in the latest extended view.
Turning both switches on is insufficient: their material sequencing and render
targets differ, and they contain overlapping objects.

One offline combined scene now repairs the visible wedge while retaining the
extra scenery. This is **not yet linked into MAME or deployed**, and does not
establish that every black texture has the same cause.

## Measured overlap

Three saved Amazon scenes have identical camera, view, bank, margin and render
context across the accepted active-only and future/waiting captures. The active
pass uses its original near-range geometry; waiting uses the 3× candidate.

| Proposal frame | Active instances | Waiting instances | Shared instances | Active instances retained | Active quads retained |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5072 | 63 | 139 | 59 | 4 | 32 |
| 6330 | 24 | 35 | 3 | 21 | 71 |
| 7187 | 0 | 1 | 0 | 0 | 0 |

All shared instances match their ordered polygon bytes, render fields and
palette contents. Independent texture-footprint comparisons find no changed
covered pages between the owned waiting image and ready-time active image.
Zero-quad instances remain explicit in these counts.

The new standalone `native/exotica_composition.h` removes only confirmed waiting
duplicates from active geometry. It preserves waiting geometry, intrinsic blend
values and the remaining active order. A conflicting overlapping instance,
material mismatch, missing/ambiguous owner mapping or malformed extent rejects
the operation before mutating either output. Native conservative texture coverage
checks 154 pages at5072 and27 at6330; unrelated image changes need not reject.

The helper does **not** infer live ownership from a RAM slot. Its caller must
validate the reconciled cohort's actual lifetimes, scene/camera/page and command
boundary, including any changes between active sealing and device completion.
The standalone analyzer checks supplied owned render data; it does not execute
or independently reconstruct that lifetime history.

## Completed-image comparison

The independent renderer replays the accepted original GPU5073 command stream
from the prior completed framebuffer and resources. Future insertion stays at
command32; retained waiting stays at3358. Active geometry follows waiting at that
same completion boundary, with its own ready-time texture/palette image.

Active drawing uses the private wide-depth shader and a copied D32 depth target
sharing its color buffer. It is scissored to the margins. Original command order
continues unchanged afterward. This preserves depth for subsequent original
commands rather than adding a second set of private depth writes to their target.

| Added active pass | Changed RGB pixels vs future/waiting | Black pixels repaired | New black pixels | Center unchanged | Completed depth unchanged |
| --- | ---: | ---: | ---: | --- | --- |
| Confirmed duplicates removed | 7,455 | 6,459 | 0 | Yes | Yes |
| All active objects, without deduplication | 7,495 | 6,459 | 0 | Yes | Yes |

The baseline run through the modified offline renderer matches both completed
color and depth from the previously accepted retained renderer exactly. Both
composed outputs preserve the other framebuffer page and finite depth bounds.
Inspection of the completed image shows the left black ground wedge filled with
ground while the additional vegetation remains. The unfiltered result differs,
supporting explicit duplicate removal even when a small color change is subtle.

The saved retained waiting packet used for this GPU comparison has all849 quads,
palette rows and owned-image hash equal to the current accepted waiting capture
used for overlap analysis. Generation numbering differs across capture chains;
the offline active image is explicitly independent, not applied as an invalid
delta to the waiting chain.

These are internal2736×4096 buffers, with one2736×1600 displayed page. This is
one offline scene around game elapsed0:34.96, not a fresh live4K drive, temporal
acceptance, performance measurement or general fix for every sharp turn.

## Validation and next integration

The compiled analyzer matches the independent Python filtered instance and
polygon bytes at all three samples. The native synthetic test covers preserved
order, alpha/geometry/material conflicts, unrelated image updates, ambiguous
owners, malformed extents, zero-quad/empty scenes and transactional rejection.
Both new C++ files compile with the local harness's C++11 and strict warnings.
Five local-check runner tests pass; the new native test is discovered automatically
and the analyzer is added to its compile list. No broad suite was repeated.
An initial analyzer compile lacked the scene-serialization header; adding that
explicit dependency resolved it before the recorded comparisons.

Next, introduce an explicit candidate-only composition gate. At each actual
completion, keep the existing early future draw, complete retained waiting, then
filter and draw active margins into the private wide target. The live consumer
must accept exactly three ordered material stages per scene: future image,
zero-page waiting continuation, then ready-time active updates. Only the last
stage may commit the still-pending guest dirty pages before the next proposal.
Original WaveRAM/palette uploads remain separate.

Before relaxing any existing mutual exclusions, add those ordering checks,
live lifetime validation for deduplication, separate composition receipts and
private-target preservation checks. Then run a short original-input Amazon
comparison covering5072/5080. A broader replay is justified only after this
integration succeeds or exposes a new risk. Do not promote either experimental
path based solely on this single offline success.

Local raw evidence under `results/diagnostics/exotica-amazon-20260909/`:

- `margin-composition-overlap.py` / `.json`: independent owner/geometry/material joins.
- `margin-composition-native/`: compiled outputs, per-sample receipts and hashes.
- `inject-composed-depth-stream.py`, `run-composed5072.py` and
  `margin-composed5072-render/`: three ordered GPU comparisons and inspected images.

Current native candidate03e43ffc3f5, personal87d04de4 and publicv0.5.0 are unchanged.
No MAME build, game launch, physical FFB, deployment or release occurred here.
