# Cruis'n Collection

Enhanced PC build of the Midway Cruis'n arcade games — **Cruis'n USA, Cruis'n
World, Off Road Challenge** (V-Unit) and **Cruis'n Exotica** (Zeus2) — built
as a renderer replacement over MAME. One fullscreen launcher, all four games,
wheel + force feedback, true 16:9 at 4× internal resolution, optional CRT
look. **No ROMs are included** — you supply your own.

This is an actively tested alpha. **v0.5.0** includes rendering fixes, all-game
gear/rev telemetry and Exotica force-polarity correction. Fresh installs default
to **CRT on**, full widescreen, 4x rendering and free play. Rendering defects beyond
the tested routes, collision feedback and broader wheel coverage remain open work.
See [release notes and known issues](docs/release-notes/v0.5.0.md), the
[current roadmap](ROADMAP.md) and [documentation index](docs/README.md).

**v0.5.0** adds a per-game **Cheats** submenu for imported MAME cheat files and
**Esc → Cheats** for live toggles and one-shot actions, applied on Resume and
recorded for playback. See [the cheat guide](docs/CHEATS.md) for supported actions,
import instructions and replay diagnostics, and [v0.5.0 notes](docs/release-notes/v0.5.0.md)
for changes and limitations. These features are not in the older v0.4.0 ZIP.

**Settings → Experiments** now sits beside Display, with Shared and per-game
contexts for current rendering trials and future gameplay experiments. Optional
**World Draw Distance** (Off / 2x / 3x) and independent **Scenery Lookahead**
(+0 / +8 / +12 track sections) now support World 2.4 and 2.5. Off Road 1.63 has
its own **Off Road Draw Distance** (Off / 2x / 3x). These trials require widescreen
and scale 2x or higher and default off. The guest-distance comparisons have not shown
additional visible scenery at 3x over 2x with equal lookahead.
On World 2.4, enabling either global distance or the older selective
**Distant Scenery** option turns the other off. **Widescreen Terrain** addresses
missing World edge geometry. Exotica's optional **Widescreen Scenery** similarly
restores edge geometry; it does not extend the far plane. USA's global distance
and Exotica's far/admission trials remain diagnostics pending further validation.
**Crack Fill (Shared)** is now on the same page: it borrows nearby pixels to hide
small gaps and can smear them; its saved setting and existing default are preserved.
**Margin Fill** is retired. Optional per-game
**Impact Cues** are available under Force Feedback, with physical feel still
awaiting validation.

A separate **World 2.4 host scenery prototype** draws pending scenery without
changing guest simulation. Its 2× trial shows earlier hills, buildings and trees;
3× adds a brief mountain benefit in a targeted interval. This is **CLI-only**,
not the menu's World Draw Distance option. Occlusion, handover, longer-range
section loading and occasional rendering stalls remain under investigation.
It is not enabled by an ordinary launcher session. [Evidence and limits](docs/reviews/2026-09-08-world-host-scenery.md).

- [Setup, controls, telemetry and troubleshooting](docs/INSTALL.md)
- [Cheats and supported actions](docs/CHEATS.md)
- [Record and replay a drive](docs/DIAGNOSTIC-REPLAY.md)
- [Current work and acceptance criteria](ROADMAP.md)
- [Local builds and release uploads](docs/LOCAL-BUILDS.md)
- [Public launch preparation](docs/PUBLIC-READINESS.md)
- [Research and historical evidence](docs/README.md#research-and-historical-evidence)

The harness records effective analog wheel inputs, initial configuration and
binary/settings provenance. Candidate changes are compared with their parent
recordings and then replayed against themselves. Native snapshots, completed GL
captures, geometry traces, camera/ADC traces and timings cover different failure
modes; no single passing screenshot certifies a complete driving experience.
The full engineering history is in [results/RESULTS.md](results/RESULTS.md).

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
   | DSP boot ROMs | `tms320c31` for USA / World / Off Road; `tms320c32` for Exotica. Older romsets use `tms32031` / `tms32032`; setup recognizes their contents. |

   Any subset works — missing games just don't appear as playable.
3. **Launch Collection**. Pick a game, drive. Keyboard out of the box:
   **5** = coin, **1** = start, arrows steer, **Esc** = in-game menu.
   Cruis'n World asks you to calibrate once on first boot (press **F2**,
   follow the prompts).
4. Have a wheel? **SETTINGS → CONTROLS → CONTROLS SETUP** binds it in about a minute
   (press-to-bind wheel, pedals, shifter or paddles). SDL force feedback
   targets the steering device; **SETTINGS → FORCE FEEDBACK → STRENGTH** sets it.
   Broader wheel-model and reconnect testing is still in progress.

**Steering feel**: each game has a **STEERING SENSITIVITY** (how far you
turn for full lock; 100% = the game's calibration) and a **STEERING
CURVE** (response shape; below 100 = more bite near center, the cure for
the games' lazy-center feel). Calibrate in-game first, then tune. Details
in [docs/INSTALL.md](docs/INSTALL.md#steering-feel-sensitivity-and-curve).

The repository and [release downloads](https://github.com/d-b-c-e/cruisn-collection/releases)
are public. Update checks and downloads work without a GitHub account.

**Updating**: `CruisnSetup.exe -> Updates...` checks GitHub and installs
the newer version in place (the launcher's SETTINGS → SUPPORT has the same *Check
for updates*). By hand: unzip the new version over the old folder;
your rig settings, calibration, bindings and scores are preserved. Recognized old
FFB input plugins are moved into backups under `rig/update`; an unknown custom
`dinput8.dll` remains intact and must be reviewed before launching or updating.

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
| **Esc** | in-game menu: resume, CRT toggle, Cheats (v0.5.0), exit to the launcher |
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
(SETTINGS → SUPPORT → SAVE SUPPORT BUNDLE in the launcher, or the button in
`CruisnSetup.exe` — it captures logs, your controller layout and the
force-feedback trace, never your ROMs). For force-feedback complaints turn
on SETTINGS → SUPPORT → FFB DIAGNOSTICS first and drive a minute.

## What it is, technically

- The V-Unit games' polygon stream is intercepted from the emulated hardware and
  re-rendered on the GPU: pixel-exact at native resolution (verified
  **100.0000 %** against MAME's own framebuffer), then scaled up 4× with
  higher-resolution edges, 16:9 margins filled with the geometry the
  arcade hardware culled at its 4:3 raster, and an optional CRT pass.
- USA, Off Road Challenge and Cruis'n World get in-memory patches to their own
  game code (ROM files are never touched) so the game itself draws the
  full 16:9 view.
- Cruis'n Exotica has a separate GPU path at 4× via MAME's Zeus2
  emulation (upstream emulation gaps remain: car-select text is illegible).
- Telemetry streams to SimHub as JSON or Forza-format UDP. USA v4.5 reads the
  game's numeric speed-display buffer, with OCR fallback; World still uses OCR.
  Off Road and Exotica now read guarded internal speed producers. All four games
  read actual player-car gears and the rev signals used by their colored tachs,
  including automatic shifts. Revs map to an explicitly estimated 900–8,000 RPM
  arcade scale; the old speed-text RPM mapping remains retired. Live packet and
  independent-memory tests cover every game; Off Road/Exotica still need attended
  all-gear and SimHub/Buttkicker acceptance.
  Wheel force and lamps are separate available output channels.

Native V-Unit comparisons cover specific archived captures. They do not
establish that scaled/widescreen gameplay is artifact-free. Player-driven,
consecutive-frame replay is the primary visual regression workload. Game-code
changes can alter later execution history; matched-state comparisons isolate
visibility fixes, and separate candidate cases check the new build's repeatability.

Full engineering log with every finding and number:
[results/RESULTS.md](results/RESULTS.md).

## Build it (developers)

Builds and checks run locally; GitHub Actions workflows are disabled to avoid
hosted runner usage. Run `python harness/local_checks.py` for Python, native and
GPU checks. [Local build and release workflow](docs/LOCAL-BUILDS.md) explains
how to package, validate and upload the exact tested ZIP.

Release roadmap and required acceptance: [docs/RELEASE-CHECKLIST.md](docs/RELEASE-CHECKLIST.md).
`harness/release_gate.py` checks fresh-install configuration and current regression
evidence, and keeps missing attended checks visible before a public release.

The emulator half is MAME 0.286 plus the patch series in `patch/`; the
launcher and tooling are Python. Setup, build commands, path overrides and
the verification workflow are in [docs/INSTALL.md](docs/INSTALL.md)
(developer section). Current agent/maintainer notes: `AGENTS.md` and
`.Codex/session-notes.md`; older session history remains under `.claude/`.

```
harness/   launcher, setup, recording/replay, local checks and release tools
native/    shared C++ renderer, drivetrain and distance helpers
tests/     Python contracts and standalone native helper checks
gpu/       renderer.py — the verified GPU pipeline (shader source of truth)
patch/     full MAME patch series + in-memory game-code patches (patch/game)
fixtures/  NVRAM so each game boots straight to attract, calibrated
lua/       headless drivers (frame snapshots, scripted coin-up/driving)
results/   RESULTS.md engineering log + proof images
docs/      player/developer guides; dated research under reviews/
media/     default menu artwork and music (excluded with -NoMedia)
lib/toolkit/ pinned wheel-toolkit profiles and version marker
```

## Legal

Cruis'n and the game artwork belong to their respective rights holders. This is
an unofficial project. No game ROMs are distributed; supply your own supported
sets. The modified MAME emulator derives from GPL-2.0+ code; its patch series and
source are included in release packages. SDL2 and the vendored wheel toolkit have
their own included licence notices.

The default package **does include menu artwork and music** from `media/`;
`make_release.ps1 -NoMedia` omits those assets. Asset provenance/permissions and
the original launcher code's licence declaration still need review before public
distribution. See [public readiness](docs/PUBLIC-READINESS.md).
