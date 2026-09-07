# Release morning: what still needs a person

Local candidate: `build/CruisnCollection-v0.4.0-rc1-20260907-050908.zip`.
The source launcher has since gained the World distance controls and moved Crack
Fill into Experiments. This ZIP is the preserved overnight baseline and does not
contain those menu changes; a replacement ZIP needs its own package acceptance.
Its [manifest and hashes](../results/proof/2026-09-07-release-hardening/release-final/package.manifest.json)
and [prepared pending ledger](../results/proof/2026-09-07-release-hardening/release-final/attended-prepared.json)
are preserved in the repo. No public release has been created.

The candidate includes renderer startup batching, restored package media/runtime
files, free-play fixes, repaired support diagnostics, safer upgrades and neutral
force-command handling. The automated evidence and exact ZIP identity are in
[the overnight review](reviews/2026-09-07-release-hardening.md). The full acceptance
contract remains [RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md).

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

Scenery pop-in is still a known limitation. 3x far distance has not shown a useful
mountain improvement over 2x at equal lookahead, and neither is a release default.
World collision feel and Exotica polarity remain explicit acceptance questions.
Record any failed check as a blocker or a clearly described candidate limitation;
do not mark an unobserved check passed. Publish only the exact accepted ZIP.
