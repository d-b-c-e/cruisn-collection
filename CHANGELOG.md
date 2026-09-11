# Changelog

All notable changes to Cruis'n Collection. Dates are YYYY-MM-DD. The full
engineering log with numbers and proof images is `results/RESULTS.md`.

## Unreleased — September 9–11 diagnostics

- Add explicit device-free observation of the actual force worker, with source/
  host clocks and independent stage verification for strength-50 calibration.
  This does not enable physical feedback or change the deployed tune.

- Add offline impact-detector reachability metrics. Exotica's raw Amazon signal
  cannot reach the enhanced detector's arrival threshold; calibration remains
  pending. Existing force stages and production settings are unchanged.

- Integrate native Exotica waiting-cohort completion observation. Full/repeat/
  disabled runs preserve original drives and sampled 4K output while verifying
  which proposed copies must be omitted. Extra waiting drawing remains pending.

- Verify actual steering reads in USA, World and Off Road against recorded ADC
  conversion timing. Full replays preserve original force and telemetry data;
  the strength-50 calibration still needs matched contacts and output conditioning.

- Add a standalone Exotica waiting-object reconciliation helper and actual
  command-fence evidence. Filtered offline drawing adds distant trees; live
  integration and transparent handover remain under investigation.

- Verify four-game recorded steering and Exotica's actual wheel reads without
  applying steering curves twice. This supports the near-term strength-50
  normalization candidate; deployed force settings are unchanged.

- Make four-game force normalization a near-term roadmap milestone, with a
  strength-50 comparison protocol, contact/headroom checks and an upstream
  Exotica plugin audit. This documents planned calibration; tuning is unchanged.
- Fix offline force analysis ignoring the current `wheel_motor` output name.
  Initial four-game strength sweeps establish algorithm baselines; they do not
  yet establish matched driving or physical force normalization.
- Add time-weighted four-game force coverage analysis with strict trace/clock
  checks, stale-sample exclusion and explicit OCR provenance. Existing recordings
  lack sufficient matched turn/contact coverage for calibration; tuning is unchanged.
- Add read-only native Exotica allocation/first-draw diagnostics. Complete Amazon
  runs reproduce the earlier trace and sampled display frames. Waiting-object
  drawing remains pending; the default suite retains a World renderer timeout.
- Add a standalone Exotica selector for allocated scenery awaiting its first
  original submission. Five real scenes and 30 geometry variants match independent
  checks; live rendering and transition acceptance remain pending.
- Integrate explicit native waiting-scenery observation. Full Amazon/repeat
  preserve original routes, future geometry and sampled 4K output. A measured
  same-scene submission overlap now guides handover work before extra drawing.

- Add a complete attended Off Road El Paso recording: archived replays and a
  candidate control preserve the full route and all 66 sampled display images.
- Fix Off Road host scenery stopping near the final section. Full 2×/3× runs
  complete the recorded route; 3× repeats all 66 sampled display images and shows
  additional distant terrain over 2×. Broader visual acceptance remains open.
- Native host future-scenery prototypes now cover all four games. World, USA
  and Off Road show measured earlier scenery; useful 3× gains remain uneven.
- World 2.4 future road rendering fills measured distant gaps. World 2.5's
  separate scenery adapter still needs its road/ground path.
- Exotica candidates address Amazon palette flicker, a stale margin rectangle
  and measured black ground wedges. Performance and broader coverage remain open.
- Exotica private wider-depth rendering now accepts independently checked future
  geometry and material packets. Dense Amazon presentation comparisons find 33
  changed 3×-over-2× frames among 233 samples; the 3× repeat matches all 233.
  Quiet performance remains about 95% at 2× and 91% at 3×. Useful visual gains,
  fade transitions and full-speed acceptance remain unfinished.
- Reduce bounded Exotica packet serialization overhead without changing its wire
  format. Full 2×/3×/repeat preserve all 233 displayed frames; paired timing shows
  only a small game-speed improvement. Allocation/fade diagnostics independently
  match 3,932 ordinary allocations and 2,539 sampled updates, providing a basis
  for the still-unimplemented host fade transition.
- Measure Exotica's allocation-to-first-draw gap and prototype continuation of
  allocated-but-undrawn scenery. A completed offline scene shows additional
  distant trees. Add a standalone reusable lifetime tracker that matches the
  recorded allocator and drawing events; live integration remains pending.
- Full recorded drives, original input/camera timing and graphics-resource checks,
  independent geometry/pixel comparisons and repeat runs support these candidates.
- Explicit host coverage/vertex-batch trials, with a targeted tunnel-seam
  improvement and synthetic GPU checks preserving shadows/transparent texels.
- Read-only road-template, projection and final-render-descriptor verification.
- Bounded completion handshake for queued diagnostic captures at shutdown.
- See the [current status](docs/reviews/2026-09-10-scenery-parity-status.md) for
  remaining acceptance work. These prototypes are undeployed; v0.5.0 is unchanged.

## v0.5.0 — 2026-09-08

- Optional Exotica Menu Force Feedback experiment; default Off preserves suppression outside driving and World remains unchanged.
- Separate local Release/Personal targets: compile away from the Stream Deck binary, stage factory defaults for releases, and deploy personal builds explicitly with a backup.

### Added

- Imported per-game Cheats: continuous toggles/choices, exact revision/hash binding,
  reset to off and recorded cheat-state verification. The updated emulator adds
  Esc → Cheats with staged live actions and a frame-stamped replay journal, including
  one-shots and code restoration. Imported effects need individual validation.
- Optional World 2.5 and Off Road 2×/3× distance menus, plus Exotica margin scenery.
  All default Off; increased limits do not guarantee visible scenery or eliminate pop-in.
- Bounded CLI-only World 2.4 host scenery prototype: earlier terrain/buildings/trees
  without guest activation changes. Occlusion, handover and timing remain experimental.
- One local Python/native/GPU check runner with source and evidence hashes.

### Changed

- Experiments is beside Display, with Shared/game contexts and saved preferences.
- Builds/checks/releases run locally. Hosted workflows are disabled; pushes, PRs
  and tags do not build or publish. Promotion uploads the exact tested ZIP.
- Refresh setup, FFB/transmission guidance and public-readiness documentation.

### Fixed

- Normal launches could fail with an uninitialized `env` after recording-override
  changes, including when enabling a USA cheat. Each launch attempt now owns its
  environment. Added process-boundary coverage with cheats on/off for all games
  and recording variants. Reopen the source launcher after updating.

## v0.4.0 — 2026-09-08

This alpha release improves rendering, wheel integration and telemetry across
Cruis'n USA, Cruis'n World, Off Road Challenge and Cruis'n Exotica.

- Fix distant red/blue texture seams, enhanced checkerboard shadows, Off Road's
  black upper sky corners and World's disappearing transmission artwork.
- Improve widescreen terrain coverage and preserve thin geometry at high resolution.
  Margin Fill is retired because it smeared sky textures.
- Restore the V-Unit Esc menu while paused and address selection-screen slowdown,
  recording hitches and startup framebuffer uploads.
- Send real game gear/rev signals for all four games, including automatic shifts.
  The rev signal maps to an estimated 900–8,000 RPM. USA, Off Road and Exotica have
  guarded internal speed readers; World speed still uses OCR.
- Correct Exotica steering/force polarity and reduce its effective force by 20%.
  Restore World menu/race-end feedback with its strength unchanged.
- Add force profiles and optional per-game impact cues. Spring, damper and friction
  respect overall strength; impact cues remain off by default.
- Add per-game graphics experiments, including World 2.4's 2x/3x distance and
  +0/+8/+12 scenery lookahead. These are optional trials, off by default.
- Add recorded-input replay, completed-frame graphics comparisons, actual UDP
  telemetry checks, fresh-save checks and extracted-package smoke tests.
- Harden setup/updates and preserve settings, calibration, bindings and scores.

Fresh installs use **full widescreen, 4x internal rendering, CRT on and free play**.
World defaults to revision 2.4 for manual transmission. Existing preferences are
preserved when updating. No ROMs are included; supply your own supported sets.

### Known issues


- World can oscillate at race end or in menus; its recent force gate was removed
  at the maintainer's request. Cross-game force normalization and impact feel need
  more wheel testing. Equal strength percentages do not yet guarantee equal feel.
- Exotica force polarity is verified in software; broader physical-wheel testing,
  including a second vendor, remains incomplete. Exotica also retains upstream
  emulation/rendering defects, including some car-selection text.
- Extended distance does not eliminate pop-in. World New York has black flashing
  artifacts, and a finish-line crash was observed with 3x/+12; causation remains
  unresolved. Leave distance experiments off for the baseline experience.
- New human recordings, broader manual-shifter coverage, clean-user-profile
  installation and a longer mixed-game soak remain follow-up coverage.
- This repository is private. Downloads require repository access; the built-in
  anonymous updater cannot currently discover this release.


## v0.3.7 — 2026-09-04

- **Exotica felt like a bare centering spring and too weak** (rig, first
  evening on the built-in path). Its crash and jump effects are single
  17 ms full-force spikes, which a direct-drive base renders as a tick
  and the new smoothing shrank further; the old plugin's per-update
  rumble burst was what made them shake. Back by default: `ffb_rumble`
  (a 100 ms vibration burst per force update, `0` to switch off), and a
  jump of 60% of full force or more now passes the smoothing unfiltered.
  Each game card gets its own **FFB STRENGTH** row (blank = the SETTINGS
  value), so Exotica can run at 100 while USA stays at 50.

## v0.3.6 — 2026-09-04

- **Force feedback is now built into the emulator; the FFB Arcade Plugin
  is gone.** On Endprodukt's advice (the plugin's own maintainer: "when
  you work at MAME driver level, avoid the plugin"), `vunit.exe` takes the
  byte each game writes to its wheel motor and drives the wheel directly
  through SDL2 haptics - one signed constant force on the steering axis,
  modelled on Cannonball DX's wheel code, interpreting the byte exactly as
  the plugin's Cruis'n handler did. What that removes: `dinput8.dll`,
  `MAME64.dll`, `FFBPlugin.ini`, `FFBReset.exe`, the wheel GUID (and the
  SDL-version GUID trap found this morning), "Detect wheel", the
  plugin-in-the-launcher problem, the first-launch enumeration hang, the
  post-exit crash attributed to its teardown, the Cruis'n USA name spoof
  Exotica needed, and the `ffb_rumble` / `ffb_alt` / `ffb_power` /
  `ffb_hold` / `ffb_constinf` knobs. What stays: **FFB STRENGTH** (0% =
  off), **FFB PEAK LIMIT**, `ffb_slew`, and the diagnostics. New:
  **SETTINGS → FFB DIRECTION** (bases differ in axis sign; the default is
  measured right for a Moza - flip it if the wheel runs away from centre
  in Exotica), and forces are released half a second after a game stops
  writing its motor (pause, menus) and at exit, and the moment the Esc
  menu opens. The zip now ships `SDL2.dll` (zlib license) instead of the
  plugin. Three `[collection]` knobs for direct-drive bases, from the
  first rig session with the native path (USA driven straight pulled left
  and right in turn - the games' 150 ms after-kick on a wheel with no
  friction): `ffb_smooth` (low-pass, ms; **default 50** now, the setting
  that fixed it on the rig), `ffb_damper` and `ffb_friction` (condition
  effects the base renders for the whole session, opt-in). A fresh
  install now starts at **FFB STRENGTH 50** instead of 100.

- **Pedals on a separate device could bind in the wizard and do nothing
  in game** (tester with a Fanatec CSW 2.5 and HID pedals). The wizard's
  axis numbers are glfw's compacted list; MAME names DirectInput axes by
  fixed slot and skips missing ones, so a sparse device's axes landed on
  the wrong MAME tokens. The launcher now asks DirectInput for each
  device's real slot layout at launch (`harness/dinput_axes.py`) and
  translates; the support bundle carries `dinput_axes.txt`.

- **SETTINGS → FFB DIAGNOSTICS** (on/off) and **SETTINGS → SAVE SUPPORT
  BUNDLE** in the launcher, so a tester never has to leave it; the bundle
  folder opens when done. The setup window keeps its buttons.

- **FFB diagnostics now capture the whole loop**: the trace records the
  steering input the game reads (`wheelpos` rows) next to the force it
  sends; the support bundle adds `ffb_trace_report.txt` (peaks, kicks,
  and now wheel swing rate/amplitude with a verdict) and `ffb_trace.png`
  (force and wheel position on one timeline, last 20 s); `midv_ffb.log`
  adds the level actually sent to the wheel for every motor write.

- **`ffb_slew`** (tester: "clipping" and constant back-and-forth on a
  Fanatec CSL DD): a per-update force slew cap in the emulator
  (`MIDV_FFB_SLEW`, V-Unit and Exotica) that turns slams into swells;
  `rig\collection.ini` `[collection] ffb_slew = 16` to try it.
- Exotica live overlay: the record ring no longer drops texture-memory
  spans, palette loads or display ticks when full (bounded wait, then a
  full texture-memory resync); drop counters in `midz_gl.log`. Dense
  snapshot controls (`MIDZ_GL_SNAP_EVERY/FROM/FROM_SEC/MAX`). Overnight
  investigation: Exotica's Amazon "glitches" and World's New York "black
  texture" both reproduce identically on MAME's own renderer (hardware
  behaviour) - details in RESULTS.md.

## v0.3.5 — 2026-09-03

- **The FFB plugin was loading itself into the launcher.** Its
  `dinput8.dll` sits beside the launcher, and the launcher's joystick
  library asks Windows for `dinput8.dll` by name - so a plugin instance
  ran inside the launcher for the whole session, enumerating the wheel
  (a tester's FFBlog shows "process name: CruisnCollection.exe"). The
  launcher now pre-loads the system DLL, so the plugin only ever runs
  inside the game. Very likely the real "FFB works once per session"
  cause; the v0.3.4 measures stay as belt and braces.
- **FFB STRENGTH never actually worked.** The plugin's Cruis'n handlers
  read per-game keys (`MaxForceCrusnUSA`, `AlternativeMaxForceLeftCrusnWld`,
  ...); the launcher only scaled the bare `MaxForce` keys, so every game
  ran at 100% whatever the setting said (tester: "0% still full force").
  The per-game keys are scaled now - expect the games to feel *much*
  lighter at your usual setting, and re-tune upward.
- **Force feedback template now runs AlternativeFFB=1**, the mode this
  project's rig was tuned in; testers were getting mode 0.
- **Measured the games' force law** (headless wheel sweep under the force
  trace): a kick opposite to and proportional to each wheel movement,
  gone within ~100 ms - a damper, not a spring. A strong direct-drive
  base at 100% turns it into a runaway left-right oscillation (a tester's
  video). World additionally holds full-strength force for ~0.5 s
  off-track and in crashes; Off Road peaks around 80. INSTALL explains it
  and says to start at 30-40%.
- `harness/ffb_trace_report.py` summarizes a support bundle's force trace
  (peaks, kicks per second, direction flips) and states the verdict.
- **Cruis'n Exotica force feedback** (experimental). MAME never emulated
  Exotica's wheel motor; a headless wheel sweep with a write log found it
  on the LED/lamp board (offset 0, "unknown purpose" upstream): a signed
  byte the game holds proportional to wheel displacement - a centering
  spring - plus race effects. The emulator now exposes it as the `wheel`
  output like the V-Unit games, and since the FFB plugin has no Exotica
  handler, the emulator reports "crusnusa" to it for Exotica launches so
  the Cruis'n handler drives the wheel. FFB STRENGTH and FFB PEAK LIMIT
  apply. Needs a wheel test; the signal path is the same as USA's.
- **Exotica sequential shifting** (prepared): the game only has an
  H-pattern shifter; in SEQUENTIAL mode the emulator now runs a virtual
  4-speed driven by the shift-up / shift-down paddles (new "Shift Up /
  Shift Down" inputs on the Exotica driver, bound by the launcher).
  Caveat: **manual transmission cannot currently be selected in MAME** -
  Exotica's TRANS SELECT screen ignores the wheel, every button, the
  gear switches, both cabinet DIPs and the operator adjustment (fully
  mapped tonight, see RESULTS.md). This looks like an emulation gap in
  the upstream driver, so the virtual shifter waits for it.
- **Pedal-stuck guard**: the launcher refuses to start a game while the
  gas or brake reads pressed and says which pedal to press and release
  (a Moza load-cell brake came up latched at full on the rig - the game
  burned out in 2nd gear with the tyres squealing until it was pressed).
- Exotica force feedback: the game's own STEERING WHEEL POWER operator
  adjustment (1-10, default 5, clock-chip byte 0xC7) is set to 10 - in
  the fixture and at every launch - and the emulator adds a 4x gain on
  top (its spring byte is small even at 10); FFB STRENGTH scales all of
  it. The chain was verified on the rig's plugin log.
- **SETTINGS → FFB PEAK LIMIT** (OFF / 100 / 80 / 60 / 40 / 30): caps
  the games' force kicks at that value of 127 while small road forces
  keep full strength (`MIDV_FFB_CLAMP` in the emulator, verified headless:
  peaks 100 -> 40, small kicks byte-identical).
- Known issues (v0.3.5): Exotica manual transmission cannot be selected
  (emulation gap, see above); Exotica's Amazon-track glitches are in our
  GL overlay (MAME's renderer via `exotica_gl = 0` is clean) - overlay
  fix queued. The USA draw-distance experiment stays opt-in
  (`gamepatch_crusnusa` / `MIDV_PATCH`); no visible change seen yet.
- Fixed: `save_config` replaced the `[collection]` section, wiping keys
  it did not own (`ffb_diag`, `exotica_gl`, `gamepatch_*`) at every
  launch; it merges now. `launch.log` starts with the applied env.
- Fixed: a stray uncalibrated `fixtures/nvram-crusnusa/crusnusa/nvram`
  file shipped in v0.3.3/v0.3.4 (harmless: the launcher seeds from the
  folder's own `nvram`).

## v0.3.4 — 2026-09-03

- **Force feedback lost after the first game of a session** (tester,
  Fanatec CSL DD; came back only after running another emulator): the
  post-exit force release used to run inside the long-lived launcher
  process, loading the plugin's SDL2 and opening the wheel's haptic device
  there. It now runs in a throwaway process, and the same clean
  open/stop/close runs before every launch.
- The plugin's own **FFBReset.exe** ships in the zip and runs at every
  exit and before every launch when present (a tester confirmed it
  restores FFB on a Fanatec CSL DD); the built-in release is the
  fallback.
- A game process that hangs after closing its window (the known
  exit-time plugin race) is ended after 15 s, and any left-over emulator
  process is ended before a launch - either would keep the wheel and
  MAME's output window, leaving the next game without forces.
- **In-app updates**: `CruisnSetup.exe -> Updates...` (and SETTINGS ->
  CHECK FOR UPDATES in the launcher) checks GitHub Releases, downloads the
  newer zip, closes the launcher, installs over the folder (rig/ and
  roms/ untouched) and reopens it. No account or token needed; the zip
  now carries `version.txt`.
- Support bundle records running emulator processes (`processes.txt`).
- INSTALL: troubleshooting entry for "FFB works once, then gone".

## v0.3.3 — 2026-09-02

- **Direct launch**: `CruisnCollection.exe --game usa|world|offroad|exotica`
  runs one game with the saved settings and no launcher screen (for
  LaunchBox, Stream Deck keys, shortcuts); the process ends with the game.
- **Shift+F12** in a game quits the game and the launcher together
  (plain F12 still returns to the launcher).
- **STEERING SENSITIVITY now actually does something.** It used to write
  MAME's per-port `sensitivity`, which MAME applies and then exactly
  un-applies for absolute controls - a wheel never felt it. It is now a
  gain on the wheel deflection (50-300%, 100% = the game's calibration,
  applied before the curve) inside the same emulator patch as the curve;
  stored values from earlier versions are discarded. INSTALL.md has a
  "Steering feel" section explaining both rows.
- Older romsets' `tms32031.zip` / `tms32032.zip` DSP boot-ROM names are
  accepted: the setup window identifies them by content, and the launcher
  copies an old-name zip to the name MAME 0.286 expects.

## v0.3.2 — 2026-09-02

- **INTERNAL SCALE setting** (SETTINGS, 2X-4X): the render resolution
  knob, for GPUs that can't hold 60 fps at 4X. Takes effect at the next
  launch.
- **FFB STRENGTH 0% now idles the force-feedback plugin** (no game
  handler at all) instead of driving zero-force effects - a one-line A/B
  for "is the plugin costing me speed?".
- Support-bundle diagnostics for slow games: the overlay log carries a
  periodic MAME speed readout and `launch.log` ends with the measured
  average; INSTALL has a four-step slow-game recipe.

## v0.3.1 — 2026-09-02

- **Fixed: v0.3.0 shipped without the force-feedback hook** (`dinput8.dll`)
  and with a Flycast-flavoured `FFBPlugin.ini` - the release build took
  the plugin's files from the first folder holding `MAME64.dll`, which is
  Flycast's. Without the Cruis'n per-game keys the plugin fell back to its
  120 ms effect length, so forces expired between the game's updates -
  the first tester's "FFB comes and goes". The build now takes the
  plugin's "MAME 64bit Outputs" folder (all four files, 64-bit) and ships
  a repo-owned ini (`ffb\FFBPlugin.ini`: the plugin's MAME defaults,
  `GameId=22`, 500 ms effects, `AlternativeFFB=0`); the release script
  refuses to build without the hook DLL.
- **FFB diagnostics** (setup window): logs every force value the game
  sends (`rig\ffb_trace.csv`) alongside the plugin's own `FFBlog.txt`;
  both ride in the support bundle, plus the last `launch.log`.
- **Painless updates**: unzip a new version over the old folder and keep
  everything - the detected wheel GUID is remembered in the rig settings
  and restored into a freshly shipped `FFBPlugin.ini` at launch. Updating
  into a new folder: `CruisnSetup.exe -> Import previous version...` copies
  ROMs, bindings, settings, NVRAM (World calibration) and the wheel over.

## v0.3.0 — 2026-09-02 (alpha test build)

- **Onboarding pass for external testers**: the setup GUI now identifies
  ROM zips by content hash as MAME does (merged sets with renamed or
  nested files, split sets, clones), accepts and reports the Cruis'n
  World rev-2.4 set the collection prefers, and evaluates each installed
  set against its own ROM list (a redumped file no longer flags a game as
  "does not look like this game"). The launcher falls back to World 2.5
  when the 2.4 files are absent and says so on screen; any failed launch
  shows its reason on the menu (emulator output kept in `rig\launch.log`).
  World 2.4 ships with the rig's calibrated NVRAM fixture (other
  hardware still gets World's one-time CALIBRATE CONTROLS prompt - press
  F2 and follow it; now explained on the launching screen). The DSP boot-ROM device sets (`tms320c31` /
  `tms320c32`) are now a setup-window row, an identifiable/installable
  zip, a ROM-table entry, and a pre-launch check with a clear notice
  (a release-layout test aborted with "c31boot.bin NOT FOUND"). **Detect wheel (FFB)** in the setup GUI runs the
  emulator for about thirty seconds, reads the force-feedback plugin's own device
  list and writes your wheel's GUID into `FFBPlugin.ini` (the plugin is
  silent until that line is set - previously a manual log-file hunt).
  README / INSTALL rewritten player-first; `make_release.ps1` no longer
  reuses a stale frozen launcher.
- **Fixed: colored vertical seam lines on 2D screens** - the Cruis'n USA
  continue-screen map showed a full-height line after a race (and Off
  Road's track select showed similar lines). 2D screens are drawn as
  tiles; the renderer's smooth-coverage mode left a half-pixel groove at
  tile boundaries that the arcade hardware's rasterizer fills. Tiles now
  cover exactly the hardware span - the lines are gone at the source on
  every 2D screen - and their textures stay pixel-aligned with the
  arcade (the review measured 2D screens now closer to hardware than
  before the fix).
- **Fixed: crash at the first `MIDV_GL_SNAP` snapshot on most window
  widths** (a buffer overrun in the backbuffer capture; only 4-byte-
  aligned widths ever survived).
- **TRANSMISSION setting** (user design): a global SETTINGS row picks
  H-PATTERN SHIFTER or SEQUENTIAL explicitly, replacing the old
  "full H-pattern wins" inference (which made paddles unreachable on a
  rig that has both). The wizard only asks for the active mode's shift
  steps, and bindings now merge on save - both modes' binds persist, so
  switching is instant and never requires rebinding. Skipped wizard
  steps keep their saved binding.
- Removed the Cruis'n USA VOLUME row that only pointed at the in-game
  = / - keys; it returns if USA's master volume byte gets pinned.
- **Fixed: wizard button capture above 32 died on re-entry** - entering
  CONTROLS SETUP a second time in one shell session left the Raw Input
  listener deaf (stale process-global window class), so wheel buttons
  33+ (e.g. Start/Test/Service on a Moza base) could not be bound again
  until the shell was restarted. The raw listener now survives any
  number of wizard entries.
- **Menu redesign** (user design): selecting a game card now opens a
  per-game submenu - PLAY (default; ENTER-ENTER still launches fast) plus
  that game's settings: steering sensitivity/curve, VOLUME and FREE PLAY
  (written straight into the game's CMOS), and for World a GAME REVISION
  toggle (2.4 manual+auto / 2.5 auto only). The main SETTINGS row is now
  global-only (CRT, crack fill, aspect, margin fill, FFB, controls setup).
- **Wheel navigation**: after the setup wizard, the steering wheel
  navigates every shell menu (left/right on the cards, up/down in lists)
  and the gas pedal is OK/confirm.
- **Sequential / paddle shifting**: the wizard offers SHIFT UP / SHIFT
  DOWN (skippable); paddle-only rigs get MAME's native Sequential shifter
  mode on the V-Unit games (a full H-pattern still wins when both are
  bound). Exotica has no sequential mode in hardware and keeps
  automatic-select for paddle rigs.
- Volume bytes pinned for Off Road (0x2FC) and Exotica (0x27, 0-30 scale)
  from the user's menu-max sessions; World rev 2.4 confirmed to share
  2.5's CMOS layout (volume 0x9C / free play 0x1AC).

- **Cruis'n World manual transmission**: the World card now boots **rev 2.4
  (crusnwld24)** - the last revision with transmission select (rev 2.5's
  factory ROMs are labeled "automatic" and removed the option; no MAME
  config can restore it). Widescreen patch fully ported to 2.4 (54/54 lines
  verified + live-applied); `world_rom = crusnwld` in collection.ini
  returns to 2.5. One-time recalibration + volume/free-play redo expected
  on first 2.4 boot (own CMOS).

- Off Road / all games: no more Windows error "ding" after quitting a game
  (the FFB plugin's exit crash is now bypassed entirely: MIDV_FAST_EXIT).
- Exotica: launcher focus watchdog — input works immediately, no click
  needed.
- Cruis'n USA / World / Off Road: Radio and View 1-3 wheel bindings landed
  one button off (wizard mapping table was shifted); fixed.
- Cruis'n World: the radio panel no longer shows parked at the right edge
  of the 16:9 margin (the game hides it off-screen; now we do too — it
  still slides in normally when Radio is pressed).
- All V-Unit games: translucency (shadows, HUD boxes, the radio panel,
  sprite backboards) now renders as smoked glass at high internal
  resolution instead of chunky black checkerboards. The hardware fakes 50%
  alpha with a per-pixel dither that a CRT blends; the renderer now
  applies that mask at fine pixel granularity (and the crack-filler learned
  to leave it alone). Native/exact mode is untouched — still 100.0000%
  bit-exact.
- Cruis'n World: remaining black terrain gaps in the 16:9 margins (crash
  cameras, close walls) fixed in the game's own polygon clipper — large
  near polygons' sub-pieces are no longer discarded at the old 4:3 edge.
- Cruis'n World: the sky now covers the full 16:9 margins (the game drew
  its scrolling sky panorama only as wide as the original 512px screen, so
  the corners went black whenever the scroll phase fell short - most
  visible behind trees/flags at the screen edges). Fixed in the game's own
  sky engine via the in-memory patch: five panorama tiles instead of
  three, correct per-track banks by construction.
- **The launch "ding" is gone** — it was the FFB plugin's own hook-installed
  chime (`BeepWhenHook=1` in the tuned ini; plugin default is off). Now
  forced off on the rig, at every launch, and in release bundles.
- Real H-pattern shifters work properly: when the wizard has all four
  gears bound, the games are configured for an H-pattern shifter and a
  sit-down cabinet — gears engage when you enter them (not when you
  leave), Cruis'n World offers MANUAL, Exotica shows transmission select.
- The wheel no longer keeps pulling after you quit a game (forces are
  released on every exit), and the launcher no longer freezes if you quit
  a game very quickly after starting it.
- Launcher: the foreground-claim no longer taps ALT (a synthesized
  keystroke that could land in a stray dialog — e.g. a Game Controllers
  panel left open — and ring the system ding at every launch); it uses a
  silent input-queue attach instead.

## v0.2.0 — 2026-08-24

The "improve on the original in every facet that's feasible" release. Four
games, one `vunit.exe`, one launcher.

### Widescreen
- **Off Road Challenge: true 16:9 on BOTH edges via game-code patches** —
  the first game-code widescreen on Midway V-Unit hardware. The right edge
  widens the game's own clip bound (`$11235`: 511 → 597); the left edge,
  which the game tests by sign bit with no constant to widen, is mirrored
  by a 12-word routine in unreachable padding that the nine reject sites
  `CALLLT` into (reject only if all four x < −86). Projection untouched:
  4:3 content is pixel-identical; the margins are drawn by the game itself.
  Auto-applies at ASPECT = 16:9 FULL. (`patch/game/offroadc-widescreen.txt`,
  `docs/offroadc-left-edge-handoff.md`, `docs/widescreen-research.md`)
- Cruis'n Exotica: true full 16:9 (the overlay's margin clear was
  page-blind; the game never culled to 4:3).
- Cruis'n USA / World: ~99 % native margin coverage confirmed — no patch
  needed.
- SETTINGS: **ASPECT / WIDESCREEN** named presets per game (4:3, TRIMMED,
  16:9 FULL); **MARGIN FILL** on/off (default OFF — the clamp-extend was the
  source of edge smear). With fill on, the sky/horizon backdrop is
  suppressed inside the margins so terrain extends instead of water.

### Cruis'n Exotica (Zeus2)
- **In-process GL renderer-replacement at 4× internal resolution**
  (`MIDZ_GL=1`, default), verified 100.0000 % ×3 against a CPU oracle;
  live overlay shipped with CRT pass; 94 % → 99.8 % speed by skipping the
  double rasterization.
- Upstream zeus2 backports: depth-0 guard (stuck black overlay post-race),
  untextured solid-colour quads (flag-girl sprites), translucency clamp
  (the near-black cars).
- Robust Esc-menu pause/resume; resolution popup silenced.

### Launcher, settings, wheel
- **In-game Esc menu** (Resume / CRT toggle / Exit to launcher), drawn by
  the overlay; F9 live CRT toggle; F12 emergency quit.
- Wheel wizard: **Raw Input HID capture (>32 buttons for good)**, axis
  (steer/gas/brake) and keyboard capture, Test/Service/Volume steps,
  service-key collision fix, cooldown UI, Backspace skips / Esc cancels.
- New settings rows: **STEER CURVE**, **STEERING SENSITIVITY**,
  **FFB STRENGTH**, CRT, ASPECT, MARGIN FILL; settings screen layout
  polish; hotkey legend; uniform volume keys; circular glow menu.
- Per-game menu music that switches on highlight with fade transitions
  (`harness/make_music.py`, `gen_game_music.py`).
- Pedal half-axis fix (root cause of Auto/Manual self-selecting); aspect
  wobble fix (hysteresis); frameskip unbind; WER ding fix; boot-message
  capture tool; **support bundle** one-click diagnostics.
- Off Road's 512×401 mode: overlay height per game (last line no longer
  missed).
- Cruis'n World: calibrated NVRAM fixture baked in — the CALIBRATE
  CONTROLS screen is gone for good.

### Telemetry (SimHub / motion / dash)
- Phase A: every MAME output (FFB force, lamps) mirrored as JSON UDP
  datagrams (`MIDV_TELEM_UDP`, `[telemetry] udp=`).
- Phase B: **speed** for Cruis'n USA and Cruis'n World (RAM words found by
  differential hunt), **RPM** for Cruis'n USA (r = +0.91 vs the on-screen
  tach); **runtime HUD OCR speed** (digit templates matched inside the
  emulator) for games without a clean RAM word.
- Phase C: **Forza Horizon "Data Out" format emitter** (`[telemetry]
  forza=`), so SimHub's stock Forza profile just works; ForzaKeeper zeroes
  the dash when no game is running. Standalone provers `forza_probe.py` /
  `forza_synth.py`.

### Tooling / research
- In-memory **game-code patcher** (`MIDV_PATCH`, ROM files untouched,
  old-value guarded) + `patch/game/README.md` technique notes.
- Program disassembly workflow via MAME's debugger; TMS320C3x float
  encoder; constant maps for Off Road (`docs/widescreen-research.md`).
- `capture_drive.py` (one-command driving RAM capture), `capture_boot.py`,
  `record_diag.py`, DSP internal-RAM / second-bank dumping in the patch
  series.
- Achievements feasibility research (`docs/ACHIEVEMENTS.md`, parked).

## v0.1.0 — 2026-08-20

First public build. Cruis'n USA / Cruis'n World / Off Road Challenge with
the in-process GL renderer-replacement (100.0000 % bit-exact vs MAME
videoram at native, 16:9 at 3–4× internal resolution, CRT pass), Cruis'n
Exotica via MAME's own renderer, fullscreen launcher shell with wheel
setup wizard, FFB Arcade Plugin integration, NVRAM fixtures, CI-built
release zip (no ROMs, no binaries hosted outside Releases).
