# Quiet Exotica journals preserve the tested output

The candidate CLI now accepts `--exotica-journals capture|quiet`. Quiet requires
the complete Exotica future/waiting/active renderer, marked original endpoints,
live GL and physical FFB disabled. Both CPU and GPU independently validate and
acknowledge the selected policy. The option is not a product menu or a continuous
runtime mode; existing diagnostic frame windows and count limits remain.

Quiet keeps ownership/admission work enabled and omits routine journals.
The harness requires all 19 completion/writer summaries, checks matching scene,
geometry, material, fence and endpoint counts, and rejects missing/duplicate/
failed summaries or unexpected journal files. Its report explicitly marks
independent per-event journals absent and continuous operation false. It does
not substitute old control files for evidence missing from the new run.

A single matching 5,300-input Amazon replay on native `f048096c58c` passes:

- All four completed 3840x2160 CRT images at 5220/5224/5228/5232 are byte-identical
  to capture mode.
- 191 camera/ADC/source/resource/geometry/original/private buffer files match.
- All deterministic native completion fields match. Host writer timing,
  scheduling-dependent batch partitioning and writer occupancy are reported
  separately and are not asserted equal.
- The initial quiet implementation omits 51,570,124 bytes across 20 journals.

Review then identified one of those files as snapshot evidence rather than a
routine journal: `exotica-endpoint-inputs.txt` carries selected and first-rejected
model operands. Separate native commit `f02c990e3a5` always captures that bounded
file, retaining diagnosis of a new failure without a rerun. The final quiet
policy therefore omits **19** routine journals. The verifier rejects missing or
empty operand evidence when endpoint snapshots are reported. Five focused Python
tests and the native policy test pass. The successor builds; the 4K equivalence
run above is on its immediate predecessor, before this file-retention-only fix.
No further full drive was run solely to repeat the unchanged rendering path.

The final frozen candidate is `f02c990e3a5`, SHA256
`0fc70a285c43cc35f647dacbc62686de6b38ba0558e2d95b8fece8f68d6ff858`.
The 238-patch series reconstructs `78a84611ee513ffdaaca897c0de83d6adac863ff`.
The personal binary and public v0.5.0 remain unchanged.

Local evidence under `results/diagnostics/exotica-amazon-20260909` includes
`quiet-journals-4k`, `quiet-journals-qualified.json`,
`quiet-journals-native-export.json` and `quiet-operands-native-export.json`.
Both one-time export scripts have already run. The earlier report preserves its
20-file scope; it is not rewritten to claim testing the later 19-file policy.

Next: remove only cumulative diagnostic limits from quiet execution with checked
counters, retaining live storage bounds and the 32-bit endpoint transport limit.
The startup/frame-window and reset/drain contracts still need separate work.
Quiet operation alone is not long-session or cross-track release parity.
