# World future-section scenery proof

Run `python verify_archive.py` here. Python and Pillow are required; ROMs and an
emulator are not. The archive contains derived traces and six completed gameplay
images at their original 3824×2073 resolution.

The verifier recomputes five full Germany input/camera/ADC and scenery-fingerprint
controls, CPU timing, three selected pixel comparisons, 6,823 scalar flag/material
descriptors, 166 partial-loader frontier comparisons, 2,686 World 2.5 allocation
membership decisions and seven telemetry/four
force-policy verdicts. Local source/check identities and evidence hashes are
validated. All automated physical force was disabled.

Full position/orientation reconstruction, model polygons, hardware draw order,
VRAM/textures/palettes, the remaining GL comparisons, native arithmetic vectors
and build results are hash-bound receipts. Raw ROM/code/model/resource dumps are
excluded. The archive cannot independently rerender a complete native scene.

Future 3x adds visible scenery over future 2x in 16 of 31 sparse samples and
repeats all 31 completed images. **Visual acceptance fails:** the dense tunnel
pair exposes a new thin green line across the road at frame 4408. This failure is
retained alongside original DMA/resource equality. Late material invalidation
also excludes 416 descriptors in 118 scenes; the four earlier snapshots did not
cover that state. The initial World 2.5 reference wrongly assumed every allocation
was pending; a separately captured control/limit correctly predicts 390 active
and 2,296 pending allocations. The original 390-mismatch report stays explicit.

The renderer still excludes road-chain/custom codecs. Distant ground gaps,
occlusion, material lifetime, clipping and handover acceptance remain incomplete.
Other games are mapping work, not accepted
3x implementations. No menu removal or deployment is implied.

Native candidate `de1d6333cd9918305d9b1d300c357d2dca5a3abf` has SHA256
`0f947fd500385cbab10bd68a857703f2659d7dcdfc1b8334bcae52d5cdc4b0d1`.
Stream Deck remains on the v0.5.0 native SHA `87d04de4…`.
See the [review](../../../docs/reviews/2026-09-09-world-future-sections.md).
