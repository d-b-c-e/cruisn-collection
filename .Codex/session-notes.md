# Session Notes
<!-- Written by wrapup; previous history is in git. -->

- **Date:** 2026-09-08
- **Branch:** master

## What Was Done
- Published v0.4.0 at c098290aeaa1f19ca37d7bee56c747cbf51350b5; tag and downloaded ZIP verified.
- ZIP build/CruisnCollection-v0.4.0-20260908-000947.zip SHA fd292b0d4ba4d2a97147c6ffc1fb95407e3891495dfb68fada2f899e3c31ba4a.
- All117Python/4CI34189532162,7replays,5freshboots,4frozenlaunches/12GL,24GPUfixtures/3menus pass.
- Actual ZIP upgrade preserves user-state fixtures and all1637files; both exact comparisons100.0000%.
- 61derived receipts in results/proof/2026-09-08-v0.4.0-release; verify_archive.py checks bytes/identity.
- Recorded explicit maintainer sign-off with41human waivers, not fabricated PASS observations.
- Created active heartbeat cruisn-overnight-cheats-and-distance, every30minutes, morning08:00local checkpoint.
- Cheat archive preflight: nested cheat.7z has23entries for5applicableROMrevisions, all4games; runtime untested.

## Decisions Made
- Repository remains private; anonymous updater remains unavailable. Release exact ZIP, no rebuild on promotion.
- CRT on/full-wide/scale4/freeplay defaults verified; experiments remain off; personal settings untouched.
- Preserve released v0.4.0 tag/package while implementing postrelease improvements in separate commits.
- World FFB passthrough restored; no strength tuning/normalization overnight. Exotica DIP motor polarity corrected.

## Open Items
- [ ] Cheats submenu first, then Experiments beside Display, then global distance across all4games.
- [ ] Physical second-wheel/manual/soak and wider track coverage remain unperformed alpha limitations.
- [ ] World oscillation/normalization, New York black flashing and3x/+12crash remain known issues.

## Next Steps
1. Follow docs/OVERNIGHT-2026-09-08.md. Read docs/reviews/2026-09-08-cheats-preflight.md.
2. MAME cheat_manager exists in frontend/cheat.h but no local Lua binding found; reuse engine, don't invent evaluator.
3. Downloaded XMLs are in ignored build/overnight-cheat-inventory; archive C:/Users/antho/Downloads/cheat0279.zip.
4. Preserve ROM revision checks, cheat-off defaults/replay identity; keep physical force off in all automation.
5. At08:00America/Chicago Sep8 checkpoint and pause heartbeat; no additional release/visibility change authorized.

## Context for Next Session
Native E:/Source/mame-src/vunit.exe SHA b5ba0021a51a1f9ec50e105dde9c8112cb3c7e4ce71009ce4294841296383ee2,
HEAD97600e9597e on poc/quadlog, pushed fork. Stream Deck uses source launcher and this binary.
Product identity4c9dd0a3d246f9bfa1160360ad551e3af841da3ecf837200626def487d7eb30d; current evidence
results/diagnostics/release-v040-20260908. Native123-patch export is current; don't republish old rc2.
