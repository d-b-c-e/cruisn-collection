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


## Callback analysis preparation, September 17

The analyzer now separates event bucket count from callback count, reports total
callback time and a callback-weighted mean, and retains the ten largest buckets
with exact native frame/scene and callback count. A bucket duration must not be
presented as the maximum individual callback latency. This makes the pending
measurement useful for distinguishing a large object burst from expensive
per-object tracking without joining unrelated clocks.

Three focused parser/receipt tests pass, including unequal bucket counts and
pre-scene events. Reanalysis of the existing 23,736-row remaining-profile control
passes unchanged; it correctly reports no lifetime event coverage because that
older binary did not capture it. The new report is
`timing-event-analyzer-existing-control.json`; original reports are preserved.
No game rerun or native build was performed for this analyzer change.

## Saved callback cadence, September 19

The shared rig coordinator confirmed that the earlier reservation expired and
the new timing replay is queued, not granted. The frozen native and frontend
candidates remain untouched. Current Windows inventory contains one primary
3840×2160 display, now named DISPLAY1. The existing Zeus `--compare-gl` path
explicitly chooses the monitor matching the reference dimensions; it does not
depend on the old DISPLAY2 name in the recording.

`harness/analyze_frame_cadence.py` now checks an existing callback trace against
its actual snapshot acknowledgments and saved invocation. The logger timestamps
before taking a snapshot, so immediate snapshot cost appears in the next
callback interval. The analyzer validates consecutive frames, finite monotonic
host time, complete requested coverage and snapshot cadence, and preserves
source hashes. It refuses an emulated-clock discontinuity within the requested
window and refuses to overwrite a prior report.

For the existing `remaining-profile/run`, frames3700..5690 contain1,991intervals:

| Group | Intervals | Over25ms | Maximum |
| --- | ---: | ---: | ---: |
| All callbacks | 1,991 | 17 | 35.514ms |
| Immediately after acknowledged snapshots | 33 | 0 | 19.362ms |

This rules out immediate scheduled-screenshot work as the source of those17
long intervals. It does not exclude delayed I/O, logging elsewhere, scheduling,
or graphics costs, and callback time is not presented-frame or wheel latency.
No native scene-clock alignment is inferred. The pending lifetime measurement
still matters; even cheap install/remove callbacks would not alone rule out
deferred address-cache effects outside their timer boundaries.

Three focused tests pass: correct next-callback attribution, missing evidence
and coverage rejection, and corrupt/discontinuous clocks or duplicate frames.
The retained report is `remaining-cadence-20260919.json` under the timing evidence
directory. No new game run, native build, deployment or physical FFB test.
