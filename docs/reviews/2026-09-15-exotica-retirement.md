# Exotica future-assembly recovery

The candidate can now recover from a rejected **future-geometry assembly** while
preserving the ordinary game. It finishes already owned scene work, retires extra
rendering in queue order and explicitly presents the original color target. This
is a candidate-only diagnostic feature; no product setting or deployment changed.

## Narrow failure contract

`--exotica-host-failure original` requires combined private drawing and extended
presentation, live GL, an explicit candidate and physical FFB0. The default
remains strict; `strict` also selects that policy explicitly.

When future assembly rejects a scene, the failed partial result is discarded.
An empty future packet maintains material sequencing without drawing or admitting
new future geometry. Already prepared waiting work and active capture complete
normally, including their existing ownership checks. New scene selection and
original endpoint-ticket commits stop. Previously committed tickets are consumed;
they are never erased to manufacture a clean queue.

At the current scene-ready fence, the CPU requires empty original FIFO, source
and endpoint queues, completed waiting work and the expected scene/frame. Only
then does it enqueue retirement after the valid current private submissions.
The GPU rejects retirement inside an endpoint pair, flushes prior work and
acknowledges the same scene/frame. It selects the original target at the first
completed frame at or after retirement. Any later auxiliary submission is fatal.

Code/revision, source ownership, read-span, camera, original model, depth,
palette/resource, waiting/active, endpoint and transport errors remain strict.
This does not turn arbitrary fatal errors into recovery. Diagnostic journals,
finite observation intervals and continued original mirroring still need a
separate continuous-runtime design before production use.

The optional `--exotica-host-inject-failure-frame N` exercises the same branch at
the first qualified assembly at or after N. Source snapshots must precede that
injection. The harness requires matching CPU failure, queued retirement, GPU
retirement and first original-presentation receipts. A successfully recovered
run deliberately fails rendering parity while retaining its independent
original-game comparison.

## Amazon result

One5300-input fault run and one same-candidate original-presentation control use
the retained combined2x setup at3440x1440 with CRT enabled. The test concerns
recovery ordering, not a new distance multiplier or performance result.

- The injected assembly failure occurs at5230, scene3819.
- CPU retirement, GPU acknowledgment and first original presentation all identify
  that scene at5231. No later auxiliary submissions occur.
- All5300 recorded inputs complete. All3500 camera,10500 ADC and50690 lifetime
  event rows match control exactly.
- All3372 pre-failure host scene rows equal control excluding named timing
  fields. The failed scene has an explicitly empty future result. Waiting,
  active, handover and composition each complete3373 scenes and pass the normal
  receipt/ownership checks.
- 187 retained source and original/private target files match control exactly.
  This includes all original color/depth captures through5280 and pre-failure
  private targets. Whole-window admission/cohort journals intentionally differ
  after the failure and are not mislabeled immutable snapshots.
- At5230, the still-extended presentation differs from original control. All four
  completed3440x1440 CRT images5231–5234 exactly equal the original-view control,
  starting at the first retirement presentation. The switch is actually observed.
- The emulator exits normally. Replay reports the intended degraded FAIL and a
  separate recovery qualification passes. This is not release parity acceptance.

Two focused Python tests exercise selection gates, late snapshot rejection,
both receipt streams, duplicate/missing acknowledgments and mismatched scene or
frame transitions. A separate short strict-mode trial is retained alongside the
main evidence: the corrected plan injects at2000, scene617, and exits with code3,
the expected failure reason and fallback0; no retirement occurs. The first two
local strict plans were rejected before launch
(empty snapshot argument, then insufficient trailing depth coverage); neither
executed a game and neither failure was overwritten.

## Provenance

Native `645ed36ba1844a290996939ea7ccdf55a6e71e6e`, candidate SHA256
`807d677ff86e492f3ffe428f71fb6fb25a93b8f724a58f26cdd5b9a048aa6567`.
235 exported patches reconstruct tree
`9d27b0fb9337051ad2d6cdcf2afc7c9d1a53c8e6`.

Local evidence under `results/diagnostics/exotica-amazon-20260909/`:
`retirement-fault/`, `retirement-control/`, `retirement-qualified.json`, their
saved plans/runners/checker and `retirement-native-export.json`. Raw game data
remain local. Personal native87d and publicv0.5.0 are unchanged; no physical FFB,
hosted CI, new4K acceptance or broad default-suite repetition occurred.
