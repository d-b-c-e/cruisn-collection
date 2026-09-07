# Global World distance trial — 2026-09-06

The global approach now has a useful short-term candidate: **160,000 units
(2× the original far limit), eight additional pending sections, normal CPU
clock**. It brings a mountain and the surrounding distant scenery into view
before the original renderer does, without any model or level allowlist in the
implementation. It remains an explicit World 2.4 experiment, not a launcher
default or a claim that pop-in has been eliminated.

Keep this candidate for a fresh attended recording and a second World level.
Do not jump straight to a full game port. For the longer-term goal of removing
conspicuous pop-in, the next engine investment is still a host-side static-scene
path: capture and verify the game's transforms, then render pending/future
scenery without changing the guest's simulation lists. The trial demonstrates
both a real visual gain and the limits of adding work to those lists.

The [comparison clip](../../results/proof/2026-09-06-global-distance-trial/bounded-scenery-comparison.mp4)
and [selected frames](../../results/proof/2026-09-06-global-distance-trial/bounded-scenery-comparison.png)
show original distance, 1.25×/lead 4, and 2×/lead 8. These are overview captures,
not pixel-accuracy evidence for the compressed video. Full-resolution frame 6040:
[original](../../results/proof/2026-09-06-global-distance-trial/fullsize-original-6040.png),
[2× candidate](../../results/proof/2026-09-06-global-distance-trial/fullsize-far2-lead8-6040.png).
The candidate has the mountain and buildings on the left where the control
still has sky. Traffic and the displayed game timer are not identical: these
pairs demonstrate earlier scenery, not complete scene equivalence.

**What was implemented.** Native commit `9ea71f601b3` adds a guarded World 2.4
experiment. `native/world_distance.h` is the canonical helper, synchronized into
MAME. The existing checked patch mechanism changes the shared far word and ten
projection-clamp instructions. Host memory supplies additional reciprocal-table
entries only at verified projection PCs; adjacent guest RAM is not overwritten
with a larger table. An independent shared pending-list threshold adds 0..8
sections. No object identity, mountain list, tree list, or track ID selects the
intervention. This mechanism still cannot draw objects that are not resident.

Supported far values are 80000/100000/160000. `MIDV_WORLD_FAR` enables the
experiment, `MIDV_WORLD_LEAD` chooses lookahead, and
`MIDV_WORLD_CPU_PERCENT` supports explicit 100/125/150/200 clock diagnostics.
Without `MIDV_WORLD_FAR`, no distance taps or distance log are installed.
The trial rejects other ROM revisions/games and simultaneous selective scenery.
The game's normal ROM files remain unchanged. The checked RAM patch is archived
alongside every replay/derived/attended case, preserving the existing widescreen
and terrain patch.

`world-distance.csv` records guard status and actual far/projection/pending
interventions with buffered output. Invalid code signatures or unavailable
diagnostic output fail the experiment. Its analyzer rejects missing/duplicate
frames, changed configurations, invalid counters and out-of-range projection
indices. The tested scope is cold-start recordings/replays; interactive reset
and save-state compatibility have not been certified for this experiment.

**Complete Germany matrix.** All six cases ran 8783 frames, with 146 native image
checks, 321 completed GL images at 512×451 (internal scale 4), 7281 camera samples,
and 21843 actual ADC reads. All frame input/time comparisons matched. All native
code guards held. The zero-extension control matched every recorded native
image. Candidate image differences remain FAILs against that original reference;
they have not been relabeled as visual correctness.

| Far / extra sections | Far-gate tests in the extra range | Extended reciprocal reads | Emulation speed, frames 1600..8700 | Callback p99 |
|---|---:|---:|---:|---:|
| Original 80000 /0 | 0 | 0 | 99.9997% | 27.627ms |
| 100000 /0 | 15032 | 560149 | 100.0000% | 26.481ms |
| 80000 /4 | 0 | 0 | 100.0001% | 26.377ms |
| 100000 /4 | 100206 | 2480984 | 99.9996% | 25.854ms |
| 160000 /4 | 107209 | 3053967 | 99.9999% | 26.365ms |
| 160000 /8 | 347915 | 7425141 | 100.0000% | 26.592ms |

These counters count repeated tests/reads, not unique objects or visible pixels.
Routes differ, so their totals are workload observations rather than a controlled
percentage increase in world geometry. Timing measures MAME frame callbacks,
not GPU presentation or wheel latency. Individual long callbacks still occurred
(including 73ms in2×/lead 8); a 100% average is not proof of stutter-free output.
The native trial did not reproduce the roughly 80% speed of the old heavy Lua
2× prototype. That old measurement was not a valid native-performance verdict.

**Why the old drive cannot be a complete visual oracle.** With far-only1.25×,
the camera differs briefly during selection starting 1619, matches again through
3099, and then diverges during driving. All actual ADC frame/value/PC sequences
still match in that far-only test. Therefore analog interpolation does not explain
every route change; altered game execution and dynamic object state also matter.

With lead 4, the first differing actual wheel sample is at frame 2299, PC 570B:
the read moves from 39.687093000000 to 39.687098800000 emulated seconds and changes
from `0x690000` to `0x680000` (105 to104 in the returned channel byte). The camera
differs at 2300. This is a measured 5.8-microsecond sampling shift despite identical
frame inputs. `compare_world_motion.py` now retains matching camera intervals and
the first actual ADC value/frame/PC difference instead of reporting only the
first camera mismatch. Camera equality alone still does not establish identical
traffic, physics, or the camera used by a completed rendered scene.

**Late, bounded comparison.** Additional diagnostic runs preserve the original
drive until 5900, then change projection/lookahead over 5900..6140. These reuse
the bounded Lua probes for object attribution and are not performance benchmarks
of the native implementation. Each run delivered 201 completed GL frames through
6300. The original-prefix control passed. Both candidates have matching camera
words through 6183 and identical 1263 ADC frame/value/PC sequences; timestamps differ,
and camera divergence starts 6184. Guest rendering phase and traffic can differ
even before that point. Later screenshots therefore remain mixed-state evidence.
The projection patch is restored after 6140; objects activated earlier are not
transferred back to their original lists. Restoration does not undo the changed
game history.

| Observed model | Original first submission | 1.25×/lead 4 | 2×/lead 8 |
|---|---:|---:|---:|
| Mountain CB1A8B | 6093 | 6037 | 5981 |
| Background CB2314 | 6119 | 6071 | 6005 |
| Forest CB2375 | 6119 | 6071 | 6005 |

For the mountain, 112 frames is about 1.93 emulated seconds. This is first
attributed submission, not first unoccluded pixel. Each listed model has one
observed instance per run in this interval, but earlier activation changes pool
allocation and therefore object addresses. The table compares model presence;
it does not assert identical simulation-object identity. A reusable native-scene
oracle should identify static placements by model plus world transform/section,
not by a recycled RAM address.

The 2× images show more useful advance visibility than1.25×. The 1.25× projection
also shows a more conspicuous changing mountain silhouette as distant vertices
encounter its clamp. Extending the reciprocal table changes already-visible
far-clamped geometry as well as newly admitted objects. Neither extra gate
admissions nor a smaller first projection alone proves a better complete drive.

Full-size control/candidate runs additionally completed 8/8 requested images each,
at 3824×2073, frames 6000..6140 every 20. Frame 6040 was inspected in both. The earlier
mountain is present at full resolution too. No blanket claim about all texture,
sorting, margin or later black-road issues follows from this narrow window.

**CPU clock.** A separate full matrix at 125% compares original distance and
2×/lead 8 with a matched clock control. Both run near 100% emulation speed. Clock
alone changes 138 of 146 original native snapshots and eventually the driven route.
In frames 3500..5800, both 100% and 125% controls still change camera pose 1150 times
over 2300 frame intervals. No measured cadence gain justifies shipping overclocking
here. Normal CPU speed remains the candidate setting.

**Reproduction and next recording.** These commands create new evidence and
never overwrite the attended source. A trial runner keeps launch completeness,
guard counters, image identity, camera/ADC comparison and timing as separate
results; successful completion is not visual acceptance.

```powershell
python harness/run_world_distance_trials.py results/diagnostics/world-germany-extended-20260906 --candidate E:/Source/mame-src/vunit.exe --output results/diagnostics/my-global-matrix --motion 1500:8780 --gl-frames 1600:8000 --gl-every 20

python harness/record_drive.py --game world --world-far 160000 --world-lead 8 --title "Germany global 2x" --with-ffb
```

The second command is for attended driving. It keeps saved display/wheel settings,
archives the composed patch and disables selective scenery for that recording.
Without `--with-ffb`, physical force stays off. All automated experiments in this
assessment used physical force OFF. Normal launcher preferences are unchanged.

Before promoting this into the launcher, get a fresh full Germany drive with2×/8,
then a second World 2.4 level. Compare against each new case on later iterations.
Inspect mountain/tree appearance, transmission selection, collisions and sharp
turns, and the later black-road window. The old attended cases remain immutable.
The next native milestone is an offline transform/clip/material oracle for a
whole static-object class, followed by host drawing and future-section decoding.
That shares work across levels without depending on individual object patches.

The [evidence directory](../../results/proof/2026-09-06-global-distance-trial/README.md)
contains the reports, source hashes, compressed raw traces and proof images.
Native binary SHA256 is
`050cf6ea393f1d44a1662ad191a5fc6d38be3084f49603ce8d7de2b379f736ce`.
The 114-patch export reconstructs native tree
`cb136368d9bcdbebc482fab6e27d1e702b95715b` from `mame0286`.

A separately archived2×/lead 8 case and its identity replay matched all 8783 frames
and 146 native images. Its parent comparison retains 120 changed native snapshots;
the source drive was not overwritten and route equivalence is not claimed.
The full-size record/replay used normal CPU speed and physical force OFF.
Driving speed was 99.7576% on the new recording and 100.0003% on replay, with
callback p99 of 26.588ms and 26.423ms. Their single worst callbacks were 312ms and
126ms respectively; average speed and repeatability do not certify frame pacing.
See [repeatability evidence](../../results/proof/2026-09-06-global-distance-trial/derived-repeatability.json).

All seven [default regression cases](../../results/proof/2026-09-06-global-distance-trial/default-regressions.json)
passed: USA original/widescreen, World 2.4 synthetic/Germany, World 2.5,
Off-Road, and Exotica (21 completed GL images). These verify the feature-disabled
paths across the four games, not the World-specific experiment on other titles.
All 79 Python unit tests and native helper arithmetic/profile checks passed.
[CI at 42f1635](https://github.com/d-b-c-e/cruisn-collection/actions/runs/34080307060)
passed all four jobs, including GPU quality. The shader pipeline was unchanged.
