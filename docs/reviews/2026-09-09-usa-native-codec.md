# USA model codec and transform verification — September 9, 2026

The USA model decoder is now a reusable native helper, verified against recorded
game output and an independent Python reference. This closes the model-format
prerequisite for USA's host scenery adapter. It does **not** yet insert additional
scenery into a running game or establish four-game distance parity.

The queue remains active every 30 minutes without a morning cutoff. The earlier
pause came from the old 08:00 work order; the maintainer's resumption supersedes it.

## Implementation

- `native/usa_model.h` decodes USA's two-word, count-minus-one header and
  interleaved polygon/UV/texture words. It supports full and compact X/Z
  transforms, billboards, direct and lookup palettes, and per-object LOD pointers.
  It shares C31 arithmetic with World without copying World's model format.
- The camera transform, compact dispatch and LOD decisions are independently
  checked. The compact branch's C31 shift tests bit27, rather than treating the
  upper nibble as a generic type. Alternate local/identity transform paths remain
  explicitly unsupported by the preparation helper.
- Host projection uses a generated reciprocal tail for extended distances,
  rejects near-plane crossings and signed16 screen-coordinate overflow, and
  bounds model spans to ROM. The offline captured mode deliberately reproduces
  the original clamps and coordinate wrapping to compare original DMA. Scene
  membership, clipping and resource lifetime are separate acceptance work.
- `lua/usa_model_capture.lua` is a bounded, revision-guarded read-only probe.
  It records actual origin and billboard operands and writes a completion
  receipt. It explicitly refuses USA's cycle-eating C93E/C93F speedup addresses.
  Raw model/material data remains local.
- `harness/verify_usa_model.py` checks nonempty, ordered, owned DMA and projection
  evidence against independent Python and the compiled native helper. It reports
  skipped clipped/special paths, rejects incomplete captures and returns a failing
  exit code. Six Python tests and a native boundary/format test join local checks.

This milestone is collection `b0d18ca`. The native helper is compiled as a
standalone analyzer; it is **not yet linked into MAME**. No MAME source, binary,
patch export, launcher default or personal preference changed. The separate
World candidate remains native `5a5e11d9ab7`, SHA256
`a5d0fb417c2277346ae1c0742e82cf7a9ee5832fadde5ce5676f01a598a0ab43`.
Stream Deck remains v0.5.0, native SHA256
`87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8`.

## Measured evidence

Five complete 5,012-input USA replays ran serially on the 3840x2160 monitor:
control, early/late model probes, and early/late probes with the additional
billboard/dispatch operands. All preserve the original input/native reference.
Each probe matches the control's 3,211 camera samples and 9,633 actual ADC reads
**and timestamps** over frames1800..5010. All three completed3824x2073 images at
4900/4950/5000 match the control for every probe. The earlier prototype's three
images near3500 are separate evidence in the preceding checkpoint.

| Captured interval | Projection/transform buffers | Unclipped calls | Ordered DMA quads | Excluded clipped/special calls |
|---|---:|---:|---:|---:|
| 3500..3550 | 5,178 | 5,068 | 44,652 | 110 |
| 4900..5000 | 13,725 | 13,473 | 66,846 | 252 |

Both references and native checks match all18,903 projected buffers, prepared
centers/matrices, dispatch/LOD selections and111,498 ordered quads in the eligible
calls. The intervals cover225 distinct model addresses and408 object addresses,
including5,610 billboard transforms. These are two short course windows, not all
models, roads, tracks or render paths. The362 excluded calls have projection
coverage but no claim that their clipped/special polygon output is reproduced.

An initial extended verifier incorrectly compared signed camera depth with an
unsigned captured word, reporting32 failures for objects behind the camera.
Those values agree after signed conversion; the failed report is retained as
`prepared-early-model.json`, and a negative-depth regression test covers the fix.
The original model/geometry comparison did not fail. Earlier empty prototype
failures remain in the preceding checkpoint.

Heavy operand logging adds host overhead: the late probe finishes roughly1.6s
behind the control over86.52s of emulation, with a sampled speed interval near79%.
This measures diagnostic capture cost, not the performance of a USA host renderer.
The guest route and ADC clock remain identical. Runtime cost must be measured
again with summary logging when scenery is actually integrated.

Final local checks pass212 Python tests with no skips,17 native helpers,
10,081 C31/137 yaw vectors and32 GPU checks across47 commands. The321-file source
identity is `b10063d3d943eadd579f31bb38303f3ce01eaf07841eab49f2821169f6aef103`.
The previous seven-game baseline still belongs to the unchanged5a5 candidate;
this milestone does not describe it as newly rerun. Physical FFB remained0.

Raw evidence lives at `results/diagnostics/usa-native-codec-20260909`.
[Publishable proof](../../results/proof/2026-09-09-usa-native-codec/README.md)
recomputes five input/camera/ADC traces and the declared image comparisons.
Model/transform/DMA and native/GPU build results are hash-bound receipts because
the raw game operands are not published.

## Next work

1. Verify USA's insertion point after sky/background drawing, pending-list
   membership and palette/texture residency. Use the verified decoder to build
   host-owned scenes without guest activation, guest writes or hardware DMA
   changes. Native reads must use direct RAM and assert zero emulated-cycle delta.
2. Map future-section descriptors and material binding, then qualify1x/2x/3x
   against original routes, original resources/order, occlusion, clipping,
   handover and completed4K images. Link/export/build MAME only when the adapter
   is integrated. No per-model allowlist or menu promotion based on counts alone.
3. Carry the shared verification contract to Off Road and Zeus. Finish World's
   2.5 road/ground adapter alongside that work. Keep existing experiments until
   verified replacements provide comparable visible distance gains.
