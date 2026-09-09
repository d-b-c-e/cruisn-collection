# Off Road transforms, LOD and pending scenery — September 9, 2026

Off Road's standalone renderer foundation now reproduces the game's ordinary
object transforms and LOD choices as well as its model decoder. All1,399 captured
matrices/LOD selections and9,602 ordered draw commands match independent Python
and native implementations. The next step is scene/section and material handling;
this milestone does not insert additional scenery into MAME.

## Implementation and measured scope

`native/offroad_transform.h` and `harness/offroad_transform.py` implement Off Road's
table interpolator, identity/yaw/full rotation paths, world translation and LOD
selection. C31 arithmetic and the game's store/reload points are explicit.
`analyze_offroad_model --prepared` reconstructs and checks each complete matrix
and selected descriptor before running the same native model/projection/DMA path.
This prevents an incorrect matrix from passing merely because sampled pixels
happen to round to the same coordinates.

The Lua probe now records actual view matrices, trigonometry resources, LOD
context and selected indices. These ROM/table operands remain local. Alternate
local/billboard transforms still fail explicitly. Existing captured-only evidence
remains supported and does not gain a prepared-transform claim retrospectively.

Three6,000-input prepared probes sample2500..2550,3500..3550 and5500..5550. They
cover68 identity matrices,1,143 yaw matrices with9 distinct yaw values and188 full
rotations with28 distinct Euler triples. All1,399 LOD decisions match, including
591 enabled ordinary-threshold decisions and captured indices0/1/2. The other
threshold groups have synthetic tests, not new live coverage.

All three runs preserve the control's4,191 camera samples and16,764 actual ADC
reads/timestamps over1800..5990, plus the original6,000 input/native reference.
All three completed3824x2073 images at5500/5550/5600 match in every run. A separate
6,000-input scene-snapshot probe preserves the same original route and three GL
images. The original codec milestone's runs remain separate evidence.

An initial yaw reconstruction failed301 of463 matrices, typically by a low bit.
The original code stores the cosine/vertical-axis product in the matrix buffer
before adding the sine product. Adding that exact store/reload makes all463 first
samples match, followed by all1,399 broader samples. The initial failure and local
v1 implementation are retained. A synthetic fractional-product regression test
detects this rounding difference without shipping captured game operands.

Local checks pass235 Python tests with no skips,21 native test executables,
10,081 C31 vectors/137 yaw vectors and32 GPU checks,58 commands total. All351
source files match identity
`ddf24a4d159ae14eae2bcf4333cc2056a32494d6fc33803c58c0870f160c9c63`.
There is no MAME build/export or seven-default renewal for this standalone work;
nativecf58/SHA37c0a4ce retains the preceding qualification. Personal Stream Deck
remains v0.5.0/SHA87d04de4. No release, deployment, hosted workflow, physical FFB,
World force tuning or experiment-menu removal occurred.

## Newly located scene gate

Five snapshots are taken at the ordinary scene entry, before its first object.
They use direct RAM-share reads and record actual callback time/PC. Local root:
`results/diagnostics/offroad-model-20260909/scene-snapshots`.

| Snapshot frame | Active list | Pending list |
|---|---:|---:|
| 4000 | 170 | 90 |
| 4500 | 209 | 87 |
| 5000 | 219 | 124 |
| 5500 | 179 | 124 |
| 5900 | 175 | 86 |

The lists are selected by DP1 fields111F4/111F5, currently pointing at1B728/1B73E.
The pending descriptors in these snapshots all use supported ordinary transforms.
At5500 they reference93 distinct models, ROM palette lookup tables and the same
track palette/texture bases. That is promising for reuse, but does not establish
material residency or lifetime.

An **unqualified local offline** pending-scene prototype projects more
screen-overlapping quads at2x than1x:6/20/116/116/110 at2x versus0/1/25/48/49 at1x
across the five snapshots. Its3x result equals2x in each snapshot. These are
conservative projected bounding-box overlaps, not measured visible pixels or
correct occlusion. Near clipping, signed screen limits and resource acceptance
still need an integrated contract. No host draw mode has been promoted.

## Next work, already underway

**Follow-up:** the [future-section source](2026-09-09-offroad-future-sections.md)
now qualifies ordinary descriptors and real partial loader boundaries. The
allocation investigation below records the starting point for that milestone.

The section loader at9B63..9BC1 advances a four-word section table and calls9C24.
The ordinary allocation path9C68/184D starts from eleven-word descriptors with
absolute positions and rotations; it assigns the current track material bases or
an alternate material binding. A bounded local allocation probe is being used to
check these initial/final fields against actual later objects. These mappings are
provisional until that oracle passes.

Qualify the pending/future descriptor sources, material bindings and original
scene insertion boundary, then integrate cached Off Road host drawing with zero
guest cycles and no activation writes. Verify actual1x/2x/3x gameplay changes,
original resources/order, clipping, occlusion, handover and4K performance. Continue
USA performance/visual acceptance, World2.5 roads and Zeus's separate adapter.
Active turns continue directly; the one-minute heartbeat is recovery only.
