# Exotica bounds integration proof

Run `python verify.py`. This recomputes the sanitized scene-clock/counter and
repeat-fingerprint comparisons, reports timing from those traces, and checks
archived source/receipt hashes. The traces contain no model bytes, RAM words,
texture/palette data, or model/source addresses. Geometry fingerprints are
compared; they cannot be recalculated without local generated geometry.

Actual driving routes, original resources, full geometry, GPU images and native
builds remain hash-bound receipts. These are observer/diagnostic results, not
extra live drawing, general occlusion, material lifetime or deployment approval.
