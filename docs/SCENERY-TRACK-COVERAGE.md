# Recorded track coverage for extended scenery

Updated September15. Full attended Amazon and El Paso recordings are now retained
and have candidate comparisons. Scripted routes remain useful but do not establish
whole-track or cross-track correctness. Keep existing cases; add contrasting
attended drives separately. Current acceptance is summarized in the
[parity status](reviews/2026-09-15-parity-remaining-work.md).

## Ready recording presets

Close any running game first. These commands use the personal stable executable,
preserve saved display and wheel preferences, and show the external emulated-time
clock in the upper-left corner. Physical FFB uses the saved strength only during
the attended recording. Playback always disables physical force.

From the repository root, record **one game at a time**:

```powershell
python harness/record_drive.py --game offroad --title "Off Road - El Paso - full drive" --offroad-distance 0 --with-ffb
```

```powershell
python harness/record_drive.py --game exotica --title "Exotica - Amazon - full drive" --exotica-visibility off --with-ffb
```

The title does not select the course: choose that course in the game. The helper
creates a new timestamped case directory and prints its path. Omit `--with-ffb`
for a recording without wheel force. These commands disable the respective
guest distance/visibility trial for this recording, without changing saved
preferences. Use a normal terminal without developer environment overrides.
The experimental host renderer is tested later with a separate candidate.

Drive from selection through the finish and leave the results screen visible
for roughly ten seconds. If the timer ends first, retain that attempt and label
its actual extent; do not call it full-track coverage. Include ordinary steering,
turns, hills and traffic. A clean first drive makes distant scenery easier to
inspect; collision-heavy coverage can be a separate case. Report defects using
the external seconds/frame display and a short description. End with F12 or
the exit menu, then wait for `recording recorded` before starting the next game.

## Coverage queue

| Game / revision | Existing route evidence | Next attended coverage | Status |
|---|---|---|---|
| USA 4.5 | Human LA Freeway route; separate candidate comparisons | Full route through finish, then a contrasting course | Broader coverage pending |
| World 2.4 | Full human Germany route | New York through finish, including distant black flashing | Recording pending |
| World 2.5 | Scripted prefix and host comparisons | Full human route; retain revision identity | Recording pending |
| Off Road 1.63 | Full9644-input El Paso2x/3x/repeat; all66 images repeat | A course with different terrain/materials | Broader coverage pending; partial-frontier recovery has no visible gain in its sampled town view |
| Exotica 2.4 | Full8860-input Amazon combined-renderer acceptance; separate current4K handover and Hong Kong segment checks | A contrasting course with an open distant sightline | Margin/handover evidence is useful; sampled third-band geometry is absent or hidden by nearer depth |

A second course should add features absent from the first: open distant terrain,
tunnels or bridges, sharp turns, elevation changes, transparency/fog, or different
sky and road materials. Choose it after reviewing the first drive's coverage.
Do not infer acceptance for every track from two representative recordings.

### Amazon, September 9

Local case `results/diagnostics/drive-crusnexo-20260909-203557` is titled
**Exotica - Amazon - full drive**. It stops cleanly after 8,860 frames / 155.071895
emulated seconds, with a fourth-place finish at game elapsed **1:30.52**.
The archived executable SHA256 starts `87d04de4` (personal v0.5.0); source-checkout
metadata at recording time does not change that actual binary identity.
Physical force was attended at the saved strength; every replay uses zero force.

The initial two original-binary replays match all inputs/native snapshots, 7,051 camera
samples and 21,153 actual ADC reads/times. Both complete 59 GL images at 3840x2160.
One initial pair, frame3600, has different sky/material colors with the same
driving path. Preserve that historical failure; it is not the acceptance result
for the subsequently repaired combined candidate. Follow the linked current
parity review for its qualified scope and remaining requirements.

Maintainer-reported windows are on the **game's elapsed timer**: black ground on
the left at **0:35, 0:45 and 0:57**, and a tall rectangular right-side artifact at
**1:12**. The latter is near replay frame 7200, whose image reads 1:12.26.
Do not treat the initial 1:16 sky-strip observation as this confirmed timestamp.
Collisions in the recording are useful stress coverage; no rerecording is needed
merely because the drive was untidy.

## Acceptance for each new case

- [ ] Retain the original recording, binary, ROM revision, settings and clean-stop
  receipt. Record the course, transmission and whether the finish was reached.
- [ ] Replay the archived binary to check every effective input and timestamp.
  Establish completed GL references across the whole route and inspect them;
  Exotica's black native framebuffer cannot serve as visual acceptance.
- [ ] Keep an archived-binary control. Repeat a route when a new nondeterminism
  concern or unresolved mismatch requires it, rather than routinely rerunning
  every established baseline.
- [ ] Compare the candidate using identical original inputs and initial state.
  Check camera and actual ADC timing over the whole drive. Add disabled/1x/2x
  controls for a specific causal question; do not automatically run the entire
  multiplier matrix for every new recording.
- [ ] Check geometry, original materials and resource state at selected landmarks,
  including late-track uploads and the finish. Reuse accepted ordered-output
  comparisons; repeat3x when the new change introduces a repeatability risk.
- [ ] Inspect temporal windows around pop-in, clipping, black textures, shadows,
  foreground occlusion and the transition into normal game drawing. Sparse stills
  alone cannot establish that these transitions are correct.
- [ ] Measure uncaptured intervals at 4K as well as diagnostic runs. Require a
  visible distance benefit and acceptable performance, not just more submitted
  objects. Leave unsupported track features explicit.

For Exotica outer-distance tests, first check saved band occupancy with
`harness/exotica_distance_samples.py --require-third-band`, then inspect whether
that geometry can survive the completed foreground. See the
[sample-selection review](reviews/2026-09-15-exotica-distance-sample-selection.md).
Another full Amazon recording is not needed merely to repeat the known occluded
views. A different open sightline is a better next distance sample.

The current Exotica source guards/probes have bounded frame windows; extend those
bounds deliberately when a full drive exceeds them. Never silently discard the
late part of a recording to make a diagnostic pass. See
[recording and replay details](DIAGNOSTIC-REPLAY.md).
