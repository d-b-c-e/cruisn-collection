# Zeus margin and panorama evidence

This archive records the Amazon checkpoint-remnant fix and a separate bounded
panorama continuation. It does not claim extended-distance parity or complete
track coverage, and neither candidate is deployed to the personal Stream Deck.

Run `python verify_archive.py` from this directory. Python, NumPy and Pillow are
required. The verifier checks every archive hash and independently compares:

- Six dense Amazon input/camera/actual-ADC prefixes and selected 4K A/B/repeat
  images at frames 7200, 7214 and 7215.
- Two complete Amazon input traces and their full 7,060 camera / 21,180 ADC
  samples. The older original motion reference ends at 8850; comparison to that
  reference explicitly uses the shared interval. The two new traces also match
  all nine additional frames through 8859.
- An enabled Hong Kong input trace and its shared original motion interval.
- The preserved failed full repeat: a consumer timeout at frame 8460, with
  112 of 117 capture files; 111 report no drops and the final file reports a
  dropped state message.

All 31-image dense repeats, the successful 117-image full repeat, complete CPU
framebuffers, original hardware/resource equality, model geometry, native/GPU
tests, builds and seven-default regression results remain hash-bound receipts.
Their raw game resources are deliberately excluded. The verifier checks those
receipts but does not reconstruct their missing private operands.

Page clearing alone removes the old post but exposes a sky gap. The panorama
candidate fills that gap with copies at the existing tile scale. Selected
central-screen pixels remain exact. Unsupported Hong Kong panorama recognition
is a retained limitation; the enabled sampled images are unchanged there.
Ground geometry missing from the submitted scene remains a separate problem.

The archive also retains the initial GPU-fixture failure, explicit motion-window
mismatches, and scalar model-lifetime/depth studies. The future-model studies
describe sampled format and resource consistency; they do not certify queued
upload readiness, ownership, occlusion or a working 3× renderer.
