# Cruis'n Collection — Installation

Two audiences: **players** setting up from a release folder, and **developers**
building from source. No ROMs, no game assets, and no MAME binaries are
distributed by this project — you supply your own ROM dumps, and the emulator
builds from source (the full patch series against MAME is in `patch/`).

---

## Player setup (release folder)

The release folder is self-contained: frozen launcher (**no Python
needed**), the emulator (`vunit.exe`, statically linked — no runtimes), the
FFB Arcade Plugin (GPL-3.0, license included), NVRAM fixtures, and this
documentation. The only things you supply are **your own ROM dumps** and,
optionally, menu music.

### Steps

1. Unzip anywhere (e.g. `C:\Games\CruisnCollection`).
2. Copy your MAME 0.286 ROM sets into `roms\`: `crusnusa.zip`,
   `crusnwld.zip`, `offroadc.zip`, `crusnexo.zip` (any subset works).
3. Run **`setup.ps1`** once (right-click → Run with PowerShell). It
   verifies everything, can auto-download the FFB plugin if absent, and
   writes a pinnable `CruisnCollection.bat`.
4. Double-click **`CruisnCollection.exe`**. Pick a game. Drive.

For wheel force feedback, put your wheel's GUID in `FFBPlugin.ini`
(`DeviceGUID=`; set `Logging=1` for one run and read it from
`FFBlog.txt`, then turn logging back off).

### Building a release folder (maintainer)

`.\make_release.ps1` from the dev checkout: freezes the shell
(PyInstaller), assembles `build\release\CruisnCollection\` (launcher +
vunit.exe + FFB plugin with the wheel GUID blanked + fixtures + patch +
source + docs), and zips it (~50 MB). Requirements: Python + pyinstaller,
a built vunit.exe, the four FFB plugin files beside it.

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
   git am path\to\cruisn-collection\patch\vunit-poc-patches.patch
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
