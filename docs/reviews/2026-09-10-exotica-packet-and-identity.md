# Exotica packet cost and scenery allocation identity

The bounded packet serializer preserves existing rendering. The new allocation
study also connects predicted future scenery to original objects as they fade
in. Neither change establishes a finished host fade transition or full-speed 3×.

## Packet serialization

Collection commit `7282583` replaces repeated byte-vector growth with one bounded
allocation and explicit little-endian writes. Material and polygon validation
remain in place, and rejection preserves the caller's existing output. The wire
format is unchanged. Five isolated captured-packet benchmarks showed 45–61% less
encoding time; that result does not measure the complete renderer.

Native `431f4810a86` contains the serializer change. The later, separately built
`583481f8283` also contains the isolated Off Road final-section correction. It is
the candidate used for renewed Exotica comparisons, SHA256
`eb4d790ddb8c84a6488cc43b89fe7f7528f1fb78e74004c677d302e87f31b850`.

Full Amazon 2× and 3× comparisons preserve all 8,860 input frames, 7,060 camera
samples and 21,180 actual ADC reads and emulated timestamps. Ten original
resources match. Both runs reproduce the previous candidate's 233 completed
3840×2160/CRT images, 14 internal buffer snapshots, five immediate insertion
packets and all 6,953 ordered scene/material records. Five independent geometry,
material and GPU insertion comparisons pass per run. The new 3× repeat also
preserves the original route/resources and reproduces all 233 displayed images,
14 internal snapshots, five immediate packets and 6,953 ordered records exactly.
Its five independent insertion comparisons pass as well. Across the three new
runs, 699 completed 4K images and 15 independent insertions are checked.

The first new uncaptured 3× run measured 89.31% emulation speed. A fresh previous-
build comparison measured 88.90%; the new repeat measured 89.41%. Earlier tests
of the previous build measured 90.79%, so comparing the new run only against that
older measurement would falsely suggest a large regression. The current paired
samples show a small difference, insufficient to claim a substantial end-to-end
gain. Both remain below full speed. These runs retain ordinary input/session and
summary diagnostics, but no completed GL, model or private-buffer readbacks.
The paired 2× comparison measured 94.03% for the new build and 93.80% for the
previous build. It likewise shows only a small improvement, with full speed and
frame pacing still unresolved.

The queue timer includes packet construction and submission, and overlaps total
material time. GPU-side host time also includes preparation and submission; it
is not a GPU execution timer. Scene construction, full geometry fingerprints and
consumer-side processing remain important targets. Do not add overlapping phase
timings or extrapolate the isolated encoding percentage to game speed.

## Original allocation-to-fade joins

A bounded read-only probe on unchanged native `9ed` records 4,018 completed
section allocations over the Amazon drive, including 3,221 uses of previously
observed RAM slots. All 2,539 sampled original fade updates join the latest
observed allocation at that slot, covering 116 distinct allocations. There are
no unowned fades in these windows. The canonical native and independent Python
fade implementations reproduce every write, including 86 completions.

The original route/ADC values and timestamps remain exact, as do all 21 completed
4K images in the fade-control window. This is a read-only study, not a new fade
policy running in MAME.

Position, rotation, model descriptor, initial material bindings, radius and
section progress remain stable across these observed fades. Linked-list data,
scratch fields, the packed fade value and several other fields change. A RAM
address alone is therefore inadequate as a lasting scenery identity. The read
at `67C4` used by the probe supplies the section matrix pointer at a known
allocation-stage instruction; it is not a general free-list allocator hook.

Three retained scene snapshots independently reconstruct 4,286 source records
each. C++ and Python match all records. Each reconstruction then matches the
initial fields of all 3,932 ordinary allocations observed during this drive;
86 custom allocations remain excluded. The earliest snapshot predicts 2,846
allocations that occur later. All 2,539 faded-object geometry/material/progress
observations also match their source definitions at each of the three snapshots.

This establishes a useful correspondence between predicted future descriptors,
actual allocation and the sampled original fade. It does not establish texture
pixel lifetime, arbitrary allocator reuse, track/bank changes, or a complete
host-to-original handover. Initial binding addresses matching does not prove
that the resources behind them remain unchanged.

## Next rendering change

Use an explicit lifetime keyed by track/bank, section and source, with allocation
generation and current render-operand checks. Keep a separate host fade clock
based on emulated progress. Verify what happens when the original allocator
admits an already visible extended object: simply removing the host copy would
restart visibility at the original low alpha, while blindly blending both
copies can alter brightness. Original texture/palette ownership, foreground
depth and complete-page ordering must remain checked.

The next bounded prototype should first observe that handover and slot reuse,
then exercise private-target fade/continuation against independent pixels and
the original full drive. It must continue excluding unsupported descriptors.
No per-model or per-level allowlist is needed for the verified ordinary sources.

Raw inputs, game operands and images stay under local
`results/diagnostics/exotica-amazon-20260909`. The
[public checkpoint](../../results/proof/2026-09-10-exotica-packet-and-identity/README.md)
recomputes source/file identity, capture coverage, saved image-hash equality and
scalar-receipt consistency. Actual game execution, raw pixels, geometry, fade
writes and native/GPU comparisons remain receipts in that archive.
The personal Stream Deck build and
public package remain v0.5.0. Automated physical FFB remains zero. The latest
source checks are 352 Python tests without skips, 48 native programs and 136
commands at source identity
`6c2c6e3f99c291f00912158a028ccda89f4272b05c86941b14f7f73a886cd315`.
The last clean seven-default gameplay suite still belongs to native `50a`; the
later USA menu stall remains open. No deployment or release acceptance is added.
