# Cruis'n Collection — Setup Guide

Two audiences: **players** (a release zip; nothing to build) and
**developers** (build from source). This project ships no ROMs, no game
assets and no stock MAME binaries — you supply your own MAME 0.286 ROM sets;
the emulator in the zip is built from the GPL patch series in `patch/`.

---

## Player setup

### You need

- Windows 10/11, 64-bit. A GPU with **OpenGL 4.3** (GeForce 600+ / Radeon
  HD 7000+ / Intel HD 4000+ or newer; integrated graphics are fine).
- Your own **MAME 0.286 ROM sets**: `crusnusa`, `crusnwld`, `offroadc`,
  `crusnexo` — plus **`crusnwld24`** for Cruis'n World and the two DSP boot
  ROM sets **`tms320c31`** / **`tms320c32`** (see the ROM table).
- Optional: a wheel (any DirectInput wheel; force feedback via the bundled
  FFB Arcade Plugin), a shifter or paddles, a gamepad.

### Steps

1. **Unzip** the release anywhere (e.g. `C:\Games\CruisnCollection`). No
   installer, no admin rights, no Python. Windows SmartScreen may warn
   about the unsigned executables the first time: *More info → Run anyway*.
2. Double-click **`CruisnSetup.exe`**. It shows one row per game plus the
   emulator and force-feedback plugin status.
3. **Add ROM file(s)…** and pick your zips (several at once is fine). Any
   filename works — each zip is identified by its contents against MAME
   0.286's ROM list and copied into `roms\` under the right name. A file or
   two with odd checksums is reported but doesn't block anything (redumps
   are common; MAME loads them).
4. Have a force-feedback wheel? **Detect wheel (force feedback)** — see
   below.
5. **Launch Collection** (or double-click `CruisnCollection.exe` any time).

| game | ROM set(s) | notes |
|---|---|---|
| Cruis'n USA | `crusnusa` | v4.5 |
| Cruis'n World | `crusnwld` + `crusnwld24` | The collection boots **rev 2.4** (`crusnwld24`), the last revision with a manual transmission. It is a MAME *clone*: a **merged** `crusnwld.zip` already contains its files; with **split** sets add `crusnwld24.zip` beside `crusnwld.zip`. Without it the launcher falls back to rev 2.5 (automatic only) and says so on screen. |
| Off Road Challenge | `offroadc` | v1.63 |
| Cruis'n Exotica | `crusnexo` | v2.4. Upstream MAME emulation is imperfect here: car-select stats text is illegible; occasional sprite glitches. |
| **DSP boot ROMs** | `tms320c31` (USA / World / Off Road) and `tms320c32` (Exotica) | MAME *device* sets — two tiny zips (one 16 KB file each) that every full MAME romset includes. Easy to overlook when you copy only the game zips; without them the game aborts with "c31boot.bin NOT FOUND". Romsets from other MAME versions name them **`tms32031.zip` / `tms32032.zip`** — same file inside; add them through the setup window (identified by content) or just copy them, the launcher accepts either name. |

### Updating to a new version

Either works, no manual file juggling:

- **Unzip the new version over your existing folder** (close the launcher
  first, say yes to overwriting). Your ROMs, wheel bindings, settings,
  World calibration and force-feedback wheel are all kept — the update only
  replaces the program files.
- **Or unzip into a new folder** and use `CruisnSetup.exe → Import previous
  version…`, pointing it at the old folder. Same result; delete the old
  folder afterwards.

### In the launcher

- **Cards row**: ← → (or A/D, or steer the wheel) picks a game; **Enter**
  (or the gas pedal) opens it. Each game's page has **PLAY** on top plus
  that game's own settings: steering sensitivity and curve, volume, free
  play, and for World the 2.4 / 2.5 revision switch.
- **SETTINGS** (below the cards): CRT effects, crack fill, aspect (4:3 /
  16:9 trimmed / 16:9 full), margin fill, FFB strength, **TRANSMISSION**
  (H-pattern shifter or sequential paddles), **CONTROLS SETUP**.
- **Esc** backs out; from the cards row it quits.

### Controls

Keyboard works with nothing bound: **5** = coin, **1** = start, arrow keys
steer / gas / brake, plus the in-game keys below.

**Wheel, pedals, gamepad: SETTINGS → CONTROLS SETUP.** It asks for each
control in turn — turn the wheel, press each pedal, press the buttons you
want for coin, start, views, radio, then your shifter (H-pattern gears 1–4)
*or* paddles (shift up / down), depending on the TRANSMISSION setting.
**Backspace** skips a step and keeps whatever it had before; **Esc**
cancels. Wheels with more than 32 buttons are fine. After the wizard the
wheel and gas pedal also navigate the launcher menus.

**Cruis'n World asks you to calibrate once.** On its first boot with your
hardware (and again if your wheel/pedals change) World shows CALIBRATE
CONTROLS: take your hands and feet off the controls, press **F2** (TEST),
then follow the prompts — turn the wheel fully each way, press each pedal
fully, F2 to advance. It's stored in the game's own settings memory and
never asked again. USA and Off Road don't do this.

Pick **TRANSMISSION** first: *H-PATTERN SHIFTER* for a real H-pattern
shifter, *SEQUENTIAL* for paddles or a sequential stick. Both sets of
bindings are remembered, so switching later needs no rebinding. (Cruis'n
Exotica has no sequential mode in its hardware — it stays on
automatic-select with paddles.)

### In-game keys

| key | action |
|---|---|
| **5** / **1** | coin / start (or whatever you bound) |
| **Esc** | in-game menu: Resume, CRT on/off, Exit to launcher |
| **F9** | toggle the CRT look instantly |
| **=** / **-** | game volume in Cruis'n USA (the other games have a VOLUME setting on their page) |
| **F2** / **9** | operator test menu / service credit |
| **F12** | quit the game, back to the launcher (instant; prefer Esc so the wheel releases cleanly) |
| **Shift+F12** | quit the game **and** the launcher - straight to the desktop |

### Force feedback

The zip includes the **FFB Arcade Plugin** (GPL-3.0) pre-configured for
these games. It needs to know *which* device is your wheel — the plugin
does nothing until `DeviceGUID=` in `FFBPlugin.ini` names it.

**Easy way:** `CruisnSetup.exe → Detect wheel (FFB)`, with the wheel base
powered on. A game window opens for about thirty seconds while the plugin
lists every connected device (it enumerates only once the game is
running); the setup then picks the device you bound as steering in
CONTROLS SETUP (or asks, if it can't tell) and writes the line for you.

**By hand:** set `Logging=1` in `FFBPlugin.ini` (beside `vunit.exe`), play
once, open `FFBlog.txt` — each device appears as `Joystick: n / Name: … /
GUID: …`. Put your wheel base's GUID on the `DeviceGUID=` line, leave
`GameId=22`, set `Logging=0` again.

Overall strength is **SETTINGS → FFB STRENGTH**. Rotation range (arcade
Cruis'n wheels turn about 270°) is set in your wheel's own software.

The shipped `FFBPlugin.ini` is the plugin's own MAME defaults (`GameId=22`,
which covers USA, World and Off Road by ROM name; 500 ms effect length so
forces don't expire between the game's updates). If your wheel only pulls
one way or feels weak, try `AlternativeFFB=1` — some bases (Moza,
Thrustmaster) want it. Keep the four plugin files that come in the zip
together; mixing a `dinput8.dll` from another plugin version with these
`SDL2.dll` / `MAME64.dll` makes forces flaky.

**FFB diagnostics** (when forces are missing or intermittent):
`CruisnSetup.exe → FFB diagnostics` turns on two logs for every drive —
`rig\ffb_trace.csv` (every force value the game sends, timestamped) and
the plugin's own `FFBlog.txt` (what it did with them). Drive for a minute,
then **Save support bundle**; the two logs tell us whether the game stopped
sending or the wheel stopped listening. Turn it off afterwards.

### Steering feel: sensitivity and curve

Each game card has two steering rows (press Enter on a game, they sit
under PLAY). Both are per game, both default to *off*, and neither
touches the game's own calibration - run the in-game control calibration
first (F2 service menu) so the wheel's full travel maps to full lock, then
tune feel here.

- **STEERING SENSITIVITY** is a gain on how far you have to turn. At
  **100%** (the default) full lock is wherever the calibration put it.
  **150%** reaches full lock at two thirds of that travel (and anything
  past it is just full lock); **70%** means turning all the way gives
  70% lock. Use it when a 900° wheel feels like too much arm work for an
  arcade game, or a short-rotation wheel feels twitchy - or set your
  wheel's rotation to 270-360° in its own software and leave this alone.
- **STEERING CURVE** shapes the response *between* center and lock
  without changing where lock is. **100** is linear. **Below 100** (70 is
  a good first try for the three V-Unit games) gives more response near
  center: these games ignore small wheel movements and then turn sharply,
  and this counteracts that lazy-center feel. **Above 100** softens the
  center instead, for a wheel that feels nervous in a straight line.

Sensitivity is applied first, then the curve. Cruis'n Exotica centers
differently from the other three, so it has its own values. If you have
used MAME's own *Analog Input Adjustments* menu: its *sensitivity* has no
effect on a wheel (MAME applies and un-applies it for absolute controls),
which is why the collection provides its own.

### Launching a game directly (frontends, shortcuts)

`CruisnCollection.exe --game usa` (also `world`, `offroad`, `exotica`, or
the MAME names) starts that game with your saved settings and no launcher
screen; the process ends when the game does. Add `--windowed` to skip
fullscreen. Point LaunchBox / a Stream Deck key / a desktop shortcut at
that line and the launcher never appears.

### Menu music (optional)

The release ships a menu track. For your own, drop an `.mp3` at
`rig\assets\menumusic.mp3` (or per game: `rig\assets\menumusic-crusnusa.mp3`
and so on).

### When something goes wrong

- **A game returns to the launcher immediately** — the reason shows on the
  menu for a few seconds (typically a missing ROM file); the emulator's
  full output is in `rig\launch.log`.
- **Nothing happens for ~20 s, then the game starts** — a known
  first-launch hang in the FFB plugin's device scan; the launcher detects
  it and relaunches automatically.
- **A game runs slow / stutters** — four one-line experiments, each a
  SETTINGS row, no files to touch: INTERNAL SCALE 2X (GPU), FFB STRENGTH
  0% (the force-feedback plugin goes idle), ASPECT 4:3 (no widescreen
  patch or margins), CRT off (F9). Whichever one fixes it names the
  culprit; then Save support bundle after the slow game — its
  `launch.log` ends with the emulator's measured speed.
- **Black screen or a driver error** — the renderer needs OpenGL 4.3;
  update the GPU driver, and on laptops make sure the game runs on the
  discrete GPU.
- **Wheel not listed in CONTROLS SETUP** — connect it before starting the
  launcher.
- **Wheel steers but never pushes back** — force feedback isn't configured
  yet: see *Force feedback* above.
- **Force feedback comes and goes** — first make sure all four plugin files
  are the ones from the zip (no `dinput8.dll` from another version), then
  turn on *FFB diagnostics*, drive a minute, save a support bundle.
- **"needs the DSP boot ROM c31boot.bin"** — copy `tms320c31.zip` (and
  `tms320c32.zip` for Exotica) from your MAME romset into `roms\`.
- **Cruis'n World shows CALIBRATE CONTROLS** — expected once per rig:
  press F2 and follow the prompts (see *Controls*). Keyboard-only works
  too (arrows for the wheel, the gas/brake keys for the pedals).
- **Cruis'n World says "2.4 ROMs not found"** — add `crusnwld24.zip` beside
  `crusnwld.zip` (or use a merged set); see the ROM table.
- **Reporting a bug**: `CruisnSetup.exe → Save support bundle` writes one
  zip (logs, your controller layout as MAME sees it, settings — never ROMs).
  Attach it with a note on *what you expected vs what you saw*. For visual
  glitches a photo or screenshot beats any description.

Advanced / scripted setup (custom paths, no GUI): `setup.ps1` in the zip.

---

## Developer setup (build from source)

1. **MSYS2** (https://msys2.org) with the MinGW64 toolchain
   (`pacman -S mingw-w64-x86_64-toolchain make git`).
2. Clone MAME 0.286 and apply the patch series:
   ```
   git clone --depth 1 --branch mame0286 https://github.com/mamedev/mame mame-src
   cd mame-src
   git am path\to\cruisn-collection\patch\vunit-poc-patches.patch
   ```
3. Build the subtarget from an MSYS2 MinGW64 shell (`OS=Windows_NT` must be
   exported *inside* that shell — its profile clears it):
   ```
   export OS=Windows_NT
   make SUBTARGET=vunit \
        SOURCES=src/mame/midway/midvunit.cpp,src/mame/midway/midzeus.cpp \
        REGENIE=1 NOWERROR=1 TOOLS=0 -j$(nproc)
   ```
   Product: `vunit.exe` (~110 MB, statically linked). Later builds drop
   `REGENIE=1`. Put the FFB Arcade Plugin files (`dinput8.dll`, `SDL2.dll`,
   `MAME64.dll`, `FFBPlugin.ini`) beside it for wheel force feedback.
4. Python 3.12+ with `pip install numpy pillow moderngl glfw` (plus
   `pyinstaller` to build a release zip; `yt-dlp` + ffmpeg for the music
   tools). Run the launcher: `python harness/collection.py`; one game:
   `python harness/run_rig.py --rom crusnusa [--crt]`.
5. Shader changes live in `gpu/renderer.py` (the source of truth). After any
   change: `python harness/gen_shaders.py`, rebuild `vunit.exe`, then verify
   `python gpu/renderer.py results/capture-8000` still prints **100.0000%**
   (bit-exact against MAME's framebuffer).
6. Release zip: `.\make_release.ps1` freezes the launcher and setup GUI and
   bundles emulator + plugin + fixtures + docs (~90 MB). Pushing a `v*` tag
   builds the same thing on GitHub Actions and publishes it.

### Path configuration

The dev checkout defaults to this machine's layout; the release folder is
self-contained. Override with environment variables (`setup.ps1` writes them
into a launcher `.bat`):

| variable | meaning | default (dev) |
|---|---|---|
| `CRUISN_VUNIT` | path to vunit.exe | `E:\Source\mame-src\vunit.exe` |
| `CRUISN_ROMS` | your ROM directory | racing build's `roms\` |
| `CRUISN_MAME_DIR` | dir with the FFB plugin files | racing build |
| `CRUISN_CTRLR` | optional EmuEZ ctrlr file to inherit | racing build's |
| `CRUISN_ART` | LaunchBox-style art root (optional) | racing build's |

Missing art falls back to generated cards; a missing ctrlr file means
wizard-only bindings; missing music means a quiet menu.

## Legal posture

Cruis'n USA, Cruis'n World, Off Road Challenge, Cruis'n Exotica and all
associated art are Midway / Warner Bros. properties. This project
distributes **no ROMs and no game assets** — original launcher code, a
GPL-2.0+ patch series against MAME (source included, as GPL requires) and
the GPL-3.0 FFB Arcade Plugin (license included). Supply your own legally
obtained ROM dumps.
