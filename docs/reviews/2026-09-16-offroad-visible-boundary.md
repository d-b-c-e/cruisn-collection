# Off-Road: visible 3x gains do not identify an outer fade boundary

The existing full El Paso comparison selected2520 and8760 as useful visible
3x-versus2x views. Saved8760geometry rules out this fade before replay: all516
quads are nearer than107893units; the proposed envelope begins130064. Its93
additional3x quads therefore receive full opacity. No game was run for8760.

One2524-input observer run captures the earlier2520view. Original input/time/
native snapshots,723camera rows and2892actual ADC reads match the accepted
drive. The completed3824x2073 CRT image is byte exact the prior full3x capture,
and was inspected: early El Paso gameplay, race time0:02.90, foreground/HUD intact.
All1482ordered DMA/depth records match independent reconstruction from the new
scene RAM/ROM;17684metadata packets reach both FIFO boundaries.

The completed visible page has46706host-owned fine pixels, but neither page
has any partial/zero opacity. Scalar geometry contains51partial-envelope quads
and one fully-zero quad; they do not survive into completed opacity. A positive
geometry count would again have overstated the visible usefulness of this fade.
This is one frame, not temporal acceptance. No separate original-resource
control was captured here and no displayed fade was applied.

## Reusable screen

harness/offroad_fade_screen.py reconstructs2x/3x from explicitly selected saved
resources, checks the exact ordered2x subset and reports both whole-scene and
additional3x depth envelopes. It decodes C31 words as C31, not integers or IEEE.
Zero geometry eligibility can avoid a pointless replay; positive eligibility
still requires completed visibility and ownership. Two focused tests cover
numeric-domain/extent rejection and envelope boundaries. Actual2520/8760 pass.

Local evidence: world25-roads-20260914/offroad-outer2520, its qualified report,
and offroad-outer2520-screen.json/offroad-outer8760-screen.json. Candidate remains
083ceb32407. No new build, fade option, deployment, release or physical FFB.

## More promising next coverage work

The saved2520future census has a large excluded0x00800000 class:657descriptors.
209 have plausible ordinary-position depth within3x, but that position calculation
is only a screening heuristic for this excluded class. Seven model pointers occur
there, mostly four-vertex/single-polygon models. Their flags use the separate bit4
billboard path, which the ordinary host transform rejects.

Actual saved code confirms bit4 dispatch at1CA7/1CA8 to1D61, copying a separate
current basis from1120E before projecting. Loader post-hook9C8C also consults
persistent hit-state bits and can change orientation/flags, so blindly clearing
exclusion flags would be incorrect. Next capture and reproduce the original
billboard transform/projection, then qualify undamaged source state and current
materials before attempting earlier drawing. This targets a whole object class
rather than individual models or tracks. No claim that these are all trees or
that they explain the user's remaining pop-in has yet been established.
