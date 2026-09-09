# Documentation

Current guides describe the source checkout as of 2026-09-08. The published
**v0.4.0** ZIP is an earlier, preserved alpha. Check the release notes before
assuming that a source feature is present in a downloaded package.

| Guide | Use it for |
|---|---|
| [Project overview](../README.md) | Games, current capabilities, downloads and limitations |
| [Setup and troubleshooting](INSTALL.md) | ROM import, controls, FFB, display, telemetry and updates |
| [Cheats](CHEATS.md) | Importing exact-revision cheats and supported actions |
| [Recorded gameplay](DIAGNOSTIC-REPLAY.md) | Attended recording, playback, captures and diagnostic evidence |
| [Roadmap](../ROADMAP.md) | Current work and acceptance criteria |
| [Local builds](LOCAL-BUILDS.md) | Local checks, packaging and exact-ZIP upload; Actions disabled |
| [Release checklist](RELEASE-CHECKLIST.md) | Automated gates, attended acceptance and promotion |
| [Attended release testing](RELEASE-MORNING.md) | Short practical drive protocol |
| [Public readiness](PUBLIC-READINESS.md) | Distribution, licence/media decisions and remaining public checks |
| [Changelog](../CHANGELOG.md) | Unreleased source changes and released versions |
| [v0.4.0 notes](release-notes/v0.4.0.md) | What the published package contains and its known issues |

## Source versus release

| Capability | Published v0.4.0 | Current source |
|---|---|---|
| Four games, CRT/full widescreen/4×/free-play defaults | Included | Included |
| Internal gear/rev telemetry, estimated RPM | Included | Included |
| World 2.4 guest distance trial | Optional 2×/3× and lookahead | Same optional trial |
| Experiments placement | Nested under Display | Beside Display, Shared/game contexts |
| Imported Cheats | Unavailable | Continuous toggles/choices; one-shots/restoration unavailable |
| World 2.5 / Off Road distance menus | Unavailable | Optional 2×/3×; default Off |
| Exotica margin scenery trial | Unavailable | Optional Widescreen Scenery; does not extend far distance |
| World host-owned pending scenery | Unavailable | Bounded CLI diagnostic; not enabled by normal launch |
| Normal-launch `env` regression | Not affected by later recording change | Fixed; reopen source launcher |

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
- [Off Road native distance](reviews/2026-09-08-offroad-native-distance.md)
- [Exotica visibility](reviews/2026-09-08-exotica-visibility-trials.md),
  [far distance](reviews/2026-09-08-exotica-far-distance.md) and
  [admission](reviews/2026-09-08-exotica-admission.md)
- [World FFB rollback](reviews/2026-09-07-world-ffb-rollback.md) and
  [Exotica polarity correction](reviews/2026-09-07-exotica-force-polarity.md)
- [Normal-launch regression and test coverage](reviews/2026-09-08-launch-environment.md)
- [Completed overnight checkpoint](OVERNIGHT-RESULTS-2026-09-08.md) and
  [archived work order](OVERNIGHT-2026-09-08.md); its heartbeat remains paused

The older [settings proposal](settings-redesign.md), [widescreen survey](widescreen-research.md),
[Off Road handoff](offroadc-left-edge-handoff.md), [achievements feasibility](ACHIEVEMENTS.md)
and [World draft patches](experiments/world-global-distance/README.md) are research
archives. They include superseded assumptions and unimplemented designs.
