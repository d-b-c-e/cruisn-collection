# Cruis'n Collection — Roadmap

Current work and acceptance criteria, with relevant legacy IDs retained.
Detail lives in `results/RESULTS.md` (chronology) and `.Codex/session-notes.md`
(handoff). Update status here as items move.

## Current priorities (2026-09-10, after v0.5.0)

v0.5.0 is published, downloaded and hash-verified, with Stream Deck deployed and
evidence in results/proof/2026-09-08-v0.5.0-release. v0.4.0 remains the rollback release.
The ordered, actionable queue
is below. The [September 9 queue](docs/OVERNIGHT-2026-09-09.md) is ACTIVE again
by explicit maintainer direction, without the expired morning cutoff. [Results and remaining work](docs/OVERNIGHT-RESULTS-2026-09-09.md)
distinguish World's visible 3x gains from unfinished cross-game parity. Retire older
experiments only where successfully replaced. The September
8 queue is historical. The repository is now public; remaining preparation is
tracked in [PUBLIC-READINESS.md](docs/PUBLIC-READINESS.md):

The heartbeat now uses a one-minute recovery wakeup, not a work cadence. During active
turns, continue directly into the next useful implementation or verification step.

The maintainer requested broader track coverage. [Recording presets and the
track checklist](docs/SCENERY-TRACK-COVERAGE.md) are ready for full Off Road El Paso
and Exotica drives, followed by contrasting courses. The maintainer selected Amazon
for its known bugs. Its 8,860-frame recording reaches the finish. Two archived-binary
replays preserve inputs, camera and actual ADC timing; 58/59 completed 4K images
repeat. The original frame3600 sky/material failure is retained; the new
[palette lifetime candidate](docs/reviews/2026-09-09-zeus-palette-lifetime.md)
reproduces and corrects it, restoring the original good4K image exactly. Both
dense windows repeat all49+21 guarded images while preserving original motion
and resources. The [marked-window CPU analysis and page-clear trial](docs/reviews/2026-09-09-amazon-margin-depth.md)
separate missing submitted ground from stale margin depth: most35/45s black
wedges lack geometry, while the1:12 checkpoint rectangle persists on alternating
pages after its model disappears. The native legacy/page/repeat validation
passes: all31 page-cleared images repeat and
the old rectangle is removed, but it exposes an uncovered sky strip. The separate
[panorama continuation candidate](docs/reviews/2026-09-10-zeus-panorama.md)
copies structurally verified original tiles into that strip at unchanged scale;
all31 dense real4K images repeat with original motion/resources/fullCPU exact.
Two fullAmazon8860 drives repeat all117GL/fullmotion; enabledHongKong preserves
all21GL and originals. All7 defaults pass on final2b55/SHAe0ba. The first full
repeat's consumer timeout8460 remains an unmeasured failure. Later instrumented
replays directly identify screenshot file I/O as another timeout cause. The
[checked background writer and explicit offline pacing](docs/reviews/2026-09-10-async-captures.md)
now preserve all49 dense V-Unit BMPs, two21-image Hong Kong runs and the full
117-image Amazon drive, including original motion/resources. Real menu/action
replays pass in both renderers; all seven defaults pass on finalb3d82b/SHAe7780a7a,
including actual UDP/memory telemetry and four software force checks. The
[capture proof](results/proof/2026-09-10-capture-writer/README.md) verifies42
hash-bound receipts. Personal Stream Deck remains on v0.5.0/SHA87d04de4.
Ordinary capture stays nonblocking; explicit offline pacing reports bounded
storage waits instead of silently losing frames. The separate odd-width packing
fix also passes guarded real-OpenGL fixtures. Hong Kong's unsupported
panorama is left alone; broader coverage remains open. The
[future-model/fade study](docs/reviews/2026-09-10-exotica-future-materials.md)
finds970model buffers already present and unchanged across later snapshots,
401later actual submissions matching earlier bytes, and a time-based fade ramp.
A standalone native fade step matches489 actual original updates/17 completions.
Live resource ownership and fade handover still require implementation. The next
source/geometry capture targets Hong Kong5000: the earlier3500 future candidates
are all outside the view, while approximate5000 centers increase359 to775 at2x.
These counts are not rendering acceptance. The [three-viewpoint scene-layer study](docs/reviews/2026-09-10-exotica-scene-layers.md)
now matches original routes,55 real4K images and three resource snapshots. A
separate D32F prototype solves tested far-depth ordering, but foreground hides
almost all extra geometry in Hong Kong5000. Amazon5072 adds visible forest in
the offline composition. Future-only drawing leaves the black left ground wedge;
adding earlier unsubmitted sources covers the measured patch, with surface
correctness and motion still unverified. All three
viewpoints show no third-band gain. Earlier unsubmitted section sources need
separate eligibility and handover checks. Broader Amazon captures also exposed
an angle-rounding bug in the evidence verifier: its corrected arithmetic matches
all2376 ordinary matrices, with291 Python/34native/96local checks passing.
These prototypes remain local and are not a deployed extension. Actual future3x
centers can exceed the current24-bit depth range; isolated host depth remains
an integration requirement.
The [reusable native scene assembler](docs/reviews/2026-09-10-exotica-scene-assembler.md)
now passes24 complete independent comparisons across these three scenes at
1/2/3x with original/completed fade and repeats. It enforces bounded private
geometry, explicit model textures and source identity;295Python/35native/99local
checks pass. This remains standalone: live resource ownership, scene insertion
and handover are the next integration requirements. No new native deployment
or visible cross-game3x acceptance is implied.
Off Road is pending; limited scripted routes cannot certify cross-track behavior.

[The fresh Zeus upstream review](docs/reviews/2026-09-09-zeus-upstream.md) checks
master and all291 open PRs; the September10 06:59UTC refresh finds no new Zeus
work. A separate default-off candidate now carries
#16094 in CPU, GPU and independent geometry oracles. Amazon's six full policy
trials preserve motion; the combined59-frame4K result repeats, and blend decoding
restores car-selection reflections. It does not fix the marked1:12 artifact.
Both CPU policies match captured full color/depth buffers exactly; all seven
default cases pass. Enabled-policy Hong Kong motion/resources also pass;19/21
sampled4K frames are identical and two differ by two pixels each. Pending palette
row reuse is now fixed in a separate diagnostic candidate; all seven defaults
pass on its final capture-drain build. Next evaluate #16058's framebuffer/timing work and
the remaining Amazon marked windows. Timer
and SGRAM fixes from #16046 are already backported. Recheck pinned upstream heads
when adopting/rebasing candidates; preserve legacy controls and renew cross-game
defaults before adoption or deployment.

[Exotica's future-section decoder](docs/reviews/2026-09-09-exotica-future-sections.md)
now matches native/Python sources across 54 sections and predicts 2,507 later
allocations from six earlier snapshots. Five drives preserve original motion and
4K captures; the final capture repeats byte-for-byte. It remains standalone:
private Zeus state, material readiness and scene insertion are next.

[Exotica's model codec](docs/reviews/2026-09-09-exotica-model-codec.md) now
reproduces 8,126 complete original geometry/state records across three scenes in
independent Python and native decoders. Model-local state is isolated; five drives
preserve original inputs, motion and 4K captures. All seven defaults pass on the
separate candidate. The section decoder above follows it; it does not yet draw
extra scenery.

[Exotica's transform foundation](docs/reviews/2026-09-09-exotica-transforms.md)
now reproduces40093 centers/scaled command packets,13693 matrix updates,
39541 actual ordinary model emissions and3051 far-model selections. Four drives
preserve inputs/camera/actualADC times and21 original4K captures. The helper is
standalone; the model codec above follows it. Future-section host drawing is next.

[Off Road host rendering](docs/reviews/2026-09-09-offroad-host-rendering.md) is now
integrated in a separate candidate. Its future2x adds mountains/terrain in40/40
sampled4K images over1x;3x adds six further changes. Original inputs/camera/ADC
and five independent live geometry snapshots pass. Both repeats match40GL/2573619orderedquads; original53.8MB resources and all7defaults
pass. Clean3x runs measure about100% speed; an interrupted79.5% repeat is retained.
El Paso start coverage is limited; full clipping,
material lifetime, foreground occlusion and handover remain open.


[USA future rendering](docs/reviews/2026-09-09-usa-future-rendering.md) now connects
the independently checked section decoder to a separate MAME candidate. 2x adds
13/16 current4K images over1x;3x adds three smaller changes beyond2x. Route,
ordered output and original resources are preserved. Cached models/reciprocals
reduce cost, but3x still measures97–98% speed: full-speed and visual acceptance
remain open. Final original-resource and seven-default regression gates pass on
the separatecf58 candidate. [Off Road's own codec](docs/reviews/2026-09-09-offroad-model-codec.md)
now matches1,399 projections/9,602 ordered draws and preserves four6,000-input
replays and4K samples. [Transform/LOD reconstruction](docs/reviews/2026-09-09-offroad-transform-and-lod.md)
also matches1,399 matrices/decisions in three further runs. Its
[future-section decoder](docs/reviews/2026-09-09-offroad-future-sections.md) now
matches2,424 loaded objects and703 later allocations/bindings across12 snapshots,
including seven real partial loader boundaries. The
[host scene foundation](docs/reviews/2026-09-09-offroad-host-foundation.md) matches
72 scenes/50,736 ordered quads and five material snapshots remain stable. Its
integrated candidate and qualified limitations are described above; continue
broader visual acceptance alongside World2.5 roads and the Zeus adapter.

The earlier [USA pending-object adapter](docs/reviews/2026-09-09-usa-host-scenery.md)
was the foundation for the current future-section renderer above. World2.4/2.5
host scenery still has ground/occlusion work open. Stream Deck stays on v0.5.0.

1. **Cheats submenu and live activation: shipped in v0.5.0.** Imported choices,
   session-only Esc actions, one-shots/restoration and frame-stamped replay work
   across the four games. Five 4K menu/replay checks and the frozen launcher pass.
   Individual rank/nitro/parameter effects and broader gameplay coverage remain
   follow-up; see [current usage and limits](docs/CHEATS.md).
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
   The [September 9 foundation](docs/reviews/2026-09-09-world-host-cost-and-sections.md)
   now separates host timing phases and avoids a measured 16-second polygon-log
   stall using summary traces; original motion and completed images stay exact.
   Full-drive section math covers8,222 objects/46section angles/970offsets, and
   corrected probes verify both initial material lookups for all objects. Candidate
   remains separate from the v0.5.0 personal binary. The newer
   [future-section implementation](docs/reviews/2026-09-09-world-future-sections.md)
   now draws eligible upcoming scenery without guest allocation. Future3x adds
   visible mountains/buildings over future2x in16/31 completed4K images; all31
   images, geometry fingerprints and original camera/ADC repeat exactly. Callback
   max6.6ms with~100% emulation. Roads/custom codecs remain excluded and distant
   ground gaps remain. The [coverage trial](docs/reviews/2026-09-09-host-layers-and-roads.md)
   removes the new green tunnel line in the targeted 4K frame (3,079 differing
   pixels reduced to139), while full visual acceptance remains open. The separate
   road oracle now checks23,589 projections/21,123 unclipped ordered calls. The
   [resumed road implementation](docs/reviews/2026-09-09-host-road-integration.md)
   now fills the distant uphill road gap;18/21 current4K frames change and all21
   repeat. Full9,269-input routes/camera/actualADC timestamps remain exact. An
   initial read-handler timing defect was fixed with direct RAM/side-effect-free
   reads and a zero-guest-cycle guard. Native8bc/SHAa2fb is separate; all seven
   defaults and204Python/16native/32GPU local checks pass. The4K monitor is back.
   The [World2.5 host adapter](docs/reviews/2026-09-09-world25-host-scenery.md)
   is now integrated in a separate native candidate. Eleven snapshot/frontier
   oracles pass; five6000-input controls preserve camera/actual ADC times.3x adds
   scenery over2x in10/30 current4K images and repeats all30. Distant ground gaps
   remain; World2.5 roads and broad visual acceptance are still incomplete.
   USA has a different two-word/interleaved model format, so verify its
   codec before reusing the shared math. Off Road/Zeus adapters remain unfinished.
   Keep the candidate undeployed; no experiment menu cleanup is justified.
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
| C2 / A3 | Global host scenery | World2.4 future packed sections are implemented and visibly help at3x. Verify the separate road codec, complete integrity/occlusion/handover acceptance and add World2.5, USA, Off Road and Zeus adapters. Keep game layouts separate from shared math and acceptance. | Original inputs/camera/ADC and guest DMA/resources unchanged; visible benefit, correct occlusion/handover, repeatability, performance and attended cross-track coverage. |
| C2 | Exotica admission | Trace render-register `0x15`: all 814 matched bias changes are 2047 → 0. Isolate state/order changes before native admission support. | Preserve original submissions/resources and repeat the candidate; additional admissions are not proof of visible scenery. |
| C2 | USA global distance | Examine geometry and simulation differences in the repeatable CLI candidate before exposing it in the launcher. | Full candidate replay, scene/resource comparisons and an attended drive. |
| C2 | World / Off Road distance | Broaden coverage beyond the current routes; determine whether activation or residency, rather than far clipping, limits additional benefit. | Matched completed images, timing and fresh drives; do not count extra admissions alone. |
| C2 / G8 | Soften remaining scenery pop-in | Investigate distance-based alpha or fog transitions after the host scenery path is stable. Capture Exotica's existing appearance and trace its alpha/depth state as a reference; do not assume the same mechanism exists on V-Unit. Prefer a shared renderer transition with game-specific depth/material adapters. | Matched drives show reduced temporal jumps without transparent roads, halos, depth/order errors, temporal trails or new stutter. Preserve native translucency and shadows; fade static distant scenery only, with default-off A/B controls. Fading cannot reveal geometry before it is available. |
| C3 | World New York artifacts/crash | Obtain a recorded race reproducing black flashes and, if reproducible, the 3×/+12 finish crash. Preserve the default/2× control. | Diagnose the first bad submission or guest instruction; retain the original failing recording. |
| B8 | Broaden Cheats coverage | Live activation/replay is shipped and deployed. Validate rank/nitro and parameter effects individually; broaden actual race-end and code-restoration gameplay coverage beyond the current memory checks. | Exact-revision effects, correct restoration, recording fidelity and default-off regression controls. |
| A3 | World future-section decoder | Final descriptor/override and partial frontier checks pass; bounded PC-owned section storage now draws eligible packed scenery. Finish GPU lifetime and road/custom-class coverage, plus exactly-once transition to ordinary drawing. | Correct XYZ/orientation/materials, no dynamic/physics initialization, no per-model/level allowlist, smooth presentation and transfer to ordinary guest drawing. |
| B1 | Speed telemetry | Replace World's remaining OCR only after finding and guarding a real producer; retain validity/lifetime checks. | Actual outgoing packets versus independent memory/HUD evidence in both revisions. |
| B2 | Gear / estimated RPM coverage | Existing guarded gear/rev producers work across all four games. Broaden automatic/manual drives and higher-gear Off Road/Exotica coverage. | Real gauges/SimHub/Buttkicker plus independent traces; RPM remains an estimate from the game's rev signal. Never use E632. |
| B4 / B9 | Per-game menu force controls | **Post-release.** Extend the Exotica Menu Force Feedback experiment to USA, World and Off Road after verifying each game's menu/driving/race-end states. Preserve current World passthrough until that work is requested. | Correct transitions, no stuck effects, recorded gate/source traces and attended wheel checks. Do not conflate this with force normalization or alter defaults without testing. |
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

- **v0.5.0 is published and deployed; v0.4.0 is preserved.** The repository became
  public at the maintainer's September 9 request. Overnight distance work does not
  authorize another release; preserve both existing tags and packages.
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
