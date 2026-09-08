# Post-release overnight queue — 2026-09-08

Authorized by the maintainer after requesting the v0.4.0 release. Finish and
verify publication first. Preserve that tag and exact package as the rollback
baseline. Work in separate commits; do not publish another release overnight.

Release is now published and verified at tag v0.4.0 / c098290. Heartbeat
`cruisn-overnight-cheats-and-distance` is active every 30 minutes, with the 08:00
local checkpoint below. [Cheat preflight](reviews/2026-09-08-cheats-preflight.md)
found 23 entries across the five applicable ROM revisions. The initial Cheats menu
and top-level Experiments are now implemented and verified; see
[the 01:40 checkpoint](reviews/2026-09-08-cheats-and-experiments.md).
Five timer on/off probes and cheat-enabled replays pass. Live one-shots and
code-restoring actions remain unavailable; rank/nitro effects need individual
validation. [Upstream inspection](reviews/2026-09-08-release-upstream-check.md) identifies
a later Zeus2 change for separate post-release compatibility study.

## 1. Cheats submenu

- [x] Inspect the user's downloaded cheat archive in Downloads and MAME's existing
  cheat manager/Lua interface. Check primary documentation and source. Inventory
  entries for all four games and World revisions without guessing compatibility.
- [x] Add a per-game Cheats submenu using the existing cheat runtime where possible.
  Support named toggles/choices, reset to off and clear unsupported/empty states.
  Do not duplicate the MAME expression interpreter or silently apply another ROM's
  addresses. User-imported cheat files are preferable to unreviewed bundled data.
- [x] Keep cheats off by default and record effective cheat state in replay and
  support diagnostics. Determinism checks must reject mismatched cheat settings.
- [x] Verify import/filtering, revision matching, menu navigation/persistence and
  real runtime on/off effects using isolated no-force runs. Check default-off
  replay compatibility across all four games. Archive evidence and limitations.

## 2. Top-level Experiments

- [x] Move Experiments beside Display in Settings, with Back returning to Settings.
  Rename the page so it can include gameplay as well as rendering experiments.
- [x] Preserve Shared / USA / World / Off Road / Exotica contexts, supported-revision
  filtering, existing preference keys, default values and option exclusions.
- [x] Update screenshots, documentation, frozen-menu checks and focused navigation
  tests. No graphics or force tuning as a side effect of reorganizing the menu.

## 3. Global draw-distance experiments across all four games

- [x] Create a capability/evidence matrix for USA, World, Off Road and Exotica:
  far clipping, reciprocal projection limits, scene activation/streaming, LOD,
  texture residency and draw budget. Keep verified facts separate from hypotheses.
  Baseline: [five-revision gameplay evidence](reviews/2026-09-08-distance-capabilities.md);
  actual far rejects differ substantially, so adapters must remain game-specific.
- [ ] Reuse the World global experiment architecture for verified V-Unit layouts
  where evidence supports it. Guard instructions, revisions, ranges and option
  composition. Do not copy World addresses into other games. Exotica needs its own
  Zeus/game analysis; add bounded emulator diagnostics before proposing changes.
  World2.5 adapter is implemented in117e8fb/native dae2569; original control and
  2x candidate repeatability pass. See [adapter evidence](reviews/2026-09-08-world25-distance.md).
  USA global CLI adapter is built in native8b151aa9/collection9e70f6a;
  [five full controls and2x repeatability](reviews/2026-09-08-usa-global-distance.md)
  expose route changes, with launcher/geometry/attended acceptance still open.
  [Off Road coherent2x/3x trials](reviews/2026-09-08-offroad-global-distance.md) now
  complete with equal camera paths and modest visible gain; instrumentation cost,
  full repeatability and attended coverage remain open. [Exotica's completed matrix](reviews/2026-09-08-exotica-visibility-trials.md)
  now supports a native optional Widescreen Scenery menu item. Margins/both each
  repeat6000 frames/35 completed GL; projection remains diagnostic, far plane
  unchanged. Later actual far rejects at4686…5986 provide the next distance target.
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

Next autonomous steps: move Off Road's coherent whole-scene trial into a guarded
native adapter and measure real cost/repeatability; inspect Exotica's later far
rejects and test a coherent far-plane/reciprocal extension. Keep scene activation,
resource residency, completed pixels and changes to gameplay history distinct.

## Completion and limits

Update this checklist, ROADMAP.md and the engineering log after each milestone.
Commit collection/native changes separately, refresh the exported native patch
series, build and verify the source used by Stream Deck after native changes.
Preserve personal rig settings and original recordings. Do not test physical force
or tune World FFB unattended. If a task needs user input, document the exact gap
and move to another independent queued item. Stop overnight work by 08:00 local
on September 8 or when the maintainer returns with different instructions.
