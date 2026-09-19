# Controls setup UI — 2026-09-19

This scoped launcher change adds a staged device/axis picker, guided calibration
and input preview to Simple Controls, and a saved Steering / explicit-device
chooser to Simple FFB. It applies to the collection launcher for Cruis'n USA,
Cruis'n World, Off Road Challenge and Cruis'n Exotica. It is source and CPU
fixture evidence; no physical device, game, native build, deployment or force
output ran for this work.

## Source and integration boundary

- Isolated worktree: `E:/Source/cruisn-collection-control-setup-20260919`.
- Branch: `codex/ux-control-setup-20260919`, created from exact
  `c93822b9c7186e2cfba67033220563642ff45ac8`.
- Owner helper commits `b0ff6fae36928c6fd1f06ce91e44f33daf5d079a` and
  `04d6782` were cherry-picked as local `e0c3d20` and `038c173` for integration
  testing. The UI handoff commit modifies only `harness/collection.py`, adds
  `harness/control_setup.py`, `tests/test_control_setup.py`, and this document.
  The owner should cherry-pick that UI commit only onto its helper successor.
- `control_launch.supported(binary)` supplies the hash-bound runtime capability
  result. A saved configuration and device preview do not establish native
  game-final input or physical FFB acceptance.
- The UI uses the owner's `clear_control_selection`, `save_ffb_selection`,
  `load_ffb_selection` and `save_legacy_bindings` APIs. The native launch seam,
  providers, control model, recordings and force tuning remain owner-owned.

Guidance is the published toolkit commit
`12df6b325d770625baffd75b2d2eb74f1fcd0a8c`, specifically UX-1 / UX-01-S and
the controls/cameras workflow. Git blob IDs at that commit:

| Document | Git blob |
|---|---|
| CONSUMER-UX.md | `3c98bda4500760eedd90d25593694a2cca5169b1` |
| CONSUMER-SETTINGS-VIEWS.md | `ed9f4640386f829b3a14b750719b0c5238868bb1` |
| CONSUMER-CONTROLS-CAMERAS.md | `58ace477b8f54e240910101bc5e9393f02209fea` |

## Placement and player flow

| Surface | Placement / behavior |
|---|---|
| Controls setup | Simple Setup opens Controls. Steering, Throttle and Brake are independent rows. |
| Bind | Enter opens the exact DirectInput device list, then the device's fixed axis slots. Friendly names are shown by default; only duplicate names get a short instance suffix. No first-device or name fallback. |
| Calibration | Simple on demand. Steering: centre, left, right, return. Pedals: released, full, return. Each position requires an explicit Capture after 350 ms stability. Restart discards only the draft. |
| Device preview | Raw sample and calibrated Left / Centre / Right or Released / Pressed / Full. It is explicitly device input, not verified game-final input. |
| Invert / Deadzone | Simple calibration review. Off/On and one percentage row, left/right changes 1%. Existing values are retained until explicitly changed; calibration and identity save together. |
| Save / Cancel | Both visible in the calibration review at 720p. Save is explicit and atomic; Cancel retains the previous assignment. Failed writes retain the proposal with Retry / Cancel. |
| Clear | Delete on an axis row, or Clear inside its editor, opens a separate confirmation. The owner's helper clears the role, its legacy fallback and writes an unbound tombstone. |
| FFB device | Simple FFB opens a choice list with Use steering wheel plus connected exact devices with current usable HID output paths. Save does not enable FFB or alter strength/tuning. Missing explicit identity is shown, never silently replaced. |
| Legacy binding setup | Retained on Controls for keyboard/gamepad and existing wizard flows. Explicit rebind replaces the same role's calibrated record; skipped roles and independent buttons remain saved. |
| Game calibration | Existing Simple information row retains the game service-menu ADC calibration instructions. Frontend endpoints do not prove that game ADC calibration is complete. |
| View / navigation | The underlying Simple/Advanced choice is unchanged. The modal says Finish or cancel to change view. Arrow keys / Enter and mouse row selection are available; Esc/F6 cancels. |

Calibration rejects changing samples, insufficient spans, a failed return to
rest, and another moving axis on the selected device. A preview does not infer
which of several connected devices the player intended: the player chooses
the device and axis explicitly. Clear, FFB choice and calibration are separate
scoped transactions; they never materialize new force defaults or alter other
roles, telemetry targets or owner tunes.

## Modal and device lifecycle

The session owns one input-only reader. It closes before device enumeration,
on focus loss, disconnect, window close and normal exit. Save closes the reader
before re-enumeration and the atomic write, then reopens that exact reader for
the release check on both success and failed-save retry. A reopened reader must
produce a fresh sample before another save. No force/haptic API is called.

Calibration input does not feed the ordinary launcher wheel navigation.
Opening drains queued menu actions; close waits for two distinct consecutive
focused neutral frames. It checks the current selected reader's resting axes
and buttons plus launcher keyboard, mouse, hats and menu-relevant legacy input.
Missing/disconnected readers close and require an explicit fresh selection.
No background reconnect or device fallback occurs. The launcher will not open
device setup while a game/launch is active, and cannot launch while the modal
is open. Returning to settings drains pending actions and briefly disarms
legacy wheel navigation.

F8 retains its existing independent saved-Off action. If it changes the file
during an edit, the modal reports this and asks the player to cancel/reopen;
optimistic concurrency refuses to overwrite that newer Off preference.

## Verification

Commands run in the isolated worktree:

```powershell
python -B -m unittest discover -s tests -p test_control_setup.py -v
python -B -m unittest discover -s tests -p test_settings_view.py -v
python -B -m unittest discover -s tests -p test_control_launch.py -v
git diff --check
```

Results: **21 controls UI tests**, **7 existing settings tests**, and **7 owner
launch-helper tests pass**. The final malformed-FFB recovery change was checked
by rerunning its focused controls test. No broad native or game suite reran.

Controls fixtures use a fake reader/inventory and real temporary configuration
files. They cover stable and ambiguous movement, reversed pedal endpoints,
staged inversion/deadzone, no-write drawing/cancel, missing/duplicate identity,
disconnect/focus loss/timeout/shutdown, real atomic replacement failure,
concurrent edits, fresh samples after failed save, held controls after save,
exact Off/unknown/telemetry/other-role preservation, Clear/tombstone and legacy
rebind integration, explicit FFB/follow-Steering and unavailable output paths.

One integration failure caught an absent-section bug in the owner's helper;
the owner fixed it in `04d6782`. Both ordinary legacy-only and fresh config
fixtures now pass. A failed assertion from reusing ConfigParser across a
removed-key read was a fixture issue and was corrected to read fresh state.

The actual `Shell.draw_settings` method also ran on the existing CPU/Pillow
fixture at **1280x720 and 3840x2160** for device list, axis list, capture,
calibration review, Clear, FFB list, FFB review, failed save and release wait:
**18 images, zero out-of-bounds text or same-row collisions**. The 720p review
and FFB list were visually inspected. These are not GLFW/GL/input-event tests.

Local generated evidence (not distributed game assets):
`C:/Users/antho/AppData/Local/Temp/cruisn-control-layout-20260919-final`.
Its `report.json` SHA256 is
`3936D2454DD216C6167CE14B27974C04259063A8560C7CB8B8C788E791EE58C2`.
To regenerate, set `CRUISN_CONTROL_LAYOUT_OUTPUT` to an artifact directory
before running the controls tests. Without it, fixtures write no images.

## Remaining acceptance and constraints

- The owner still needs to package this frontend with its feature-attested
  native candidate and perform the coordinated live no-output acceptance.
  This UI commit does not qualify or deploy that candidate.
- Verify real device order changes, same-name twins, physical disconnect,
  focus return, keyboard/mouse modal opening and held-input release in GLFW.
  Fake-provider checks establish controller behavior, not driver timing.
- The selected reader checks all reported buttons. Devices with phantom
  presses or latched controls may need a deliberate device-specific policy;
  no claim is made that the owner's MOZA rig passed this flow.
- Legacy launcher wheel navigation retains its prior name/axis mechanism.
  New strict records control the next native launch via the owner adapter;
  this commit does not claim a new strict launcher-navigation backend.
- The game tables expose Steering, Throttle and Brake; they do not expose
  separate clutch/handbrake roles. Existing camera/game buttons stay in the
  legacy binding flow. No new camera capability or game physics hook is added.
- World force behavior, release gating, tunes and primary renderer baseline
  are outside this scoped UI work and were not changed.

## Wording follow-up

The coordinator's bounded source review found no transactional blocker and
requested simpler player language before packaging. The successor shows
**Ready for next launch** or **Update required**, with a concrete save/launch
or update instruction. Device preview explains that the game applies its own
input settings; the FFB chooser explains that this screen does not test forces.
Friendly names now lead all device choices; a short suffix appears only for
duplicate display names, with exact identity matching unchanged internally.

The focused readiness-label and duplicate-name tests pass. The actual CPU
layout fixture reran its 18 images at 720p/4K for the wording change; evidence
is in `C:/Users/antho/AppData/Local/Temp/cruisn-control-layout-20260919-wording`.
No owner helper, lifecycle, save transaction or native/game code changed in
this follow-up.


## Live empty-inventory wording correction

The exact frozen6c4407e frontend ran at3840x2160 with isolated settings and
literalMIDV_FFB0. Warning/cancel, mouse opening, F6 modal cancellation, F8 Off
with50% retained, and focus-loss cancellation/return worked. No game launched.
Both frozen and source providers returned an empty inventory, so actual axis
preview and endpoint capture remain unqualified. All43 owner settings, wrapper
and deployed native/receipts/profiles stayed exact after normal launcher exit.

That live observation found a misleading axis-picker row: native capability
alone displayed Setup status: Ready for next launch, beside No devices found.
The row now explicitly says Controls support: Available and instructs the
player to choose a connected device before saving/checking in game. It makes
no device/readiness claim. FFB's separately resolved identity status is retained.
The focused opening/empty-inventory assertion and actual CPU layout fixture are
the relevant checks; no repeated game or native rebuild is needed for wording.

All29 focused setup tests pass; the updated layout test generates32 CPU images
at720p/4K with no bounds/collision failures. The720p empty-device fixture was
viewed. These files are software-rendered placement evidence. Actual live4K
screenshots were inline Computer Use images only, without returned file paths.
Evidence: local `results/diagnostics/ux-20260919/empty-readiness-layout` and
`live-final-6c4407e/observed.json`.
