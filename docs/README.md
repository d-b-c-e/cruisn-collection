# Documentation

Current guides describe the source checkout as of 2026-09-10. The published
**v0.5.0** ZIP is the accepted baseline; v0.4.0 remains preserved for rollback.
Check the release notes before
assuming that a source feature is present in a downloaded package.

| Guide | Use it for |
|---|---|
| [Project overview](../README.md) | Games, current capabilities, downloads and limitations |
| [Setup and troubleshooting](INSTALL.md) | ROM import, controls, FFB, display, telemetry and updates |
| [Cheats](CHEATS.md) | Importing exact-revision cheats and supported actions |
| [Recorded gameplay](DIAGNOSTIC-REPLAY.md) | Attended recording, playback, captures and diagnostic evidence |
| [Roadmap](../ROADMAP.md) | Current work and acceptance criteria |
| [Four-game FFB normalization](FFB-NORMALIZATION.md) | Near-term strength-50 calibration, measurements and attended acceptance |
| [Exotica FFB plugin audit](reviews/2026-09-10-ffb-plugin-and-normalization.md) | Upstream comparison and measured adapter clipping |
| [FFB condition coverage](reviews/2026-09-10-ffb-condition-coverage.md) | Time-weighted source comparisons, OCR/steering provenance and remaining matched-drive gaps |
| [Four-game scenery status](reviews/2026-09-10-scenery-parity-status.md) | Demonstrated gains, unequal 3× results, performance and remaining coverage |
| [Off Road complete drive](reviews/2026-09-10-offroad-full-drive.md) | Attended El Paso recording, exact full-route replay and extended-scenery checks |
| [Exotica fade and performance](reviews/2026-09-10-exotica-fade-and-performance.md) | Original fade reconstruction and measured future-rendering costs |
| [Exotica packet and identity checks](reviews/2026-09-10-exotica-packet-and-identity.md) | Exact serializer comparisons, paired timing and original allocation/fade joins |
| [Exotica drawing admission](reviews/2026-09-10-exotica-drawing-admission.md) | Measured allocation-to-draw delay, reusable lifetime tracking and offline waiting-scenery continuation |
| [Native Exotica lifetimes](reviews/2026-09-10-exotica-native-lifetimes.md) | Exact live event observation, full-drive repeat and the retained World renderer regression |
| [Exotica waiting selection](reviews/2026-09-10-exotica-waiting-selection.md) | Allocation-owned selection before first submission, checked against five real scenes |
| [Live waiting observation](reviews/2026-09-10-exotica-waiting-observation.md) | Full-drive native waiting geometry, repeat checks and measured original-draw overlap |
| [Exotica pool lifetimes](reviews/2026-09-10-exotica-pool-lifetimes.md) | Allocation/removal generations, slot reuse and the post-race reset |
| [September 9 handoff](OVERNIGHT-RESULTS-2026-09-09.md) | Measured 3x progress, undeployed candidates and remaining cross-game work |
| [Local builds](LOCAL-BUILDS.md) | Local checks, packaging and exact-ZIP upload; Actions disabled |
| [Release checklist](RELEASE-CHECKLIST.md) | Automated gates, attended acceptance and promotion |
| [Attended release testing](RELEASE-MORNING.md) | Short practical drive protocol |
| [Public readiness](PUBLIC-READINESS.md) | Distribution, licence/media decisions and remaining public checks |
| [Changelog](../CHANGELOG.md) | Unreleased source changes and released versions |
| [v0.5.0 notes](release-notes/v0.5.0.md) | What the current published package contains and its known issues |
| [v0.4.0 notes](release-notes/v0.4.0.md) | Preserved rollback release |

## Source versus release

| Capability | Published v0.5.0 | Current source |
|---|---|---|
| Four games, CRT/full widescreen/4×/free-play defaults | Included | Included |
| Internal gear/rev telemetry, estimated RPM | Included | Included |
| World 2.4 guest distance trial | Optional 2×/3× and lookahead | Same optional trial |
| Experiments placement | Beside Display, Shared/game contexts | Same |
| Imported Cheats | Launcher choices and Esc live actions | Same |
| World 2.5 / Off Road distance menus | Optional 2×/3×; default Off | Same |
| Exotica margin scenery trial | Optional Widescreen Scenery | Same; does not extend far distance |
| World host-owned scenery | Pending prototype, disabled by normal launch | Future-section CLI candidate; not deployed, visual acceptance incomplete |
| USA / Off Road host future scenery | Not included | Separate native CLI candidates; measured earlier scenery, acceptance incomplete |
| Exotica host future scenery | Not included | Private wide-depth native candidate; dense comparisons repeat, performance and fade/handover incomplete |
| Normal-launch `env` regression | Fixed | Fixed |

## Research and historical evidence

Dated reviews and checkpoints are evidence of particular source/binary states.
Their trial settings, unsuccessful approaches, status and commands are preserved;
they are **not current installation or release instructions**. Later findings can
supersede them without rewriting a recorded FAIL into a PASS.

- [Engineering chronology](../results/RESULTS.md) and [proof archives](../results/proof)
- [Initial independent assessment](reviews/2026-09-05-assessment.md)
- [Global distance and native-port reassessment](reviews/2026-09-06-global-distance-and-native-port.md)
- [World guest distance trial](reviews/2026-09-06-global-distance-trial.md)
- [World host scenery prototype](reviews/2026-09-08-world-host-scenery.md)
- [World future sections and retained tunnel regression](reviews/2026-09-09-world-future-sections.md)
- [World 2.4 host roads](reviews/2026-09-09-host-road-integration.md) and [World 2.5 scenery](reviews/2026-09-09-world25-host-scenery.md)
- [USA future rendering/performance](reviews/2026-09-09-usa-future-rendering.md) and [Off Road host rendering](reviews/2026-09-09-offroad-host-rendering.md)
- [Exotica live future rendering](reviews/2026-09-10-zeus-live-future.md) and [Amazon margin acceptance](reviews/2026-09-10-exotica-margin-acceptance.md)
- [Off Road native distance](reviews/2026-09-08-offroad-native-distance.md)
- [Exotica visibility](reviews/2026-09-08-exotica-visibility-trials.md),
  [far distance](reviews/2026-09-08-exotica-far-distance.md) and
  [admission](reviews/2026-09-08-exotica-admission.md)
- [World FFB rollback](reviews/2026-09-07-world-ffb-rollback.md) and
  [Exotica polarity correction](reviews/2026-09-07-exotica-force-polarity.md)
- [Normal-launch regression and test coverage](reviews/2026-09-08-launch-environment.md)
- [September 9 morning handoff](OVERNIGHT-RESULTS-2026-09-09.md) and
  [paused work order](OVERNIGHT-2026-09-09.md)
- [Completed September 8 checkpoint](OVERNIGHT-RESULTS-2026-09-08.md) and
  [archived work order](OVERNIGHT-2026-09-08.md); their older scheduling statements are historical

The older [settings proposal](settings-redesign.md), [widescreen survey](widescreen-research.md),
[Off Road handoff](offroadc-left-edge-handoff.md), [achievements feasibility](ACHIEVEMENTS.md)
and [World draft patches](experiments/world-global-distance/README.md) are research
archives. They include superseded assumptions and unimplemented designs.
