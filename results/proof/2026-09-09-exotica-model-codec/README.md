# Exotica model codec proof

Run `python results/proof/2026-09-09-exotica-model-codec/verify_archive.py` with
Python and Pillow. The verifier checks the archive and every member hash, then
recomputes five original input/camera/actual ADC-time traces, three selected
3840×2160 images per run, seven telemetry verdicts and four software-force checks.

The 182-file archive also contains qualified receipts for the native/Python
model oracle: 939 models, 13,876 input polygons and 8,126 exact ordered output
records across three scene windows, plus the frame-4700 repeat. Model geometry,
state, original resource equality, full 21-image coverage and native/GPU/build
execution are receipts; their raw game operands are deliberately not included.
No ROM, model, WaveRAM or raw geometry dumps are published here.

Source identity: `1f74e3a1f37d9c5ea06dc36595ffe640489ae2c48b6b98258c0b14d51055441c`.
Native: `eb17cf2dd0483e9e08907eb994643570977b289b`, separate candidate SHA256
`ee2bd4d0070f3b2126c9971b30074e1160bc3f4bece76839f30559a9cff0017f`.
All seven default cases and 257 Python/no-skip, 25 native, 32 GPU checks pass.

This does not establish extra Exotica scenery, future material residency,
occlusion, handover or cross-game 3x acceptance. Personal v0.5.0 is unchanged.
See the [review](../../../docs/reviews/2026-09-09-exotica-model-codec.md).
