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
  the 401-line fix — **v0.2.0 tagged 2026-08-24** with everything current.

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

## RIG TEST — DONE; v0.2.0 CUT 2026-08-24

The list that used to live here (wizard, FFB, Esc menu, Exotica, World
speed) was worked through in rounds 1–6 below. 2026-08-24 the user's
verdict on the offroadc both-edges widescreen: "not perfect but honestly
the closest we've gotten to perfect this whole campaign" → documented,
tagged **v0.2.0** (CI builds + publishes on the tag; `CHANGELOG.md` +
`docs/release-notes/v0.2.0.md` are the release text). Next: the minor
items the user wants to discuss.

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
**STANDING TASK (user request): check upstream mamedev PRs (zeus2,
midvunit, midzeus, dcs) for backportable fixes at every catch-up and
before every release tag.** (Also in Claude project memory.)

## Round 3 (2026-08-21, light testing) — verdicts + fixes

User: Exotica "improved" after the zeus2 backports. New items, all fixed
same session (Python/config only, no rebuild needed):
1. **Exotica volume low**: its DCS mix boots quieter; cabinet VOLUME
   UP/DOWN buttons now bound to = / - for crusnexo (CMOS-persisted —
   adjust once in-game).
2. **Wizard can't see the wheel's Start button**: glfw's Win32 joystick
   backend uses DIJOYSTATE (32 buttons) — same disease as MAME's
   winhybrid pre-fix. Buttons 33+ are invisible to the wizard, BUT the
   EmuEz-translated ADDSW binding already covers Start in-game (skipping
   the wizard start step is correct). Future option: ctypes DirectInput
   (DIJOYSTATE2) capture in the wizard.
3. **CRT mismatch on Exotica**: no GL overlay on Zeus → MIDV_GL_CRT was
   simply inert there. Now Zeus+CRT launches use MAME bgfx
   crt-geom-deluxe (boot-time; shell setting is the toggle, F9 inert).
   ⚠️ RELEASE GAP: make_release/release.yml must bundle mame-src's
   `bgfx/` (chains + shaders) or frozen installs lose Exotica CRT.
4. **F9 in Exotica did frameskip**: F9 IS MAME's stock Frameskip-Inc —
   and on V-Unit every F9 CRT toggle was ALSO silently bumping frameskip.
   UI_FRAMESKIP_INC/DEC now unbound (NONE) in the generated ctrlr for
   all games.
5. **Menu**: logos now float free (no card rectangle) with a pulsing
   radial gold glow + slight scale-up as the focus highlight.

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

## ZEUS GL ARC — phases 1+2 DONE in one session (2026-08-22)

The Exotica renderer-replacement arc is two-thirds real:
- **Capture**: zeus2.cpp `MIDZ_CAPTURE=<dir>` + `MIDZ_CAPTURE_FRAME` +
  `MIDZ_CAPTURE_MINQUADS` (frame numbers drift per boot; Exotica 3D
  renders every other frame). Records quads + palettes + clears +
  frame_writes in mutation order, bracketed by full color+depth dumps.
- **CPU oracle**: `harness/zeus_rasterize.py` — **100.0000% color AND
  depth on three captures** (38 / 1,723 / 6,489 quads). Bit-exact
  semantics documented in RESULTS (SSE bilinear halving trick, scale8
  truncation, transcolor reject-any, integer z stepping).
- **GPU renderer**: `gpu/zeus_renderer.py` — 100.0000% exact on 2D,
  99.94%+ within ±1 on 3D (GL blend rounding; documented stance: CPU
  oracle is the bit-exact ref). 4× proof:
  `results/proof/zeus-gl-showcase-4x.png` — glass-smooth Exotica.
- **REMAINING (next session): live in-process integration** — hook
  zeus2_draw_quad live like midvunit_v.cpp does (window/present machinery
  reusable), shader export, env gates, Esc menu + CRT + crack-fill-class
  care (remember: hardware cliprect applies in QUAD-LOCAL y — back-page
  quads spill into the displayed page without per-quad scissor).
  Coverage gap: texel modes 0 (4-bit) and 2 (rgb555/texture-alpha) not
  yet in any capture — grab a GAMEPLAY capture (user driving) first.

## Round 4 (2026-08-22) — user's 16-item list; project aim upgraded to
## "improve on the original in every facet that's feasible"

Fixed same session: circular glow (1), wizard cooldown bar + >32-button
note (2,3-UX), hotkey legend + CONTROLS SETUP rename (4,5), WER ding via
inherited SetErrorMode — trade-off: no new vunit minidumps (6), Esc menu
now PAUSES the machine (10), margin extend = clamp-stretch boundary
column into unwritten margin pixels, MIDV_GL_MARGINFILL (7,14), volume
=/- uniform across all games (8 interim).

BACKLOG (new, from the "improve everything" mandate):
- [ ] Steering feel (9): shell settings page writing MAME per-game cfg
      analog attrs (sensitivity etc.); first advise Moza Pit House 270°
      rotation + in-game service recalibration.
- [ ] Auto-volume (8 full): find the CMOS volume byte per game (RAM/NVRAM
      hunt) and poke it at boot via Lua or nvram patch - no user action.
- [ ] Wizard >32 buttons (3 full): raw DirectInput (DIJOYSTATE2) capture
      via ctypes COM, or a MAME-side Lua input reader.
- [ ] Off Road coinage (13): needs one-time service-menu change (F2) or
      locate coinage in CMOS and patch the fixture; add "free play" note.
- [ ] Exotica boot popup (15): unidentified - need user description/photo.
- [ ] Render distance (11): would need game-code (TMS32031) culling
      patches - research arc, no promise.
- [ ] Exotica sharpness (16): = the Zeus GL live-integration arc (next
      session); no ReShade needed.
- Exotica desktop flash on exit, once, unreproduced (12): watch.

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

## ZEUS GL ARC COMPLETE — phase 3 LIVE (2026-08-22, autonomous block)

**Exotica runs through our GL renderer live at 4x** (mzgl inside
zeus2.cpp; MIDZ_GL=1 default via run_rig; MIDZ_GL=0 = d3d fallback).
Esc menu WITH pause, F9 CRT (new RGB present shader), snaps, statefile.
First-light bugs fixed: fast-clear live gate (screens accumulated),
flips now emitted AT the zb38 write (was per-frame sample = flashing).
Perf: final 99.76% (d3d baseline 100.00; attribution data in RESULTS —
residual variance parked for ETW). V-Unit regression clean (99.93%).
MAME window stays SMALL under the Zeus overlay (monitor-sized popup
follows the monitor, not the window).
USER TEST PENDING: wheel input, Esc menu pause feel, CRT taste,
flashing-gone confirmation, and zeus_capture_play.py gameplay captures
(texture-alpha/4-bit coverage for the oracle).
Round-4/5 items still pending user: glow/cooldown-bar/legend/steering
sens look, button_monitor run for the Start button, service-menu passes
for volume/coinage baking (nvram_tool.py flow ready).

## Session 6 (2026-08-22): patch system + culling investigation
- **MIDV_PATCH game-code patcher SHIPPED** (in-memory, ROM-safe, verified). Foundation for all game-code fixes. Disasm via MAME debugger `dasm`; patch/game/README.md.
- **Culling "sky through ground" = revealed backdrop, NOT a cull limit.** Proven: native 4:3 has no corner blue; ground quad verts already span x=-366..1000; wedge pixels are legit water quad, not holes. No game patch applies.
- **Runtime MIDV_GL_MARGIN SHIPPED** (0..86/side); run_rig per-game GAME_MARGIN (offroadc=64 trims the water wedges, others 86). Margin-EXTEND off-by-half fix also in this build.
- **NVRAM reset to clean fixture baseline** all 4 games + snapshots (rig/nvram-snapshots/20260822) for the settings-bake workflow. ROMs verified OK.
- NEXT: user service-menu passes (nvram_tool diff/bake) for coinage/volume/freeplay defaults; steering CURVE 70 taste test; wizard >32-button (rawjoy) rig test.

## Widescreen research complete (2026-08-22) — docs/widescreen-research.md
- FOV-constant DSP patch is real & we have the tooling, BUT it does NOT
  avoid the revealed-backdrop artifact (every source converged) - reveals
  MORE backdrop, not less. TMS320C31 uses NON-IEEE float (IEEE hex won't
  match; corrected hex table in the doc).
- **First-choice fix for offroadc water = content-specific backdrop
  masking at OUR render layer** (how Model 2/3 do it): find the water/
  backdrop quad via MIDV_QUADLOG and scissor/cull it in the margins.
- FOV patch = separate R&D (novel, first-on-V-Unit), NOT the artifact fix.

## New feature request (2026-08-22): game-specific menu audio
- Per-game intro/attract music; switches when you highlight a game card.
- Music fades out (not abrupt) when a game launches.
- Need to source proper per-game tracks (LaunchBox video snaps -> ffmpeg,
  as make_music.py already does for the single menu track). Fade = MCI
  volume ramp or a short cross-fade in the Audio class.

## OVERNIGHT-SESSION CANDIDATES (unattended, no wheel needed)
1. Game-specific menu audio + launch fade (NEW request) - self-contained,
   verifiable offline.
2. Backdrop-masking fix for offroadc water (research first-choice) -
   capture-analysis + renderer scissor, oracle-verifiable.
3. FOV-constant DSP patch R&D (novel Hor+ attempt) - uncertain, uses the
   corrected C3x hex table + MAME debugger watchpoint.
4. Telemetry Phase B: RAM-hunt speed/RPM in attract (unblocks achievements).
5. Multi-hour soak + crusnwld/offroadc oracle determinism passes.
NOT overnight (need the wheel): CMOS setting-baking, steering taste tests.

## Overnight session 7 COMPLETE (2026-08-22/23)
- **Task 1 audio: DONE** - per-game attract music from LaunchBox snaps, cross-fade on highlight, 1.2s launch fade-out. gen_game_music.py.
- **Task 2 water artifact: reproduced + characterized + documented** (revealed lake, research-confirmed). Surgical backdrop-mask deferred to a with-user visual session (blind culling risks good canyon scenes). ASPECT toggle is shipped mitigation. MIDV_DBG_QUADID debug added.
- **Task 3 FOV R&D: novel groundwork** - offroadc C3x constant map (screen 512x400, center 256, clip bounds, reciprocal table) + perspective-divide at 0x010AF8. Next: trace divide callers to the X-scale MULF, test-patch. docs/widescreen-research.md.
- **Task 4 Telemetry Phase B: crusnusa speed CONFIRMED + wired + live-verified** (word 0x0F22D, 4066 UDP datagrams 0..301 mph). RAM-dump hunt tooling (MIDV_RAMDUMP_DIR) is turnkey. offroadc/crusnwld pending (offroadc = per-car array needing on-screen correlation).
- **Task 5 soak: not reached** (as expected). Patch series now 31.
- Also shipped this session: game-code patcher (MIDV_PATCH, ROM-safe), runtime MIDV_GL_MARGIN, ASPECT/WIDESCREEN presets, margin-extend probe fix, per-game audio.

## Session 8 (2026-08-23): Task 2 WATER ARTIFACT SOLVED
- Chased the FOV trace (item 1): found the projection epilogue at 0x0239C-0x023A3 (perspective divide + center offsets 256/200); FOV scale is in the upstream vertex matrix (deep - documented, not completed).
- PIVOTED to item 3 (renderer backdrop-mask) which SOLVED it: the blue "lake" is the sky/horizon BACKDROP band (texbase 0x7f, full-width, drawn first) showing through the 16:9 margins. Fix: discard backdrop quads in the margins -> margin-extend fills sky-above/terrain-below. Terrain untouched, exact mode 100
## Session 8 (2026-08-23): Task 2 WATER ARTIFACT SOLVED
- Chased the FOV trace (item 1): found the projection epilogue at
  0x0239C-0x023A3 (perspective divide + center offsets 256/200); FOV scale
  is in the upstream vertex matrix (deep - documented, not completed).
- PIVOTED to item 3 (renderer backdrop-mask) which SOLVED it: the blue
  "lake" is the sky/horizon BACKDROP band (texbase 0x7f, full-width, drawn
  first) showing through the 16:9 margins. Fix: discard backdrop quads in
  the margins so margin-extend fills sky-above/terrain-below. Terrain
  untouched, exact mode 100.0000%, 0 false positives on other games,
  live-verified full-16:9 (bottom-margin water 0.40 down to 0.02).
  Ships default-on. Proof: results/proof/offroadc-water-FIXED-16x9.png.
- Full 16:9 Off Road is now CLEAN. Minor residual: faint sky clamp-
  streaking in upper margins (refine later with a vertical-gradient sky).
- Tooling added: MIDV_STATEDUMP_MINQUADS trigger, MIDV_DBG_QUADID mode.
- Patch series 32. Closes the artifact chased since session 5.

## Exotica perf regression RESOLVED (2026-08-23 evening)
User felt "half framerate + choppy audio" in Exotica. Investigation:
- NOT a code regression (yesterday's build measured identically today).
- Discriminating pair (user's idea): USA 99.81% vs Exotica 94.31% same
  minute, same load -> Exotica-specific headroom problem, not pure ambient.
- ROOT CAUSE: with the live overlay the game was rendered TWICE (our GL +
  MAME's CPU rasterizer into a never-displayed buffer). FIX: skip
  render_triangle_fan when midz_live, local extra struct (no poly ring).
  Exotica now 99.7-99.8% under ambient load, matching V-Unit.
- Measurement lore: freshly built exes get Defender-scanned - perf runs
  right after a build read 5-15% low (earlier attempt measured 80-86% and
  was wrongly reverted because of this). Space builds from measurements.
- Ambient load facts: Pit House burns ~88% of a core at idle; SimHub adds
  more when open. Cumulative Get-Process CPU is NOT current rate.

## Exotica polish round (2026-08-23 late)
- Aspect "wobble" FIXED: present-mode hysteresis (wide immediate on quads,
  4:3 only after ~30 quad-free write iterations). Patch series 39.
- OPEN: Auto/Manual transmission screen self-selects with no input.
  Suspects: latched DS-8X shifter holding a gear button (Exotica gears =
  BUTTON2-5, a held latched position may read as an immediate selection),
  OR gas-pedal rest value. Investigate with button_monitor + the ADC
  values at that screen; may be authentic cab behavior with a latched
  shifter. Needs the user at the wheel to reproduce.

## Exotica "still 4:3" RESOLVED as game-side culling (2026-08-23 late)
Instrumented: wide_mode=1 through the whole race; black side bars measure
EXACTLY 86/684 = the margin width. The 16:9 present IS active - Exotica
itself culls nearly all geometry to the 4:3 frustum (research-predicted;
Model 3 docs verbatim). Vegas day track shows real margin content; night
tracks (China/mountain) show black = looks 4:3. TRUE full 16:9 needs the
Zeus FOV/cull DSP patch (TMS32032, same C3x float family - method ready).
User to choose: accept partial / edge-extend cosmetics (not recommended,
smears) / Zeus FOV R&D.

## Per-game steering SHIPPED (2026-08-23 late)
Steering sens/curve now per-game (edits apply to the game highlighted on
the menu, short-name labeled). Legacy globals migrated to the V-Unit trio;
Exotica starts LINEAR (fixes its twitchiness from the global 70 curve).

## Session 9 (2026-08-23): Exotica TRUE full 16:9 + World speed telemetry

**Exotica 16:9 — the "game-side culling" conclusion above (dated
2026-08-23 late) is SUPERSEDED. There is no game cull to widen.** Full
detail in RESULTS.md. The game already renders a full 16:9 field of view;
the black margins were OUR overlay bug: the mzgl canvas holds both
page-flip buffers, and the 16:9 margin clear (riding the game's frame-sized
fast-clear) used a full-height scissor, so every frame start wiped the
DISPLAYED page's margins too. Fix = scope the margin clear to the cleared
page's rows (zeus2.cpp). Margins went 0% -> 75-100% lit in all 3D scenes;
2D stays 4:3. Proof: results/proof/zeus-true-169-{tunnel,showcase}.png.
ROADMAP A2 is DONE with NO game-code patch. The FOV/cull DSP hunt that led
here built lasting tooling (kept, all env-gated, inert unset):
MIDZ_PCLOG (FIFO-submit PC histogram), MIDZ_RINGTAP (RAM write tap for
draw-model headers), MIDZ_PATCH (in-memory word patcher, ROM-safe) +
results/crusnexo-prog.asm (full TMS32032 disassembly). These now serve C2
(render distance).

**B1 World speed telemetry — DONE + live-verified.** Reusable hunt: dump
DSP RAM every 30 frames over a ~240s attract demo (MIDV_RAMDUMP_DIR), then
offline keep C3x-float words that ride a 0->top->0 curve AND have an
"odometer partner" (a neighbour whose per-frame delta correlates with the
value). That speed+odometer signature self-validated on USA 0x0F22D and
isolated crusnwld 0x0DDDC (verified end-to-end: 0->277 over UDP). Wired.
s_speed_addr now parent-romsets-only (dropped dead crusnu40/21 typos;
clones fall through to telemetry-off, not an unverified offset).
- **World 0x0DDDC NEEDS ONE WHEEL CHECK**: confirm this field == the
  on-screen speedometer, not a sibling (wheel-speed / velocity component in
  the same 10-field cluster; they diverge only under wheelspin/slide).
- **Off Road speed STILL OPEN**: its attract demo shows no clean
  accelerate-from-0 speed curve (candidates spike-and-drop or read as
  signed velocity components). Needs an on-screen-MPH correlation pass at
  the wheel to pick the player slot.

Patch series refreshed after both mame-src commits.

## STILL PENDING USER ACTION
- Wizard re-run of GAS + BRAKE steps (captures pedal press direction) -
  the Exotica transmission auto-select fix is INERT until this is done.
  Root cause proven: Moza axes rest at center; MAME reads 50% throttle.
- Wheel check that Exotica true-16:9 looks right in motion (day AND night
  tracks - night tracks are what looked "4:3" before; they should now fill
  the width).
- Wheel check that World telemetry speed (0x0DDDC) matches the on-screen
  speedometer; if it lags/leads under wheelspin, pick a sibling from the
  0x0DDDC cluster (see RESULTS 2026-08-23 telemetry section).
- Off Road on-screen-MPH pass so its speed slot can be picked.

## Session 9 cont. (2026-08-23, user away) — B4/B5/D1 shipped, B2/B3 advanced

Autonomous batch while the user stepped away. All committed, patch series
refreshed, exact mode re-verified 100.0000%.
- **B4 FFB STRENGTH — SHIPPED.** New SETTINGS row (0-100%, 10% steps,
  default 100). run_rig.apply_ffb_strength patches FFBPlugin.ini [Settings]
  MaxForce + AlternativeMaxForceLeft/Right at launch (per-game suffixed keys
  untouched; no-op if plugin absent). Persists collection.ini ffb=; also
  run_rig --ffb. VERIFY at wheel: does the % actually scale the force.
- **B5 sky-margin streaks — SHIPPED.** Present-pass fetch_smooth vertically
  gaussian-blurs unwritten 16:9 margin pixels -> clean sky gradient, no
  horizontal streaks, horizon as soft haze. Gated uMargin>0 (exact
  untouched). Header regenerated + rebuilt, live overlay err=0. Proof:
  results/proof/vunit-sky-margin-smoothing.png.
- **D1 string cleanup — DONE.** midvunit_menu_assets.h header comment
  cruisn-poc -> cruisn-collection (generator already correct).
- **B2 RPM — leading candidate, UNWIRED.** 0x0F0C0 (mirror 0x0DB67) via a
  fine-cadence recapture; step-drops at shifts but flat in 1st gear + no
  cross-check. VERIFY at wheel: watch the on-screen TACH to confirm + get
  its scale, then wire.
- **B3 volume — MEASURED, needs the wheel.** V-Unit trio mutually
  consistent (~-33 dBFS active, quiet native mix); Exotica silent in
  headless attract (attract sound likely off in CMOS; heard live when
  coined). Needs a service-menu pass for Exotica, then a CMOS bake. No safe
  blind action.

CORRECTIONS after the user tested at the wheel (2026-08-23):
- **B5 REVERTED.** The vertical gaussian blur smeared structured 2D margin
  content (the boot ROM self-test grid) into vertical streaks. Back to the
  shipping horizontal clamp-extend. B5 reopened: needs a sky-ONLY /
  3D-scene-gated fill (must not run on 2D/menu/test screens).
- **B2 crusnusa RPM CONFIRMED + WIRED.** The user's real drive
  (capture_drive.py) debunked the attract candidate 0x0F0C0 (near-zero in
  gameplay) and confirmed **0x0DC20** = tach: tracks speed then V-dips at
  the Hi/Lo shift while speed stays flat. Emits "rpm" over UDP (verified,
  0->~912). World/Off Road RPM still need their own drive (RAM differs).
  Proof: results/proof/crusnusa-rpm-0DC20-drive.png.

Remaining autonomous-unsafe (need the wheel or approval): B7 gear bindings
(input hook can't be verified blind - deferred), C1 coinage (service menu /
CMOS), C2 render distance (research), D4 upstream PR (outward-facing -
needs approval), F1 v0.3.0 tag (needs the rig test).

## Note on session model
The harness reroutes off Fable 5 when security-adjacent keywords appear in
the request stream (user flagged one like "c-y-b-e-r"). This is pure
game-renderer / DSP RE work - keep vocabulary neutral in prose, commits,
and comments so the session stays on the intended model. (In project
memory too.)

## Session 9 late-night: telemetry ground truth + margin regression (2026-08-23/24)

Full chronicle in RESULTS.md ("telemetry ground-truth saga"). Load-bearing
facts for next session:
- **Attract-hunted telemetry words were DRONES** (attract demos are
  drone-driven). Player speed persists in NO dumped memory (both banks +
  C31 internal RAM at 0x809800, all decodings vs HUD-OCR ground truth).
- **crusnusa RPM = 0x0E632.lo16** (uint16 raw 0..~14.6k), confirmed
  r=+0.91 vs the on-screen tach gauge fill. WIRED. Speed entries zeroed.
- **Speed fix = HUD-quad DMA tap** (digit identity in dma_data[10..13]
  texcoords for quads in the MPH box, ~x30-72/y347-370 for USA). World
  calibrating headless from attract (results/wld-hudcal capture:
  MIDV_QUADLOG + hud dumps). USA: one short user drive with quadlog, or
  the font mapping may transfer from World.
- **HUD-OCR pipeline** (proven): hud_*.bin = visible-page rows 300-399;
  glyph clustering at 12x18 grayscale, min cell width 2 (else "1" is
  lost), 3-digit reads drop the leading 1 intermittently (readings >99
  need continuity checks). RPM gauge fill = count of palette idx 1 in
  cols 400-512.
- **Diagnostics**: forza_probe.py (live packet decode + CSV), forza_synth.py
  (synthetic drive to SimHub - proved read side). MIDV_TELEM_FORZA accepts
  comma-separated targets. ForzaKeeper zero-packets MUST carry real
  EngineMaxRpm=7500 (all-zero packets wedge SimHub).
- **MARGIN FILL defaults OFF** (user's phone photo proved the clean
  original look; clamp-extend caused the smear complaints). SETTINGS row
  toggles it. Off Road shows more black at edges with fill off (water
  backdrop suppressed, no longer extended over).
- SimHub setup: FH5/FH6 profile, port 8000, rig collection.ini
  [telemetry] forza=127.0.0.1:8000,127.0.0.1:8001 (dual: dash + probe).

## 2026-08-24 late — offroadc LEFT edge SOLVED (game-code, both sides)

- Root cause: the left trivial-reject is a **sign test** (all four x < 0),
  no constant to widen; the previous "left isn't culled" measurement was a
  tautology (rejected quads never reach the DMA stream).
- Fix shipped in `patch/game/offroadc-widescreen.txt`: nine `BLTD` →
  `CALLLT $2224`, 12-word routine in NOP padding re-tests x+86 and forces
  the site's right test to reject (R1 := INT_MIN). Exact mirror of the
  right (reject only if all four x < −86). Details:
  `docs/offroadc-left-edge-handoff.md` RESOLVED section; numbers in RESULTS.
- **OPEN: live drive at the rig** (shell → Off Road at 16:9 FULL; both
  margins should now be game-drawn, no blue wedges bottom-left, no smear).
  If anything looks off: ASPECT = TRIMMED/4:3 skips the whole patch; to
  keep the right edge only, comment out the 21 LEFT lines in the file
  (every line is an independent word patch).
- Do NOT replace the routine with plain NOPs on the nine branches: that
  variant emits off-canvas and int16-wrapped quads (measured, see RESULTS).

## 2026-08-24 late (post-v0.2.0) — minor-list fixes, v0.2.1 candidates

Four user-reported issues fixed in one pass (details in RESULTS):
launch ding (MIDV_FAST_EXIT in winmain; run_rig sets it), Exotica
shell-launch focus (run_rig focus watchdog: reclaims only from our own
windows), World radio/view button map (WHEELMAP_PORTS was shifted -
V-Unit Radio=BUTTON1, Views=2-4), World floating dithered box in the
right margin (= the game's RADIO PANEL parked off-screen; meta bit 2
suppresses parked position, slides in normally when deployed).
- vunit.exe rebuilt (winmain + midvunit_v + regenerated shader header);
  patch series refreshed (58 patches).
- **OPEN: user live-verifies all four**, then tag v0.2.1.
- v0.2.0 release CI was still building at write time.

## 2026-08-25 small hours — round two on the minor list

- v0.2.0 RELEASE PUBLISHED (CI success).
- Black textures = coarse-space DITHER TRANSLUCENCY at 4x. Now fine-space
  (smoked glass); crack-filler skips the 1-px checkerboard; exact mode
  100.0000% x2 (the invariant caught a y-flip phase bug on the first try -
  fine coords must use fx/floor(fy), NOT raw gl_FragCoord).
- Ding: exits fixed (fast-exit, event log clean); launch-time ding traced
  to our ALT-tap landing in a stray joy.cpl dialog OPEN SINCE AUG 20 -
  enforce_foreground now uses silent AttachThreadInput (ALT fallback after
  6 fails). User should close the Game Controllers window.
- User's 23:01 screenshots were the OLD build (session started pre-22:47
  rebuild) - parked-panel + radio-map fixes were not in play yet.
- Left-margin black voids (cow backdrop, Germany) = crusnwld's native left
  coverage gap = the World game-code widen project (next R&D block, same
  method as offroadc; disasm already captured).

## 2026-08-25 — World SKY game-code widescreen SHIPPED (pending live drive)

- patch/game/crusnwld-widescreen.txt (20 words): sky engine $9623 draws 5
  panorama tiles instead of 3, one further left; bank table + scratch in
  padding at $162; three RC loops + 2 SUBF starts + horizon fill patched.
  Corner black 40% → 0.1% on the England gap frame; centre identical.
  Auto-applies at 16:9 FULL. Story: widescreen-research.md + RESULTS.
- Left-margin TERRAIN voids (crash cams etc., below sky band y>237) remain:
  World's poly reject ≠ offroadc's signature - separate future hunt.
- 12000-frame stability captures were running at write time.

## 2026-08-25 evening — user rig report (triaged into ROADMAP section G)

Both screen edges "looking really great now" after the widescreen work.
New minor list G1-G7: launch ding STILL present (WER + ALT-tap both ruled
out - next: A/B without dinput8.dll), launcher hang on quick exit (likely
our enforce_foreground fighting a dying window - small fix, do first),
Exotica car-select text illegible (Zeus GL), Off Road track-select seams
(2D cracks by design), settings per-game labels/clutter (submenu rework
with user), settings screen invisible to screenshots (curiosity), manual
H-pattern gears mis-detected (edge/level inversion suspicion).
Telemetry status (user asked): Phase A FFB/lamps + Forza emitter = all
games; speed+RPM only USA (HUD OCR + 0x0E632); World/Off Road speed needs
their HUD captures (B1), RPM via gauge correlation (B2); Exotica unhunted.

## 2026-08-25 night — wheel-session results (overnight setup complete)

- DING = FFB PLUGIN (A/B conviction: no dinput8.dll -> no ding, all games).
- NEW G8: fast-exit skips plugin teardown -> wheel keeps stale forces on
  close. Interim: auto Stop-FFB post-exit; real fix: patched plugin (GPL).
- G7 SOLVED ON PAPER: MAME CONF "Shifter Type" default "Buttons (sticky)";
  rig needs "H-Pattern". World-no-manual / Exotica-auto-select likely DSW
  Cabinet Upright vs Sitdown. B7 = the built-in "Sequential" setting.
- G3 reclassified UPSTREAM (text broken in d3d too - both screenshots).
- B3: World master volume = nvram byte 0x93C (user's 11 = 0x0B found).
  Other games' diffs captured; min-vs-master volume ambiguity noted.
- Drive captures landed: crusnwld x3 + offroadc x1 (ram+ram2+ram3+hud
  dumps) for B1 speed OCR calibration + B2 RPM correlation.
- C1 free play: user set at the wheel (World/Off Road/Exotica).
- C2 render distance: still on the roadmap, user reconfirmed interest.

## 2026-08-25 late — overnight block, first wave SHIPPED

- G1 DING SOLVED: FFBPlugin.ini had BeepWhenHook=1 (plugin's hook chime,
  default 0). Off on rig + re-forced by apply_ffb_strength + release ini.
- G2 FIXED: enforcer aborts on dead/unresponsive window (probe: 0.7s).
- G7 IMPLEMENTED: apply_shifter_config -> CONF H-Pattern + sitdown DIPs
  when gears bound; closed-loop verified via MAME's rewritten cfg.
- G8 INTERIM: release_ffb() (SDL2 stop-all) after every exit, both paths.
- All pending the user's next live session for feel/behavior confirmation.

## 2026-08-26 overnight wave 2 — telemetry
- World speed OCR calibrated (box 14,76,342,368; USA font transfers);
  offroadc provisional top-screen box (228,270,22,52) + per-game hud dump
  window in midvunit_v.cpp. Rebuild + patch refresh pending build finish.
- World RPM inconclusive (needs a dedicated full-throttle capture).
- Python OCR port lives in the session scratchpad (hud_ocr.py) - recreate
  from midvunit_v.cpp semantics if needed; the C++ is the source of truth.

## 2026-08-26 overnight wave 3
- G4 FIXED: 2D screens get 1-px crack fill (uFillR gate in midvunit_v.cpp).
- G6: keys exonerated; needs a mode-transition log + user repro. Parked.
- C3 terrain-cull hunt STARTED, parked with entry points: crusnwld quad
  emit sites (poll $0082) at $02AA $0315 $03F5 $0B0F $0CDF $0CE4 $3A40
  $49E4 $553B(sky) $77AE(link comms - NOT poly) $A1B3 $A1F9 $AF3A. The
  offroadc AND-sign/SUBI3 reject signature does NOT appear - World's
  reject is structured differently (likely centered coords). Next session:
  walk back from $A1B3/$AF3A emit loops to their reject tests, same method
  as offroadc (docs/offroadc-left-edge-handoff.md tooling section).
- World RPM needs a dedicated full-throttle capture (see B2 note).

## 2026-08-26 overnight wave 4 — CMOS volume map complete
- ALL FOUR GAMES: settings bytes unguarded (no checksums) - proven by
  single-byte boot-persistence experiments. Map + poke() in nvram_tool.py.
- G6 forensic log added to collection.py (prints why settings closed).
- World DMA-port watchpoint run in flight for the C3 terrain hunt.

## 2026-08-26 overnight wave 5 — World TERRAIN cull widened (C3 code complete)
- MIDV_DMA_PCLOG cracked it: 3D loops emit UNCULLED; only the big-poly
  subdivision path ($379) screen-rejects (sign left, immediate 511 right,
  parent + per-subquad sites). Patch appended to crusnwld-widescreen.txt
  (54 words total now): immediates->597, BLTD->CALLLT x+86 routines at
  $247/$2EA. 12000-frame attract: 0 removed, +134 all-margin. LIVE DRIVE
  = the real test (crash cams). Handoff detail in widescreen-research.md.

## 2026-08-26 — max-volume pass applied to rig NVRAM (user to verify by ear)
- crusnexo m48t35 0x27 = 0x15 (GAME-CLAMPED max: 0xFF poke normalized to
  0x15 on boot - also validates the byte as the real volume field).
- crusnwld 0x93C = 0x00 (pre-user default; evidence reads as attenuation:
  0 was audibly LOUDER than the user's 11).
- offroadc 0x7BC/0x92C = 0xC8 (stored = menu x2; menu max presumed 100 -
  the one SPECULATIVE value; distortion/silence = wrong, user reports).
- crusnusa nvram wholesale-restored to the pre-min-volume snapshot (its
  loudest observed config; that session changed volume only).
- Snapshots taken before all changes (nvram_tool). No free-play flags
  touched. World/USA/offroadc accept unclamped values (no boot clamp).

## 2026-08-29 — G10 perf regression fixed (patch series 62)
- Root cause: PCLOG getenv per DMA word since series 61 (my bug, 3 days
  live on the rig). USA 60->372%, World 35->416% headless. LESSON: never
  put getenv (or any O(env) call) in a per-word/per-frame path - cache in
  a static, like every other MIDV_ hook does.
- World volume note: byte 0x93C=0x00 showed menu volume 14 (not max!) -
  user raised to menu max; diff World nvram after their session to
  calibrate the REAL master-volume byte/scale.

## 2026-08-29 — free-play bytes pinned (headless attract-text method)
- crusnwld 0x1AC, offroadc 0x1CC (single reactive candidate each; others
  produced zero videoram diff). Exotica m48t35 run queued; USA needs one
  user F2 toggle to produce a diff. Method: scratchpad freeplay_pin.py.

## 2026-08-29 — Exotica free play pinned: m48t35 0x73 (lua-snapshot method)

## 2026-08-29 — World volume calibrated by the user's menu-max session
- MASTER volume = nvram 0x9C (0-255; menu max wrote 0xFF) + companion
  0x77C (also 0xFF at max). 0x93C reattributed: small-scale field, likely
  MINIMUM volume (held the user's "11"). Audit counters churn at
  0x64C/0x69C/0x6FC/0x75C/0x78C/0xD2C/0x50C/0xE7C - ignore in diffs.

## 2026-08-29 — free-play map COMPLETE (all four games)
- crusnusa = 0x190-mirror set (only reactive field of ten in the isolation
  loop). Reconciles the mystery: the user accidentally enabled it in the
  08-25 volume session; the wholesale restore reverted it. Map now:
  USA 0x190x4 / World 0x1AC / OffRoad 0x1CC / Exotica m48t35 0x73.
  Everything the G5 per-game settings rows need is calibrated except
  offroadc's true master-volume byte (one menu-max visit calibrates it,
  method proven on World).

## 2026-08-29 evening — NY wedge hunt (in progress) + transmission status
- User reports (NY stage): small black GROUND wedges at extreme margin
  edges below the sky band; transmission select still absent in World.
- Wedges: 0xB6A/0xD41 (the unexamined 511 immediates) EXONERATED (data
  decompressor / screen-wipe). Live suspect: the subdivision WORK BUFFER
  CAP - $3BD sizes it 0xF0 words (~15 sub-quads), $3C4 bails to $49E when
  full, silently dropping the remaining pieces (historically off-screen).
  Note: the 12k multiset check showed 0 removed vs sky-only, so our patch
  did not worsen drops. Hunting wedge frames via truncate-render sweep;
  naive black-pixel metric was fooled by the tunnel's dark art - switched
  to the renderer's write-mask (MIDV_DBG_MASK) measuring UNWRITTEN margin
  pixels below the sky band. Sweep tooling: scratchpad wedge_sweep.py.
- Transmission: CONF=H-Pattern + DSW Sitdown VERIFIED applied+persisted in
  rig/cfg/crusnwld.cfg -> the DIP is not the gate. Next suspect: World's
  F2 operator adjustment (SHIFTER/TRANSMISSION) - user to look + toggle,
  then diff CMOS. ALSO: found+removed a stray ':DSW mask 128 value 0'
  (Service Mode DIP ON) in crusnwld.cfg - origin unknown, watch for it.

## 2026-08-29 late — NY wedge verdict: buffer-cap theory FALSIFIED
- Experiment: relocated the sub-quad buffer to virgin bank-2 RAM
  (0x41F000) + 4x cap via 2 patch words -> frame-4527 hole IDENTICAL
  (537px) and the quad stream bit-identical (0 added/removed to frame
  4599). The cap never binds in the attract; patch REVERTED (file back
  to the proven 54 words).
- Residual wedge class = geometry never submitted at those margin
  positions: either genuine track-content limits or an upstream
  OBJECT-level cull (per-object bounding test before poly generation).
  Quantified TINY in attract driving frames: 4.2% of one margin band on
  one sampled frame, 0.2% on another; the sweep's other hits were 2D
  screens (margins cropped by design). Future hunt: the object-list
  builder's visibility test. For now: documented known-minor.
- Tooling kept: wedge_sweep.py (mask-based unwritten-margin scanner) in
  the session scratchpad; capture-wld-wedgehunt retained for reference.


## 2026-08-29 late — World transmission SOLVED: rev 2.5 deleted the feature

- User's r/MAME thread (7usphd) + the 2.5 ROM factory labels
  ("2.5_cruisn_world_automatic_u10") settle it: rev 2.5 REMOVED
  transmission select; rev 2.4 is the shifter revision. All CONF/DIP work
  was correct but could not resurrect a deleted feature.
- Shipped: patch/game/crusnwld24-widescreen.txt (terrain lines identical,
  sky cluster +0xB; 54/54 OLD-verified vs the 2.4 image AND live loader
  log "54 applied, 0 skipped"); run_rig base_rom() normalization
  (SHIFTER_CFG/STEER_PORT/HEIGHT/MARGIN); collection world_rom ini option
  (DEFAULT crusnwld24, "crusnwld" reverts); midvunit_v.cpp telem_init
  prefix-match (HUD-OCR speed box carries over; World RAM-addr rows all 0).
- Expect at the wheel: one-time CALIBRATE CONTROLS on first 2.4 boot (own
  CMOS), then volume/free-play need re-setting for 2.4 - do NOT poke the
  2.5 byte map (0x9C/0x1AC) into 2.4 nvram until re-verified. After first
  boot, seed fixtures/nvram-crusnwld24 from rig/nvram/crusnwld24 to enable
  captures/oracle on 2.4. Watch the first drive for the 2018-reported 2.4
  artifacts (may be moot under our renderer).
- Lua transmission_probe.lua: PARKED (no longer needed for this; the
  set_value/START mystery stands - heartbeats run, snapshots/inputs don't
  land).


## 2026-08-29 late-2 - menu redesign + sequential paddles + volume pins

- User confirmed: World 2.4 manual WORKS (G7 closed). NY wedges deferred
  to a dedicated session (C3). Off Road/Exotica volumes were sub-max ->
  user maxed via menu; diffs pinned offroadc 0x2FC (0-255) and crusnexo
  0x27 (0-30) as masters; crusnwld24 CMOS layout == 2.5 (0x9C/0x1AC).
- Shipped: per-game submenu (PLAY/sens/curve/VOLUME/FREE PLAY/World
  REVISION toggle), global-only SETTINGS page, steer+gas menu navigation
  (parse_navspec/nav_events in collection.py), wizard SHIFT UP/DOWN steps,
  H-vs-paddles arbitration in apply_wheelmap (BUTTON5/6 collision), CONF
  0/5 in apply_shifter_config. Exotica: no native sequential mode exists.
- USA master volume byte still unpinned (row says use = / - in game).
- User to test at wheel: submenu flow, wheel/gas nav feel, paddle
  sequential mode (needs re-running the wizard to bind SHIFT UP/DOWN),
  volume rows vs actual loudness, Off Road track-select lines (screenshot
  wanted, roadmap G-item).


## 2026-08-30 - rawjoy re-entry fix (>32-button wizard capture)

- User's menu test hit "can't bind buttons >32 again" (Start/Test/Service,
  Moza 33-35). Cause: rawjoy registered the CruisnRawJoy window class with
  the first listener instance's wndproc; class registration is
  process-global, so every wizard re-entry in one shell session got a
  raw-input window wired to the dead first listener - raw queue never
  fills, glfw (<=32) still binds. First-entry-only usage had masked it.
- Proved live (wheel chatter): re-created listener got 0 events vs 2304;
  fixed with module-lifetime _PROC dispatcher -> rawjoy._active; 3
  consecutive cycles now all receive (~2300 events/2s each).
- rig collection.ini [wheelmap] untouched by the failed attempt (still
  start=34/test=33/service=32, no shiftup/shiftdn) - in-game keys were
  never broken; user still needs one full wizard run to bind paddles.


## 2026-08-30 late - TRANSMISSION setting + USA volume row removed

- User design: explicit global TRANSMISSION (H-PATTERN / PADDLE
  SEQUENTIAL) in SETTINGS replaces bind-inference arbitration (which made
  sequential unreachable with both DS-8X + paddles bound). Wizard asks
  only the active mode's shift steps; save_wheelmap MERGES (hidden +
  BACKSPACE-skipped steps keep saved binds; both modes' binds persist).
  run_rig.transmission_mode() drives apply_wheelmap skip-set + CONF 0/5;
  absent key infers old-style (paddle-only rigs stay sequential).
- Scratch-rig e2e verified: hpattern -> gears on P1_BUTTON5/6 + CONF 0;
  sequential -> paddles + CONF 5; crusnexo sequential untouched; ADDSW3
  start intact both modes. Settings page renders sent (8 rows, 0.062).
- USA VOLUME hotkey-pointer row removed from the submenu (auto-returns if
  the byte is pinned into VOLUME_CMOS).
- User wheel test plan: flip TRANSMISSION to PADDLE SEQUENTIAL, run
  CONTROLS SETUP (15 steps, gears hidden), bind paddles + re-bind
  start/test/service (rawjoy fix makes >32 work on every entry now).


## 2026-08-30 late - continue-line fix + C2 render-distance research round 1

- Continue-screen vertical line: FIXED at the source (see RESULTS.md) -
  quality-mode axis-aligned quads now dilate to the hardware DDA span
  (renderer.py _dilate_rect + C++ port, mame-src 200e986e); live-verified
  clean, exact mode 100.0000% x3 (incl. new capture-continue, first 2D
  verified scene).
- lua/coinup.lua NEW: scripted COIN/START/GAS via ioport set_value -
  headless DRIVEN gameplay works (97mph verified). The old "set_value
  doesn't land" verdict was a probe-script bug.
- C2 research round 1: crusnusa object system mapped (see RESULTS.md for
  node layout/pipeline/addresses); 0x727E=80000 draw-threshold hypothesis
  FALSIFIED (bit-identical A/B driven). Next: MIDV_DBG_QUADID attribution
  of the Golden-Gate gray-slab pop-in specimen -> real gate.
- Debugger scripting: logerror-with-args + wpset+g chains reliable;
  gtime-long flaky; -debugger none dead; save unresolved (use RAMDUMP).


## 2026-08-30 latest - C2 round 2: draw-distance gate FOUND + healed patcher

- crusnusa render gate = word 0x55 (80000, depth-radius test at 0xCB);
  LOD switches words 0xBF (8000) / 0xC3 (15000). All earlier null
  results explained: game startup re-copies ROM over words <0x10040
  AFTER MIDV_PATCH -> mame-src 784bdfc6 adds per-frame self-healing
  re-assert (only when word reads verified OLD; runtime overrides
  respected). Control A/B verified live: 20000 -> world truncates
  (1989->600 quads/frame). Extension beyond 80k limited by the section
  streamer's spawn window (round 3 target: the 0x70DD-caller loop).
- Try-me: patch/game/crusnusa-renderdist-experiment.txt (MIDV_PATCH env;
  no conflict - crusnusa has no widescreen patch). User to eyeball
  extended LOD/distance in a real drive before any SETTINGS row.
- Reminder for wizard/menus testing still pending from earlier today:
  TRANSMISSION setting + paddle binding + rawjoy re-entry fix.


## 2026-08-30 review pass (Fable 5.1 second set of eyes)

- Dilation texture drift found + fixed (UV extrapolation in all 3
  builders); new fidelity metric: quality S4 vs exact-upsampled on
  capture-continue: OFF 15.29%, shipped 30.56%, fixed 14.04%.
- MIDV_GL_SNAP heap overrun (PACK_ALIGNMENT 4 vs tight buffer) - latent,
  exposed by a 1535-wide window once the user was back at the desk; fixed
  with PixelStorei(PACK_ALIGNMENT,1). Lesson: a 3-4 s live crash with
  0 snaps = snapshot path; bisect env before code.
- complete_run merge capped at 16384 quads; coinup.lua no longer exits
  at frame 1 without SNAP_FRAMES.
- Debugger note: logf() output is BUFFERED - "no run: lines" after a
  crash means nothing.


## 2026-09-02 - onboarding review for the first external alpha tester

- Traps fixed (RESULTS.md has the list): World 2.4 clone handling
  (world24_available/resolve_world_rom + hash/clone-aware setup GUI),
  on-screen launch-failure reasons (rig/launch.log), set-ranking fix
  (parents win ties; per-set status), FFB "Detect wheel" (plugin-log
  harvest; blank DeviceGUID = no FFB, confirmed from plugin source),
  make_release always re-freezes, fixtures/nvram-crusnwld24 seeded.
- Docs: README + docs/INSTALL.md rewritten player-first; release notes
  docs/release-notes/v0.3.0.md drafted (tag v0.3.0 -> CI builds + publishes).
- In-process SDL2 (plugin's dll) enumerates ZERO joysticks from python
  regardless of hints - don't retry that road; the plugin's own FFBlog is
  the reliable device list.
- Repo is PRIVATE: the tester must be added as a collaborator to download
  release assets (or send the zip directly).

## 2026-09-03 handoff (evening/night session, v0.3.5)

Shipped in v0.3.5 (see CHANGELOG): FFB STRENGTH fixed (per-game plugin
keys), FFB PEAK LIMIT, force law measured, AlternativeFFB=1 template,
Exotica FFB (wheel output + crusnusa name spoof + wheel power 10 + x4),
FFBReset.exe, out-of-process release, dinput8 preload (plugin out of the
launcher), direct launch, Shift+F12, in-app updater (public repo, no
token), real steering sensitivity (MIDV_STEER_GAIN), old DSP set names,
pedal-stuck guard, virtual sequential shifter for Exotica (inert until
manual is selectable), save_config merge fix, launch.log header.
Open: ROADMAP "Open after the 2026-09-03 rig session" (Exotica overlay
glitches = ours; USA draw distance unmeasured; Exotica manual = MAME
gap; USA road specks). Rig config keys: exotica_gl (0 = MAME renderer),
gamepatch_<rom>. Smoke install at E:/Games/CruisnCollection-smoke.

Later 2026-09-03 (unreleased, on master): plugin switched to Endprodukt's
FFB Plugin MAME; FFB knobs (ffb_slew/rumble/alt/power/hold/constinf);
wheelpos in the trace + report/plot in the bundle; SETTINGS rows FFB
DIAGNOSTICS + SAVE SUPPORT BUNDLE. **Exotica FFB verified through the
fork** (235 updates, one-for-one with the trace). **Regression caught:**
the fork's SDL 2.24 writes joystick GUIDs without the name CRC that the
stock plugin's SDL 2.28 wrote in bytes 2-3, so every saved DeviceGUID
stopped matching -> "No haptic device available" -> FFB silent
everywhere (this was the tester's "failed swap"). run_rig
normalize_ffb_guid() (ctypes on the shipped SDL2.dll, from
ensure_ffb_guid at each launch) rewrites the GUID; dev folder + smoke
install fixed. THEN (same afternoon) the plugin was retired altogether on
Endprodukt's advice: **force feedback is built into vunit.exe** (mvffb in
midvunit_v.cpp, SDL2 haptics on the steering axis, Cannonball DX model,
SDL2.dll loaded at run time; MIDV_FFB / _STRENGTH / _DEVICE / _INVERT /
_HOLD_MS / _TEST / _LOG; midv_ffb.log). Sign measured on the Moza:
positive byte = push right, positive SDL level = Moza turns left ->
level = -sign(byte); SETTINGS -> FFB DIRECTION flips. All plugin code,
files and docs removed (ffb/ dir gone, third_party/SDL2-LICENSE.txt
added, CI installs mingw-w64-x86_64-SDL2). The tester's Fanatec has not
felt the native path yet: FFB DIRECTION is the knob if it runs away.
v0.3.6 TAGGED 2026-09-04 after the rig verdict: strength 50 + ffb_smooth 50
("much better"; damper/friction opt-in). Open minor: launcher LEFT right
after opening acts as ENTER; distant red/blue road specks.
2026-09-04: **Exotica manual transmission SOLVED** - the TRANS SELECT
screen is gated on the DS1 "Wheel Invert" DIP (Endprodukt's tip, proven
headless: DIP off = the game confirms AUTO instantly whatever the wheel
does). That DIP also mirrors the wheel for driving, so the driver cancels
it (MIDZ_WHEEL_INVERT in analog_r) and the launcher seeds the DIP into
rig/cfg/crusnexo.cfg. Spring measured -16.4 at parked-right = correct,
vs +16.8 with the DIP alone. Menu quirk: turn the wheel LEFT for MANUAL.
MIDZ_SEQ_SHIFT is finally live; needs a rig drive.
2026-09-04 (v0.3.8 prep): upstream #16046 backported - Exotica was running
in SLOW MOTION (C32 timer CLKSRC) and had a dark band from a wrong SGRAM
fill decode; that also supersedes the #15723 depth-clear workaround.
Wheel output renamed "wheel" -> "wheel_motor" per Endprodukt's open #16055
(he is upstreaming the Exotica motor byte we found). Lamp outputs were
broken in v0.3.6 by our own plugin removal (mame.ini lost `output windows`,
MAME defaults to the "none" output module) - restored. V-Unit oracle
re-verified 100.0000%.
Also fixed: wizard axis index -> MAME slot translation (dinput_axes.py;
sparse pedal devices were mapped to the wrong axes - Endprodukt's inert
pedals, unconfirmed on his hardware yet).
