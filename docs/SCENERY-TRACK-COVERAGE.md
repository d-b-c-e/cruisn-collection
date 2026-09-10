# Recorded track coverage for extended scenery

The maintainer requested full Off Road and Exotica recordings on September 9.
Current scripted routes establish repeatability over limited gameplay. They do
not establish whole-track or cross-track correctness. Keep their existing cases;
add new attended drives as separate cases.

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
python harness/record_drive.py --game exotica --title "Exotica - Hong Kong - full drive" --exotica-visibility off --with-ffb
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
| Off Road 1.63 | Limited El Paso start/hillside sequence | Full El Paso, then a course with different terrain/materials | Preset ready; recording pending |
| Exotica 2.4 | Limited Hong Kong sequence | Full Hong Kong, then a visually distinct course | Preset ready; recording pending |

A second course should add features absent from the first: open distant terrain,
tunnels or bridges, sharp turns, elevation changes, transparency/fog, or different
sky and road materials. Choose it after reviewing the first drive's coverage.
Do not infer acceptance for every track from two representative recordings.

## Acceptance for each new case

- [ ] Retain the original recording, binary, ROM revision, settings and clean-stop
  receipt. Record the course, transmission and whether the finish was reached.
- [ ] Replay the archived binary to check every effective input and timestamp.
  Establish completed GL references across the whole route and inspect them;
  Exotica's black native framebuffer cannot serve as visual acceptance.
- [ ] Repeat the completed GL references on the archived binary. Keep an original
  control even if a changed candidate is internally repeatable.
- [ ] Compare candidate disabled/1x/2x/3x using identical original inputs and
  initial state. Check camera and actual ADC timing over the whole drive.
- [ ] Check geometry, original materials and resource state at selected landmarks,
  including late-track uploads and the finish. Repeat 3x and compare ordered output.
- [ ] Inspect temporal windows around pop-in, clipping, black textures, shadows,
  foreground occlusion and the transition into normal game drawing. Sparse stills
  alone cannot establish that these transitions are correct.
- [ ] Measure uncaptured intervals at 4K as well as diagnostic runs. Require a
  visible distance benefit and acceptable performance, not just more submitted
  objects. Leave unsupported track features explicit.

The current Exotica source guards/probes have bounded frame windows; extend those
bounds deliberately when a full drive exceeds them. Never silently discard the
late part of a recording to make a diagnostic pass. See
[recording and replay details](DIAGNOSTIC-REPLAY.md).
