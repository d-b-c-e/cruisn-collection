# Exotica packet storage and performance — September 14, 2026

The combined future/waiting/ground-margin renderer remains a development
candidate. This change reduces repeated CPU packet allocation without changing
visibility, projection, material ownership or command order.

## Why this change

The readback-free full Amazon baseline on native `e4cfcb864be` passes all 8,860
inputs, 7,060 camera samples and 21,180 actual ADC records. Its 6,953 scene records
match the earlier captured run except host timing columns; lifetime, handover
and cohort files are byte-identical. It reports 93.58% average speed, with
93.40% measured over recorded frames 3501–8859. Removing heavy screenshots is
insufficient to establish full-speed operation. Native frame snapshots and
scene/material/lifetime diagnostics remain enabled; this is not uninstrumented
performance or new 4K acceptance.

A local clipping shortcut was rejected: its median improvement was only 0.83%
in an alternating benchmark of 239 captured models. Three bounded scene profiles
instead exposed repeated setup/placement allocation as a substantial cost.

Scene assembly now copies constant setup operands once per scene, reuses the
setup packet's capacity across objects, and appends placement commands directly.
Every setup still resets all commands and state. Invalid setup returns the same
empty/default result as before. The ordinary packet-returning API remains
available and uses the same append implementation. No storage survives a scene.

## Focused offline evidence

Five alternating old/new timing rounds, each containing 300 assemblies of each
captured scene, give these medians:

| Native frame | Prior assembly | Reused storage | Reduction |
| --- | ---: | ---: | ---: |
| 5072 | 2,761.67 µs | 2,175.95 µs | 21.21% |
| 5644 | 2,660.86 µs | 2,360.70 µs | 11.28% |
| 7187 | 2,945.39 µs | 2,590.07 µs | 12.06% |

All full ordered instance/quad bytes equal the previously captured native
artifacts, and all non-timing counters match. These are assembly microbenchmarks,
not equivalent improvements in game speed. The first benchmark compile failed
because local and canonical copies of a header were both included; it is retained.
The corrected benchmark freezes the complete header dependency set.

Five focused strict C++11 tests pass: setup, transform, scene, waiting and
composition. Added cases exercise reusable output across setup branches,
discarding previous placement commands, reset after rejection, and appending
both placement forms after existing commands. A separately compiled analyzer
using the canonical headers reproduces all three captured scenes byte-for-byte.

## Full replay result

The frozen successor passes all 8,860 inputs, native frame comparisons, 7,060
camera samples and 21,180 ADC records. All non-timing fields match in 6,953 early
scenes, 6,953 active scenes and 20,859 ordered material stages. Lifetime events,
handover records/cohorts and composition records are byte-identical.

Early scene assembly drops from 17.361s to 15.241s, a 12.21% reduction. Full
geometry hashing remains 4.466s. Over frames 3501–8859, measured game speed rises
from 93.40% to 94.20%; MAME's whole-run average rises from 93.58% to 94.26%.
The late 7001–8859 interval is effectively unchanged at 93.46%. This is a modest
end-to-end gain, not full-speed acceptance; one matching A/B run does not isolate
all host scheduling effects. No heavy readbacks were added for this optimization.
The preceding composition milestone retains its completed-image evidence.

Next complete the missing World 2.5 road adapter while retaining Exotica's open
performance, temporal handover and final 4K acceptance requirements. No broad
four-game replay matrix was repeated for these Exotica-only helper changes.

## Reproduction

Native `f6e47894b08273f1b2332059b094f546053295e5` is frozen separately at
`build/candidates/f6e47894b08/vunit.exe`, SHA256
`36eab0cffc0cc92bcdef44e690a4e8b3bf3d57274f51f48f7c281ae1aadcf999`.
The 194-patch export reconstructs tree
`e8e99fdbe741e5a2af9d3342ce665bb75d883b2f` and preserves the previous 193 patches.

Local evidence under `results/diagnostics/exotica-amazon-20260909/`:
`composition-quiet-acceptance.json`, `projection-fastpath`, `scene-stage-profile`,
`scene-storage-benchmark-final`, `scene-storage-checks`, and
`scene-storage-native-export.json`, `scene-storage-live`, and
`scene-storage-live-acceptance.json`. Raw game data stays local.

Personal Stream Deck/native87d and public v0.5.0 remain unchanged. No hosted CI,
deployment, release, physical FFB or experiment-menu removal was performed.
