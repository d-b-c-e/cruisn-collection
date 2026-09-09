# Preparing public access

Updated 2026-09-08. The repository is currently **private**. v0.4.0 is published
inside that private repository; the source contains newer work. The maintainer
wants public access soon. This document records preparation, not a completed
visibility change or authorization to publish another version.

## Completed preparation

- [x] Refresh player/developer guidance and distinguish current source from v0.4.0.
- [x] Document unresolved rendering/FFB issues and diagnostic-only distance work.
- [x] Disable hosted workflows and remove automatic push/PR check triggers.
  Local checks and exact-ZIP promotion are documented in [LOCAL-BUILDS.md](LOCAL-BUILDS.md).
- [x] Preserve the published tag/ZIP, original recordings and local settings.
- [x] Correct the normal-launch environment regression and add launch-boundary
  tests for five ROM revisions with cheats on/off and recording overrides.

## Decisions and checks before public access

- [ ] Decide whether to expose this repository/history or publish from a reviewed
  distribution repository. Review tracked history and archived diagnostics for
  material intended only for development. The top-level `rig/`, local recordings,
  support bundles and `build/` are ignored; that does not audit Git history.
- [ ] Document the licence for original launcher/tooling code. There is no tracked
  root licence file. The MAME patch distribution, SDL2 and vendored toolkit have
  separate existing notices/source that must remain with their components.
- [ ] Review menu asset provenance/permissions. `media/` tracks eight logo/title
  images and one music file, and the normal package includes them. `-NoMedia`
  excludes these from a candidate ZIP but does not remove them from repository
  history. The previous blanket claim that packages contained no game assets
  was inaccurate and has been removed.
- [ ] Select the package to offer publicly. Keeping v0.4.0 means documenting that
  Cheats, new game distance menus and top-level Experiments are not in that ZIP.
  Shipping current source requires a new clean candidate and renewed gates.
- [ ] Complete [release acceptance](RELEASE-CHECKLIST.md), including actual
  launch/drive/exit, all-game shifters, telemetry/tactile output, FFB direction,
  clean-profile installation, upgrade preservation and second-wheel coverage.
  Public testing must describe remaining unperformed checks accurately.
- [ ] After an explicitly requested visibility/distribution change, verify anonymous
  source/release access and download the exact asset without authentication.
  The updater currently queries `d-b-c-e/cruisn-collection`; a separate destination
  needs a code/config update. Test the packaged updater against the chosen endpoint.
- [ ] Review the player-facing notes and release ZIP one final time. Publish only
  the same ZIP that passed acceptance; no tag-triggered rebuild.

The documentation audit checks claims against current code and packaging inputs.
It does not constitute an asset-rights determination, a full history review or
new physical-wheel acceptance. These remaining tasks should be explicit before
describing the project as ready for unrestricted public distribution.
