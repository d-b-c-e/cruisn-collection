# Session Notes
<!-- Handoff notes. Read these first, then CLAUDE.md, then results/RESULTS.md. -->

- **Date:** 2026-08-20 (overnight session 3 complete)
- **Branch:** master (mame-src side: `poc/quadlog` @ ad4d2d8b)

## Where things stand

**CRUIS'N COLLECTION is now four games in one exe** (midzeus joined the
vunit subtarget): USA/World/Off Road bit-exact through our GL renderer,
Exotica through MAME's own renderer at rig-parity (NOT_WORKING-flagged
upstream but play-tested; GL replacement scoped VIABLE — zeus2_draw_quad,
≤6.3k quads/frame). Shell has proper nav (games row + Settings screen),
working wheel/wizard input (pyGLFW pointer-tuple bug fixed), the user's
chosen soundtrack via the make_music.py pipeline, install docs + setup.ps1.

## Morning checklist (user)

1. Deck button → new nav: up/down to SETTINGS, CRT toggle + WHEEL SETUP
   inside. **Wizard should now react to wheel/shifter/stalk buttons** —
   bind everything, then verify in-game from the wheel.
2. **Exotica card** → launches fullscreen d3d; FFB as in the racing build.
3. Music: the requested track plays in the shell (swap any time:
   `python harness/make_music.py <url> --skip N`).
4. Still watching: CRT taste (F9), World margin black-bars, mid-game
   crash singleton (dumps in rig/crashdumps).

## Open Items

- [ ] Physical wizard/nav/Exotica pass (above).
- [ ] Esc in-game settings overlay (designed; GL-thread menu +
      GetAsyncKeyState + WM_CLOSE exit).
- [ ] UDP telemetry Phase A (mirror the FFB output value to UDP for
      Buttkicker/SimHub) then Phase B (speed/RPM via Lua RAM hunt).
- [ ] Zeus GL renderer (level 2): capture → reference → GL over
      zeus2_draw_quad; MIDZ_STATS=1 profiler is in.
- [ ] Release packaging dry-run: follow docs/INSTALL.md + setup.ps1 on a
      clean layout; consider PyInstaller freeze of the shell.
- [ ] C++ overlay HEIGHT=400 vs offroadc's 401 lines (cosmetic).
- [ ] Teardown-AV minidump analysis; margin pop-in heuristics; soak.

## Next Steps

1. Ingest wheel-test results (wizard + Exotica).
2. Esc overlay implementation; telemetry Phase A (both small C++/launcher).
3. Zeus GL capture arc when a session can afford it.

## Context for Next Session

All committed: cruisn-poc master, mame-src poc/quadlog @ ad4d2d8b (patch
series exported — now includes zeus2 + winhybrid + frontend files),
Launchbox-Racing unchanged tonight. Build command now needs BOTH sources
(midvunit + midzeus) — see CLAUDE.md; shader regen is
`python harness/gen_shaders.py` (raw strings break REGENIE).

## Addendum (2026-08-20 afternoon): distribution sprint

- **CruisnSetup.exe** (tkinter, frozen onefile): identifies ANY zip by
  member names+CRCs vs roms_manifest.json (from vunit -listroms, 25 sets)
  - filename-independent, clone-aware, missing-file reporting, installs
  under correct set name. Verified: real/renamed/wrong-game zips.
- **Support bundle** (GUI button + harness/support_bundle.py): MAME input
  dump (lua/input_dump.lua), -verbose device lines, glfw joydump, FFB log,
  configs -> CruisnSupport-<stamp>.zip for bug reports.
- **Media bundled** (user decision): media/ in repo (8 art + menumusic.mp3
  as mp3); make_release -NoMedia for clean variant. ROMs stay out.
- **Patch series is now FULL from mame0286 tag** (17 patches - clean-clone
  git am was silently missing the DIJOYSTATE2 base before).
- **GitHub**: repo d-b-c-e/cruisn-poc (private), pushed; release.yml
  builds vunit from upstream+series (cached), freezes both apps, downloads
  FFB plugin, publishes zip on tag. **v0.1.0 tagged - first CI run in
  progress** (watch: gh run list).
- Release zip (local build): 86 MB, E2E-verified from the folder.

### Newly queued features
- [ ] Gamepad support: wizard already binds gamepad BUTTONS (glfw sees
      XInput pads); verify MAME's default XInput axis mapping for
      steer/gas/brake and add axis coverage to the wizard if needed.
- [ ] Keyboard remapping: wizard capture mode for KEYCODE_x bindings
      (glfw key -> MAME token table).
- [ ] UDP telemetry Phase A/B (design in RESULTS 2026-08-20 section).
- [ ] Esc in-game overlay (design standing).
- [ ] CI first-run shakeout (MAME build on runner ~1 h; expect iteration).

## Addendum 2 (2026-08-20 evening): controller/keyboard support + crash attribution

- Wizard now captures AXES (move-to-bind: steering/gas/brake as the first
  three steps) and KEYBOARD keys (press any mappable key on a button step
  -> KEYCODE binding). New wheelmap grammar: dev|btn:N, dev|axis:N:G,
  KEYBOARD|key:KEYCODE_X (legacy dev|N still parses).
- E2E-verified via simulated bindings + Lua dump: pad LSX->steering
  (:WHEEL Paddle = JOYCODE_3_XAXIS), RT/LT->gas/brake (SLIDER2/1 - these
  ports are EMPTY in stock MAME defaults, so the wizard is REQUIRED for
  pad-only installs), pad button coin, KEYCODE_ENTER start.
- PHYSICAL capture test (turn wheel / press pedal detection) needs a human:
  tonight's checklist. NOTE: the Moza idle-sleeps when unused - wake it
  before wizard runs.
- Teardown crash ATTRIBUTED with minidump stack evidence: faulting thread's
  chain includes dinput8.dll+0x22AAD (FFB plugin proxy) in msvcrt memcpy at
  exit. Cosmetic, post-game. Second dump class = call into unloaded code.
- CI v0.1.0 attempt 2 running (permissions fixed; cache missed -> full
  MAME rebuild ~50 min).
