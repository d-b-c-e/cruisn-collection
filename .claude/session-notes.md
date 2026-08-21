# Session Notes — COMPLETE HANDOFF
<!-- Read these first, then CLAUDE.md, then results/RESULTS.md (the full
     chronological engineering log - trust it over memory). Written
     2026-08-20 night as a self-sufficient handoff in case the repo rename
     resets Claude's project context. -->

- **Repo:** GitHub **d-b-c-e/cruisn-collection** (private; renamed from
  cruisn-poc 2026-08-20, old URL redirects). Local folder is STILL
  `E:\Source\cruisn-poc` (rename checklist at the bottom).
- **Branches:** this repo `master` (pushed); emulator half in
  `E:\Source\mame-src` branch `poc/quadlog` @ 366f8119 (NOT on GitHub —
  the full patch series `patch/vunit-poc-patches.patch`, 20 patches from
  the upstream `mame0286` tag, IS the export and is what CI builds from).
- **Released:** **v0.1.0** on GitHub Releases (83 MB zip, CI-built from
  scratch: MAME+patches → vunit.exe → frozen apps → FFB plugin download →
  media → publish). Tag = release; emulator build is cached on patch hash.
  NOTE: v0.1.0 predates the axis/keyboard wizard, Esc menu, telemetry and
  the 401-line fix — **tag v0.2.0 after the rig test passes** to publish
  everything current.

## What this product is right now

**CRUIS'N COLLECTION** — four games, one `vunit.exe` (subtarget =
midvunit.cpp + midzeus.cpp):
- Cruis'n USA / Cruis'n World / Off Road Challenge: our GL
  renderer-replacement, **all three verified 100.0000% bit-exact** vs MAME
  videoram (offroadc's 512×401 mode included; overlay height is runtime
  via MIDV_GL_HEIGHT).
- Cruis'n Exotica: Zeus2 hardware, MAME's own renderer via d3d
  (NOT_WORKING-flagged upstream but play-tested; GL replacement scoped
  VIABLE at `zeus2_draw_quad`, ≤6.3k quads/frame — see RESULTS).

**Shell** (`harness/collection.py`, frozen `CruisnCollection.exe`):
4-card menu + logos, menu music (user's chosen track via
`harness/make_music.py <url> --skip N`), nav = arrows/wheel-hat + Enter,
SETTINGS screen (CRT toggle / WHEEL SETUP wizard / back). Wizard does
**press-to-bind buttons, MOVE-to-bind axes (steer/gas/brake), and
keyboard-key capture**; results in `rig/collection.ini [wheelmap]`,
applied by run_rig's ctrlr generator (translates EmuEZ BUTTON33-48 →
ADDSW1-16; wizard beats per-game EmuEz sections; bare ctrlr when no
EmuEz file). Game launch: borderless-fullscreen enforced for the window's
lifetime, focus enforced (fg+focus on MAME's window — NEVER let the
overlay activate), FFB plugin auto-hang retry, instant shell return
(0.6 s — watches the game WINDOW, not process teardown).

**In-game:** Esc = overlay OPTIONS menu (Resume / CRT toggle / Exit to
launcher; GL-thread drawn, GetAsyncKeyState-polled; UI_CANCEL remapped to
F12 in the generated ctrlr). F9 = live CRT toggle. Coin=5, Start=1.

**Setup/distribution:** `CruisnSetup.exe` (tkinter GUI): identifies ANY
zip by member names+CRCs vs `harness/roms_manifest.json` (25 sets,
clone-aware, missing-file reporting), installs under correct set name,
health-checks, **Save support bundle** button (MAME input dump via
`lua/input_dump.lua` + glfw joydump + FFB log + configs → zip for bug
reports). `setup.ps1` = scripted alternative + FFB plugin auto-download.
`make_release.ps1` builds the release folder/zip (media/ bundled from the
repo — user's decision; `-NoMedia` for clean; ROMs are the bright line).
`.github/workflows/release.yml` does it all on tag push.

**Telemetry (Phase A):** `MIDV_TELEM_UDP=host:port` (or collection.ini
`[telemetry] udp=`) mirrors every MAME output as JSON datagrams
(`{"game","out","value"}`); "wheel" = FFB force. Verified with lamp
outputs in attract. Phase B (speed/RPM via RAM hunt) designed, not built.

## THE PENDING RIG TEST (user, at the wheel — everything else is done)

Nothing below has physically touched the wheel yet; all verified
programmatically at the binding/render level:
1. Deck button → shell → SETTINGS → **WHEEL SETUP**: axis steps first
   (turn wheel / press pedals), then buttons (wheel/shifter/stalk all
   visible; keyboard keys also bind). **Wake the Moza first — it
   idle-sleeps and vanishes from enumeration.**
2. In-game: wheel buttons (start/gears/views), real FFB forces
   (MAME64.dll fixed the silent-FFB issue; RunningFFB=RacingFullValueActive2
   confirmed), **Esc menu** (Resume/CRT/Exit), F9 CRT taste check.
3. Exotica from the shell (d3d fullscreen; FFB as in racing build).
4. World at full speed (perf was the "bad emulation" — priority 1 fixed).
5. If good → `git tag v0.2.0 && git push origin v0.2.0`.

## Open items

- [ ] Rig test above; ingest findings.
- [ ] Telemetry Phase B: RAM-hunt speed/RPM per game (differential search
      during attract demo races — unattended-capable; also unblocks the
      parked achievements idea, see docs/ACHIEVEMENTS.md).
- [ ] Gamepad axis-order table is positional/approximate — validate on a
      real pad-only run (support bundle shows truth if a device deviates).
- [ ] Wanszai-style shell settings page could grow: FFB strength, scale,
      aspect (his settings.ini is the model — RESULTS teardown notes).
- [ ] Margin pop-in class (World black side bars where sky geometry ends;
      floating parked geometry at margin edges) — documented, heuristics
      possible later.
- [ ] Mid-game EIP=0 crash singleton (2026-08-19) — unexplained; WER
      minidumps land in rig/crashdumps/. Teardown AV at exit is ATTRIBUTED
      (FFB plugin dinput8.dll in the faulting chain — cosmetic, post-exit,
      masked by instant shell return).
- [ ] Zeus GL renderer (level 2) when a session can afford the arc:
      capture → reference → GL over zeus2_draw_quad (MIDZ_STATS=1
      profiler is in the patch).
- [ ] Multi-hour soak; crusnwld/offroadc oracle determinism passes
      (fixtures exist; captures must run in rig config — headless
      re-demands calibration, no input devices).
- [ ] Consider upstreaming the winhybrid DIJoystick2 fix to MAME proper.

## Parked ideas
- Achievements: docs/ACHIEVEMENTS.md (research complete, idea only).

## Critical lore (cost real hours — do not relearn)

- **Shader regen:** `python harness/gen_shaders.py` after ANY
  gpu/renderer.py shader edit, then rebuild. Raw strings break REGENIE.
  Exact-mode check `python gpu/renderer.py results/capture-8000` must say
  100.0000% (needs four decimals).
- **Build:** both SOURCES (midvunit + midzeus) — see CLAUDE.md. OS
  env var inside MSYS2 shell.
- **Patch refresh:** `git format-patch --stdout mame0286..HEAD` (FULL
  series — 6f55ed93.. silently drops the DIJOYSTATE2 base).
- **GDI screenshots show the GL overlay black** — use MIDV_GL_SNAP;
  judge subpixel effects (CRT) on 1:1 crops, never downscales.
- **Injected keys never reach MAME's rawinput** (keybd_event useless for
  MAME input; fine for our GetAsyncKeyState menu + glfw shell).
- **pyGLFW returns (pointer, count) tuples** from joystick calls.
- **Never activate the overlay window** (owner's last-active-popup
  redirection eats keys; SwitchToThisWindow is banned).
- Wheel buttons 33-48 = ADDSW1-16 tokens; 49+ unaddressable.
- FFB needs all four plugin files incl. **MAME64.dll**; success =
  RomName=<rom> in FFBlog.txt. Never hard-kill mid-game with FFB active.
- `priority 1` in the rig mame.ini keeps MAME at ~100% under ambient load.

## Local folder rename (when no Claude session is open)

Rename `E:\Source\cruisn-poc` → `E:\Source\cruisn-collection`, then:
1. `Launchbox-Racing\scripts\Launch-Cruisn.bat`: update the `cd /d` line.
2. This repo's CLAUDE.md + mame-src patch-refresh path mentions.
3. Claude Code project memory is keyed to the folder path — first session
   under the new path starts fresh; say "catch up" and these notes +
   CLAUDE.md + RESULTS.md carry everything.
