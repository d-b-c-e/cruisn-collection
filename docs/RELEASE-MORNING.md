# Release morning: what still needs a person

Updated 2026-09-08. **v0.4.0 is published and preserved**; the source checkout has
newer Cheats, menu and distance work. The old rc1/rc2 candidates are historical,
and rc2 includes a rejected World force gate. Do not use either as the next
candidate or copy their acceptance forward.

This is the practical attended companion to [RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md).
Use the exact candidate being considered for the next release. Build and validate
it locally using [LOCAL-BUILDS.md](LOCAL-BUILDS.md); hosted workflows are disabled.
World force passes through in menus/race end and retains its existing strength.
Exotica keeps the separate polarity correction and 20% trim. These software changes
do not substitute for physical-wheel observations.

## Start with the release configuration

Use full widescreen, CRT on, scale 4, World 2.4, launcher force at 50%, and the
default force profile (`cruisn-vunit@2`). Record the wheel-base settings separately.
Leave per-game graphics trials and extra impact cues off for the release baseline.
Crack Fill (Shared) under Settings → Experiments retains the baseline ON setting
in current source. Published v0.4.0 still nests Experiments under Display.
Saved personal preferences were preserved, so an existing installation may differ
from these fresh defaults. Check the settings before recording. The Stream Deck
entry uses the source checkout and the root native executable on this machine;
the extracted candidate ZIP must also receive an attended check before publication.

## Four useful recordings

Run each command separately, with someone at the wheel. These commands keep the
saved settings and enable physical force explicitly. They create new timestamped
cases and preserve the original recordings.

```powershell
python harness/record_drive.py --game usa --title "Release USA manual" --with-ffb
python harness/record_drive.py --game world --title "Release World manual Germany" --with-ffb
python harness/record_drive.py --game offroad --title "Release Off Road manual" --with-ffb
python harness/record_drive.py --game exotica --title "Release Exotica manual" --with-ffb
```

For each drive:

- Wait 10–15 seconds on car selection, then select **MANUAL** and exercise every
  gear. A short follow-up should cover the other shifter style (paddles/H-pattern).
- Start without coins, complete the race, retry, and confirm audio and steering.
- Include a gentle car contact and a wall impact. Rate steering weight, car contact
  and wall impact separately: absent / barely noticeable / clear / excessive.
- Watch the telemetry gauges through shifts in both automatic and manual modes.
  Confirm speed, gear and tachometer agree with the game and SimHub/Buttkicker
  responds. RPM is an arcade scale derived from the game's actual rev signal.
- Exotica: confirm right turns right, comfortable startup, and comparable driving
  weight. World: finish the race and check for any continuing wheel oscillation.
- Check physical Esc: menu, resume, exit to launcher, then relaunch. Rebind one
  button and verify the new binding persists and the old binding stops working.
- Note the external clock time and side of each graphical defect. If using the
  game's ELAPSED TIME, say so explicitly. Germany needs the D/A selection transition,
  distant mountains/trees and the late left-side black road inspected again.
- End the recording and wait for its validation/encoding to finish before the next.

One complete drive can support several checklist entries. The synthetic Off Road
and Exotica cases do not replace this acceptance. A second World level is useful
for breadth after Germany; no special new route is required for the baseline.

## Public access before publishing

The current GitHub repository is private, and an unauthenticated update check
returns404. Choose the public distribution destination before promising working
in-app updates. No repository visibility or publication settings were changed.

## Remaining shared checks

Rehearse the exact ZIP on a clean Windows profile without Python, then upgrade an
older installation while preserving calibration, scores, bindings and preferences.
Known old input plugins should move to a backup; unknown custom input DLLs should
remain intact and require review. Keep the prior ZIP and rig backup for rollback.

A second wheel vendor, preferably Fanatec, and a 30-minute mixed-game soak are still
needed. Check disconnect/reconnect, no-wheel startup, repeated game switching and
force release on pause/exit. Logs cannot certify comfortable rim torque or detect
an unattended driver's subjective discomfort.

Scenery pop-in is still a known limitation. 3x/+12 has a confirmed New York guest
CPU crash and distant black flashing; the causal mechanism remains unresolved.
Keep distance off for release acceptance. Record New York for the ongoing investigation; a single clean2x race does not certify that experiment.
World collision feel, race-end force release and Exotica direction remain explicit
attended acceptance questions.
Record any failed check as a blocker or a clearly described candidate limitation;
do not mark an unobserved check passed. Publish only the exact accepted ZIP.
