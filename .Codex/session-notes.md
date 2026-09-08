# Session Notes
<!-- Written by wrapup; previous history is in git. -->

- **Date:** 2026-09-08
- **Branch:** master

## What Was Done
- Overnight02:40: World2.5 global Off/2x/3x +0/8/12 adapter/menu in117e8fb; native dae2569f793 built/pushed.
- Sourcevunit SHA f06a160b57c72737e89aedcc159f87cbe173c82620722ea109e84dcdffe70252;125patch exacttree2f4f89c388ba380aa578036143049a723dcad00c.
- All7defaultcases actualtelemetry/memory/Worldpassthrough/Exo21GL pass; existingWorld2.4global2x8783/146 passes.
- World25 original/2x+8/3x+8 full6000 trials complete at~100%; extended trials change original route (retainedFAIL).
- Separate2xcase repeats6000/100native/11GL. 2xvs3x match100native+42GL but33camera samples/ADCtimes differ.
- 132tests/all4CI34199270158; local/Linux/Windows all229sourcehashes match identity85ad5a17558ffc18d7f3d8eac431151e6c7582ba6359bd3b8ad3392e573ee152.
- 67file ROM-free proof archived under results/proof/2026-09-08-world25-distance, counters recompute.
- USA residency b720b98 read-onlyprobe matches4305;22713 pending visits within2x75k, max117026.
- Overnight02:05: all5revision distance capability matrix now measured. Native44c3494d6af unchanged.
- Four4305frame V-Unit probes pass; Exotica6000/21GL passes with identical distance trace to headless.
- 131tests pass;35file ROM-free proof recomputes counters. See docs/reviews/2026-09-08-distance-capabilities.md.
- Overnight01:40: Cheats menu + top-level Experiments implemented/pushed in separate commits.
- Native44c3494d6af bridge uses MAME engine; built eb2db42a90288bf37ac0dcce9b9ce2106c136fad198c52320ee2b3af3c435a97.
- Full124patch export tree f7af3475d0ce0b6347e2be669338283437a81447 verified; source Stream Deck uses new native.
- 128Python/4CI34195061384 pass; seven default binary controls pass (six initial + Exotica4K rerun).
- Fixed Zeus monitor selection for exact replay: secondary1080p mismatched4Kreferences. All21GL now match.
- Five4000frame cheat-on replays against final binary and five real timer on/off memory probes pass.
- Frozen devZIP f8a804f passes9pages/4defaultboots+1Worldcheatboot/15GL/import/setup/support,1649files.
- 75derivedfiles archived in results/proof/2026-09-08-cheats-and-experiments; ROM-free verifier passes.
- Published v0.4.0 at c098290aeaa1f19ca37d7bee56c747cbf51350b5; tag and downloaded ZIP verified.
- ZIP build/CruisnCollection-v0.4.0-20260908-000947.zip SHA fd292b0d4ba4d2a97147c6ffc1fb95407e3891495dfb68fada2f899e3c31ba4a.
- All117Python/4CI34189532162,7replays,5freshboots,4frozenlaunches/12GL,24GPUfixtures/3menus pass.
- Actual ZIP upgrade preserves user-state fixtures and all1637files; both exact comparisons100.0000%.
- 61derived receipts in results/proof/2026-09-08-v0.4.0-release; verify_archive.py checks bytes/identity.
- Recorded explicit maintainer sign-off with41human waivers, not fabricated PASS observations.
- Created active heartbeat cruisn-overnight-cheats-and-distance, every30minutes, morning08:00local checkpoint.
- User archive now imported into rig/cheats; all selections remain OFF. Continuous toggles/choices supported.

## Decisions Made
- Repository remains private; anonymous updater remains unavailable. Release exact ZIP, no rebuild on promotion.
- CRT on/full-wide/scale4/freeplay defaults verified; experiments remain off; personal settings untouched.
- Preserve released v0.4.0 tag/package while implementing postrelease improvements in separate commits.
- World FFB passthrough restored; no strength tuning/normalization overnight. Exotica DIP motor polarity corrected.

## Open Items
- [x] Initial Cheats submenu and top-level Experiments. See docs/reviews/2026-09-08-cheats-and-experiments.md.
- [x] Global distance capability matrix across all4games, including World2.4/2.5; no native changes yet.
- [x] Guarded World2.5 global adapter, optional/defaultOFF; no attended/geometry/order acceptance yet.
- [ ] NEXT USA75k admission/80k removal plus virtual projection. Read docs/reviews/2026-09-08-distance-next-adapters.md:
      include277/278 clamp +27C/27F dynamic reads;823E/8240+A727 require attribution.
      OffRoadfloat47296/ROMtable (tail resembles504/(index+1), unverified) and Exotica CPUfrustum/activation
      require their own paths. No per-model allowlists. All code clean/pushed; no game process at02:40.
- [ ] Live cheat activation for one-shot/code-restoring actions; individual rank/nitro/custom-choice validation.
- [ ] Physical second-wheel/manual/soak and wider track coverage remain unperformed alpha limitations.
- [ ] World oscillation/normalization, New York black flashing and3x/+12crash remain known issues.

## Next Steps
1. Follow section3 of docs/OVERNIGHT-2026-09-08.md. Cheats initial milestone and Experiments move are done.
2. Start cross-game distance capability mapping; reuse verified global architecture, never World addresses blindly.
3. Downloaded XMLs are in ignored build/overnight-cheat-inventory; archive C:/Users/antho/Downloads/cheat0279.zip.
4. Preserve ROM revision checks, cheat-off defaults/replay identity; keep physical force off in all automation.
5. At08:00America/Chicago Sep8 checkpoint and pause heartbeat; no additional release/visibility change authorized.

## Context for Next Session
Native E:/Source/mame-src/vunit.exe SHA eb2db42a90288bf37ac0dcce9b9ce2106c136fad198c52320ee2b3af3c435a97,
HEAD44c3494d6af on poc/quadlog, pushed fork. Stream Deck uses source launcher and this binary.
Collection commits eea6ef5/e6154e1/f8a804f/1baa99a separate Cheats/menu/frozen-checks/display-targeting.
Current proof manifest records final source identity and component scopes. Local devZIP
build/CruisnCollection-dev-20260908-012408.zip SHA f7a5a641affe81d7e44102d86cc9a6fa19411820a8b9d76607a99e7d08ecfdf5.
It is built at f8a804f, before diagnostic-only1baa99a; no further release published.
The initial all7aggregate FAIL is retained; Exotica4K rerun restores exact21GL. No shader/force change.
All helpers/games completed. Personal settings/calibration unchanged; imported cheats defaultOFF.
