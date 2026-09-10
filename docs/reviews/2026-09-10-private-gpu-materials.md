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

## Candidate and pending acceptance

Native `99442f1a7b6ed6079a40d315feb067c03c89ddfa` is separately built and pushed.
Frozen executable: `build/candidates/99442f1a7b6/vunit.exe`, SHA256
`70a190d7bc732a42848644cfaf5becb777a749b3468699712d7f4219bf6a8c40`.
The163-patch export reconstructs tree`d6dd3cc96b336080b35b084b9299cc62af89e07b`.
Initial315 Python tests,38 native programs and109 commands pass before export;
the final source-identity run and live Amazon comparison are next.

Live acceptance is **pending**. Preserve any failed trial. Then compare Amazon
and Hong Kong original motion/ADC timing, resources and4K images; independently
check scene geometry, queue repeatability and sampled GPU materials. Separate
initialization, snapshot I/O, steady CPU cost and GPU upload time. The last
seven-default acceptance remains native86deac, not this new candidate.

Personal Stream Deck remains v0.5.0/SHA87d04de4. No deployment, release, hosted
workflow, physical FFB, World tuning or experiment-menu removal. Following this
material gate, continue directly to guarded live scenery insertion, private depth,
foreground occlusion and handover. Earlier-source eligibility remains necessary
for Amazon's missing left-margin ground.
