# Next adapter notes — 2026-09-08

These are static analysis leads from the program captures bound in
`results/diagnostics/distance-layouts-20260908/sources.json`, plus the explicitly
identified runtime observations below. They are not patches to apply blindly.
All addresses are hexadecimal C3x word addresses. Current built native remains
`dae2569f793`; the following USA/Off Road/Exotica interventions are **not built**.

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
accounted for when building a global adapter. An additional clamp/table consumer
around `823E/8240` and a table load at `A727` need attribution before deciding
whether they should retain stock behavior. Do not assume every reciprocal use is
world rendering. Inspect the code before/after each lookup and guard its base
register as well as PC. Reads inside a table tap must use backing RAM or captured
values; nested address-space reads caused a prior broken World prototype.

## Off Road 1.63: a different table and far comparison

The observed far comparison at `1C35:0420B724` reads **DP=1**, i.e. word `1B724`,
and branches on depth minus radius >= 47,296. Initialization copies the C31 float
at `11221` to that word (`1820/1821`). The reciprocal base is ROM word `CB0FC8`,
selected through `111A7`; upper index `111A8` is 63,679, with a -4,096 lower bound.
Runtime culler indices were 184..59,845 in the measured drive.

The far-tail samples numerically resemble **504/(index+1)**, not World's
512/(16×index+1) table. Samples at 1000, 4900, 4999 and 63679 differ from that
candidate formula by only a few float ULPs. This is an inference from four samples,
not a verified generator. Near entries use another behavior (e.g. index100 is
approximately1.7996), so extrapolating the whole table with that formula is wrong.
Dump/check a bounded far-tail interval before implementing a host extension.

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
