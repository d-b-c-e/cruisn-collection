# Cruis'n POC — Claude Agent Instructions

## What this is

Working proof-of-concept for a **native PC port of the Midway V-Unit racers**
(Cruis'n USA, Cruis'n World, Off Road Challenge — the "**V-Unit Cruis'n
Collection**"), built as a renderer-replacement over MAME, the same
architecture as wanszai's arcade ports. As of 2026-08-18 the whole chain is
**working and rig-verified**: the game runs in one window with an in-process
GPU renderer at 16:9 / 3-4× internal resolution, artifact-free, with FFB
staged for wheel testing.

**Read these two documents before doing anything:**

1. `results/RESULTS.md` — the complete chronological engineering log. Every
   phase, every bug, every number, current staging state. This is the primary
   handoff document.
2. `E:\Source\launchbox\Launchbox-Racing\docs\cruisn-usa-port-feasibility.md`
   — strategy, product roadmap, feature wishlist, collection framing, legal
   posture (WB owns a live brand: no ROMs shipped, no binaries hosted, GPL
   obligations from deriving from MAME).

`.claude/session-notes.md` has the immediate open items.

## Repo map

```
cruisn-poc/
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
  physically cannot clobber `mame.exe`).
- **`midvunit_gl_shaders.h` is GENERATED — never hand-edit.** Regenerate after
  any shader change in `gpu/renderer.py`:
  `python -c "import sys; sys.path[:0]=['gpu','harness']; import renderer as R; open(r'E:\Source\mame-src\src\mame\midway\midvunit_gl_shaders.h','w',newline='\n').write('// GENERATED from cruisn-poc/gpu/renderer.py\n\n' + ''.join('static const char *MVGL_%s = R\"GLSL(%s)GLSL\";\n\n' % (n, getattr(R,n)) for n in ('VS','FS','PAL_VS','PAL_FS')))"`
  (run from cruisn-poc; the header names are MVGL_VS/FS/PAL_VS/PAL_FS).
- **FFB Arcade Plugin** files sit UNTRACKED beside vunit.exe (`dinput8.dll`,
  `FFBPlugin.ini`, `SDL2.dll`, **`MAME64.dll`** — copied from the racing
  build's mame286, which holds the tuned Cruis'n settings, GameId=22).
  MAME's own .gitignore hides them; re-copy if missing. ⚠️ Without
  MAME64.dll (the MAME output client) the plugin shows a "MAME64.dll is
  missing!" dialog and FFB is static spring/damper only — game forces need
  it (success = `RomName = <rom>` in FFBlog.txt beside vunit.exe).
- Known-cosmetic: vunit exits sometimes log a post-exit ACCESS VIOLATION
  (Event Log; also fires headless with our GL thread not running — plugin
  teardown race). Our GL thread stops cleanly via a machine-exit notifier.
  WER minidumps land in `rig/crashdumps/` for future forensics.
- After committing in mame-src, refresh the exported series:
  `git format-patch --stdout 6f55ed93..HEAD > E:/Source/cruisn-poc/patch/vunit-poc-patches.patch`
- ⚠️ **NEVER touch the racing build's deployed
  `Launchbox-Racing\Emulators\mame286\mame.exe`.** The POC only reads its
  `roms/`, `ctrlr/`, and nvram fixtures.

## Build environment

- **MSYS2 at `E:\msys64`** (NOT C:\ — that died in the C: wipe), GCC 16.2.0.
- Build (incremental ≈1 min; from Git Bash):
  ```
  env MSYSTEM=MINGW64 /e/msys64/usr/bin/bash.exe -lc "export OS=Windows_NT; \
    cd /e/Source/mame-src && make SUBTARGET=vunit \
    SOURCES=src/mame/midway/midvunit.cpp NOWERROR=1 TOOLS=0 -j18"
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
| `MIDV_SKIP_STARTUP_SCREENS=1` | boot straight past MAME warning/info screens (frontend gate) |
| `MIDV_GL_SNAP=<dir>` | backbuffer BMP every ~150 presents (unattended verify) |
| `MIDV_GL_LOG=1` | diagnostics to `midv_gl.log` in cwd |
| `MIDV_LIVE=1` | shared-memory ring only (drive `gpu/live_viewer.py`) |
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
  Runs with `video gdi` underneath; NOACTIVATE/TRANSPARENT/DISABLED keep all
  input on MAME's window.

## Rig facts

- Product entry: `python harness/collection.py` — fullscreen shell, all
  three games; C toggles CRT per launch; config `rig/collection.ini`.
  Stream Deck entry: Elgato "Games" profile key [7,2] →
  `Launchbox-Racing\scripts\Launch-Cruisn.bat` (start /min wrapper) opens
  the shell. Direct single game: `python harness/run_rig.py --rom crusnusa
  [--crt]`. Coin=**5**, Start=**1** on keyboard, **F9** = CRT live toggle.
  crusnwld needs a ONE-TIME wheel calibration at first boot (persists in
  `rig/nvram`; crusnusa's fixture already has it, offroadc boots clean).
- run_rig makes MAME's window **borderless-fullscreen** post-boot
  (`--windowed` opts out) and **enforces fg+focus on MAME's window** —
  keyboard and foreground-mode DirectInput FFB die without it. Never
  activate the overlay (owner's last-active-popup redirection eats keys;
  SwitchToThisWindow is banned).
- ⚠️ **Never hard-kill with FFB active** — stranded constant-force torque on
  the Moza; Esc out normally; Stream Deck "Stop FFB" key clears a stuck
  wheel. Remote/automation quit: WM_CLOSE on MAME's window is clean.
- FFB plugin quirk: ~50% first-launch hang in device enumeration —
  run_rig auto-detects (no responsive window in 20 s) and relaunches once.
- If wheel steers but FFB is silent: flip `output windows` → `output network`
  in run_rig.py's ini writer (one word) — first thing to try.
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
- Commit mame-src and cruisn-poc separately; refresh the patch series after
  mame-src commits.
- Bit-exactness claims require four decimal places — "100.00%" once hid a
  99.9985 that cost an hour.
