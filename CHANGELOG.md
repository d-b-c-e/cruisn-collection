# Changelog

All notable changes to Cruis'n Collection. Dates are YYYY-MM-DD. The full
engineering log with numbers and proof images is `results/RESULTS.md`.

## Unreleased

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
- Cruis'n World: the sky now covers the full 16:9 margins (the game drew
  its scrolling sky panorama only as wide as the original 512px screen, so
  the corners went black whenever the scroll phase fell short - most
  visible behind trees/flags at the screen edges). Fixed in the game's own
  sky engine via the in-memory patch: five panorama tiles instead of
  three, correct per-track banks by construction.
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
