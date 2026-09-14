# Native Exotica original-command endpoint observation

The original-model ownership and fade endpoint helpers are now linked to MAME
behind an explicit, read-only diagnostic. They still do not change rendering.
This provides the native boundary needed for a later private-target replacement.

`--exotica-model-endpoint observe` requires a named candidate, Exotica, bounded
frames and surrounding lifetime observation. Replay explicitly disables physical
FFB. Original CPU commits carry immutable owner identities and copied setup
operands through an ordered ring-ticket queue. At the exact device callback,
the observer verifies the consumed packet and prepares an endpoint using current
device state and owned model words. It does not change guest state, upload
materials, infer earlier visibility admission or submit replacement geometry.

The corrected native candidate is `e0afe6360fd`, executable SHA256
`de9b80c5944d291a56dbfa5f369cb2da5a39751e7e5138b54d392ad426435f46`.
It is frozen separately in `build/candidates/e0afe6360fd/`. Its unchanged force
profile remains beside it. The 202-patch export reconstructs native tree
`52b66c9d33e6c1eac120d4b8c6c2cc9eb75129c6`; native commits are pushed to the fork.

## Bounded live result

The first5,260 Amazon inputs pass original input/time and native-image comparisons.
Camera and ADC traces, lifetime journal, CPU model/emission capture, independent
FIFO capture and all captured original model/resource bytes exactly match the
older native0cc control. Original and mirror completed color/depth at5219/5220
also match byte for byte. This is the existing non4K display/internal target.

Across native frames5218–5222, all1,150 owned commits are consumed in order;
none remain pending.503 other model callbacks remain untracked. All58 marked
fade preparations succeed. The11 saved examples contain98 original/endpoint
quad pairs. Every saved operand matches the independent CPU/device capture;
both quad outputs match independent Python reconstruction, and the originals
match actual native emitted quads. All seven earlier handover examples are
included. The four additional examples are not automatically claimed to have
earlier private visibility admission.

All1,150 commits independently join to their lifetime owners. The older Lua CPU
capture covers937 of these commits;213 are outside that narrower window.232
native observer events join to the bounded device-model capture. These coverage
differences are explicit; they do not become full-window independent acceptance.

Five harness tests exercise explicit gating, disabled-artifact detection,
surrounding lifetime bounds, corrupt owner/time/command/input receipts and
unexpected geometry/state changes. The existing standalone endpoint and ticket
tests supply the algorithm coverage. No unrelated full suite was repeated.

## Retained failure and next step

The first candidate `d65bcb2a319` stopped at its first marked preparation because
the adapter mistakenly used the ROM-only scenery pointer validator for RAM
setup programs. The corrected adapter validates actual RAM/ROM operand spans.
The initial failed build's replay and receipt remain intact; the successful run
uses a separately frozen executable and a separate output directory.

Next track **actually queued private-scene admissions**, then replace qualified
original quads at their existing positions only in the private extended target.
Preserve the ordinary target, material order, intrinsic alpha and foreground
depth. A visibility floor or fade policy still needs a temporal comparison across
first original submission and completion. The observer alone does not reduce
pop-in or resolve sharp-turn black margins.

Local evidence under `results/diagnostics/exotica-amazon-20260909/`:
`endpoint-observer5220` (failed), `endpoint-ram5220` (passed),
`endpoint-ram-qualified`, `endpoint-ram-native-export.json`, and
`endpoint-private-next.md`. Raw game operands stay local. Personal87d,
publicv0.5.0, force behavior and launcher options are unchanged. No deployment,
release, hosted CI or physical FFB was performed.
