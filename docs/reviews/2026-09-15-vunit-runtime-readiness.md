# V-Unit runtime readiness and diagnostic write failures

USA, World2.4/2.5 and Off-Road still use finite host-renderer frame windows.
Their scene hooks already check the relevant guest instruction, code revision,
source pointers and material state. This is not yet proof that those hooks can
safely activate during initial game setup without a recording-specific start.

## Saved evidence and existing bounds

One read-only inventory of three known passing replays measures the existing
summary journals. No game was rerun for this audit.

| Sample | Summary bytes | Scenes | Native frame range | Extra quads |
| --- | ---: | ---: | --- | ---: |
| USA, horizontal-culling candidate | 129,881 | 750 | 3501–4999 | 1,637,123 |
| World2.5, active-road candidate | 280,577 | 1,666 | 1800–5990 | 4,121,905 |
| Off-Road, partial-source candidate | 211,718 | 1,578 | 1800–5056 | 1,940,175 |

These are different retained route segments, not comparable whole-drive timings.
They contain at most one host scene per native frame; Off-Road includes134 empty
scenes. Neither one scene per emulated frame nor a nonempty scene every frame is
a valid universal completion requirement. File sizes are much smaller than the
previous Exotica event/cohort journals. Do not claim a major performance problem
or prioritize another broad benchmark on this evidence alone.

Source inspection finds bounded runtime caches already present:

- World retains at most128 decoded upcoming sections, prunes passed sections,
  and clears on track reset or a backwards frontier. Its synthetic source ID
  allocation rejects exhaustion rather than wrapping.
- USA also prunes/limits upcoming sections, clears on track change or rewind,
  and bounds palette entries. Its immutable model cache evicts at1024 entries
  or a1,048,576-word budget.
- Off-Road clears on pretrack/track change and applies the same model-cache
  entry/word budgets. Current material readiness remains checked on each build.

These are source-level logical limits, not measured heap peaks or multi-race
acceptance. Original guest state and resource ownership must still be verified
across actual menus, track changes and reset boundaries.

## Fixed: ignored buffered journal errors

The common `world_host_exit` also serves USA and Off-Road. It previously ignored
both the existing stream error flag and close results for scene, quad and clip
logs. Fade logs checked only close. An earlier failed buffered write could
therefore escape explicit native failure even when `fclose` subsequently
succeeded.

The shared `native/checked_journal_close.h` helper clears the owner's pointer,
checks the stream's existing error flag, then always closes it and checks final
flush/close success. The exit handler closes all four logs before reporting
which failed. This changes diagnostic failure reporting, not geometry, frame
windows, game simulation, FFB or defaults.

A native test passes for null ownership, a successful buffered write and an
actual failed write to a read-only stream. The latter sets `ferror` while close
can succeed, reproducing the previously missed condition without modifying its
source file. Native compilation passes. No game replay was justified for this
isolated I/O closure change; the retained gameplay results are not described as
fresh runs of this successor.

Frozen native `71c8339c8c7`, SHA256
`ffe224ca4cd6c4b59a644aeb27f85bf6b2b61477a4d6dfe78badbe44f79c0b20`.
247patches reconstruct tree `94ff46cdd92067358f022e6b4c5915e5aa176459`.
Local `checked-journal-close-native-export.json` and build log are under
`results/diagnostics/exotica-amazon-20260909`; the export script already ran.
The saved CSV inventory is `world25-roads-20260914/vunit-runtime-audit.json`.

## Next implementation

1. Observe and qualify actual first safe scene activation separately for USA,
   both World revisions and Off-Road. Existing callbacks check different guest
   instructions and readiness structures; Exotica's pool protocol cannot simply
   be copied onto them. Reuse existing saved startup evidence where available.
   The subsequent [USA startup observation](2026-09-15-usa-startup-observation.md)
   qualifies six original RAM/fast-RAM states at first scene and first frontier
   against native code guards and independent Python preparation. Early live
   rendering and the other game profiles remain to be exercised.
2. Add an explicit continuous policy with optional bounded capture, keeping
   live cache/source/resource bounds and the existing latched preparation-only
   fallback. Suppress persistent journals for normal operation without making
   file presence the renderer's enable flag. Small final scene/submission
   summaries should preserve useful failure evidence.
3. Verify original inputs/resources and completed images on one justified
   segment per affected adapter, then exercise real track transitions. Treat
   actual CPU/GPU queue completion separately from reaching a chosen frame.

The separate Exotica continuous-policy replay has passed; its two-race recording
is pending user availability. World's Hawaii custom-handler/no-op and adjacent
mesh investigations have already been completed for the retained sample:
see the [terrain boundary](2026-09-14-world-terrain-boundary.md) and
[neighbor search](2026-09-15-world-terrain-neighbors.md). Do not restart the older
custom-dispatch investigation as though those results were missing. The authored
terrain gap remains unresolved.

Personal Stream Deck executable and publicv0.5.0 remain unchanged.
