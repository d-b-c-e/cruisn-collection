# Off Road distance checkpoint proof

92 derived files, archive SHA256
`b6295bb08e60a39b6b8f2e8ed06919ad4b5df6c99ec789db87dc3e95c4445c2d`.
Run `python verify_archive.py` without ROMs. It recomputes five distance/input/
camera/ADC comparisons and the matched scene's ordered quad hashes. Completed
GL and raw texture/palette equality are bound run receipts; their original BMPs
and RAM captures remain local.

Original controls pass.1.25× adds15 sampled pixels;2×/3× each add220 across42
completed512×451 images, with no sampled3× gain. Camera/ADC values remain equal,
while timestamps and original pixel identity differ. The strict geometry verdict
remains FAIL:715 unchanged quads retain their order, one changes coordinates,
and23 others are added. Lua instrumentation slows the larger runs substantially.
No product performance or attended acceptance is claimed.

The resource-read attribution and limit-reinitialization failures are retained.
Native8b151aa9c2f/SHA638 is unchanged; every archived invocation disables physical
FFB. No ROM, raw texture data, emulator binary or original INP is included.

Review: [Off Road global distance](../../../docs/reviews/2026-09-08-offroad-global-distance.md).
