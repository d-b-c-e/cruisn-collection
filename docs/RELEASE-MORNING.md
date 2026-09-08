# Release morning: what still needs a person

**Update:** the source now restores World menu/race-end feedback following the
user's regression report. World strength stays unchanged. The rc2 ZIP below still
contains the rejected gate and must be replaced before publishing. See the
[rollback and normalization issue](reviews/2026-09-07-world-ffb-rollback.md).

The preserved local candidate is **v0.4.0-rc2**, incorporating the earlier September7 player
feedback. The earlier `CruisnCollection-v0.4.0-rc1-20260907-050908.zip` remains a
rollback baseline; it lacks the newer menus, drivetrain telemetry and force fixes.
Use the new candidate's own manifest and pending ledger for acceptance. No public
release has been created.

Exact ZIP: `build/CruisnCollection-v0.4.0-rc2-20260907-170505.zip`.
Its [manifest](../results/proof/2026-09-07-release-feedback/package.manifest.json)
and [43-check pending ledger](../results/proof/2026-09-07-release-feedback/attended-pending.json)
are preserved with the [automated evidence](../results/proof/2026-09-07-release-feedback/README.md).

The new work adds game-derived gears/revs for World, Off Road and Exotica,
restores Off Road speed and Exotica UDP packets, and gates World/Exotica force
outside active driving. Exotica's automatic steering mirror is removed and its
output is trimmed20%. Read [the feedback review](reviews/2026-09-07-release-feedback.md)
alongside [the overnight baseline](reviews/2026-09-07-release-hardening.md).
The full acceptance contract remains [RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md).

## Start with the release configuration

Use full widescreen, CRT on, scale 4, World 2.4, launcher force at 50%, and the
default force profile (`cruisn-vunit@2`). Record the wheel-base settings separately.
Leave per-game graphics trials and extra impact cues off for the release baseline.
Crack Fill (Shared), now under Graphics Experiments, retains the baseline ON setting.
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
Keep distance off for release acceptance. Record New York and investigate it
after release as requested; a single clean2x race does not certify that experiment.
World collision feel, race-end force release and Exotica direction remain explicit
attended acceptance questions.
Record any failed check as a blocker or a clearly described candidate limitation;
do not mark an unobserved check passed. Publish only the exact accepted ZIP.
