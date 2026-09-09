# Cruis'n Collection — Setup Guide

Two audiences: **players** (a release zip; nothing to build) and
**developers** (build from source). This project ships no ROMs — you supply
your own MAME 0.286 ROM sets;
the emulator in the zip is built from the GPL patch series in `patch/`.

---

## Player setup

### You need

- Windows 10/11, 64-bit. A GPU and driver supporting **OpenGL 4.3**.
  Performance at 4K depends on the GPU; model-wide minimums have not been qualified.
- Your own **MAME 0.286 ROM sets**: `crusnusa`, `crusnwld`, `offroadc`,
  `crusnexo` — plus **`crusnwld24`** for Cruis'n World and the two DSP boot
  ROM sets **`tms320c31`** / **`tms320c32`** (see the ROM table).
- Optional: DirectInput wheel/pedals/shifter or a gamepad (force feedback is driven by
  the emulator through SDL2 haptics). Wheel compatibility is still being expanded.

### Steps

1. **Unzip** the release anywhere (e.g. `C:\Games\CruisnCollection`). No
   installer, no admin rights, no Python. Windows SmartScreen may warn
   about the unsigned executables the first time: *More info → Run anyway*.
2. Double-click **`CruisnSetup.exe`**. It shows one row per game plus the
   emulator and force-feedback status.
3. **Add ROM file(s)…** and pick your zips (several at once is fine). Any
   filename works — each zip is identified by its contents against MAME
   0.286's ROM list and copied into `roms\` under the right name. A file or
   two with odd checksums is reported but doesn't block anything (redumps
   are common; MAME loads them).
4. Have a wheel? Bind it in the launcher (**SETTINGS → CONTROLS → CONTROLS SETUP**);
   force feedback follows the steering device by itself — see *Force
   feedback* below.
5. **Launch Collection** (or double-click `CruisnCollection.exe` any time).

| game | ROM set(s) | notes |
|---|---|---|
| Cruis'n USA | `crusnusa` | v4.5 |
| Cruis'n World | `crusnwld` + `crusnwld24` | The collection boots **rev 2.4** (`crusnwld24`), the last revision with a manual transmission. It is a MAME *clone*: a **merged** `crusnwld.zip` already contains its files; with **split** sets add `crusnwld24.zip` beside `crusnwld.zip`. Without it the launcher falls back to rev 2.5 (automatic only) and says so on screen. |
| Off Road Challenge | `offroadc` | v1.63 |
| Cruis'n Exotica | `crusnexo` | v2.4. Upstream MAME emulation is imperfect here: car-select stats text is illegible; occasional sprite glitches. |
| **DSP boot ROMs** | `tms320c31` (USA / World / Off Road) and `tms320c32` (Exotica) | MAME *device* sets — two tiny zips (one 16 KB file each) that every full MAME romset includes. Easy to overlook when you copy only the game zips; without them the game aborts with "c31boot.bin NOT FOUND". Romsets from other MAME versions name them **`tms32031.zip` / `tms32032.zip`** — same file inside; add them through the setup window (identified by content) or just copy them, the launcher accepts either name. |

### Updating to a new version

As of 2026-09-08 the repository is private. Downloads need repository access and
the anonymous updater cannot discover releases. Public access is being prepared;
see [PUBLIC-READINESS.md](PUBLIC-READINESS.md).

**In the app** (v0.3.4+): `CruisnSetup.exe` -> **Updates...** checks
GitHub for a newer release; **Download and install** downloads it, closes
the launcher, installs over this folder and reopens the launcher. ROMs,
settings, bindings, calibration and the wheel stay. The launcher's
SETTINGS -> SUPPORT -> CHECK FOR UPDATES does the same from the menu.

**By hand**: close the launcher and unzip the new version over your
existing folder (say yes to overwriting). Or unzip into a new folder and
use *Import previous version...* in the setup window to bring everything
across. Your `rig` folder and `roms` are never inside the zip.

### In the launcher

- **Cards row**: ← → (or A/D, or steer the wheel) picks a game; **Enter**
  (or the gas pedal) opens it. Each game's page has **PLAY** on top plus
  that game's own settings: steering sensitivity and curve, volume, free
  play, [imported Cheats](CHEATS.md), and for World the 2.4 / 2.5 revision switch.
- **SETTINGS** (below the cards): **Display** controls CRT, aspect and internal
  scale; **Experiments** selects shared/per-game trials; **Force Feedback** controls
  strength, direction, spring, feel and impact cues; **Controls** selects transmission
  and bindings; **Support** provides updates, diagnostics and support bundles.
- Cheats and top-level Experiments describe the current source. The published
  v0.4.0 ZIP has no Cheats menu and still nests Experiments under Display.
- **Esc** backs out; from the cards row it quits.

### Optional experiments

Open **SETTINGS → EXPERIMENTS**, beside Display, then choose Shared or a game.
This top-level menu can contain gameplay as well as rendering experiments.
Per-game trials start off and take effect on the next launch. World lookahead
presets to +8 but is inactive while World Draw Distance is Off. Shared Crack Fill
retains its existing On default; moving the menu does not change preferences.

| Setting | Games | What to expect |
|---|---|---|
| **Crack Fill** (Shared) | USA, World, Off Road | Borrows nearby pixels for small gaps; can smear fine detail. Its existing default remains On. This is separate from the retired broad Margin Fill. |
| **Seam Alignment** | USA, World, Off Road | Aligns certain mismatched terrain edges at enhanced resolutions. Closed a measured blue seam in Off Road, but can shift nearby texture interpolation. |
| **Widescreen Terrain** | World 2.4/2.5 | Repairs some missing edge terrain, including a measured Germany road hole. Does **not** extend draw distance. Adds drawing work; old recordings can take a different route. |
| **Distant Scenery** | World 2.4, widescreen, scale 2×+ | Draws five verified Germany mountain models, four tree variants and one forest strip earlier. Preserves the mountains' later shape. Experimental and limited to identified scenery; remaining pop-in and object activation are still being investigated. |
| **World Draw Distance / Scenery Lookahead** | World 2.4/2.5 | Off/2×/3× with +0/+8/+12 section lookahead. Shared across the World revisions; excludes Distant Scenery. Requires full widescreen and scale 2×+. New York 3×/+12 has a reported finish crash. |
| **Off Road Draw Distance** | Off Road | Off/2×/3× global far/projection trial. Modest measured benefit; no sampled 3× gain over 2×. Requires full widescreen and scale 2×+. |
| **Widescreen Scenery** | Exotica | Restores some missing margin geometry. Does not extend far distance; enhanced renderer/full widescreen/scale 2×+ required. |
| **Menu Force Feedback** | Exotica | Allows the game's wheel forces during selection screens and race end. Off by default retains driving-only suppression; applies next launch in every display mode. |
| **Detail Distance** | USA v4.5 | Keeps higher-detail models farther away. The recorded route required about 5.25% more polygon submissions. |
| **Draw Limit** | USA v4.5 | Raises a distant-object rejection limit. It added submissions but **no visible improvement** in the tested scene; it cannot load missing scenery. |

Unavailable options cannot be enabled for other games. These experiments do not
replace the graphics fixes already applied automatically. Return a setting to
Off/Standard to remove its effect on the next launch.

World's Widescreen Terrain option was previously labelled Terrain Visibility / Extended.
The fresh attended Germany recording confirms that distant pop-in remains.
Keep old recordings as controls and record a separate case after choosing the
graphics settings. Its bounded visibility change is separate from draw distance;
it does not bring in more distant scenery. The transmission artwork fix applies
automatically to enhanced World 2.4 rendering.

**Margin Fill has been retired from the launcher.** It stretched edge pixels
into the widescreen margins and could suppress useful sky detail. The newer
geometry/texture fixes work with it off. **Crack Fill** remains a separate,
local treatment for small unwritten gaps; neither setting creates missing terrain.

### Controls

Keyboard works with nothing bound: **5** = coin, **1** = start, arrow keys
steer / gas / brake, plus the in-game keys below.

**Wheel, pedals, gamepad: SETTINGS → CONTROLS → CONTROLS SETUP.** It asks for each
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

Pick **SETTINGS → CONTROLS → TRANSMISSION** first: *H-PATTERN SHIFTER* for
a real shifter, *SEQUENTIAL* for paddles or a sequential stick. Both binding sets
are preserved when switching. Select **MANUAL inside the game** as well.
World revision 2.5 is automatic-only; choose 2.4 on its game card for manual racing.

Exotica's hardware has a four-position shifter. The collection provides a virtual
four-speed shifter when sequential mode and both paddle bindings are present.
The launcher also sets the cabinet option needed for transmission selection;
steer to the displayed **M** and confirm with the accelerator. Older instructions
that Exotica always selects AUTO or requires reversed driving input are obsolete.
If `exotica_manual = 0` was saved in `rig/collection.ini`, it disables this cabinet
setup. All-gear acceptance with both physical shifter styles remains incomplete.

### In-game keys

| key | action |
|---|---|
| **5** / **1** | coin / start (or whatever you bound) |
| **Esc** | in-game menu: Resume, CRT on/off, Exit to launcher; the new native candidate adds [Cheats](CHEATS.md#during-gameplay) |
| **F9** | toggle the CRT look instantly |
| **=** / **-** | game volume in Cruis'n USA (the other games have a VOLUME setting on their page) |
| **F2** / **9** | operator test menu / service credit |
| **F12** | quit the game, back to the launcher (instant; prefer Esc so the wheel releases cleanly) |
| **Shift+F12** | quit the game **and** the launcher - straight to the desktop |

### Force feedback

FFB is built into the emulator through SDL2 haptics and the shared wheel toolkit.
It follows the device bound to steering; no FFB Arcade Plugin, GUID or external
FFB application is required. If no steering device is bound, the emulator tries
the first wheel-type haptic device. `midv_ffb.log` identifies the selected device.

Use **SETTINGS → FORCE FEEDBACK**:

| Control | Meaning |
|---|---|
| **Strength** | Shared 0–100% level; fresh default 50%. 0 disables physical output. There is no current per-game strength row. |
| **Feel** | CRISP (`cruisn-vunit@2`) is the current default. STANDARD uses more smoothing; RAW removes smoothing; CALM smooths more heavily. These are signal-conditioning presets. |
| **Spring** | Optional extra centering; default Off. Scales with Strength and is not applied to Exotica, which supplies its own centering force. |
| **Direction** | Physical device force sign, separate from steering input and Exotica's cabinet-polarity correction. |
| **Impact Cues** | Per-game trial, default Off. Infers contacts from force spikes and adds short pulses while reserving 25% of the constant-force budget, making sustained steering lighter. It does not read collision flags. |

There is no current **FFB Peak Limit** menu row; older guides described a removed
control. Start with a low Strength on an unfamiliar base and compare one setting
at a time. If the wheel oscillates or pulls away from centre, turn Strength to 0
before adjusting it. Comfortable force has not been certified across every wheel.

Exotica applies an effective 20% trim (80% becomes 64%) and normalizes its cabinet
motor polarity independently of steering. Its menu/race-end forces are suppressed
by default; **SETTINGS → EXPERIMENTS → EXOTICA → MENU FORCE FEEDBACK** turns them
back on for the next launch. This does not change strength or steering direction.
World strength and menu/race-end force
remain unchanged after the rejected driving gate was rolled back. **World can
still oscillate in menus or after finishing**; equal strength percentages do not
yet imply equal feel across games. Collision feel and cross-game normalization
remain known work. Software traces do not measure torque at the rim.

Opening the collection's Esc menu and closing the game release its force effects.
A motor-command timeout also releases stale output. This does not guarantee that
an in-game menu or stopped car is quiet: World may continue issuing commands.

**Custom profiles:** copy/edit `force-profiles.user.ini.example` beside `vunit.exe`
as `force-profiles.user.ini`, then select its tune under Feel. The supplied example
starts from STANDARD; the release default is CRISP. Keep custom edits in the
`.user.ini` file; updates replace the shipped `force-profiles.ini`. Additional
`[collection]` controls include `ffb_rumble`, `ffb_damper`, `ffb_friction` and
`ffb_spring_<rom>`. Change one at a time and preserve a copy of your settings.

**Diagnostics:** enable **SETTINGS → SUPPORT → FFB DIAGNOSTICS**, drive briefly,
then choose **SAVE SUPPORT BUNDLE** in that same submenu. The bundle contains
`rig/ffb_trace.csv` (motor and wheel-position observations), `midv_ffb.log`, a
trace report and plot. Record wheel model, driver/base settings, selected profile
and strength, and distinguish road weight, car contacts and wall contacts in the
report. Turn diagnostics off after collecting the case.

### Telemetry and SimHub

USA, World, Off Road and Exotica send actual game gear/rev signals, including
automatic shifts. The game's rev signal is mapped to **estimated 900–8,000 RPM**;
it is an arcade display scale, not a measured engine speed. USA, Off Road and
Exotica have internal speed readers; World still reads the displayed speed using
OCR. Invalid or inactive HUD samples are cleared.

Close the launcher before editing `rig/collection.ini`. For a Forza-compatible
SimHub receiver on the same PC, add or update the existing section:

```ini
[telemetry]
forza = 127.0.0.1:5300
```

Configure the receiver for the same UDP port and relaunch. `forza = on` selects
that same address. The optional `udp = host:port` key sends JSON for custom
consumers. Explicit `MIDV_TELEM_FORZA` / `MIDV_TELEM_UDP` environment overrides
win over the file. SimHub/Buttkicker output and higher gears still need broader
attended Off Road/Exotica coverage; packet tests alone do not certify tactile feel.

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
- **Nothing happens for ~20 s, then the game starts** — a hang in the
  wheel's device scan (rare); the launcher detects it and relaunches
  automatically.
- **A game runs slow / stutters** — four one-line experiments, each a
  setting change: DISPLAY → INTERNAL SCALE2X, FORCE FEEDBACK → STRENGTH
  0%, DISPLAY → ASPECT4:3 (no widescreen
  patch or margins), CRT off (F9). These comparisons help narrow the cause; then Save support bundle after the slow game — its
  `launch.log` ends with the emulator's measured speed.
- **The menu opens a game or a settings row by itself** — fixed in this
  version. Some wheel bases report dozens of buttons they do not have and
  pulse them by themselves; the menu used to accept any of them as OK.
  It now only accepts the buttons you bound in CONTROLS SETUP, so bind at
  least a start button there if you want to confirm with the wheel.
- **The menu selection scrolls on its own** — the steering axis moves the
  highlight, so a wheel resting away from centre scrolls continuously.
  Centre the wheel, or re-run CONTROLS SETUP if its centre looks wrong.
- **Exotica transmission selection does not respond** — use the displayed M/A
  highlight and accelerator; confirm the Controls transmission mode/bindings.
  Check that `exotica_manual = 0` has not disabled the launcher cabinet setup.
  Do not reverse driving input to compensate for a force-polarity problem.
- **Exotica shows glitches (the Amazon track especially)** — known.
  To tell our GL overlay from MAME's own Zeus2 emulation, put
  `exotica_gl = 0` under `[collection]` in `rig\collection.ini`: Exotica
  then runs on MAME's renderer. Tell us whether the glitch survives.
- **Black screen or a driver error** — the renderer needs OpenGL 4.3;
  update the GPU driver, and on laptops make sure the game runs on the
  discrete GPU.
- **Wheel not listed in CONTROLS SETUP** — connect it before starting the
  launcher.
- **Wheel steers but never pushes back** — force feedback needs
  `SDL2.dll` beside `vunit.exe` (it is in the zip) and a wheel whose
  driver offers force feedback (DirectInput). `midv_ffb.log` beside
  `vunit.exe` - in every support bundle - says which device was taken, or
  why none was; FFB STRENGTH 0% also means off.
- **Force feedback works for the first game, then is gone** — this was
  the old force-feedback plugin holding the wheel from inside the
  launcher; the emulator now drives the wheel itself and releases it when
  the game closes. If you still see it, turn on *FFB diagnostics*,
  reproduce, then *Save support bundle*.
- **Pedals (or a shifter axis) bind fine in CONTROLS SETUP but do nothing
  in game** — seen with pedals on their own USB device. The wizard numbers
  a device's axes 0, 1, 2 in the order they exist; MAME names them by fixed
  slot (X, Y, Z, RX, RY, RZ, two sliders) and skips slots the device lacks,
  so a pedal set exposing Y, RZ and a slider used to be written as X, Y, Z.
  Since this version the launcher reads each device's real slot layout
  from DirectInput at every launch and translates; `dinput_axes.txt` in
  the support bundle shows what it saw. Wheels with all eight axes were
  never affected.
- **USA (or World / Off Road) crawls in 2nd gear with the tyres
  squealing, even in automatic** — the game thinks the brake is pressed.
  Some load-cell pedals (Moza) come up reading fully pressed until they
  are pressed once: press the brake fully and release it. The launcher
  now refuses to start a game while a pedal reads pressed and tells you
  which one.
- **The wheel slams left-right or pulls away from centre** — turn Force Feedback
  Strength to 0, then check the device direction at low strength. World also has a
  known race-end/menu oscillation issue; reducing gain does not establish its cause.
  Collect FFB diagnostics and report whether other games behave the same way.
- **Force feedback comes and goes** — turn on *FFB diagnostics*, drive a
  minute, save a support bundle: `midv_ffb.log` shows every level sent to
  the wheel next to the game's trace.
- **"needs the DSP boot ROM c31boot.bin"** — copy `tms320c31.zip` (and
  `tms320c32.zip` for Exotica) from your MAME romset into `roms\`.
- **Cruis'n World shows CALIBRATE CONTROLS** — expected once per rig:
  press F2 and follow the prompts (see *Controls*). Keyboard-only works
  too (arrows for the wheel, the gas/brake keys for the pedals).
- **Cruis'n World says "2.4 ROMs not found"** — add `crusnwld24.zip` beside
  `crusnwld.zip` (or use a merged set); see the ROM table.
- **`launch.log` says "ROM NEEDS REDUMP WARNING: the machine might not
  run correctly"** — MAME's standard note about the DSP boot ROM's known
  checksum, printed at exit; harmless. The on-screen version of that
  warning is the one the launcher skips. The "Average speed" line after
  it is the useful part.
- **Which version am I on?** The setup window's *version / updates* row
  says (folder names can lie after unzipping over an old folder), and
  the support bundle includes `version.txt`.
- **Reporting a bug**: **SETTINGS → SUPPORT → SAVE SUPPORT BUNDLE** in the launcher
  (or `CruisnSetup.exe → Save support bundle`) writes one
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
   `REGENIE=1`. Put `SDL2.dll` beside it for wheel force feedback (the
   MSYS2 package `mingw-w64-x86_64-SDL2` supplies both the headers the
   build needs and `/mingw64/bin/SDL2.dll`; the emulator loads it at run
   time and runs without it, force feedback off).
4. Python 3.12+ with `pip install numpy pillow moderngl glfw` (plus
   `pyinstaller` to build a release zip; `yt-dlp` + ffmpeg for the music
   tools). Run the launcher: `python harness/collection.py`; one game:
   `python harness/run_rig.py --rom crusnusa [--crt]`.
5. Shader changes live in `gpu/renderer.py` (the source of truth). After any
   change: `python harness/gen_shaders.py`, rebuild `vunit.exe`, then verify
   `python gpu/renderer.py results/capture-8000` still prints **100.0000%**
   (bit-exact against MAME's framebuffer).
6. Run `python harness/local_checks.py` for Python/native/GPU checks. Release
   ZIPs are assembled locally with `.\make_release.ps1 -Version vMAJOR.MINOR.PATCH`;
   this freezes launcher/setup and bundles the already-built emulator, SDL2,
   fixtures and source/docs. Hosted workflows are disabled; tags do not build
   or publish. Follow [LOCAL-BUILDS.md](LOCAL-BUILDS.md) and the release checklist
   to validate and promote the exact tested ZIP.

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

## Distribution and licences

The project includes no game ROMs. The default package includes menu artwork
and music; `make_release.ps1 -NoMedia` excludes those assets. MAME, SDL2 and the
vendored wheel toolkit have separate included licence notices/source. Original
launcher licensing and menu asset provenance/permissions are public-readiness
work; see [PUBLIC-READINESS.md](PUBLIC-READINESS.md). This project is unofficial.
