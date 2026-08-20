# Session Notes
<!-- Handoff notes. Read these first, then CLAUDE.md, then results/RESULTS.md. -->

- **Date:** 2026-08-19 (overnight session 2 complete, user away)
- **Branch:** master (mame-src side: `poc/quadlog` @ cc0aff8c)

## Where things stand

Phase 1 remains rig-verified; the collection shell is the product entry
(deck button). **All three games verified 100.0000% bit-exact** vs MAME.
CRT pass shipped with F9 live toggle. FFB game forces fixed (MAME64.dll).
Perf crackle fixed (priority 1). Wheel high-button root cause found and
fixed at BOTH levels (winhybrid DIJoystick2 + BUTTONnn→ADDSW translation).
Wheel-setup wizard shipped in the shell (S key). Shell has music/blips and
returns 0.6 s after game exit. Overlay cursor/click fixed; fullscreen now
enforced for the window's lifetime (crusnwld's mode-change resize).

## Morning checklist (user, at the wheel)

1. **Deck button → shell**: music + blips; navigate (wheel hat works too).
2. **S → WHEEL SETUP**: press wheel/shifter buttons for COIN, START,
   VIEW1-3, RADIO, GEAR1-4 (Esc skips a step, Backspace cancels). Then
   launch a game and test every bound button. This exercises the whole
   new input chain (winhybrid DIJoystick2 + ADDSW translation + wizard).
3. **FFB**: real game forces should now fire (collisions, road) — the
   plugin logs `RunningFFB = RacingFullValueActive2` when active.
4. **Cruis'n World**: should now hold fullscreen; cursor should vanish
   over the game; clicking should refocus (no beep). Re-judge "emulation
   quality" at full speed — it is bit-exact vs MAME; the dark dithered
   rectangles are MAME's own output (research: no matching bug report;
   MT 01798 = known green-neutral-gear artifact, minor, open since 2008).
5. F9 CRT A/B taste check still open from yesterday.

## Open Items

- [ ] Physical wheel test of wizard bindings + FFB (above).
- [ ] **Esc in-game settings overlay** (wanszai parity) — designed, not
      built: GL-thread menu drawn in the overlay, polled via
      GetAsyncKeyState (rawinput ignores injection; physical Esc IS
      pollable), Exit = WM_CLOSE to owner, CRT/FFB toggles as items.
      MAME's Tab menu remains the deep-settings path meanwhile.
- [ ] C++ overlay HEIGHT=400 vs offroadc's 401-line mode (last line not
      presented; cosmetic).
- [ ] Margin pop-in class: floating parked geometry at margin edges
      (crusnwld left edge); sky black-bars where 3D sky runs out
      (scene-dependent). Possible heuristics later; documented.
- [ ] Mid-game EIP=0 crash singleton (8:46pm 08-19) — unexplained; WER
      minidumps now land in rig/crashdumps/ for attribution.
- [ ] Plugin teardown AV at exit (cosmetic, post-exit; masked by instant
      shell return). Analyze first minidump eventually.
- [ ] Multi-hour soak + margin sweep (unchanged).
- [ ] Zeus scoping capture for Exotica (stretch, unchanged).

## Next Steps

1. Ingest morning wheel-test results (wizard, FFB, World re-judgment).
2. Esc in-game overlay implementation.
3. Shell settings page (scale/aspect/FFB strength — wanszai settings.ini
   is the model, see RESULTS teardown notes).
4. Consider upstreaming the winhybrid DIJoystick2 fix (benefits vanilla
   MAME users with >32-button wheels).

## Context for Next Session

All committed: cruisn-poc master, mame-src poc/quadlog @ cc0aff8c (patch
series exported), Launchbox-Racing (bat → shell). The Lua input-dump
harness pattern (dump joystick items + resolved seqs) lives in RESULTS —
recreate from there if needed; it is the fastest way to verify binding
questions without touching the wheel.
