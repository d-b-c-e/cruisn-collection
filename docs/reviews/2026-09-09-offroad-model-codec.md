# Off Road model codec — September 9, 2026

Off Road now has its own standalone native model decoder, independent Python
oracle and bounded read-only capture tool. They reproduce 1,399 prepared
projections and 9,602 ordered hardware draw commands across three sampled
windows. This is a prerequisite for host-owned future scenery, **not yet an
Off Road extended renderer or a four-game 3x claim**.

Work continues directly during active turns. The one-minute heartbeat is recovery
only; there is no planned idle interval or morning cutoff.

## Verified format and limits

`native/offroad_model.h` decodes five-word LOD descriptors after a seven-word
model header. Vertices contain three C31 floating-point words. Each polygon has
six words, with separate flags, packed UVs, texture offset and vertex offsets.
Its palette is a per-polygon lookup plus the object's palette base; texture
offsets use the object's texture base.

This differs from both USA's packed/interleaved format and World's codec.
Off Road uses a three-word projected vertex stride, but the ordinary polygon
path consumes only XY. The third slot can contain prior buffer data and is not
claimed as current depth. Projection preserves the original C31 operation order,
including translation after the first product and FIX before any final reload.
Backface testing uses signed 32-bit wrapped arithmetic and retains zero-area
polygons, matching the original branch.

The native analyzer loads captured ROM spans through the same bounded decoder
used by the helper. It does not bypass decoding by constructing a model directly.
Counts, address spans, polygon offsets and palette aliases are checked before
use. Failed projection or quad emission returns empty output. Original near/far
clamp branches have synthetic tests; the live samples exercised the ordinary
unclamped branch only. There is deliberately no unqualified host-extension mode.

`lua/offroad_model_capture.lua` uses DP1 data addresses and direct RAM-share reads,
with revision signatures, a window of at most121 frames, at most20,000 calls,
bounded operands and completion counts. It records the actual framebuffer
control register, including separate visible/draw bits. Model/material/ROM
operands remain local; no guest writes, allocations or activation changes occur.

`harness/verify_offroad_model.py` checks independent Python, native output,
original XY buffers and ordered hardware DMA. It rejects empty, partial,
duplicate, unowned and unordered evidence. Reports record identities and counts.

## Runtime evidence

Local root: `results/diagnostics/offroad-model-20260909`.

| Window | Projections | Ordered DMA quads | Models | Captured LOD indices |
|---|---:|---:|---:|---|
| 2500..2550, corrected prototype | 463 | 3,309 | 32 | 0, 1, 2 |
| 3500..3550 | 182 | 4,633 | 7 | 0 |
| 5500..5550 | 754 | 1,660 | 29 | 0, 1, 2 |
| 2500..2550, canonical probe repeat | 463 | 3,309 | 32 | 0, 1, 2 |

The first three windows cover68 unique model pointers,78 LOD descriptors and67
object addresses. Capturing a selected LOD and prepared matrix does **not** yet
independently verify the game's LOD choice or transform preparation. The canonical
probe separately records547 clipped/special calls excluded from its ordinary
projection contract. The prototype did not count those exclusions.

Three initial3,001-input headless runs preserve1,201 camera samples and3,603
actual ADC reads/timestamps over1800..3000. Four6,000-input runs—control, middle,
late and canonical—preserve4,191 camera samples and12,573 actual ADC reads/times
over1800..5990. Every replay also passes its original input/native comparison.
All three completed3824x2073 GL images at5500/5550/5600 match the control in each
of the four visible runs. The late scene is gameplay, not attract mode. These
checks demonstrate diagnostic transparency, not better scenery or whole-track
visual correctness; the baseline itself has visible road/terrain defects.

Two initial assumptions failed and are retained locally:

- The first model prototype assumed a two-word vertex stride. Captured offsets
  such as3 and6 disproved that; both independent and native checks failed.
  `initial-failure.json` and the v1 scripts/header retain the failing version.
- The promoted verifier initially treated the raw page register as a0/1 page
  number. Actual values were0x201 and0x204. `verified-model-v2.json` retains that
  failure; the final verifier checks the raw32-bit register without discarding
  its control flags. The capture and rendering never changed for this correction.

The local suite passes232 Python tests with no skips,20 native test executables,
10,081 C31 vectors/137 yaw vectors and32 GPU checks,56 commands total. All348
source files match identity
`df90e4202a5af21db24ebc49d4016958dba301003050119d863cf43e9b3e52ba`.
Native/GPU execution and private geometry comparisons remain hash-bound receipts
in the public proof; raw geometry/material operands are not published.

## Next work

1. Independently reproduce Off Road's world/object transform and LOD selection.
   The canonical capture now includes the view matrix. A local first check
   reproduces all463 translation components and68 identity-basis cases; yaw/full
   rotation paths and LOD selection remain to be qualified.
2. Map static scene membership, section loading and live material ownership.
   Capture original insertion/occlusion boundaries before adding host scenery.
3. Integrate bounded cached Off Road future descriptors without guest CPU cycles,
   allocations or activation changes, then prove1x/2x/3x visible gains and
   original route/resources, clipping, occlusion, handover and4K performance.
4. Continue Zeus's separate scene/material adapter, USA performance/visual
   acceptance and World2.5 roads alongside the shared contracts.

No MAME source, native build, patch export, launcher settings or deployment changed
for this codec milestone. Separate candidatecf58/SHA37c0a4ce still owns the seven
default regression passes from the USA milestone. The personal Stream Deck copy
remains v0.5.0/SHA87d04de4. No physical FFB, World force tuning, hosted workflows,
release or experiment-menu removal occurred.
