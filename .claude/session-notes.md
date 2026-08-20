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
