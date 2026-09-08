# Next adapter notes — 2026-09-08

These are static analysis leads from the program captures bound in
`results/diagnostics/distance-layouts-20260908/sources.json`, plus the explicitly
identified runtime observations below. They are not patches to apply blindly.
All addresses are hexadecimal C3x word addresses. USA's adapter is now built in native `8b151aa9c2f`; see [its trial report](2026-09-08-usa-global-distance.md).
Off Road now has a bounded Lua trial, not a native product adapter; see
[the results](2026-09-08-offroad-global-distance.md). Exotica now has
[a validated read-only frustum audit](2026-09-08-exotica-frustum.md); its
projection/margin intervention is still unbuilt. The static leads below are historical context.

## USA 4.5: complete the projection profile before extending admission

Runtime residency evidence is in [the USA report](2026-09-08-usa-residency.md).
The admission and removal consumers are `729B`→`727D` (75,000) and
`7280`→`727E` (80,000). A potential 2× adapter should keep those windows and the
renderer limit coherent; the guest still manages its linked lists. Preserve a
stock control and explicitly measure old-route divergence versus repeatability.

Static reciprocal consumers identified in the low renderer:

| Clamp instructions | Consumer instructions | Addressing |
|---|---|---|
| `D0/D1`, R3 | `D5:0741C300` | `AR3 = B2B3 + index`, culler |
| `157/158`, IR1 | `15D:24C00182`, `15F:DE180B82` | `AR2=B2B3`, indexed vertex projection |
| `1B1/1B2`, IR1 | `1B5:24C00182`, `1B7:DE380B82` | `AR2=B2B3`, alternate vertex projection |
| `23B/23C`, IR1 | `241:24C00182`, `243:DE180B82` | `AR2=B2B3`, transformed model vertices |
| `277/278`, R0 | `27C:24E0C3C2`, `27F:24E0C3C2` | `AR2=R5+index`, `R5=B2B3`; dynamic model path |

The last pair is easy to miss when searching only for clamps on R3/IR1. It must be
accounted for when building a global adapter. The `823E/8240` path is a screen-extremum helper with an explicit >=4999 reject;
its original behavior is retained. `A727/A728` scales an attached object from
its parent's cached depth; the guarded host tail covers it, but no extended reads
from that consumer occurred in the initial USA trials. Do not assume every reciprocal use is
world rendering. Inspect the code before/after each lookup and guard its base
register as well as PC. Reads inside a table tap must use backing RAM or captured
values; nested address-space reads caused a prior broken World prototype.

## Off Road 1.63: a different table and far comparison

The observed far comparison at `1C35:0420B724` reads **DP=1**, i.e. word `1B724`,
and branches on depth minus radius >= 47,296. Initialization copies the C31 float
at `11221` to that word (`1820/1821`). The reciprocal base is ROM word `CB0FC8`,
selected through `111A7`; upper index `111A8` is 63,679, with a -4,096 lower bound.
Runtime culler indices were 184..59,845 in the measured drive.

All **63,680 nonnegative table entries** now match this generator bit-for-bit:
use `2-(index+1)/504` below index503, otherwise `504/(index+1)`; round the exact rational to eight
decimal places with ties to even, convert to float32, then encode C31. Six-, seven- and nine-decimal
controls produce 62,856 /56,246 /48,268 mismatches. Direct ROM decoding was checked
against every previously captured runtime table sample. Table SHA256
`8b4c0581664a93f0225556c87c9cc383f8d43f97e5e779561ccf3ecb41397c76`;
source ZIP SHA4499df321ede9592f4ad9b3ab255d445acc89754c7c0ead80f9471e131084f63.
Evidence: `results/diagnostics/offroad-tail-20260908/{analysis,generator}.json`.
The remaining4,096 negative-index entries also match the same linear near formula
(`negative.json`): all67,776 entries are now checked. Original entries should still
stay untouched. Python's direct `round(float,8)` fails two exact decimal ties (20479 and61439);
integer quotient/remainder rounding fixes both. The failed direct-round receipt
is retained, and `recompute.py` rechecks all entries with the user's ROM ZIP. This
validates a reconstruction of the existing table, not an extended renderer or resource lifetime.

Static follow-up also identifies `1E9D` testing `B725`=63,680 after adding the
object radius: a separate vertex-path clipping boundary. Projection-table base
loads occur in multiple paths (`1D73`, `1DF4`, `22F7`, `2357`, `237B`, `2575`,
`259E`, `2787`, `2838`, plus helper `E02E` and `E21F`). Profile these consumers
and the clipping boundary before any2× table extension. The ROM table ceiling
can remain unchanged in the bounded1.25× far-culler experiment.

A 1.25× far-limit trial reaches 59,120 and would test the 1,173 measured nearby
rejections while retaining the existing table ceiling. Even this needs vertex
depth/clamp counters and completed GL/resource checks; bounding spheres and long
polygons can cross the table end. A larger multiplier needs an Off Road-specific
virtual tail and guards for its multiple vertex consumers. `B725`/`11223`=63,680
is a separate initialized value, not automatically another far plane to patch.

## Exotica 2.4: inspect CPU visibility before increasing an unused far limit

The measured CPU culler had zero far rejects at 204,800, but 85,388 upper-table
clamps. Original camera-space X/Y/Z for that culler are stored at
`87FF47/87FF48/87FF49` (guard pointer `67C3=87FF48`). The table read at `688B`
uses base `EAAB` plus IR0, clamped to 4,999. The far test at `6887` uses
depth **plus** radius; object radius is `AR7+15`, depth `AR7+14`.

Subsequent CPU sphere tests use `67D1` (200, Y bounds), `67D0` (256, X center),
and `67CE` (511, right bound): instructions `688F/6892`, `6897/689B`. A bounded
read-only probe can record transformed position, actual reciprocal and the
observed branch operands, then ask whether the 80,000 projection clamp rejects
objects that a true extended reciprocal would keep in the view. This is a
hypothesis, not evidence that changing it already helps. Distinguish CPU object
rejection from Zeus geometry/viewport clipping and widescreen margins.

The renderer traverses lists reached through `BBB5`, `BBB6`, `BBB7` (calls around
`681F..6834`); identify their producers to investigate activation/streaming.
There is also an apparent model LOD switch at `6968:04E261A8` (25,000), following
`AR7+11` model selection. LOD detail is separate from drawing distance. Neither
these lists nor the LOD threshold has a runtime intervention or acceptance yet.

### Exotica follow-up after the USA checkpoint

Static attribution reduces the projection scope: `6B99` merely restores the table
base before returning to the main culler. The other lookup at `C371/C375` belongs
to a helper with an explicit depth100..30000 gate (`C36A..C36D`), so its stock
reciprocals should remain unchanged. The main culler `688B` is the observed
80,000-unit clamp candidate; Zeus receives geometry through its separate path.

For a read-only frustum probe, snapshot object depth/radius and camera XYZ in the
`67DA` far-word tap atPC6888. Reading them inside a broad reciprocal-table tap risks
nested address-space callbacks because object RAM overlaps the table range.
Then observe the actual float-register operands atPC6890(Y lower),6893(Y upper),
6898(X lower),689C(X upper), retaining which stages execute. This permits checking
whether a proposed true reciprocal would admit objects the original CPU tests
reject. Predicted sphere visibility must be compared with actual branch operands;
it is not a completed-GL result. Guard the fast pointer67C3=87FF48 and all planes.

If justified by that probe, a bounded host/Lua trial could replace only the
main culler's clamped reciprocal read, using a depth cached outside the table tap,
without changing guest RAM or the unused204,800 far plane. `688B` also runs in the
far-reject branch delay slot; do not treat its read count as an accepted object,
or fail merely because a rejected object would require an out-of-range index.
No such Exotica intervention has been run at this checkpoint.
