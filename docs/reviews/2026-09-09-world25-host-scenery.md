# World 2.5 host scenery — September 9, 2026

World 2.5 now uses a separately guarded adapter for the host scenery renderer.
The same diagnostic controls select pending/future scenery and 1x/2x/3x limits.
Roads remain explicitly restricted to World 2.4. This is a separate candidate,
not a deployed feature or a claim of completed four-game parity.

## Implementation

`native/world_host_layout.h` binds each revision's scene and pending lists,
reciprocal table, section-loader frontier, material tables and trig constants.
The addresses are independently mapped; no global relocation is assumed. The
shared C31 math and World packed-model decoder remain unchanged. Caches clear
when the revision or road mode changes. Unsupported revisions and World 2.5
road requests fail before use. Absent options preserve older recordings.

The first native candidate, `f027edd9d8654c45acf6ee81e83036b6fcf5aa4e`, stopped at
frame2602 because World 2.5 clears its section pointer and lookahead count during
track selection. Menu objects can remain in the pending list during this reset.
A read-only scene trace found350 such scenes over2602..3300, all with section0,
lead0, stock far80000 and the expected reciprocal table. Its overall harness
result failed because a prefix inherited later GL capture targets; that failure
is retained separately from the observed state values.

The corrected adapter recognizes only this exact World 2.5 reset state, clears
its future cache and waits for track initialization. Code/far guards remain
active. It preserves direct main-RAM reads, bounded side-effect-free ROM/internal
reads and the zero-emulated-cycle check. World 2.4 behavior remains unchanged.

## Current evidence

- Eleven World 2.5 snapshots include uninitialized track state and four partial
  loader frontiers. Native and independent Python agree on42,679 descriptor and
  9,322 later-allocation comparisons, including repeated objects across snapshots,
  plus projected quads at all three limits. The four earlier World 2.4 road
  snapshot oracles also pass through the revision abstraction.
- The independent reference initially missed the uninitialized state, then counted
  polygons whose projected coordinates overflow signed16-bit DMA coordinates.
  Both failed reports remain. The corrected reference explicitly reports whole
  objects excluded by that existing native bound; it does not wrap coordinates.
  Broader geometric clipping remains unfinished.
- Five full6000-input runs complete: control,1x,2x,3x and repeated3x. Each preserves
  the original input/time and native framebuffer reference. All four candidates
  match the control's4,191 camera samples and12,573 actual ADC reads/timestamps
  over1800..5990. The earlier allocation probe extends to5998: the full-interval
  comparison fails on length, while its explicitly measured1800..5990 prefix
  matches exactly. Original traces remain intact.
- Each run completes30 captures at3824x2073 on the3840x2160 monitor.2x changes18
  captures relative to1x;3x changes10 relative to2x. All30 images and3,773,825
  ordered host quads across1,666 scene fingerprints repeat at3x. Its callback
  p99/max is5.09/5.50ms; reported average emulation speed is99.87%. This is not a
  whole-track smoothness or GPU latency measurement.

**Visual acceptance remains open.** Earlier distant rocks/trees are visible, but
the5900 image also shows disconnected terrain beyond the checkpoint. The road
and ground path has not been integrated for this revision. Sparse captures cannot
certify handover, foreground occlusion, material lifetime or elimination of pop-in.
At4700,3x versus2x changes34,678 pixels; at5900,103,745. These are measured image
differences, not automatic quality verdicts. Keep the existing experiments.

## Qualification and continuation

Native `5a5e11d9ab7eda0ef8ae467ee325aed8d482d727` is built separately and pushed,
SHA256 `a5d0fb417c2277346ae1c0742e82cf7a9ee5832fadde5ce5676f01a598a0ab43`.
The141-patch export reconstructs tree `a60b47afefbd679d627d4ad4179d9c9e6f54a007`.
Implementation is collection `0fcfe3e`. Stream Deck remains v0.5.0 native
SHA87d04de4; personal settings, packages and defaults are unchanged. No physical
force, hosted workflow, menu removal or release occurred.

The matched4502-input resource pair preserves the original79,636,262-byte hardware
DMA stream,2MB VRAM,8MB texture RAM,128KB palette RAM and metadata byte-for-byte;
camera and actual ADC timing also match. This certifies those captured originals,
not every future material's lifetime or foreground occlusion.

All seven default regressions pass on the final candidate, including actual UDP
and independent memory telemetry, four software force policy/polarity checks and
Exotica's21 completed4K captures. The full local suite passes206 Python tests with
no skips,16 native helpers,10,081 C31/137 yaw vectors,32 GPU checks and44 commands.
Both reports bind to the314-file source identity
`9c155b9359ecce9800bbf9584c52c52eda775f98f6cd68e061747ea81b59e3bf`.

[Publishable proof](../../results/proof/2026-09-09-world25-host/README.md) recomputes
the five full input/motion traces, observed reset-state scalars, repeated
fingerprints, three selected4K pairs and seven telemetry/four force verdicts.
Full resources/geometry, unbundled images, numerical snapshot oracles and builds
remain receipts. Raw evidence and rejected attempts stay local under
`results/diagnostics/world25-host-20260909`. No physical force was tested.

Next carry the verified observation/adapter contracts to USA's different model
codec, then Off Road and Zeus. USA's first two draft probes completed input replay
but captured no complete projection records; their numerical oracle correctly
fails rather than treating empty data as success. The ordinary race path uses a
separate four-coefficient X/Z transform, selected by C8F5/E8A1, in addition to the
full nine-coefficient path. The direct-palette draw boundary was also one
instruction later than the draft expected.

Corrected local probe/oracle v4 verifies5,178 projected vertex buffers and44,652
ordered DMA quads across5,068 unclipped calls at3500..3550. It covers141 models,
256 object addresses,5,113 compact/65 full transforms and4,516 direct/662 lookup
palette paths. The110 clipped/special calls are excluded from the polygon oracle.
Control and probe preserve3552 inputs,1,751 camera samples,5,253 actual ADC
reads/timestamps and all three completed4K images. Raw operands stay local.

This remains a local prototype: promote bounded reusable capture/reference tools,
then implement the native USA codec and verify scene insertion, pending/future
residency and resource binding. Files are `usa-model-probe-v4.lua`,
`usa-oracle.py` and `usa-codec-v4` under the current diagnostic directory. Do not
reuse World's header or material layout. World2.5 road/ground decoding remains
a separate follow-up alongside cross-game work.
