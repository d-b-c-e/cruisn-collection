# World host scenery: tracing cost and full-drive section evidence

This is the first September 9 overnight milestone toward useful 3x scenery across
all four games. It improves the World diagnostic foundation; it does **not** add
future scenery, establish a cross-game distance feature or justify removing older
experiments. v0.5.0 remains the published and personal Stream Deck baseline.

## Separate candidate and logging mode

Native `c1ef52c2dccfd9ccc2f4a9e0e6f30516b17036b3` is built separately and pushed.
Candidate SHA256: `41b0fdf35edf3c61ec2448721a5d283061f1e310c794028a0ec1e83fd5c01690`.
The 135-patch export reconstructs tree `1cab12fd29e633d412b0b07a1ccd6ac37a3855c6`.
Personal root native remains v0.5.0, SHA256
`87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8`.

`--world-host-log summary` on replay/derive selects `MIDV_WORLD_HOST_QUADS=0`.
It retains scene counts, an ordered polygon fingerprint and phase timings while
omitting per-polygon CSV formatting. Explicit `quads`, and the older default when
the option is absent, preserve full geometry tracing. Recorded settings retain
the mode; unsupported values fail. The ordinary game path still installs no host
scenery hook when the experiment is disabled.

The native helper fingerprints the exact flattened 16-word polygons using
little-endian FNV-1a. The analyzer independently reconstructs those fingerprints
from detailed CSV records and can require equality with `--require-host-equal`.
This is a compact diagnostic receipt, not a cryptographic replacement for retained
geometry. Detailed geometry and independent projection checks remain necessary.

Timing separates revision guards, geometry preparation, packing/fingerprinting,
polygon logging and GPU submission. `previous_scene_log_us` explicitly attributes
the previous row's scene-CSV write, which cannot time its own write in the same
row. The final row's write/exit flush and unrelated emulator work are outside the
callback total. GPU submission measures CPU enqueue time, not completed GPU latency.

## Full Germany controls

All five runs finish the original 9,269-frame recording with its 154 native
snapshots. Camera data and actual ADC values **and timestamps** match. The four
captured runs contain 31 completed 3824x2073 client images on the 3840x2160 monitor.
The last run omits GL screenshots, while retaining the ordinary native recording
snapshots and diagnostic traces; it is not an entirely uninstrumented game.

| Mode | Host callback p99 | Maximum callback | Emulation ratio, frames 1800–9260 |
|---|---:|---:|---:|
| 3x, full polygon CSV | 1.566 ms | **16,126.929 ms** | **88.633% — timing FAIL** |
| 3x, summary | 0.305 ms | 0.631 ms | 99.953% |
| 3x, summary repeat | 0.329 ms | 0.860 ms | 100.004% |
| 2x, summary | 0.314 ms | 0.671 ms | 99.832% |
| 3x, summary, no GL screenshots | 0.295 ms | 0.450 ms | 100.005% |

The long pause falls inside the polygon logging phase: 16,126.635 ms. Preparation
in that entire run peaks at 0.641 ms, and submission at 0.110 ms. This locates the
newly observed stall in logging, but does not identify an OS/filesystem root cause
or retrospectively prove what caused the old unpartitioned 120 ms outlier.
Wall-clock phase measurements include scheduling interruptions.

Summary 3x preserves all **663,078** polygons across 3,731 scenes. Its ordered
fingerprints match the detailed run and repeat, including the no-GL-screenshot run.
Detailed polygon CSV bytes also match the previous native 3x control exactly.
All 31 completed images match between old/new detailed, detailed/summary and the
summary repeat. The visible scene is unchanged by the tracing improvement.

The 2x run has 662,946 polygons. Its 31 sparse images match 3x despite 132 extra
polygons in 3x. The earlier dense mountain-window evidence remains the evidence
for their brief visual benefit; sparse equality does not erase that result.
No new texture/RAM/DMA dump comparison or occlusion acceptance is claimed here.

Evidence and recipes: `results/diagnostics/world-host-cost-20260909/`.
`cost-comparison-v2.json` explicitly retains the detailed control's timing failure
while requiring the summary runs to meet 99% emulation speed. The earlier comparison
report checks geometry/motion separately and is preserved.

## Broader section placement

The read-only section probe now supports a bounded full-drive interval, up to
12,000 frames. The Germany control independently reproduces XYZ, heading, section
matrix and object yaw for **8,222 allocations across 92 section records**. It covers
**46 section orientations and 970 extra-offset placements**, with no mismatch.
The original replay passes. This replaces the earlier two-orientation/no-offset
coverage gap on this route, not every possible track/layout case.

The yaw fixture grows from two to **137 distinct actual numerical inputs/results**,
including object and section rotations. It contains no model, texture, section
definition or placement-position data. The original vectors and their provenance
remain intact. Model/material initialization is a separate acceptance problem.

## Material-binding investigation

The first write probe started at the existing placement boundary, after the main
allocator call. It captured only 410 later writes across 8,222 objects. Their final
values match the ready objects, and no change within that interval lacks a write,
but most texture/palette assignments were already complete at entry. That limited
PASS must not be described as complete allocator coverage.

The second probe moved the entry point earlier but incorrectly treated AR4 as the
new allocation's owner during the initial stores. The allocator returns AR0; the
caller copies it to AR4 only after those stores. This retained another 410-write
trace with **incomplete allocator coverage**, despite its original replay passing.
Replay equality alone did not validate the diagnostic interpretation.

The corrected third probe captures both initial fields for all **8,222 objects**:
**16,444 initial lookup writes plus 410 later writes**. Each initial value matches
its independent table lookup; the last observed write matches the ready object's
field. No changed field lacks an observed write. Original placement records,
camera samples and actual ADC values/timestamps remain exact. Guards cover the
model-argument read, allocator stores, owner and relevant instructions. Reads are
bounded and reentrancy-protected; the probe writes no guest state.

The initial binding is a general model-header lookup, rather than an association
with a particular model or metadata flag:

```text
palette = memory[memory[0x4151] + model[-2]]
texture = memory[memory[0x4150] + model[-1]]
```

The fields are stored at object offsets 16 and 17, with observed callbacks at
0x6266 and 0x6269. A signed metadata value shifted right by 20 can override the
palette through the same table; 399 later writes use that path. Eleven other
material writes come from special class handlers. Identical metadata flags can
resolve to different bindings, so flags alone are not a material decoder.

This is the mapping at the captured allocation boundary, not proof that every
future model's resource is already resident or every class is static. In particular,
special type 0xB processing continues after the current 0x7C1C boundary and adjusts
other object fields. Later animation, special handlers and resource lifetime need
separate coverage before those paths can be drawn safely from host-owned data.

## Candidate checks and archived proof

All seven default regressions pass on candidate `41b0fdf3…`, including actual UDP
telemetry versus independent memory, four force-policy/polarity verdicts and 21
completed Exotica 4K images. Physical force is disabled. The suite began at source
identity `acf7c0b4de4d2289006c6eb68e48865d8371fd0619b48292738c2d6ab07ea660`.
Exactly three later files changed: the allocation probe, its analyzer and its test;
the complete before/after source maps bind that difference. No product or default
regression probe changed after the suite began.

Final local checks pass **199 Python tests with no skips**, 14 native helpers,
10,081 C31 vectors, 137 yaw vectors, 24 GPU fixtures and all 39 commands. The final
299-file source identity is
`d4237a33c3d590ac4b12fb3eac44f459f64392a6a20370074e50d7283161844d`.
No hosted workflows were run.

[ROM-free proof](../../results/proof/2026-09-09-world-host-cost-and-sections/README.md)
contains 145 derived files. Its verifier recomputes scene counts/fingerprints,
timing, original input/camera/ADC equality, yaw vectors, scalar binding equality
and the seven telemetry/four force verdicts. Full placement, ownership, resources,
geometry, GPU images and build results remain hash-bound receipts. Raw section
definitions, model/texture data and disassembled ROM dumps are excluded. The
detailed timing failure and both incomplete early binding probes stay explicit.

## Next work

Verify metadata overrides and the final static-class flags, check future material
residency, then implement PC-owned future-section storage and drawing using the
verified lookup and placement math. Keep allocation special cases explicit rather
than silently treating every section definition as a static mesh.
Retain proper occlusion/handover, stock simulation and per-revision guards before
extending to World 2.5, USA, Off Road and Zeus. The current options remain in place
because this milestone has not replaced their useful rendering behavior.
