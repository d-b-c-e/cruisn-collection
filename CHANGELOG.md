# Changelog

All notable changes to Cruis'n Collection. Dates are YYYY-MM-DD. The full
engineering log with numbers and proof images is `results/RESULTS.md`.

## v0.3.4 — 2026-09-03

- **Force feedback lost after the first game of a session** (tester,
  Fanatec CSL DD; came back only after running another emulator): the
  post-exit force release used to run inside the long-lived launcher
  process, loading the plugin's SDL2 and opening the wheel's haptic device
  there. It now runs in a throwaway process, and the same clean
  open/stop/close runs before every launch.
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
