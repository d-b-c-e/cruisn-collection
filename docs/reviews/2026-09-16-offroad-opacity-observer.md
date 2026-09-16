# Off-Road: completed opacity confirms occlusion in the sampled view

The Off-Road observer preserves its own projection rules instead of borrowing
World's clipping plane. Its3x transport accepts positive camera depths from503
through values below191,040. The hypothetical fade uses the nearer141,888-unit
sphere-admission boundary and an11,824-unit transition. Neither admission nor
displayed opacity changes. There is no new road classification or product option.

The shared64-byte packet now requires an explicit Off-Road profile at both CPU
and GPU. That profile rejects road/margin permissions, depths outside projection
bounds and a sphere-admission value substituted for the projection limit. It
never produces a far-clipping mask. Default World/USA decoding stays unchanged.
The existing independently qualified Off-Road depth calculation is enabled only
for this diagnostic. The ordinary ordered quad stream and current materials remain.

## One targeted El Paso pair

Both runs use frozen native e13ed764ed7. All3382 recorded inputs/native images,
1581 camera samples and6324 actual ADC reads match. All21 scene rows match except
six named duration fields. The original DMA/framebuffer/texture/palette capture
at3380 matches, as do all eight completed indexed/mask planes at3360 and all five
3824x2073 CRT captures3358..3362 on the4K primary monitor.

All21,065 metadata packets reach the GPU. The856 captured polygons at3360 match
independent Python reconstruction from the existing RAM/ROM snapshot, including
every ordered DMA and camera-depth word. Their depths extend beyond141,888,
up to167,308 in the prior saved-depth qualification. Zero packets invoke World's
far-coverage clipping.

The visible page contains603 host-owned fine pixels; the other has six.
**Neither page contains a partially or fully faded pixel.** The earlier isolated
host render had821 partial and9,976 zero-opacity pixels in this same scene.
Ordinary foreground drawing covers them in the actual completed frame. That
distinction explains why isolated geometry or submission counts would have
overstated a visible improvement.

No additional replay of this interval is justified. This is a negative result
for this particular final-distance fade, not proof that Off-Road never benefits
from3x: the existing full El Paso comparison already shows22 of66 images changing
between2x and3x. A useful fade needs a different, demonstrably visible boundary
and surface/handover qualification.

## Validation and next work

The shared native packet test covers both profiles, wrong-profile rejection,
the503/191040 bounds and preservation of vertices beyond sphere admission.
Ten focused mirror/metadata tests pass. Saved World and USA receipts revalidate
exactly with the generalized checker; no cross-game replay was necessary.
The new native opt-in path passed on its first control/observer pair.

Native SHA256 b33d91db38f19f412a41523e2264601bad9fbc78e52c078bd09a91b6fd0cfb6d,
260-patch tree6a7fb8edad8938e699d0fa518b451a9d3ad1a1ed. The candidate has an
executable-matched build attestation. Local evidence is under
results/diagnostics/world25-roads-20260914/offroad-opacity-live-off,
offroad-opacity-live-on, offroad-opacity-qualified.json and
offroad-opacity-prior-profiles.json.

Next inspect the remaining Exotica reset boundaries before another scenery
replay. Pending-work, pre-bootstrap and already-degraded resets still fail
strictly. They must not clear queued ownership merely to avoid an error.
The broader-track/attended visual and physical-wheel gates remain.

Personal Stream Deck87d/publicv0.5.0 stay unchanged. No deployment, release,
hosted CI, physical force testing or menu removal occurred.
