# Cruis'n POC — Codex Agent Instructions

## Current verified handoff (2026-09-06)

Read `docs/reviews/2026-09-06-seams-distance.md` and `.Codex/session-notes.md` for
current limits; older artifact-free/general speed claims below are historical.
Broad `MIDV_GL_MARGINFILL` is OFF by default after gameplay proved it destroyed
World/Off Road sky detail. `=1` restores that explicit experiment. Local crack
fill is separate. V-Unit GL captures have completed-frame fences; legacy external
viewer captures are not an oracle. USA numeric displayed speed is guarded to
v4.5 and actual HUD submissions, with OCR fallback; other games need their own
producers. Force impacts and attended recording are opt-in, never run unattended.
Toolkit pin is v0.11.1. Keep the new LOD patch experimental, not a default.
Quality rendering now retains fine samples in native-empty spans. Geometry
T-junction alignment is opt-in (`MIDV_GL_TJUNCTIONS=1`), never native-exact mode.
Zeus now has completed-frame captures and a 6,000-frame driving case with 21
actual GL reference images. Its live path skips CPU polygons: old matching black
native images were NOT a gameplay oracle, and headless/live differences did not
establish nondeterminism. Use `replay.py --compare-gl`; `--zeus-native` is a slow
double-rasterization diagnostic. `run_regressions.py` runs six local cases with
explicit coverage and timing gates. RPM is unavailable; never restore the old
E632 mapping, which interpreted packed speed text as engine RPM.

## What this is

Working proof-of-concept for a **native PC port of the Midway Cruis'n
games** (Cruis'n USA, Cruis'n World, Off Road Challenge — V-Unit hardware,
renderer-replaced and verified bit-exact — plus **Cruis'n Exotica**, Zeus2
hardware, with a live Zeus GL replacement and a MAME-renderer fallback;
upstream emulation limitations remain). Built as a
renderer-replacement over MAME, the same architecture as wanszai's arcade
ports. As of 2026-09-05 the collection launches all four games with scaled
widescreen rendering and built-in SDL force feedback, conditioned by the
vendored wheel-toolkit shaper. Gameplay rendering artifacts, collision feel,
and telemetry coverage remain open. USA's measured GDI selection slowdown is fixed
with an underlying D3D window; native exactness
on archived captures must not be described as proof of artifact-free gameplay.

Current assessment: `docs/reviews/2026-09-05-assessment.md`, with dedicated
widescreen/distance, replay/testing, FFB and telemetry companion reports.
The user authorized implementation after committing/pushing this assessment
baseline. Prioritize diagnostic evidence and real gameplay input replay;
automated graphics runs must disable physical wheel output. Preserve the
review reports as a dated baseline and record fixes separately.

Implemented workflow: `docs/DIAGNOSTIC-REPLAY.md`; results and remaining work:
`docs/reviews/2026-09-05-implementation.md`. Record with `run_rig.py --record-case`;
replay with `harness/replay.py`. Both disable wheel force. Real USA synthetic
gameplay has matched 6,000 input frames and 100 native snapshots on replay.
The user's LA Freeway recording and a separate improved-build candidate each
replay 5,012 frames / 83 native images exactly. This does not establish other
games or GL pixel equality. Preserve `results/diagnostics/my-drive` unchanged.
See `docs/reviews/2026-09-05-recorded-drive-findings.md` for the UV atlas-bleed
fix, USA object-visibility patch and crack-filler reassessment. A full-run game
patch changes later native frames; use late matched-state tests for causal
graphics comparisons and a separate candidate case for new-build determinism.
New recordings defer PNG encoding until exit (`raw-snap/` retained and hashed).
`replay.py --patch --patch-at-frame --capture-state` checks effective program
words; `verify_scene_extension.py` checks preserved draw order and native RAM.
`verify_quality.py` runs ROM-free GPU fixtures locally and under Mesa in CI.
Run `python -m unittest discover -s tests -v` for hardware-free harness checks.
Toolkit source is pinned to v0.11.1: `harness/sync_toolkit.py --ref v0.11.1`
checks both consumers; `--write` updates. The OCR filter's canonical source is
`native/hud_speed_filter.h`; reset-time patch preflight is in `native/checked_patch.h`.
`harness/sync_native.py` checks both MAME copies. Patch installation validates
the entire file before writing; the legacy per-frame self-healer remains per-word.
Configured game experiments compose with widescreen defaults; conflicts fail.
An explicit `MIDV_PATCH` environment setting replaces all defaults.

**Read these two documents before doing anything:**

1. `results/RESULTS.md` — the complete chronological engineering log. Every
   phase, every bug, every number, current staging state. This is the primary
   handoff document.
2. `E:\Source\launchbox\Launchbox-Racing\docs\cruisn-usa-port-feasibility.md`
   — strategy, product roadmap, feature wishlist, collection framing, legal
   posture (WB owns a live brand: no ROMs shipped, no binaries hosted, GPL
   obligations from deriving from MAME).

`.Codex/session-notes.md` has the immediate open items and a complete
self-sufficient handoff (written for context-loss resilience).

**GitHub:** `d-b-c-e/cruisn-collection` (private; renamed from cruisn-poc
2026-08-20 — old URL redirects). Releases publish via tag push
(`.github/workflows/release.yml`); see CHANGELOG.md for releases. Local folder renamed
to `E:\Source\cruisn-collection` 2026-08-20 (matches the repo name).

## Repo map

```
cruisn-collection/
├── harness/
│   ├── collection.py     ← THE product entry: fullscreen game-select shell
│   │                     (Stream Deck button opens this; config rig/collection.ini)
│   ├── run_rig.py        single-game launcher (in-process GL, sound, wheel);
│   │                     importable: collection.py calls launch_game()
│   ├── run_oracle.py     determinism oracle (2 cleanroom runs, pixel diff)
│   ├── run_capture.py    instrumented capture (quads + state dumps)
│   ├── rasterize.py      CPU reference rasterizer (bit-exact vs MAME)
│   ├── widescreen.py     16:9 margin analysis/render
│   └── record_diag.py    60fps desktop capture + frame-diff (flashing detector)
├── gpu/
│   ├── renderer.py       verified GPU pipeline (moderngl). THE SHADER SOURCE OF
│   │                     TRUTH — midvunit_gl_shaders.h is generated from it
│   └── live_viewer.py    out-of-process viewer (debug/reference path, MIDV_LIVE)
├── lua/snap.lua          frame-scheduled snapshots (SNAP_FRAMES env)
├── fixtures/nvram-crusnusa/  calibrated NVRAM (skips CALIBRATE CONTROLS boot)
├── patch/vunit-poc-patches.patch  FULL series vs mame-src base 6f55ed93
├── results/              RESULTS.md + proof images + flash-evidence
└── rig/                  gitignored per-user runtime (ini/nvram/cfg)
```

## The mame-src relationship (critical)

- The emulator half lives in **`E:\Source\mame-src`**, branch **`poc/quadlog`**
  (MAME 0.286 + our DIJOYSTATE2 base patch `6f55ed93` + the POC series).
  POC code: **`src/mame/midway/midvunit_v.cpp`** (env-gated, zero cost when
  unset) + `midvunit.h` (visibility + `mvgl_exit` teardown hook) + one
  7-line env-gated block in `src/frontend/mame/ui/ui.cpp`
  (`MIDV_SKIP_STARTUP_SCREENS` — BAD_DUMP warning screens refuse
  skip_warnings by design and block launcher boots).
- Build product is **`E:\Source\mame-src\vunit.exe`** (subtarget build —
  physically cannot clobber `mame.exe`). Since 2026-08-20 the subtarget
  includes **midzeus** (Cruis'n Exotica): build with
  `SOURCES=src/mame/midway/midvunit.cpp,src/mame/midway/midzeus.cpp`.
- **`midvunit_gl_shaders.h` is GENERATED — never hand-edit.** Regenerate
  after any shader change in `gpu/renderer.py`:
  **`python harness/gen_shaders.py`** (emits escaped C strings — genie's
  REGENIE source scanner cannot tokenize raw strings and dies with
  "unterminated character literal").
- **Force feedback is built into vunit.exe** (2026-09-03, `mvffb` in
  `midvunit_v.cpp`, replaces the FFB Arcade Plugin on Endprodukt's advice):
  the drivers hand the signed motor byte to `midv_ffb_write()` (V-Unit
  WHLCTLZ, Exotica LED-board offset 0, after gain/slew/clamp) and a worker
  thread drives ONE signed constant force on the wheel's steering axis
  through SDL2 haptics (Cannonball DX / Flycast model: STEERING_AXIS,
  infinite length, update + run per write). **`SDL2.dll` (MSYS2
  `/mingw64/bin`, 2.32) sits UNTRACKED beside vunit.exe** and is loaded at
  run time - no import, no build-time link; without it FFB is off and
  `midv_ffb.log` says so. Byte interpretation = the plugin's Cruis'n
  handler (0 stop, |v|/126). Sign: a positive byte pushes RIGHT (Exotica
  spring measurement) and a positive SDL level turns the Moza LEFT, so the
  level is `-sign(byte)`; `MIDV_FFB_INVERT` / SETTINGS FFB DIRECTION flips
  it. The game writes the motor every frame (~17 ms), so the 500 ms hold
  watchdog only fires on pause/exit. The old plugin files are parked in
  `mame-src/_plugin-backup-*` (never copy them back: its dinput8.dll hooks
  the process).
- Known-cosmetic: vunit exits sometimes logged a post-exit ACCESS VIOLATION
  (Event Log; also fired headless with our GL thread not running — it was
  attributed to the plugin's teardown; re-observe now that it is gone).
  Our GL and FFB threads stop cleanly via machine-exit notifiers.
  WER minidumps land in `rig/crashdumps/` for future forensics.
- After committing in mame-src, refresh the exported series (FULL series
  from the upstream tag — CI and INSTALL.md apply it onto a clean mame0286
  clone, so the DIJOYSTATE2 base commit must be included):
  `git format-patch --stdout mame0286..HEAD > E:/Source/cruisn-collection/patch/vunit-poc-patches.patch`
- ⚠️ **NEVER touch the racing build's deployed
  `Launchbox-Racing\Emulators\mame286\mame.exe`.** The POC only reads its
  `roms/`, `ctrlr/`, and nvram fixtures.

## Build environment

- **MSYS2 at `E:\msys64`** (NOT C:\ — that died in the C: wipe), GCC 16.2.0.
- Build (incremental ≈1 min; from Git Bash):
  ```
  env MSYSTEM=MINGW64 /e/msys64/usr/bin/bash.exe -lc "export OS=Windows_NT; \
    cd /e/Source/mame-src && make SUBTARGET=vunit \
    SOURCES=src/mame/midway/midvunit.cpp,src/mame/midway/midzeus.cpp \
    NOWERROR=1 TOOLS=0 -j18"
  ```
- ⚠️ `OS=Windows_NT` must be exported **inside** the MSYS2 login shell — its
  profile clears the inherited value and MAME's makefile then fails OS
  detection. Add `REGENIE=1` only on first build / project changes.
- Python side: system Python 3.14 with numpy, pillow, moderngl, glfw
  (pygame has no 3.14 wheels — don't try).

## Env vars (all read by vunit.exe, all inert when unset)

| var | effect |
|---|---|
| `MIDV_GL=1` | **in-process GL renderer** (the product path) |
| `MIDV_GL_SCALE` | internal scale (default 3; rig uses 4) |
| `MIDV_GL_CRT=1` | CRT pass on at boot (mask+scanlines+curvature); **F9** toggles live |
| `MIDV_GL_CRACKFILL=0` | disable crack fill (default ON: unwritten hardware quad-crack pixels get filled from axis-bounded neighbours in the palette pass; 3D scenes only; shell SETTINGS has the toggle) |
| `MIDV_SKIP_STARTUP_SCREENS=1` | boot straight past MAME warning/info screens (frontend gate) |
| `MIDV_TELEM_UDP=host:port` | mirror MAME outputs (wheel force, lamps) as JSON UDP datagrams (SimHub/Buttkicker); also via collection.ini `[telemetry] udp=` |
| `MIDV_FFB=1` | **built-in force feedback** (SDL2 haptics on the wheel's steering axis); `MIDV_FFB_STRENGTH` 0-100, `MIDV_FFB_DEVICE` name substring or vid:pid, `MIDV_FFB_INVERT=1`, `MIDV_FFB_HOLD_MS` (500), `MIDV_FFB_TEST=<pct>` (1.5 s level at start), `MIDV_FFB_LOG=2` (every write) → `midv_ffb.log` |
| `MIDV_FFB_SMOOTH` / `MIDV_FFB_DAMPER` / `MIDV_FFB_FRICTION` | low-pass time constant (ms) on the level; DirectInput damper / friction condition effects in % for the session (launcher: `[collection] ffb_smooth / ffb_damper / ffb_friction`) |
| `MIDV_FFB_CLAMP` / `MIDV_FFB_SLEW` | cap the motor byte at ±N / limit its change per write (driver side, before the FFB output and the trace) |
| `MIDV_FFB_TRACE=<csv>` | every output change + `wheelpos` rows (the FFB diagnostics trace) |
| `MIDZ_FFB_GAIN` | Exotica spring gain percent (launcher passes 400) |
| `MIDV_GL_SNAP=<dir>` | backbuffer BMP every ~150 presents (unattended verify) |
| `MIDV_GL_LOG=1` | diagnostics to `midv_gl.log` in cwd |
| `MIDV_LIVE=1` | shared-memory ring only (drive `gpu/live_viewer.py`) |
| `MIDZ_GL=1` | **live Zeus GL overlay** (Cruis'n Exotica renderer-replacement; default ON via run_rig, =0 falls back to MAME d3d/bgfx). MIDZ_GL_SCALE/CRT/SNAP/LOG/VSYNC variants |
| `MIDV_QUADLOG=<file>` | offline quad capture (38-byte records) |
| `MIDV_STATEDUMP_FRAME/DIR` | one-shot videoram/texram/palette dump |

## Verification workflow (the project's superpower)

Attract mode is a **bit-identical deterministic oracle** (seeded NVRAM
fixture required). The invariant to protect: `gpu/renderer.py` exact mode
(`--scale 1`) must stay **100.0000%** vs MAME's videoram on
`results/capture` and `results/capture-8000`. After any shader/pipeline
change: `python gpu/renderer.py results/capture-8000` and expect zero
differing pixels. Fresh captures: `run_capture.py <vunit> <frame>`.

Semantics that everything relies on (full detail in RESULTS.md):
- `page_control` bit 2 = render-target page, bit 0 = visible page; a run of
  consecutive same-pc quads = one **scene**; last COMPLETE scene =
  second-to-last run (never trust quad-count thresholds for this).
- Pages persist between scenes (hardware behavior — 3px cracks show prior
  frame); the 16:9 **margins are ours** and get scissor-cleared per scene
  with a 2px overscan inset.
- 2D screens are detected by **axis-aligned-rectangle dominance ≥70%** and
  crop to 4:3 (quad counts overlap between 2D ~160 and sparse 3D ~260).
- The in-process overlay is an **owned top-level popup**, NOT a child window
  — MAME's gdi caches its window DC so child-clipping can never work.
  V-Unit now runs with `video d3d` underneath; `CRUISN_VUNIT_VIDEO=gdi` is the
  compatibility fallback. NOACTIVATE/TRANSPARENT/DISABLED keep input on MAME.

## Rig facts

- Product entry: `python harness/collection.py` — fullscreen shell, all
  four games, menu music + blips (`rig/assets/`, regenerable via ffmpeg
  from LaunchBox video snaps); C toggles CRT per launch; **S = wheel-setup
  wizard** (press-to-bind → `[wheelmap]` in `rig/collection.ini`, applied
  by the ctrlr generator each launch; wins over EmuEz per-game sections).
  Config `rig/collection.ini`. Stream Deck entry: Elgato "Games" key [7,2]
  → `Launchbox-Racing\scripts\Launch-Cruisn.bat` opens the shell. Direct:
  `python harness/run_rig.py --rom crusnusa [--crt]`. Coin=**5**,
  Start=**1** keyboard, **Esc = in-game options menu** (Resume / CRT
  toggle / Exit to launcher — drawn by the GL overlay, physical-key
  polled), **F9** = CRT live toggle, **F12** = emergency instant quit
  (UI_CANCEL is remapped off Esc in the generated ctrlr). crusnwld needs ONE-TIME
  wheel calibration at first boot (persists; headless runs always
  re-demand it — no input devices — so captures must run in rig config).
- All three games verified **100.0000% bit-exact** vs MAME videoram
  (offroadc runs 512×**401** with visarea right edge 510 — renderer.py
  honors meta visarea in exact mode; the launcher passes MIDV_GL_HEIGHT=401
  to the C++ overlay for Off Road).
- Wheel buttons 33-48 = MAME tokens `ADDSW1-16` (not BUTTON33+; 49+ are
  unaddressable OTHER_SWITCH). winhybrid (default provider) needed the
  DIJoystick2 fix (mame-src 3cac3d67) — without it every wheel caps at 32
  buttons (this also silently afflicted the racing build).
- run_rig makes MAME's window **borderless-fullscreen** post-boot
  (`--windowed` opts out) and **enforces fg+focus on MAME's window** —
  keyboard and foreground-mode DirectInput FFB die without it. Never
  activate the overlay (owner's last-active-popup redirection eats keys;
  SwitchToThisWindow is banned).
- ⚠️ **Never hard-kill with FFB active** — stranded constant-force torque on
  the Moza; Esc out normally; Stream Deck "Stop FFB" key clears a stuck
  wheel. Remote/automation quit: WM_CLOSE on MAME's window is clean.
- run_rig still relaunches once when no responsive window shows in 20 s
  (a plugin-era safety net; harmless).
- If the wheel steers but FFB is silent: read `midv_ffb.log` beside
  vunit.exe (device list, which one was taken, "no constant-force device",
  strength 0). The wizard's steering device name is what
  `MIDV_FFB_DEVICE` gets.
- Known: `JOYCODE_1_BUTTON33+` tokens are dropped by the token parser AND
  invalidate the whole seq (killed keyboard Start). run_rig writes a
  sanitized EmuEzRacing copy to `rig/ctrlr/` (never edits the racing
  build's). Root cause vs the 128-button DIJOYSTATE2 patch: **deferred by
  user decision (2026-08-18) into the collection shell's wheel-mapping
  frontend** — keyboard 5/1 is the accepted interim for coin/start.
- Probe facts: GDI screen capture shows the GL overlay as pure black — use
  `MIDV_GL_SNAP` for ground truth; keybd_event-injected keys never reach
  MAME's rawinput — keyboard verification needs physical keys.
- The user's live observations at the screen are the best debugger this
  project has — four artifact root-causes came from them. Describe-what-you-
  see beats instrumentation; `record_diag.py` catches what screenshots can't.

## Working style

- RESULTS.md is append-only chronology: add dated sections, never rewrite
  history. Keep proof images in `results/proof/` (capture dirs are regenerated
  and gitignored).
- Commit mame-src and cruisn-collection separately; refresh the patch series after
  mame-src commits.
- Bit-exactness claims require four decimal places — "100.00%" once hid a
  99.9985 that cost an hour.
