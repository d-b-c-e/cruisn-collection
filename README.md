# Cruis'n Collection

Native PC port of the Midway Cruis'n arcade games — **Cruis'n USA, Cruis'n
World, Off Road Challenge** (V-Unit) and **Cruis'n Exotica** (Zeus2) — built
as a renderer replacement over MAME. One fullscreen launcher, all four games,
wheel + force feedback, true 16:9 at 4× internal resolution, optional CRT
look. **No ROMs are included** — you supply your own.

## Play it (players / testers)

1. Download the latest zip from
   [Releases](https://github.com/d-b-c-e/cruisn-collection/releases) and
   unzip it anywhere (no installer, no Python, no admin).
2. Double-click **`CruisnSetup.exe`** → **Add ROM file(s)** and pick your
   MAME 0.286 ROM zips. Any filename works — files are identified by their
   contents. You need:

   | game | set(s) |
   |---|---|
   | Cruis'n USA | `crusnusa` |
   | Cruis'n World | `crusnwld` **plus** `crusnwld24` (rev 2.4 keeps the manual transmission; a merged `crusnwld` set already contains it) |
   | Off Road Challenge | `offroadc` |
   | Cruis'n Exotica | `crusnexo` |
   | all three V-Unit games / Exotica | `tms320c31` / `tms320c32` (older romsets: `tms32031` / `tms32032` — same files) | tiny DSP boot-ROM *device* sets from the same MAME romset — easy to miss, required |

   Any subset works — missing games just don't appear as playable.
3. **Launch Collection**. Pick a game, drive. Keyboard out of the box:
   **5** = coin, **1** = start, arrows steer, **Esc** = in-game menu.
   Cruis'n World asks you to calibrate once on first boot (press **F2**,
   follow the prompts).
4. Have a wheel? **SETTINGS → CONTROLS SETUP** binds it in about a minute
   (press-to-bind; any wheel, pedals, shifter or paddles). Force feedback
   then goes to that wheel by itself; **SETTINGS → FFB STRENGTH** sets it.

**Steering feel**: each game has a **STEERING SENSITIVITY** (how far you
turn for full lock; 100% = the game's calibration) and a **STEERING
CURVE** (response shape; below 100 = more bite near center, the cure for
the games' lazy-center feel). Calibrate in-game first, then tune. Details
in [docs/INSTALL.md](docs/INSTALL.md#steering-feel-sensitivity-and-curve).

**Updating**: `CruisnSetup.exe -> Updates...` checks GitHub and installs
the newer version in place (the launcher's SETTINGS has the same *Check
for updates*). By hand: unzip the new version over the old folder;
everything you set up is kept.

## Skip the launcher (frontends, shortcuts, Stream Deck)

Start one game directly, with your saved settings and no launcher screen:

```
CruisnCollection.exe --game usa
```

`usa`, `world`, `offroad` or `exotica` (the MAME names `crusnusa`,
`crusnwld`, `offroadc`, `crusnexo` work too); add `--windowed` to stay
windowed. The process ends when the game does, so LaunchBox, a Stream Deck
key or a desktop shortcut can treat it like any other game executable.

## Keys while playing

| key | does |
|---|---|
| **5** / **1** | coin / start (or your bound wheel buttons) |
| **Esc** | in-game menu: resume, CRT toggle, exit to the launcher |
| **F9** | CRT look on/off |
| **F12** | quit the game, back to the launcher |
| **Shift+F12** | quit the game **and** the launcher — straight to the desktop |
| **F2** / **9** | game test menu / service |

Everything else — the in-game menu, per-game settings, force feedback,
troubleshooting, and how to report a bug with a support bundle — is in
**[docs/INSTALL.md](docs/INSTALL.md)**. What changed per version:
[CHANGELOG.md](CHANGELOG.md).

**Alpha testers:** when something looks or feels wrong, the most useful
report is *what you expected vs what you saw*, plus a **support bundle**
(SETTINGS → SAVE SUPPORT BUNDLE in the launcher, or the button in
`CruisnSetup.exe` — it captures logs, your controller layout and the
force-feedback trace, never your ROMs). For force-feedback complaints turn
on SETTINGS → FFB DIAGNOSTICS first and drive a minute.

## What it is, technically

- The games' polygon stream is intercepted from the emulated hardware and
  re-rendered on the GPU: pixel-exact at native resolution (verified
  **100.0000 %** against MAME's own framebuffer), then scaled up 4× with
  sub-pixel-accurate edges, 16:9 margins filled with the geometry the
  arcade hardware culled at its 4:3 raster, and an optional CRT pass.
- Off Road Challenge and Cruis'n World get in-memory patches to their own
  game code (ROM files are never touched) so the game itself draws the
  full 16:9 view.
- Cruis'n Exotica renders through the same GPU path at 4× via MAME's Zeus2
  emulation (upstream emulation gaps remain: car-select text is illegible).
- Telemetry (speed, RPM, wheel force, lamps) streams to SimHub / motion
  rigs as JSON or Forza-format UDP.

Full engineering log with every finding and number:
[results/RESULTS.md](results/RESULTS.md).

## Build it (developers)

The emulator half is MAME 0.286 plus the patch series in `patch/`; the
launcher and tooling are Python. Setup, build commands, path overrides and
the verification workflow are in [docs/INSTALL.md](docs/INSTALL.md)
(developer section). Agent/maintainer notes: `CLAUDE.md`.

```
harness/   launcher (collection.py), run_rig.py, setup GUI, capture/oracle tools
gpu/       renderer.py — the verified GPU pipeline (shader source of truth)
patch/     full MAME patch series + in-memory game-code patches (patch/game)
fixtures/  NVRAM so each game boots straight to attract, calibrated
lua/       headless drivers (frame snapshots, scripted coin-up/driving)
results/   RESULTS.md engineering log + proof images
```

## Legal

Cruis'n USA, Cruis'n World, Off Road Challenge, Cruis'n Exotica and their
art are Midway / Warner Bros. properties. This project distributes no ROMs
and no game assets: original launcher code, a GPL-2.0+ patch series against
MAME (source included, as GPL requires) and SDL2 (zlib license, included) for
wheel force feedback. Supply your own legally obtained ROM dumps.
