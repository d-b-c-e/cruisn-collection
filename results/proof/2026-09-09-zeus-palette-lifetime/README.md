# Zeus palette lifetime evidence

Run `python verify_archive.py` with NumPy and Pillow installed. The archive holds
245 publishable files, including lossless selected4K images, input/camera/actual
ADC traces, source hashes and verification receipts. Raw ROM/model/palette,
framebuffer and WaveRAM operands remain local.

The verifier recomputes twelve original Amazon input/motion prefixes, selected
palette corrections at3600/4200, equality with the original good3600 image, and
preserved failures. Complete70-image dense repeats and49-image shutdown repeats
are hash-bound comparison receipts; only selected images are included as pixels.
Native geometry/resources/CPU rasterization/GPU/build and seven-default results
are also receipts, not independently rerun by this archive.

The palette trials use nativef537/SHA37515ca7. The subsequent shutdown candidate
5a80/SHA66b0132e preserves their49 corrected images and passes all seven default
cases. Both are isolated; personalv0.5/SHA87d04de4 remains unchanged.

The retained47/49 capture failure led to a bounded diagnostic drain. Its boundary
case finishes49images; a stopped consumer still fails immediately. A separate
CPU-oracle fixture catches hidden-page color/depth mismatches even when the
displayed image matches. Passing helpers alone does not establish gameplay.

This evidence fixes reproduced palette corruption near game0:09/0:19. It does
not close the later marked Amazon margins/rectangle or establish extended
scenery, physical FFB, every-track acceptance or deployment readiness.
