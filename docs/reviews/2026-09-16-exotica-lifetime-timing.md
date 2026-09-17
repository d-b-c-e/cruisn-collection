# Remaining Mars pauses: narrow the unmeasured cost

The new `remaining-profile` replay uses the already-recovered Mars recording,
with the same continuous3x controls and native1fccd423f39. It measures frames
3700..5690 once. All8209 inputs/times,136 native snapshots and four completed4K
images pass; displayed images remain100.0000% exact. Continuous ownership and
drained/joined shutdown also pass. No new attended recording was needed.

The23736 phase rows contain1978 instances of each measured phase. Source-cache
work peaks at0.205ms, future texture staging at0.060ms and future queue submission
at0.173ms. Future geometry peaks at4.341ms. Several repeatable30–35ms callback
intervals have only a few milliseconds of nearby measured scenery work. This
rules out those measured phases as the complete explanation; callback timestamps
and native scene frames are separate clocks, so proximity is not an exact join.
`remaining-pauses.json` preserves the three CSV identities and shared spike frames.

Source review found dynamic memory-tap installation/removal for each newly bound
scenery object. These operations invalidate emulator address-space caches, but
their cost has not yet been measured. Do not call them the cause of the pauses.

Native4df727db105 extends the existing bounded profiler with `lifetime_install`
and `lifetime_complete`. Repeated callbacks aggregate into a scene/frame bucket;
units counts callbacks. Scene0 is valid for these events before the first scene.
No hot-path allocation or file writes are added. Regular scene phases still reject
duplicate rows. One native buffer/bounds test and three Python tests pass; the
local build and268-patch export pass. No renderer or ownership policy changed.

Candidate SHA256:
`60aa7de2ba894f09143e4d9408de24d92ada97e91b1319c271a0e2f8dee3162c`.
Evidence is under `results/diagnostics/exotica-mars-timing-20260916`.
`export-lifetime-timing.py` has already run; do not rerun it.
Live qualification of this additional measurement is pending a serialized rig
slot coordinated with the overnight UX task. The previous qualified candidate
remains1fccd423f39. Personal87d/publicv0.5.0 are unchanged.
