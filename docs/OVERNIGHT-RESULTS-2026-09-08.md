# Overnight results — September 8, 2026

The Stream Deck button still opens the source checkout and its built emulator.
The changes below are available there. **The published v0.4.0 ZIP and tag remain
unchanged as the rollback baseline.** No further release was published.

## Available in the launcher

| Feature | Result |
|---|---|
| Experiments | Its own Settings submenu beside Display. Shared/game/revision contexts and saved preferences are preserved. It can now accommodate gameplay experiments. |
| Cheats | Per-game/revision imports, continuous toggles and parameter choices using MAME's engine. The downloaded archive was imported with all selections off. Timer effects were tested in all five ROM variants. One-shots/restoration scripts remain unavailable pending live activation support. |
| World 2.5 distance | Optional Off/2×/3× and independent +0/+8/+12 lookahead, matching the existing 2.4 controls. Candidate repeatability is verified; this is not a promise of eliminated pop-in. |
| Off Road distance | Optional Off/2×/3× global distance controls. The 2× candidate repeats at full emulation speed and shows modest additional detail. 3× adds no visible benefit in the sampled comparisons. |
| Exotica widescreen scenery | Optional CPU margin visibility fix that restores actual edge geometry. It preserves original submissions/resources in the matched acceptance scene. This is not increased draw distance. |

Cheats and the new per-game experiments default off. Existing personal settings
were preserved. Fresh CRT/widescreen/scale4 defaults remain intact. Shared Crack
Fill keeps its existing preference/default; Margin Fill remains retired.

Details: [Cheats and menu](reviews/2026-09-08-cheats-and-experiments.md),
[World 2.5](reviews/2026-09-08-world25-distance.md),
[Off Road](reviews/2026-09-08-offroad-native-distance.md),
[Exotica margin visibility](reviews/2026-09-08-exotica-visibility-trials.md).

## Distance findings that remain diagnostic

- **USA:** a guarded global command-line adapter now extends projection and
  scenery admission/removal together. It repeats against itself, but changes
  the original drive. It needs geometry and attended handling coverage before
  launcher promotion. [Evidence](reviews/2026-09-08-usa-global-distance.md).
- **Exotica far plane:** 2× removes actual far rejections but changes none of 15
  sampled completed images. Added objects are occluded in the matched scene;
  doubling depth range alone does not reveal them.
  [Evidence](reviews/2026-09-08-exotica-far-distance.md).
- **Exotica earlier admission:** the game adjusts a separate scenery limit from
  an emulated hardware timer. Bounded 160k trials repeat and change a few distant
  pixels at 4K, but original draw order/depth state also changes. This identifies
  a more relevant global control; it is not yet a deployable fix.
  [Evidence](reviews/2026-09-08-exotica-admission.md).

These results support continuing global work. They also show why increasing one
far-plane number is insufficient: activation, emulated work budgets, projection,
depth ordering and asset lifetime are separate constraints. No per-object
allowlists were added as the main strategy.

## Validation and deployment

- The latest deployed native build is `12e9ea6a374`; its 129-patch export exactly
  reconstructs the native tree. Source and native work are committed separately.
- All seven default driving regression cases pass on that binary, including
  actual telemetry, independent memory checks and 21 completed Exotica GL images.
- The latest 168 Python tests and all four CI jobs pass. Windows/Linux/local agree
  on all 268 source hashes. Completed capture checks select the correct physical
  monitor and reject size mismatches.
- New diagnostics distinguish CPU admission from actual GPU submissions and
  completed pixels. Explicit scene alignment preserves separate strict timing
  failures; evidence archives recompute numerical conclusions without ROMs.
- No new attended wheel/FFB or handling acceptance was collected. World force
  normalization/oscillation stays deferred. Failed geometry, timing and old-route
  comparisons are retained rather than relabeled as passes.

## Recommended next work

1. Investigate Exotica's admission-induced depth-state/order changes before a
   native adapter. Keep the host static-scenery drawing approach as the route to
   extending visibility without adding guest simulation work.
2. Record World New York to diagnose black flashes and the 3×/+12 finish crash.
   Keep the original Germany recordings intact.
3. Obtain an open-level Exotica drive and a longer Off Road drive for meaningful
   scenery comparisons. Then validate the USA global candidate with an attended
   drive before offering it in the launcher.
4. Add live cheat activation, then individually validate one-shots and rank/nitro
   effects. Current timer verification is not blanket acceptance of every entry.

The detailed queue remains in [the overnight checklist](OVERNIGHT-2026-09-08.md)
and [ROADMAP.md](../ROADMAP.md). The scheduled overnight work stops at 08:00 local;
the final checkpoint records its paused state in the session notes.
