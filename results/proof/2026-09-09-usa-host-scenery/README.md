# USA host scenery proof

Run `python verify_archive.py` with Python and Pillow. It verifies the archive and
file identities, then recomputes the declared checks from the archived data:

- Six original5,012-input runs and two4,502-input resource controls, with exact
  camera and actual ADC clocks.
- Ordered scene fingerprints and counters for2x/3x/repeat/observe.
- Selected completed3824x2073 images at3700,3800 and4900. All16-image comparisons
  remain separate hash-bound receipts; this archive does not recompute every image.
- Seven default telemetry and four software force policy/polarity checks.
- Source/check identities and the217 Python/18 native/32 GPU check receipts.

The native model/scene oracle, complete geometry, original resource comparison and
native/GPU builds are receipts. Raw ROMs, models, palette/texture operands and
hardware polygon dumps remain local. The verifier checks the recorded verdicts
and their identities; it cannot recreate those omitted inputs.

The candidate is native `4e565971954`, SHA256
`248aef7c5c56402ed117d52ef228cc3864d9f14dadbfaf654a025d4cb834f20b`.
Collection implementation is `492bf48`. The personal Stream Deck build remains
v0.5.0. No physical force or release/deployment is certified here.

USA2x adds scenery;3x currently matches2x because the pending list does not contain
farther eligible objects in this interval. Material lifetime, sky/foreground
occlusion, clipping, handover, future sections and four-game parity remain open.
Retained failures cover duplicate probe callbacks, differing replay/native frame
clocks and the first allocator draft's unsupported internal-RAM stack.

See [the review](../../../docs/reviews/2026-09-09-usa-host-scenery.md) for scope and
continuing work. The30-minute heartbeat is a recovery wakeup; active work proceeds
directly without waiting for its next trigger.
