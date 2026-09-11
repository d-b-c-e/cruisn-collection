# Exotica waiting scenery: completion boundaries and draw order

Follow-up: [native completion observation](2026-09-11-exotica-native-completion.md)
now passes full/repeat/disabled runs. The standalone results below describe the
earlier checkpoint; private waiting drawing and transparent handover remain open.

The next scenery step now has an actual completion boundary and a tested way to
remove objects that the original game has started drawing. In a completed
offline Amazon sample, the remaining waiting geometry still adds visible distant
trees. This is progress toward reducing pop-in, not an accepted live feature:
transparent composition, resource continuity and full-speed presentation remain
open. Personal87d and published v0.5.0 are unchanged.

## Actual scene completion

A full 8,860-input Amazon run on unchanged native9ad enabled the existing command
fence observer alongside waiting/lifetime observation. It preserves the original
7,060 camera rows, 21,180 actual ADC timestamps, five resource snapshots and 21
completed 3840x2160/CRT images. The 17 waiting/lifetime files are byte-identical
to the earlier accepted observer run; all 6,953 future scene fingerprints remain
unchanged. The original target is displayed.

The actual scene-end and command-consumer logs now join all 6,953 scene proposals.
There are 2,692 first original submissions between proposal and CPU scene end,
and none between CPU scene end and device readiness. These are all observed
first submissions in those intervals, not a count of waiting objects. Of the
fences, 5,514 wait for queued commands; the longest measured wait is 16.976 ms.

Proposal boundaries use native journal-record counts. CPU-end/ready event
prefixes are inferred from their captured timestamps only after rejecting
rounded-time ties. This is separate from claiming every event has a native
end/ready record watermark; the live helper integration should record those
watermarks directly.

Five actual waiting cohorts reconcile as follows:

| Proposal frame | Proposed owners | Submitted before CPU end | Retained at device readiness |
|---|---:|---:|---:|
| 3900 | 252 | 0 | 252 |
| 5072 | 155 | 10 | 145 |
| 5644 | 298 | 0 | 298 |
| 6330 | 52 | 0 | 52 |
| 7187 | 1 | 0 | 1 |

All five have identical CPU-end/device-ready journal prefixes, so there is no
additional retirement in that interval for these samples. This replaces the
earlier assumption that looking as far as the next proposal was necessary to
identify the ten original admissions at5072.

## Independent command placement

For proposal5072, all 3,349 original CPU/GPU quad payloads join exactly apart
from their frame identifier. The actual fence follows original model160 and
3,219 original quads, at command index3358 of completed GPU interval5073.
Model160 shares the fence's rounded timestamp but must be included: Zeus invokes
the FIFO observer after processing the original word/model. A strict floating
timestamp comparison would omit it. The next polygon command is3359, with one
palette update between; inserted packets own their materials.

Offline comparisons preserve original command order, the other page and finite
depth. Independent-interpreter controls reproduce the earlier future-only and
combined-early images exactly. Splitting the passes keeps the existing future
geometry at command32 and places filtered waiting geometry at the actual fence.
The 1x/2x/3x runs complete, and 3x repeats exactly. At this sample, 2x and3x match.

The completed internal 2736x1600 page shows additional distant trees; original
cars and dinosaurs remain visible. Compared with future-only, the split3x pass
changes73,346 RGB pixels, including72,385 in the original center viewport, with
zero newly black pixels. The old left black wedge remains. These are internal
offline pages, not new live 4K/CRT or temporal acceptance.

Placement is materially significant. The split pass has the same completed depth
as putting both additions early, but different colors. Moving both additions
late also changes47,820 RGB pixels from the early combined result. Existing
translucent composition must be preserved deliberately; identical depth and more
geometry are not sufficient acceptance criteria. No forced-opaque policy is used.

## Canonical reconciliation helper

`native/exotica_waiting_handover.h` is **standalone and not linked into MAME**.
It derives its cohort using the actual registry/source selector, then reconciles
that cohort against the later registry. Submitted, freed and reused allocations
are excluded; retained items keep their proposal geometry/material fields and
source order. Reset and backwards-observation errors fail transactionally.

The caller supplies the actual observation-record watermark. The registry's
allocation sequence alone is insufficient because bindings and submissions do
not advance that counter. The adapter must still establish the same scene,
correct device fence, camera/page ownership, material lifetime and draw ordering.
The helper does not authorize drawing from a stale registry or guessed counter.

A compiled local analyzer folds the actual proposal and completion event prefixes,
derives each cohort from the original RAM/ROM sources, and invokes this helper.
All30 independent Python ordered-geometry comparisons pass across five snapshots,
1x/2x/3x and current/completed fade variants. At5072 the result retains145 owners,
139 projected instances and849 quads at2x/3x. The completed-fade variant is still
diagnostic; it does not establish a host fade policy.

Full local checks pass **390 Python tests with no skips, 51 native tests and144
commands including GPU** at source identity
`0f503b9717510a44bc5722d01f07106b02a42b9e978177dc463624fb93eef0e2`.
The initial local analyzer compile missed an explicit `<sstream>` include; its
failed source/receipt are retained, and the corrected build passes. This is not
a new MAME build or renewed seven-gameplay-default acceptance.

Next integrate bounded native completion **observation** with actual record
watermarks and compare the full original route, candidate identities and sampled
geometry. Then evaluate private waiting drawing with owned materials and a
deliberate transparency/handover policy. FFB normalization proceeds separately.

LOCAL evidence under `results/diagnostics/exotica-amazon-20260909/` includes
`waiting-fence-full`, `waiting-fence5072-command-join.json`,
`waiting-separated5072-render`, `waiting-separated5072-visual`,
`waiting-handover-actual` and `waiting-handover-local-checks`.
[Public receipts](../../results/proof/2026-09-11-exotica-waiting-handover/README.md)
verify source/hash and aggregate consistency; raw game/native/GPU execution stays
separate local evidence.
