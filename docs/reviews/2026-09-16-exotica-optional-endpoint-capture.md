# Exotica continuous runtime without a scheduled endpoint snapshot

Explicit continuous quiet operation now accepts endpoint snapshot0. This removes
its last mandatory scheduled original-model operand dump. Finite captures retain
the existing selected-frame requirement. First rejected marked models still save
their owned operands automatically, opening the checked file only when needed.
No rendering, admission, material, lifecycle, depth or transport guard is relaxed.
Other explicitly requested scene/depth snapshots remain supported.

The canonical runtime helper selects capture for a nonzero matching frame or the
first rejected marked model. Native integration checks zero against the already
qualified continuous policy; that policy requires the combined quiet renderer and
physical FFB0. Lazy operand output retains the existing size/count/write/close
checks. The harness requires explicit continuous+quiet selection and rejects
unexpected endpoint files or saved-model counts in a successful snapshot0 run.
Missing the snapshot argument remains an error; zero is an intentional selection.

## Validation

Twenty-one focused Python checks cover endpoint selection, quiet summaries and
continuous runtime. One native runtime executable checks ordinary capture bounds,
zero selection, unchanged normal snapshots and first-failure selection away from
any scheduled frame. Failure operand selection is compiled and tested; no new
live rejection was injected. The unrelated continuation wrapper has its own two
focused checks and is committed separately.

One5,300-input Amazon replay retains the previous continuous4K trial's2x settings,
old finite reference ends and explicitly requested scene/depth/GL snapshots.
It changes only the candidate and routine endpoint snapshot5219 to0:

- All original input/time/native images and3,500 camera records/10,500 actual ADC
  reads match. CPU preparation reaches5298 and GPU presentation5299; joined exit
  is quiescent with no outstanding work or renderer/writer errors.
- All170 retained non-endpoint source, packet, geometry, palette, original/private
  color/depth and bootstrap files match the previous control exactly.
- Four completed3840x2160 CRT images5220/5224/5228/5232 are exact.
- No endpoint operand or geometry files are created. The previous11 selected
  models/50,960 geometry bytes become0/0.9,842 endpoint preparations still occur,
  all consumed and none rejected. Rendering was not skipped to remove captures.
- All compared semantic summaries agree. Writer timing/queue peaks are separately
  retained. Depth-mirror batch count differs142,665 to142,630, with identical
  vertex/clear/frame counts. `zeus2.cpp` reads a current producer watermark then
  flushes after draining it, even without a completed frame, so host scheduling
  can split a batch differently. That count is not an ordered-geometry oracle.

The first local checker assumed that batch count was deterministic and failed.
The failure is retained. Source-guided qualificationv2 explicitly separates the
batch count and checks the unchanged geometry, resources, completed pixels and
other semantic fields. No game was rerun for this analyzer correction.
This is capture-policy acceptance, not a new distance, performance, multi-race
or release claim. Other startup/reference configuration and product gates remain.

Native `f0b4db1f25d869d010d396997bb1839c412a4b23`, SHA256
`435123cf0e1026fbdda94a8069a59f025a3d8b98fc2d1cebda0146b871fd95c1`.
253 patches reconstruct `476814a23a6864416d95e564830a464b0e4672c3`.
Local evidence under `results/diagnostics/exotica-amazon-20260909`:
`continuous-no-endpoint-snapshot`, its original failed qualification and
`continuous-no-endpoint-snapshot-qualified-v2.json`. Checks/build/export are under
`world25-roads-20260914/endpoint-routine-capture-*`; the named export already ran.
Personal Stream Deck binary87d and publicv0.5.0 remain unchanged.
