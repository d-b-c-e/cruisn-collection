# Next public release: roadmap and acceptance checklist

Owner: maintainer + attended testers. Updated 2026-09-08. **v0.4.0 is explicitly
approved by the maintainer, subject to renewed automated gates.**
The [recorded sign-off](releases/v0.4.0-approval.md) accepts the current alpha's
known issues and remaining human coverage. It supersedes older blockers below
for this release only; unperformed checks must not be relabeled as passes.
Scope: USA 4.5, World 2.4, Off Road, **and Exotica**. World 2.5 remains a compatibility
check; its factory automatic-only behavior cannot satisfy manual-transmission acceptance.
The machine-readable checklist is [fixtures/release/checklist.json](../fixtures/release/checklist.json).

Latest [World FFB rollback](reviews/2026-09-07-world-ffb-rollback.md): game-menu
feedback restored, strength unchanged. Cross-game force normalization and World
oscillation remain known issues for later work. The prior rc2 ZIP contains the
rejected driving-state gate; replace it and renew acceptance before publishing.

## Roadmap

1. **Choose and freeze the candidate.** The [2x/3x comparison](reviews/2026-09-07-world-3x-and-release.md)
   is complete: 3x adds no demonstrated mountain benefit over 2x at equal lookahead.
   Keep distance experiments off for the release unless fresh Germany and another
   World level justify promotion. Freeze source, emulator, DLLs, toolkit profiles,
   default graphics settings and package hash. Do not make distance elimination a
   prerequisite for shipping the other fixes.
2. **Clear automated gates.** Run CI, the complete seven-case local replay suite,
   exact/quality GPU checks, configuration contracts, and V-Unit pause-menu checks.
   Check selection and driving speed separately; average speed does not clear stutter.
3. **Collect attended acceptance.** Record one complete manual-transmission race
   per game at release defaults, plus a short check of the other shifter style.
   Inspect the resulting completed GL captures and FFB traces. Request replacements
   when a candidate changes the route; preserve all original recordings.
4. **Package and rehearse.** Build a local candidate ZIP, test fresh install and
   upgrade away from development paths, run the wheel/soak checks below, close release
   blockers, then tag/publish that exact reviewed candidate. Retain the prior ZIP and
   configuration backup for rollback. This checklist does not publish a release.
   The release workflow now builds a candidate only. Tag pushes do not publish.
   `promote_release.py` rechecks current evidence and uploads the exact accepted ZIP;
   it performs a dry run unless `--publish` is explicitly requested. A locally
   tested executable does not certify a newly compiled CI candidate.

## Public distribution decision

As of 2026-09-07 the repository is **private**. An anonymous request to the updater's
`/repos/d-b-c-e/cruisn-collection/releases/latest` endpoint returns404, although an
authenticated maintainer can see v0.3.7. Ordinary players cannot use this update
source yet. Decide whether to make a reviewed source repository public or use a
separate public distribution destination and update the client/workflow accordingly.
Changing repository visibility exposes its contents and history; no such change
was made during unattended work. Keep credentials out of distributed packages.
A private candidate artifact and a successful local install do not clear this item.

## Required acceptance

| Area | Automated evidence | Attended acceptance still required |
|---|---|---|
| Launch/play | Seven isolated replay cases, all four games; complete frames and timing gates | Fresh launch, complete race, retry, audio, game switching |
| Free play | All seed bytes/mirrors = 1; Off Road checksum; real fresh boot/replay persistence; existing NVRAM preserved | Start/restart without coins, then relaunch |
| Manual transmission | Generated H-pattern/sequential ports, World 2.4 selection, cabinet configuration | Select MANUAL; hold gears 1–4; neutral/downshift; one shift per paddle press |
| Bind/rebind | New button replaces old; high buttons translated; keyboard fallback and inactive-mode bindings retained | Wizard, persistence after relaunch, sparse axes, wheel reconnect; no stuck inputs |
| Force feedback | Toolkit signal fixtures and per-game source traces; automated output always off | Correct direction, comparable default weight, distinct car/wall impacts, no oscillation; pause/exit releases torque |
| Telemetry | Actual private-loopback UDP compared with independent game-memory probes in all seven cases; active coverage and speed thresholds; World/Exotica force-state checks | All four games: auto/manual gears, loaded upshift rev drops, speed/tach gauges, SimHub/Buttkicker response; menus/end-of-race clear appropriately |
| Graphics | Default full widescreen + CRT; native exactness and completed GL evidence | Selection screens and a whole race: margins, sky, shadows, seams, sharp turns, collisions; no visibility defect that prevents driving |
| Menu/exit | V-Unit real menu-handler diagnostic and controller remapping | Physical Esc opens menu/resumes/exits; F12 fallback; clean relaunch; Exotica menu separately |
| Package/upgrade | Exact ZIP/file hashes; four frozen boots, menu pages, setup/support; real Windows updater and preservation checks | Clean Windows profile without Python, no development paths; import/upgrade retains calibration, bindings and scores |

Fresh defaults: CRT on, full widescreen, scale 4, World 2.4, FFB 50% with
`cruisn-vunit@2`; distance/terrain/scenery/seam-alignment experiments and added
impact cues off. These are **fresh-install defaults**, not an instruction to reset
saved player choices. The seed correction changes seven setting bytes across
USA, World 2.5, Off Road and Exotica, plus Off Road's checksum byte. World 2.4
already had free play on. Off Road discards a free-play edit with a stale checksum;
the launcher toggle and NVRAM tool now maintain it too.

A concise morning sequence and four recording commands are in
[RELEASE-MORNING.md](RELEASE-MORNING.md).

## Short attended drive protocol

- Record wheel model, firmware/driver, rotation, base strength, damping, launcher
  strength/profile, game revision and shifter mode. Compare games on the same setup.
- Leave car selection running for 10–15 seconds. Select MANUAL deliberately and
  exercise every gear. Rebind one noncritical button, relaunch, and verify the old
  button no longer triggers that action.
- Complete a race, include a gentle car contact and a wall impact, and note elapsed
  time plus the exact side of any artifact. World: Germany and a second level;
  revisit transmission D/A textures and the late black-road/left-margin problem.
- Rate **steering weight, road feel, car contact and wall impact separately**:
  0 absent, 1 barely perceptible, 2 clear, 3 strong but controllable, 4 excessive.
  Car/wall contacts must be identifiable without looking. Normal steering should
  be within one category across games on the same wheel; no self-sustained oscillation.
  Exotica polarity remains an explicit open check. A shared strength percentage
  alone is not evidence of similar feel.
- Repeat the default-feel check on a second vendor, preferably Fanatec given the
  historical report. Do a 30-minute mixed-game soak, reconnect/no-wheel checks,
  pause/resume and clean exit. Logs can locate force events but cannot certify feel.

## Repeatable commands and evidence

```powershell
python -m unittest discover -s tests -v
python harness/run_regressions.py --candidate E:/Source/mame-src/vunit.exe --output results/diagnostics/release-candidate
python harness/check_fresh_boots.py --candidate E:/Source/mame-src/vunit.exe --output results/diagnostics/release-fresh-boots
python harness/release_gate.py --candidate E:/Source/mame-src/vunit.exe --regressions results/diagnostics/release-candidate/report.json --fresh-boots results/diagnostics/release-fresh-boots/report.json --init-attended results/diagnostics/release-attended.json --report results/diagnostics/release-readiness.json
# Only with a person at the wheel; uses SAVED settings, so confirm release defaults first:
python harness/record_drive.py --game world --title "Release World manual Germany" --with-ffb
```

Use a new output path each run. The gate exits 1 while anything is missing. Its
configuration checks run in a temporary rig and do not launch games. It requires
the full suite, all five fresh-seed boot/persistence checks, matching binary/source/suite
hashes and no physical output. A matching replay alone cannot clear failed persistence.
Source identity normalizes known text line endings while preserving binary bytes.
CI exports the complete identity on both Windows and Linux; compare both with the
local checkout before freezing a candidate. Raw ZIP/file hashes remain exact.
Configuration tests that are skipped on non-Windows cannot clear the gate.
The candidate workflow runs the harness tests and `check_release_package.py`:
required runtime/source files, menu media, fallback shaders, candidate emulator hash,
free-play seeds and absence of files in the ROM/personal-rig directories. The ZIP
manifest records every packaged file hash and source identity. This is not a complete
asset/licence audit or proof that the frozen application starts on a clean machine.
Local packaging additionally invokes the actual frozen launcher's settings reader
before zipping and requires CRT on, full widescreen, scale4 and per-game experiments
off in an installation without personal settings. Existing CRT preferences are preserved.
`ready_for_release` additionally requires the attended ledger: reviewer, date,
observations and existing evidence files with SHA256 hashes for every check.
Paths in the ledger are relative to that JSON. One drive/report can support
several checks; leave unobserved checks pending. Attach CI and package evidence
there too, including the actual ZIP hash.

An explicit maintainer sign-off may instead accept specified remaining human checks
as `waived`, each with a reason and coverage limits. The same ledger must include
`maintainer_approval` with decision `release-current-state`, reviewer, date, notes,
hashed approval evidence and the exact `waived_checks` list. Candidate/source
binding still applies. The report exposes `waived` and `all_checks_passed=false`;
automated configuration, regression and fresh-boot gates cannot be waived.

Rerun with `--attended results/diagnostics/release-attended.json` after filling
the ledger; omit `--init-attended`, which refuses to replace an existing ledger.
Changes to product code, tests, workflows, profiles, patches or fixtures invalidate
old acceptance. Updates confined to the top-level README and `docs/` do not. A passing replay means the
recording repeated, **not** that every texture or physical control is correct.

Current blockers: updated attended gameplay/FFB acceptance (especially World's
weak collision feel), Exotica direction and
manual behavior, all-game telemetry/tactile acceptance, race-end force release,
default-setting visual coverage beyond existing recorded cases,
longer startup/soak coverage after the masked-upload improvement,
and clean-profile/attended-upgrade/second-wheel acceptance. Twelve repeated full-window
starts pass; deliberate long consumer stalls remain correctly rejected. The existing synthetic
Off Road and Exotica drives are useful regressions but insufficient release coverage.

## Candidate packaging and promotion

Build from a clean committed checkout with `./make_release.ps1 -Version v0.4.0-rc2`
(or manually dispatch the **release candidate** workflow with that version). The
version is a candidate label, not a published tag. ZIP names include a timestamp;
previous packages remain available. `-NoMedia` deliberately omits artwork/music.
Normal packages restore the repository artwork and music, with custom music in
`rig/assets` taking precedence. Personal rig directories are never bundled.

Keep the `.zip`, `.zip.check.json`, `.zip.defaults.json` and `.zip.manifest.json` together. Test the
extracted ZIP away from development paths. For a CI build, download its artifact
using the [GitHub CLI artifact workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts?tool=cli);
replay evidence must reference that extracted emulator. A different compile is a
different candidate. Source, media or runtime changes require renewed acceptance.

After all acceptance is recorded, attach the exact ZIP and its SHA256 in the
`shared/package-review` ledger entry. Run `harness/promote_release.py ZIP` with
`--manifest MANIFEST --candidate EXE --regressions REPORT --fresh-boots REPORT
--attended LEDGER --notes NOTES.md`. Its dry run rechecks the complete gate.
Only a subsequent explicit `--publish` creates a release, targeting the recorded
commit and uploading the same ZIP without rebuilding. Existing tags are refused.
