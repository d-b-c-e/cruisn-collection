# Public access and remaining preparation

Updated 2026-09-09. The maintainer explicitly requested that this repository be made
public, and its visibility is now **public**. Anonymous source access, the latest
release endpoint and the updater's v0.5.0 download pass. The downloaded ZIP matches
the accepted SHA256 `20d1cf67cc7db82fa6cebf494369117e25bf5cf6eae0e8b7d717a55c830d3734`.
v0.4.0 remains available for rollback. Hosted workflows remain disabled. This
visibility change does not complete the remaining reviews or authorize a new release.

## Completed preparation

- [x] Refresh player/developer guidance and distinguish current source from v0.4.0.
- [x] Document unresolved rendering/FFB issues and diagnostic-only distance work.
- [x] Disable hosted workflows and remove automatic push/PR check triggers.
  Local checks and exact-ZIP promotion are documented in [LOCAL-BUILDS.md](LOCAL-BUILDS.md).
- [x] Preserve the published tag/ZIP, original recordings and local settings.
- [x] Correct the normal-launch environment regression and add launch-boundary
  tests for five ROM revisions with cheats on/off and recording overrides.
- [x] Separate local Release/Personal targets; verify a clean dev ZIP's actual
  frozen factory defaults and reject personal config/profile/runtime files.

## Public-access decision and remaining checks

- [x] The maintainer chose to make this repository and its history public.
- [ ] Review tracked history and archived diagnostics for material intended only
  for development. The top-level `rig/`, local recordings, support bundles and
  `build/` are ignored; that does not audit Git history.
- [ ] Document the licence for original launcher/tooling code. There is no tracked
  root licence file. The MAME patch distribution, SDL2 and vendored toolkit have
  separate existing notices/source that must remain with their components.
- [ ] Review menu asset provenance/permissions. `media/` tracks eight logo/title
  images and one music file, and the normal package includes them. `-NoMedia`
  excludes these from a candidate ZIP but does not remove them from repository
  history. The previous blanket claim that packages contained no game assets
  was inaccurate and has been removed.
- [x] Build and verify v0.5.0 with Cheats, new game distance menus and top-level
  Experiments. Exact ZIP uploaded/downloaded and source/runtime gates renewed.
  Its distribution is now publicly accessible under the September 9 instruction.
- [ ] Complete [release acceptance](RELEASE-CHECKLIST.md), including actual
  launch/drive/exit, all-game shifters, telemetry/tactile output, FFB direction,
  clean-profile installation, upgrade preservation and second-wheel coverage.
  Public testing must describe remaining unperformed checks accurately.
- [x] Finish five visible Esc → Cheats recordings/replays, all seven defaults and
  the actual frozen live-menu check. Matching native deployed to Stream Deck.
- [x] Verify anonymous source/release access and download the exact asset without
  authentication. The current updater's check/download functions retrieved v0.5.0
  from `d-b-c-e/cruisn-collection` and verified its accepted hash on September 9.
  No installed files were updated during this check.
- [ ] Exercise the packaged updater UI against the now-public endpoint. The prior
  frozen and upgrade/rollback checks remain valid, but are not this new live UI check.
- [ ] Review the player-facing notes and release ZIP one final time. Publish only
  the same ZIP that passed acceptance; no tag-triggered rebuild.

The documentation audit checks claims against current code and packaging inputs.
It does not constitute an asset-rights determination, a full history review or
new physical-wheel acceptance. These remaining tasks should be explicit before
describing the project as ready for unrestricted public distribution.
