# Changelog

All notable changes to Cruis'n Collection. Dates are YYYY-MM-DD. The full
engineering log with numbers and proof images is `results/RESULTS.md`.

## Unreleased

- Added an independent assessment of widescreen/rendering, force feedback,
  telemetry and reliability, plus a design for recording and replaying actual
  driving as the primary gameplay regression suite. No behavior changes are
  included in the assessment baseline.

- **CRISP is the default feel**, with no centring spring. Driven at the rig
  against original MAME plus the FFB Arcade Plugin at matched strength, that
  pairing read closest to the arcade signal; the 50 ms STANDARD tune remains
  as the reference point to compare against.

- **The centring spring was drowning everything, and is now adjustable.**
  It was created at its full percentage of the *wheel's* maximum force with
  no ceiling, while the game's own feedback was scaled down by FFB STRENGTH
  - so the spring was stronger than the road it was meant to sit under and
  reached maximum at a modest angle. Spring, damper and friction now scale
  with FFB STRENGTH and cap their saturation to the same level, so the
  balance between them holds wherever STRENGTH is set (72 at strength 50 is
  36% of the wheel, and `midv_ffb.log` states it per effect).
- **SETTINGS > FORCE FEEDBACK > SPRING** sets it directly - OFF, then 10 to
  100 - instead of a config-file edit. Cruis'n Exotica never gets one
  whatever the setting says, because that game generates its own.

- **Force feedback got simpler on purpose.** Three settings were removed
  because each had a twin that did the same job - `ffb_smooth`, `ffb_slew`
  and the FFB PEAK LIMIT row all duplicated something in the FEEL profile,
  and where two settings do one job one of them silently wins. That was not
  hypothetical: `ffb_smooth` was overriding every FEEL tune with the same
  number, which made all four tunes identical and the whole feature inert
  from the moment it shipped. Fixed, and the duplicates are gone.

  There are now three places, each owning one thing: **STRENGTH** decides how
  strong, **FEEL** decides how the force is shaped (smoothing, ceilings, rate
  limits), and `rig\collection.ini` holds only the effects your wheel adds
  that the game never sent - spring, rumble, damper, friction. Anything the
  old knobs did is still available, in the profile, where it can be changed
  coherently instead of fighting a menu row.

- **The centring spring is back on for Cruis'n USA.** Releases up to v0.3.0
  packaged the force-feedback config from this project's own rig, which runs
  a 72% centring spring on USA and none on World or Off Road. From v0.3.1 the
  packaging switched to a clean template where the spring is off everywhere,
  and it has been missing since - the "centre feels looser than normal"
  report. It is available again as **SETTINGS > FORCE FEEDBACK > SPRING**,
  but **off by default**: shipped at 72 for a few hours on the strength of
  the config the early releases carried, it buried the road detail it was
  meant to sit under, because the games' own forces are small next to a
  constant device effect. Turn it on if you want centring; start low.
  Cruis'n Exotica is deliberately excluded: that game generates its own
  centring force, so a second one on the wheel would fight it.
  Override per game with `[collection] ffb_spring_<rom>` (0 turns it off).

- **SETTINGS > FORCE FEEDBACK > FEEL** steps through alternative tunes of the
  same forces, so trying one is a menu row rather than a config edit. Four
  ship, and they differ in exactly one parameter - how quickly the wheel
  follows the game - so an A/B can only be that: **RAW** (no filtering, most
  detail, liveliest), **CRISP**, **STANDARD** (the default, unchanged from
  v0.3.7) and **CALM** (for a strong base that hunts). Drive two and say
  which you preferred. Your own tunes go in `force-profiles.user.ini` beside
  the emulator, which updates never overwrite. A ready-made
  **`force-profiles.user.ini.example`** ships beside the emulator for that:
  every value already at the shipped default with a comment on what it
  changes, inert until you drop the `.example` from its name.

- FFB DIAGNOSTICS moved from the FORCE FEEDBACK page to SUPPORT, next to the
  bundle it feeds.

- **The launcher menu no longer jumps into a submenu by itself.** It looked
  like the left arrow key was acting as ENTER; in fact a wheel base can
  report far more buttons than it has (this project's Moza R12 exposes 132)
  and pulse the unused ones on its own - measured at ~30 edges a second,
  on a different button from one run to the next. The menu accepted *any*
  wheel button as OK, so an isolated phantom pulse became ENTER, landing in
  whatever frame you happened to be pressing a key. Only buttons you bound
  in CONTROLS SETUP can confirm a menu row now (gears excluded - an
  H-pattern shifter holds one closed). With nothing bound yet, any button
  still works, so a fresh install is unaffected.
- `CRUISN_INPUT_DEBUG=1` traces where each menu action came from (keyboard,
  hat, wheel button, steering, gas) - what pinned the above down.

- **Cruis'n Exotica can be driven with a manual transmission at last.** The
  TRANS SELECT screen ("A / AUTO / M") always confirmed AUTO no matter what
  the wheel, shifter or buttons did, and we had it logged as a gap in the
  upstream emulation. It is not: the screen is gated on a barely documented
  DIP switch, DS1 **"Wheel Invert"**. With it off the game confirms
  instantly; with it on the screen reads the wheel properly. Credit to
  Endprodukt for spotting it. The launcher now sets that DIP for Exotica
  (and cancels the wheel mirroring it would otherwise apply to driving, so
  steering is unchanged). **On that screen, turn the wheel LEFT for
  MANUAL.** `[collection] exotica_manual = 0` opts out.
  This also brings the virtual sequential shifter for Exotica to life - it
  has been shipped but inert since v0.3.5, waiting for exactly this.

- **Lamp and LED outputs came back.** Retiring the force-feedback plugin in
  v0.3.6 removed one line from the emulator's config - the Windows output
  module the plugin needed - and that module is what *every* external
  consumer reads (cabinet lamps, LED boards, SimHub and Buttkicker feeds).
  MAME's default silently resolves to "no output module", so they all went
  quiet. Restored; our own force feedback never used it.
- **Cruis'n Exotica was running in slow motion** — fixed upstream and
  backported (mamedev/mame#16046 by mourix). The driver clocked the
  TMS320C32 timers at 10 MHz, but the games select the chip's internal
  clock at 15 MHz, so the whole game ran about a third too slow. Expect
  Exotica to feel quicker; its force effects arrive at the right rate too.
- **The dark band across Exotica's background during races is gone** (same
  backport): a Zeus register bit picks between two colour/depth buffer
  layouts and the driver decoded only one of them, so a screen clear wrote
  colour bytes into the depth buffer.
- The wheel-motor output is now named `wheel_motor` (was `wheel`), matching
  the naming in mamedev/mame#16055, which upstreams the Exotica wheel motor
  this project located. Support-bundle force traces read either name.

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
