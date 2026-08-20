# Session Notes
<!-- Handoff notes. Read these first, then CLAUDE.md, then results/RESULTS.md. -->

- **Date:** 2026-08-19 (overnight session, user away)
- **Branch:** master (mame-src side: `poc/quadlog` @ b565ee3e)

## What Was Done (2026-08-18 day → 2026-08-19 overnight)

1. **Wheel test PASSED** (user-confirmed): coin/Start/Esc/steering/FFB
   through the Stream Deck button, fullscreen. Along the way: `output
   windows` staging gap fixed, borderless-fullscreen + focus enforcement
   added to run_rig, ctrlr sanitizer (BUTTON33+ tokens killed keyboard
   Start), FFB-hang auto-retry, bat start /min.
2. **CRT pass shipped** (user-prioritized): mask+scanlines+curvature in
   PAL_FS, uCrt-gated; MIDV_GL_CRT=1 at boot, F9 live toggle; exact mode
   re-verified 100.0000%. In-process verified via MIDV_GL_SNAP 1:1 crops.
3. **Collection shell shipped**: harness/collection.py fullscreen menu
   (3 games, LaunchBox art, C=CRT toggle, config rig/collection.ini,
   --shot test mode); run_rig refactored importable; deck button now opens
   the shell. E2E machine-verified round trip shell→game→shell.
4. **MIDV_SKIP_STARTUP_SCREENS** added to frontend ui.cpp (first non-driver
   patch; env-gated): BAD_DUMP warning screens refuse skip_warnings by
   design and blocked crusnwld boots; injected keys can't dismiss (rawinput).
5. **offroadc runs full 3D attract through the renderer** — first ever run,
   zero changes. crusnwld boots to its one-time CALIBRATE CONTROLS screen.

## Decisions Made

- CRT look: "full fat" (mask + scanlines + curvature), two-phase
  magenta/green mask (RGB triads = moiré), tuning constants in PAL_FS.
- Launcher: fullscreen shell is the product entry; deck button opens it.
- JOYCODE high-button root cause stays deferred to the mapping frontend.
- Probe lore: GDI captures show GL content black; downscaled previews hide
  scanlines/mask (judge at 1:1); injected keys never reach MAME input.

## Evening session results (2026-08-19, user at rig)

- FFB game forces FIXED: MAME64.dll (MAME output client) was missing beside
  vunit.exe — RomName/RunningFFB now latch. User to re-feel.
- Audio crackle FIXED: `priority 1` in rig mame.ini (ambient load had MAME
  at 94-97%; now 99.8%+). User confirmed "improved".
- Crash triage: GL thread exonerated (headless repro without it) + hardened
  with machine-exit notifier; residual post-exit AV = plugin teardown,
  cosmetic; WER minidumps armed → rig/crashdumps/. One mid-game EIP=0
  crash (8:46pm) unexplained singleton — watch.
- **crusnwld renderer VERIFIED 100.0000% bit-exact** (frame-3400 attract,
  61 MB quads). "Bad emulation" was the perf underrun, not emulation.
  fixtures/nvram-crusnwld added (rig-config captures only: headless runs
  re-demand calibration — no devices). run_capture.py takes a rom arg now.

## Open Items (user first)

- [ ] **Rig pass on the night's work**: deck button → shell → each game;
      F9 A/B the CRT look (tuning knobs in gpu/renderer.py PAL_FS: mask
      0.62, gain 1.42, beam 0.35/0.65, warp 0.041/0.052 — regen header +
      rebuild after edits); C in shell persists CRT choice.
- [ ] **crusnwld one-time calibration** at the rig (CALIBRATE CONTROLS,
      TEST=F2), persists in rig/nvram. Consider snapshotting a
      fixtures/nvram-crusnwld afterward for cleanroom boots.
- [ ] offroadc FFB feel — plugin runs the Cruis'n GameId=22 tuning; may
      deserve its own FFBPlugin profile.
- [ ] Oracle verification passes for crusnwld/offroadc (needs their NVRAM
      fixtures + capture runs; harness unchanged).
- [ ] Shell polish backlog: per-card "needs calibration" badge, settings
      page (scale/aspect), attract-video cards, wheel-mapping frontend
      (absorbs deferred JOYCODE work).
- [ ] 16:9 margin pop-in sweep + multi-hour soak (unchanged from before).

## Next Steps

1. Ingest the user's morning rig feedback (CRT taste + shell feel).
2. crusnwld/offroadc NVRAM fixtures + oracle passes.
3. Shell settings page / mapping frontend.

## Context for Next Session

Everything committed: cruisn-poc (master), mame-src (`poc/quadlog`,
b565ee3e, patch series exported), Launchbox-Racing (bat → shell). Proofs in
results/proof/2026-08-19-*.png. The rig config the user verified by hand is
unchanged except: vunit.exe rebuilt (CRT + startup-skip, both env-gated
default-off), launcher entry is now the shell.
