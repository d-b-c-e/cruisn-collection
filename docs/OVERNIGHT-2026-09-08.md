# Post-release overnight queue — 2026-09-08

Authorized by the maintainer after requesting the v0.4.0 release. Finish and
verify publication first. Preserve that tag and exact package as the rollback
baseline. Work in separate commits; do not publish another release overnight.

Release is now published and verified at tag v0.4.0 / c098290. Heartbeat
`cruisn-overnight-cheats-and-distance` is active every 30 minutes, with the 08:00
local checkpoint below. [Cheat preflight](reviews/2026-09-08-cheats-preflight.md)
found 23 entries across the five applicable ROM revisions; none is runtime-validated
yet. [Upstream inspection](reviews/2026-09-08-release-upstream-check.md) identifies
a later Zeus2 change for separate post-release compatibility study.

## 1. Cheats submenu

- [ ] Inspect the user's downloaded cheat archive in Downloads and MAME's existing
  cheat manager/Lua interface. Check primary documentation and source. Inventory
  entries for all four games and World revisions without guessing compatibility.
- [ ] Add a per-game Cheats submenu using the existing cheat runtime where possible.
  Support named toggles/choices, reset to off and clear unsupported/empty states.
  Do not duplicate the MAME expression interpreter or silently apply another ROM's
  addresses. User-imported cheat files are preferable to unreviewed bundled data.
- [ ] Keep cheats off by default and record effective cheat state in replay and
  support diagnostics. Determinism checks must reject mismatched cheat settings.
- [ ] Verify import/filtering, revision matching, menu navigation/persistence and
  real runtime on/off effects using isolated no-force runs. Check default-off
  replay compatibility across all four games. Archive evidence and limitations.

## 2. Top-level Experiments

- [ ] Move Experiments beside Display in Settings, with Back returning to Settings.
  Rename the page so it can include gameplay as well as rendering experiments.
- [ ] Preserve Shared / USA / World / Off Road / Exotica contexts, supported-revision
  filtering, existing preference keys, default values and option exclusions.
- [ ] Update screenshots, documentation, frozen-menu checks and focused navigation
  tests. No graphics or force tuning as a side effect of reorganizing the menu.

## 3. Global draw-distance experiments across all four games

- [ ] Create a capability/evidence matrix for USA, World, Off Road and Exotica:
  far clipping, reciprocal projection limits, scene activation/streaming, LOD,
  texture residency and draw budget. Keep verified facts separate from hypotheses.
- [ ] Reuse the World global experiment architecture for verified V-Unit layouts
  where evidence supports it. Guard instructions, revisions, ranges and option
  composition. Do not copy World addresses into other games. Exotica needs its own
  Zeus/game analysis; add bounded emulator diagnostics before proposing changes.
- [ ] Prefer global admission/activation or host scenery drawing over growing
  lists of individual models or levels. Investigate distant mountains/trees and
  World's New York black flashing/3x+12 finish crash using retained diagnostics.
- [ ] For each viable change, preserve baseline recordings and run stock/disabled
  control, candidate replay against itself, completed GL comparisons, geometry/
  texture/order checks and timing measurements. FFB stays off; telemetry loopback
  is private. Extra admitted polygons alone are not proof of earlier visible scenery.
- [ ] Keep successful trials optional and default-off. Record unsupported games
  honestly. Request fresh attended drives only where additional route/handling
  acceptance is needed; lack of a human drive need not stop independent diagnostics.

## Completion and limits

Update this checklist, ROADMAP.md and the engineering log after each milestone.
Commit collection/native changes separately, refresh the exported native patch
series, build and verify the source used by Stream Deck after native changes.
Preserve personal rig settings and original recordings. Do not test physical force
or tune World FFB unattended. If a task needs user input, document the exact gap
and move to another independent queued item. Stop overnight work by 08:00 local
on September 8 or when the maintainer returns with different instructions.
