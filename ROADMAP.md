# Cruis'n Collection — Roadmap

Current work and acceptance criteria, with relevant legacy IDs retained.
Detail lives in `results/RESULTS.md` (chronology) and `.Codex/session-notes.md`
(handoff). Update status here as items move.

## Current priorities (2026-09-08, after v0.4.0)

v0.4.0 is published, with its exact ZIP verified after download and release evidence
archived in results/proof/2026-09-08-v0.4.0-release. The ordered, actionable queue
is below. The [overnight checklist](docs/OVERNIGHT-2026-09-08.md) is a completed
historical work order; its automation remains paused. Public access preparation
now also follows [PUBLIC-READINESS.md](docs/PUBLIC-READINESS.md):

1. **Cheats submenu: initial implementation complete.** Continuous imported
   toggles/choices, default-off selections and replay state work across the four
   games. Five timer probes/replays and a frozen activation pass. Live one-shots,
   code-restoring actions and individual rank/nitro validation remain follow-up.
2. **Experiments beside Display: complete.** Contexts, preferences and exclusions
   are preserved; Back returns to Settings. See [overnight evidence](docs/reviews/2026-09-08-cheats-and-experiments.md).
3. **IN PROGRESS: Global draw-distance experiments for all four games**, prioritizing earlier
   visible mountains/trees and diagnosing activation, residency and draw limits.
   The [capability matrix](docs/reviews/2026-09-08-distance-capabilities.md) now has
   guarded gameplay measurements for all five revisions. The optional World2.5
   adapter is implemented and 2x repeats (see [evidence](docs/reviews/2026-09-08-world25-distance.md));
   USA now has [global CLI trials](docs/reviews/2026-09-08-usa-global-distance.md) with
   a repeatable2x candidate, but substantial original-route divergence and no
   launcher promotion yet. [Off Road native 2×/3×](docs/reviews/2026-09-08-offroad-native-distance.md)
   now runs at full speed with a default-off Experiments control. 2× repeats6000
   frames and13 completed3824×2073 captures; 3× adds no detail in42 small-window
   samples. The strict geometry check still finds one changed original quad.
   [Exotica's full trials](docs/reviews/2026-09-08-exotica-visibility-trials.md) now
   include a native optional Widescreen Scenery menu item, unchanged far plane,
   matched geometry/resources and6000-frame/35GL candidate repeats. Projection
   remains diagnostic. [True far trials](docs/reviews/2026-09-08-exotica-far-distance.md)
   admit3035 more spheres but change none of15 completed GL samples. A matched
   scene's extra199 quads are occluded even with a doubled depth range; no new
   far menu is promoted. The [earlier adaptive admission control](docs/reviews/2026-09-08-exotica-admission.md)
   is now verified: bounded160k trials repeat and change a few distant pixels,
   but strict state/order checks fail. Isolate depth bias/order effects before
   native promotion; the host static-scenery path remains the longer-term target.
   World New York black flashing and the 3x/+12 crash need further investigation.
   The newer [World host-rendering prototype](docs/reviews/2026-09-08-world-host-scenery.md)
   now draws pending static scenery without changing guest simulation. Full Germany
   inputs/camera/ADC remain identical; 2× adds visible distant terrain/buildings/trees
   and repeats 31 completed images on the 4K monitor. Its 61-scene geometry oracle
   reproduces 13,215 polygons while original DMA/VRAM/texture/palette captures stay
   identical. This is CLI-only; correct occlusion and future-section residency
   remain acceptance work. No first-class cross-game or zero-pop-in claim yet.
4. Broaden attended drives, shifter and second-wheel coverage. World oscillation
   and cross-game force normalization remain known issues, with tuning deferred.

Current automated suite has seven cases, including completed Exotica GL frames.
All games now have guarded gear/rev telemetry with estimated RPM; World speed
still uses OCR. Fresh free-play seeds are corrected, including Off Road's checksum.
The [overnight results](docs/OVERNIGHT-RESULTS-2026-09-08.md) distinguish source-launcher
features from diagnostic-only trials. The older milestone tables remain available
in [the preserved September 8 checkpoint](https://github.com/d-b-c-e/cruisn-collection/blob/fde07bdf8276f6c6ab21803207894cb999d4e052/ROADMAP.md).
They include superseded assumptions and should not be used as current instructions.
Relevant legacy IDs are retained below.

## Next work and acceptance

| ID | Work | Next concrete step | Acceptance needed |
|---|---|---|---|
| C2 / A3 | Global host scenery | Extend the verified World pending-object renderer to PC-owned future sections, then add USA, Off Road and Zeus adapters. Keep layout/codec checks separate from shared math and acceptance. | Original inputs/camera/ADC and guest DMA/resources unchanged; visible benefit, correct occlusion/handover, repeatability, performance and attended cross-track coverage. |
| C2 | Exotica admission | Trace render-register `0x15`: all 814 matched bias changes are 2047 → 0. Isolate state/order changes before native admission support. | Preserve original submissions/resources and repeat the candidate; additional admissions are not proof of visible scenery. |
| C2 | USA global distance | Examine geometry and simulation differences in the repeatable CLI candidate before exposing it in the launcher. | Full candidate replay, scene/resource comparisons and an attended drive. |
| C2 | World / Off Road distance | Broaden coverage beyond the current routes; determine whether activation or residency, rather than far clipping, limits additional benefit. | Matched completed images, timing and fresh drives; do not count extra admissions alone. |
| C3 | World New York artifacts/crash | Obtain a recorded race reproducing black flashes and, if reproducible, the 3×/+12 finish crash. Preserve the default/2× control. | Diagnose the first bad submission or guest instruction; retain the original failing recording. |
| B8 | Complete Cheats | Add live activation before enabling one-shots and code-restoring actions. Validate rank/nitro and parameter effects individually. | Exact-revision on/off behavior, correct restoration, recording fidelity and default-off regression controls. |
| A3 | World future-section decoder | Placement/yaw match 180 objects (two distinct angles). Broaden angle/offset coverage, reconstruct palette/texture bindings, then decode eligible definitions outside guest RAM. Split host preparation/logging/submission timings and test without per-quad CSV logging. | Correct XYZ/orientation/materials, no dynamic/physics initialization, no per-model/level allowlist, smooth presentation and transfer to ordinary guest drawing. |
| B1 | Speed telemetry | Replace World's remaining OCR only after finding and guarding a real producer; retain validity/lifetime checks. | Actual outgoing packets versus independent memory/HUD evidence in both revisions. |
| B2 | Gear / estimated RPM coverage | Existing guarded gear/rev producers work across all four games. Broaden automatic/manual drives and higher-gear Off Road/Exotica coverage. | Real gauges/SimHub/Buttkicker plus independent traces; RPM remains an estimate from the game's rev signal. Never use E632. |
| B4 | Force normalization and impacts | **Deferred by maintainer.** Preserve World passthrough and existing Exotica polarity/trim. Prepare per-device measurements for a later attended tuning session. | Comparable steering weight, distinguishable impacts, correct centering and no sustained oscillation across games/wheels. |
| B7 / G7 | Shifter coverage | Verify H-pattern and paddles with current bindings in every game. World 2.5 is automatic-only; use 2.4 for manual acceptance. | Gear engagement, neutral/downshift, one action per press, persistence and reconnect. |
| F2 | Next release baseline | Freeze a new candidate only when requested; renew all automated gates and explicitly record attended acceptance or maintainer waivers. | Exact ZIP promotion, clean install/upgrade, default CRT/widescreen/scale4/free play, seven driving regressions and wheel checks. |

## Testing and reusable infrastructure

- Run `python harness/local_checks.py` locally; hosted GitHub workflows are disabled.
  Release gates require the complete Windows report through `--checks`. Preserve
  source-bound evidence. Ordinary launch and replay are separate paths: test both.
- The September 8 normal-launch `env` regression is fixed and covered at the
  process boundary; source launchers need reopening after the update.

- Keep original human recordings immutable. Freeze inputs, starting state,
  effective options, cheats and source/native identity for every derived case.
- Keep original-route fidelity, candidate repeatability, actual ADC timing,
  completed GL pixels, resource/geometry order and performance as distinct results.
  A scene-aligned comparison cannot erase a strict frame mismatch.
- Extend completed-capture coverage with World New York, an open Exotica course
  and a longer Off Road drive. The current synthetic routes do not cover every
  track or establish attended handling acceptance.
- Continue archiving numerical traces with standalone recomputation. Mark GPU,
  raw-resource and attended results as receipts when their inputs are not included.
- Keep native adapters revision-guarded and default-off; share projection/math,
  force conditioning and diagnostic contracts without sharing unverified addresses.
- Carry reusable wheel/telemetry improvements through the pinned
  `dbce-wheel-mod-toolkit` workflow and consumer checks. Avoid divergent copies of
  shared conditioning code. [Toolkit review](https://github.com/d-b-c-e/dbce-wheel-mod-toolkit/blob/master/docs/REVIEW-2026-09-05.md).
- For broader portability, pursue the host scenery milestone before committing
  to a partial native port. [Architecture and research](docs/reviews/2026-09-06-global-distance-and-native-port.md).

## Attended checks and secondary backlog

| ID | Remaining work | Current constraint |
|---|---|---|
| D2 | Gamepad, sparse-axis and second-wheel coverage | Needs actual hardware input, rebind/reconnect and physical-force acceptance. Fanatec remains valuable. |
| B3 | Volume consistency / remaining USA operator-volume mapping | Recheck in live gameplay and preserve calibrated NVRAM. Off Road **does** checksum settings; use `cmos_settings.py`, never lone-byte edits. |
| G3 | Exotica car-selection text | Reassess against current upstream Zeus2 work and a matched capture; old claims of no upstream fix are dated findings. |
| G6 | Menu/capture and input-arming reports | Reproduce with current source and mode-transition evidence before changing behavior. Existing menu diagnostics do not certify every physical input path. |
| D3 | Intermittent host crash reports | Keep WER/minidumps and source identity; distinguish these from World's confirmed guest-fatal instruction. |
| D4 / D5 | Upstream compatibility and contributions | Review the identified later Zeus2 changes separately, retain control captures, and consider upstreaming general input/driver fixes. |
| E1 | Achievements | Optional future work; no supported RetroAchievements path is established. Do not make it a release requirement. |

## Fixed baseline and limits

- **v0.4.0 is published and preserved.** Overnight source features are newer than
  that package. Public access is being prepared; another release or visibility
  change still needs an explicit request after that preparation.
- **Experiments is beside Display**, retaining Shared/game/revision contexts.
  Cheats are per game/revision and start off. New distance/scenery trials start off.
- Fresh installs retain CRT on, full widescreen, scale4, free play and World2.4.
  Personal saved choices are preserved; a default is not an instruction to reset them.
- Broad **Margin Fill is retired** after smearing gameplay sky textures. Shared
  Crack Fill remains optional with its existing default. Prefer real missing
  geometry and sampling corrections over a new broad blur/fill workaround.
- FFB uses the built-in SDL path and toolkit conditioning. Historical FFBPlugin,
  global direction compensation and World menu-force gate instructions are obsolete.
  Physical FFB never runs unattended.
- See [RELEASE-CHECKLIST.md](docs/RELEASE-CHECKLIST.md) for the full release protocol,
  and [RESULTS.md](results/RESULTS.md) for dated engineering evidence.
