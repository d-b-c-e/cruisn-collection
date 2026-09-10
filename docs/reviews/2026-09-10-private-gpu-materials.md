# Private Exotica GPU materials — September 10, 2026

The diagnostic candidate adds `--exotica-host-materials observe|off` alongside
the bounded scene observer. It uploads owned texture-memory changes and private
palette rows to separate GPU textures. It does **not** draw extra scenery.
Absent options preserve original recording behavior and install no material cache.
Physical force must be zero, an explicit candidate is required for overrides,
and native rendering without the enhanced GL consumer rejects the request.

HMT1 wraps the checked PIM1 image update, scene/frame identity and explicit RGB555
palette rows. The producer advances its image only after the complete packet has
entered the renderer's queue. The consumer checks the matching generation and
each palette's colors against the proposed WaveRAM image before committing.
Unsupported palette layouts fail closed. Changed consecutive 4 KB pages upload
as texture rows; no UV footprint estimate is involved.

Private resources use separate texture units and do not flush or close the
original sky span. The original WaveRAM mirror, palette slots and depth resources
receive no private writes. Selected snapshots read back the entire private GPU
WaveRAM and active private palettes, compare them with owned CPU bytes, and check
the original GPU texture and palette images before and after the private update.
Ordinary updates check GL errors and command ordering; snapshot readback is the
separate completion check. There is no claim that every frame is read back.

Producer and consumer CSVs must match every scene, generation, page/palette count,
payload size and image hash. The independent Python verifier checks queue drain
and sampled texture/palette bytes against the device snapshot and scene instance
bindings. The full-packet budget is explicit and below the 64 MiB native ring.

## Candidate and observed acceptance

Native `99442f1a7b6ed6079a40d315feb067c03c89ddfa` is separately built and pushed.
Frozen executable: `build/candidates/99442f1a7b6/vunit.exe`, SHA256
`70a190d7bc732a42848644cfaf5becb777a749b3468699712d7f4219bf6a8c40`.
The163-patch export reconstructs tree`d6dd3cc96b336080b35b084b9299cc62af89e07b`.
Final315 Python tests,38 native programs and109 commands pass at source identity
`c663201f86c493c380235b37476d3d58e55e22149ec701617af16ad8ac5aa3d2`.
All seven default regressions now pass on this candidate, including actual UDP
versus memory, four software force checks, full Germany and Exotica's21GL images.

Seven6000-frame material trials pass: Amazon5072/repeat and5978 at1×/2×/3×;
Hong Kong5000 and5990 at3×. Each preserves4191 camera samples and12573 actual ADC
reads/times, ten original capture files, and independent scene/context/geometry
checks. All123 requested4K images match the controls. All17199 producer/consumer
updates agree; each run has2457 scenes. The5072 repeat also matches every queue
identity/hash/count and the selected complete GPU WaveRAM/palette/packet bytes.
Snapshots contain0/11/23 palette rows for Amazon5978 at1×/2×/3× respectively.

The first5072 replay passed, then its LOCAL postcheck script failed with a Python
`NameError` in a tuple comparison. That failure is retained. The corrected
postcheck verified the same immutable run; the emulator trial was not relabelled
or silently rerun. Public proof under
`results/proof/2026-09-10-private-gpu-materials` recomputes sanitized queue and
clock comparisons. Raw game resources, image bytes and geometry remain local;
those checks and the native builds are hash-bound receipts.

## Performance remains open

Amazon's3501..5990 interval runs at81.66%/81.51% with private materials, compared
with87.05% for the earlier bounds control. These runs include observer work,
regular raw snapshots, telemetry and selected GL/resource snapshots. They do
not establish smooth gameplay. Hong Kong outside its dense capture window is
approximately100% on the same candidate.

The first full image costs about49ms on the producer and25ms on the consumer.
Later material staging averages1.411ms; GPU upload averages0.208ms outside the
selected snapshot. An88.357ms GPU upload at5064, the first GL-capture frame,
remains unexplained. Separate runs with GL/model/material snapshots disabled
are in progress; regular harness raw snapshots still occur every60frames.

A LOCAL selected-page prototype matches1000 synthetic full-scan packets and
401 generations using two captured Hong Kong images. The measured update step
averages0.030ms versus1.332ms for a full scan, with packet bytes identical.
Dirty marks were derived offline, and the benchmark ran alongside the default
regression suite. This is not validation of live emulator write tracking.
Next: track every WaveRAM write, account for save-state restoration, clear marks
only after enqueue/commit, and compare against the full-scan oracle before use.
Initial image cost still needs separate initialization/prewarming work.

Personal Stream Deck remains v0.5.0/SHA87d04de4. No deployment, release, hosted
workflow, physical FFB, World tuning or experiment-menu removal. Following this
material and performance gates, continue directly to guarded live scenery insertion, private depth,
foreground occlusion and handover. Earlier-source eligibility remains necessary
for Amazon's missing left-margin ground.
