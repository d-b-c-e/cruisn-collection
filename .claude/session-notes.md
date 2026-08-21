# Session Notes — COMPLETE HANDOFF
<!-- Read these first, then CLAUDE.md, then results/RESULTS.md (the full
     chronological engineering log - trust it over memory). Written
     2026-08-20 night as a self-sufficient handoff in case the repo rename
     resets Claude's project context. -->

- **Repo:** GitHub **d-b-c-e/cruisn-collection** (private; renamed from
  cruisn-poc 2026-08-20, old URL redirects). Local folder renamed to
  `E:\Source\cruisn-collection` 2026-08-20 (checklist at bottom DONE:
  Launch-Cruisn.bat + CLAUDE.md paths updated).
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

## Rig test round 1 (2026-08-20, user at wheel) — findings + fixes

1. **Boot went straight into last game (offroadc)** — shell remembers
   `state["rom"]`, and a phantom wheel-button press during device
   enumeration (Moza wake: zeros first, real state later; 0→1 settle
   read as a press) became ENTER. FIXED in collection.py: per-device 1 s
   silence after a joystick appears, 1.5 s input arming after boot,
   1.0 s after game return, and joy_prev/joy_seen/hat rebaseline on
   return (the stale-joy_prev instant-relaunch latent bug too).
2. **Several seconds of desktop + weird focus after quitting** — MAME's
   window outlives its message pump through the teardown drag (FFB exit
   race + WER dump), so the IsWindow watch waited it out. FIXED: shell
   also exits its wait after two consecutive 1 s WM_NULL timeouts
   (`run_rig.window_responding`).
3. **Wizard bound the wheel's return-spring to GAS** — baseline was
   snapshotted while the wheel was still returning. FIXED: press-Enter-
   to-begin gate screen, 0.8–1.0 s swallow-everything cooldown after
   every bind/skip, and axis baselines armed only after ALL axes are
   still (0.35 s samples, <0.06 delta).
4. **Off Road: momentary see-through gaps between ground polys** (user
   observation, not game-breaking). Matches the documented V-Unit crack
   class — pages persist between scenes, cracks show prior-frame pixels —
   so likely authentic to hardware/MAME, possibly widened by the 4×
   upscale. Triage later: MIDV_GL_SNAP captures vs native res / plain
   MAME comparison.

Fixes 1–3 are code-verified only (compile + --shot render); NOT yet
re-verified at the wheel. Deck bat runs live source — next launch has them.

## Overnight session (2026-08-20 night, user away) — round 2

**Shell (collection.py):** stays alive fullscreen BEHIND the game for the
whole session (wanszai-style — no desktop flash either direction);
LAUNCHING screen while MAME boots (launch on a background thread); cursor
hidden in shell + parked off-screen corner in-game; auto-relaunch phantom
fixed twice over (joystick input dead while old vunit still tearing down
+2 s, and per-button 0.6 s debounce vs re-enumeration 1→0→1 glitches);
shell foreground-enforce is stoppable so it never fights the game's.

**Exotica (all config-level, run_rig.py):** -keepaspect (was stretched),
-prescale 4 (was fuzzy), -view "Screen 0" (drops the internal lamp/7seg
panel that ate the bottom fifth), Esc keeps MAME quit (UI_CANCEL→F12 now
V-Unit-only — Exotica was unquittable), and a `<system name="crusnexo">`
ctrlr section translating the wizard map to Exotica's wiring (gears
BUTTON2-5, radio 6, views 7-10 — the latched shifter was holding a wrong
button: prime suspect for the throttle "flutter"). Its black-car/sprite
garbage is upstream zeus2 emulation (racing build identical) — only the
Zeus GL arc could improve it.

**CRACK FILL shipped end-to-end** (`MIDV_GL_CRACKFILL`, default ON, shell
SETTINGS toggle, 3D scenes only): scene pass writes a "written this
frame" R8UI mask (attachment 1); palette pass redirects unwritten pixels
to the nearest written neighbour ONLY when bounded on both sides along an
axis (true cracks; silhouettes vs margins untouched). renderer.py is
reference (—crackfill); exact mode untouched — re-verified **100.0000%**
on capture + capture-8000. Live-verified: crusnusa (99.97%) + offroadc
(100% speed, 512×401) attract snaps clean, GL err=0.

**Finding:** quality mode's continuous coverage already closes almost all
static cracks (canyon 4×: 166 px filled; offroadc capture: 11 px). The
in-game "see-through ground" the user saw is likely transient (game's own
LOD/pop or a live-path scene-timing case) — needs an at-the-wheel capture
(record_diag or MIDV_GL_SNAP while driving Off Road) to classify.

**Round-2 re-test list (user):** launch flow (no flash, cursor, no
auto-relaunch), wizard (Enter gate, no return-spring misbind), Exotica
(4:3 sharp, no panel, Esc quits, gears/views right, flutter gone?),
Off Road gameplay with crack fill ON vs OFF (SETTINGS toggle).

## Round 2 first observations (2026-08-21, user at wheel) — fixed same night

1. **Hat-left launched the card it landed on**: the wheel d-pad reports
   as hat AND buttons; the hat moved selection while the button hit "any
   wheel button = OK". 2. **Esc-quit → relaunch again**: latched shifter
   gear reappearing as a fresh 0→1 edge after re-enumeration (debounce
   forgets after minutes). ONE fix kills both classes: menu/settings OK
   now fires on button RELEASE with no hat movement between press and
   release — d-pad presses always move the hat first (suppressed), and
   latched phantoms never release (can never fire).
3. **CRT menu/game drift**: F9 + Esc-menu toggles never persisted. Now:
   overlay writes `crt=` to `MIDV_GL_STATEFILE` (rig/gl_state.txt) at
   teardown; shell reads it back into collection.ini after each game.
4. **Card art**: per-game title screenshots never lined up → cards are
   now the clear logo centered on a uniform gradient panel
   (card_panel_image); screenshots dropped from the menu entirely.

## ZEUS2 BACKPORTS — Exotica rendering (the big one)

Jos van Mourik (mourix) is actively fixing zeus2 upstream RIGHT NOW, and
our 0.286 base (2026-02-26) predates all of it. Backported onto
poc/quadlog (clean applies, zeus2.cpp/.h only):
- **mamedev/mame#15719** (merged 2026-07-18): road disappearing (bad
  fast-HSR pre-cull), nearest road segment dropped (near-plane clip
  instead of reject), perspective-correct texturing.
- **mamedev/mame#15723** (OPEN, "Assisted by Claude Opus 4.8"): fast-clear
  depth-0 guard (stuck black overlay post-race), untextured solid-color
  quads via texmode bits 10-11 (triple flag-girl sprites), clamp 1.8
  fixed-point translucency before rgb_t::scale8 (**cars scaled
  near-black — the rig-observed black cars**). Watch the PR for review
  changes before v0.2.0; re-sync if upstream amends it.
- NOT taken: #15760 (crusnexo.lay dashboard rework — we hide the layout
  with -view "Screen 0").
User verdict pending at the wheel. If Exotica becomes playable-good,
consider thanking/tracking mourix's future zeus2 PRs each MAME bump.

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
- [ ] mame-src still says `cruisn-poc` in POC-NOTES.md and generated-header
      comments — piggyback the path fix on the NEXT mame-src commit (any
      standalone fix forces a patch-series refresh + CI cache invalidation).

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
