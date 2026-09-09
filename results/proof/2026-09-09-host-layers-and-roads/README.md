# Host coverage and road checkpoint proof

Run `python verify_archive.py` with Pillow installed. It verifies the archive's
hashes and recomputes selected 4K pixel comparisons, four input/camera/ADC/host
fingerprint comparisons, road template selection and final scalar render fields.
It also checks the capture-drain boundary receipt and local-check artifact hashes.

The archive preserves failed boot/capture/display attempts and the initial road
tag and synthetic-dither mistakes. Whole geometry/material/projection, native
build, remaining images and GPU checks are hash-bound receipts, not independently
rerendered here. No ROMs, raw game models/textures or personal settings are included.

The final native candidate is undeployed. Final 4K and seven-default renewal are
pending; cross-game 3x parity remains incomplete. See the
[review](../../../docs/reviews/2026-09-09-host-layers-and-roads.md) and
[morning handoff](../../../docs/OVERNIGHT-RESULTS-2026-09-09.md).
