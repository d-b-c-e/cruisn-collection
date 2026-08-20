# Cruis'n Collection — Installation

Two audiences: **players** setting up from a release folder, and **developers**
building from source. No ROMs, no game assets, and no MAME binaries are
distributed by this project — you supply your own ROM dumps, and the emulator
builds from source (the full patch series against MAME is in `patch/`).

---

## Player setup (release folder)

### What you need

1. **Windows 10/11, 64-bit**, a GPU with OpenGL 4.3 (anything from the last
   decade).
2. **Python 3.12+** from https://python.org (check "Add to PATH" during
   install).
3. **Your own ROM sets** (MAME 0.286 romset names): `crusnusa.zip`,
   `crusnwld.zip`, `offroadc.zip`, and optionally `crusnexo.zip`.
4. **A `vunit.exe`** built from the patch series (see developer section), or
   from a trusted build of this project you obtained yourself.
5. Optional, for force feedback: the **FFB Arcade Plugin** by Boomslangnz
   (https://github.com/Boomslangnz/FFBArcadePlugin) — you need these four
   files beside `vunit.exe`: `dinput8.dll`, `SDL2.dll`, `MAME64.dll`,
   `FFBPlugin.ini` (set `GameId=22`, Logging off, your wheel's GUID).

### Steps

1. Unpack/clone this folder anywhere (e.g. `C:\Games\CruisnCollection`).
2. Run **`setup.ps1`** (right-click → Run with PowerShell). It checks all of
   the above, installs the Python packages, asks where your ROMs and
   `vunit.exe` live, and writes a `CruisnCollection.bat` you can pin to
   Start, Stream Deck, or a frontend.
3. Put your ROM zips where you told setup they'd be.
4. Double-click `CruisnCollection.bat`. Pick a game. Drive.

### In the launcher

| key | action |
|---|---|
| ← → ↑ ↓ (or wheel d-pad) | navigate |
| Enter / any wheel button | select / launch |
| Settings → WHEEL SETUP | press-to-bind coin/start/views/gears on your wheel |
| Settings → CRT EFFECTS | scanline/mask/curvature pass on or off |
| Esc | back / quit |

In-game: **5** = coin, **1** = start (plus whatever you bound in WHEEL
SETUP), **F9** = CRT toggle, **Esc** = back to the launcher.

First boot of Cruis'n World asks for a one-time wheel calibration (follow
the on-screen service prompts; it persists). Menu music: drop any audio
file's URL into `python harness/make_music.py <url> --skip <seconds>`.

---

## Developer setup (build from source)

1. **MSYS2** (https://msys2.org) with the MinGW64 toolchain (`pacman -S
   mingw-w64-x86_64-toolchain`).
2. Clone MAME 0.286 and apply the patch series:
   ```
   git clone --branch mame0286 https://github.com/mamedev/mame mame-src
   cd mame-src
   git am path\to\cruisn-poc\patch\vunit-poc-patches.patch
   ```
3. Build the subtarget (from an MSYS2 MinGW64 shell; `OS=Windows_NT` must be
   exported inside the shell):
   ```
   export OS=Windows_NT
   make SUBTARGET=vunit \
        SOURCES=src/mame/midway/midvunit.cpp,src/mame/midway/midzeus.cpp \
        REGENIE=1 NOWERROR=1 TOOLS=0 -j$(nproc)
   ```
   Product: `vunit.exe` (~110 MB). Subsequent builds drop `REGENIE=1`.
4. Python side: `pip install numpy pillow moderngl glfw` (plus `yt-dlp` for
   the music pipeline).
5. After ANY shader change in `gpu/renderer.py`: run
   `python harness/gen_shaders.py` and rebuild. Then verify:
   `python gpu/renderer.py results/capture-8000` must print **100.0000%**.

### Path configuration

Everything defaults to this machine's dev layout; override with environment
variables (setup.ps1 writes them into the launcher .bat):

| variable | meaning | default |
|---|---|---|
| `CRUISN_VUNIT` | path to vunit.exe | `E:\Source\mame-src\vunit.exe` |
| `CRUISN_ROMS` | your ROM directory | racing build's `roms\` |
| `CRUISN_MAME_DIR` | dir with FFB plugin files etc. | racing build |
| `CRUISN_CTRLR` | optional EmuEZ ctrlr file to inherit | racing build's |
| `CRUISN_ART` | LaunchBox-style art root (optional) | racing build's |

Missing art falls back to generated cards; a missing ctrlr file falls back
to wizard-only bindings; missing audio just means silence.

## Legal posture

Cruis'n USA, Cruis'n World, Off Road Challenge, Cruis'n Exotica and all
associated art are Midway/WB properties. This project distributes **no
ROMs, no game assets, and no emulator binaries** — only original launcher
code and a GPL-2.0+ patch series against MAME (source available, as GPL
requires). Supply your own legally-obtained ROM dumps.
