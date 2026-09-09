# Live Cheats, menu feedback and separate local builds

## Status

The source launcher now exposes **Settings → Experiments → Exotica → Menu Force
Feedback**. Off preserves the existing suppression outside driving; On allows
Exotica's menu and race-end motor feedback on the next launch. It works with the
existing personal native binary. The explicit developer environment override
still wins. This is independent of display scale and widescreen experiments.
Exotica's polarity correction and 20% effective gain trim are unchanged. World
passthrough and its deferred normalization are unchanged. Equivalent controls for
USA, World and Off Road are a post-release roadmap item, per the user.

The live Cheats implementation is built as native `4ac6a84b51b4ae549399c81ffe1b9346e2c04758`,
separate candidate SHA256 `87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8`.
Its 134-patch export reconstructs tree `007c6ac1f1b6471237241d07275fd57024c19d01` exactly.
It is **not deployed to the personal Stream Deck emulator** yet. Visual Esc-menu
checks and the seven default driving regressions remain pending a free testing
window. The previous personal binary is retained, SHA256
`e0cf8a8b498d4499f81228b2fbb3e40367d29fd25e1c86edb9c95ee500c689d1`.
The old binary remains compatible with the updated launcher and cheat loader.

## Live action design

Both enhanced renderers add Cheats between CRT and Exit in the Esc menu. The
shared native menu only edits metadata and queues actions. MAME's emulation-thread
Lua callback executes them after Resume, using the existing MAME cheat interpreter.
No render-thread guest writes or second expression evaluator are introduced.

Arrow keys change values; Enter activates one-shots. Esc inside Cheats returns to
the root pause menu without applying the queue. Resume submits it once; Exit
discards it. Session edits do not overwrite saved prelaunch preferences. One-shots
and instruction-restoring cheats remain excluded from prelaunch preferences.
Imported but unselected catalogs enable the engine with every entry off, making
live activation possible. Without an imported catalog, the engine remains disabled.

Recordings retain a frame-stamped `actions.csv` in addition to exact XML, initial
selections, loader and state events. Playback and derived cases preserve the
journal; changed/missing/out-of-range actions are rejected. Replay's menu is
read-only. Repeated one-shot activations remain separate events. Older recordings
and native binaries retain compatibility. Support bundles include actions and
state events, excluding XML and ROMs.

## Verification completed

- Full local Windows inventory: 196 Python tests, no skips; 14 standalone native
  helpers; host C31 math and force/T-junction analyzers; 24 OpenGL quality fixtures.
  `results/diagnostics/local-checks-live-cheats-20260908/report.json` binds all297
  source inputs, 39 commands, results and logs; source identity
  `6899b54e3067a8e6bffa6b59bbd0b706cae70be77102d101ab7535f852faeed9`.
  No hosted minutes were used.
- Native staged-menu tests cover Resume versus Back/Exit, read-only replay, repeated
  one-shots, parameter selection, an empty catalog and the per-pause action limit.
- Actual Lua 5.4 runs the shipped loader in tests, with a mocked native boundary:
  ordering, repeated actions, replay fidelity, invalid/tampered inputs and older
  native compatibility. These tests do not claim to implement MAME expressions.
- Five real native 3300-frame timer runs, one per ROM revision, passed with video,
  audio and physical force disabled. The live loader applied Infinite Time at
  frame2600 and disabled it at3000; memory held and then resumed progression.
- Five additional real native runs exercised instruction restoration and available
  one-shot activation. USA restored four inspected instruction words; World2.5,
  Off Road and Exotica restored three each. World2.4's catalog has no Drive Anywhere
  entry. Finish this Race Now zeroed the running timer exactly at3200 in USA, both
  World revisions and Exotica. Off Road's imported catalog has no finish one-shot.
  Every actual action journal matched the scheduled action frames. Raw reports:
  `results/diagnostics/live-cheats-restoration-<rom>-20260908/report.json`.
- `harness/check_live_cheat_menu.py` is implemented for windowed navigation,
  staging, paused-frame stability, resume, exit, actual recorded actions and
  completed-image replay. **It has not run yet**. Headless timer checks do not
  establish the visible menu layout or input handling in an actual game window.

Rank, nitro, imported parameter effects, every game-specific cheat limitation,
physical force and attended gameplay remain unverified. The real engine tests
establish the named timer/restore effects only.

## Personal versus release builds

`build_local.ps1 -Target Release` compiles with `SEPARATE_BIN=1`, freezes into fresh
staging and packages factory defaults. It never copies the personal rig or deploys
over the Stream Deck emulator. `-Target Personal` explicitly installs the candidate
binary with a hash-named backup and refuses while that personal game is running.
Settings remain runtime data. `-SkipNativeBuild` explicitly reuses a candidate;
it is not a claim that its sources were rebuilt.

Package validation rejects personal config/profile/runtime files and checks actual
frozen CRT-on, full widescreen, scale4, World2.4, 50% strength, CRISP profile and
per-game experiment-off defaults; Shared Crack Fill retains its existing default.
No target publishes anything. See [local build commands](../LOCAL-BUILDS.md).
The published v0.4.0 tag/ZIP, personal preferences and original recordings remain
intact. This candidate is preparation, not a new release or a public visibility change.

The Release target was exercised end-to-end with `-SkipNativeBuild -Version dev`:
`build/CruisnCollection-dev-20260908-220014.zip`, SHA256
`0a45aec96dea094a04a672d7180ebb2ab683cf371edf1628d2a4a52d236e9ad1`.
Its 1724 files, native identity and actual frozen factory defaults pass. Source
commit245b318 was clean while packaging. Native compilation was verified separately;
the explicit Personal deployment target has not run. No frozen game launch is claimed.

`results/proof/2026-09-08-live-cheats/verify_archive.py` verifies the 78-file archive
and recomputes all five timer/restoration/action verdicts without ROMs or cheat XML.
Build, native helper, GPU and package verdicts are hash-bound receipts; the verifier
does not rebuild the binary, rerender the GPU fixtures or execute a packaged game.

## Other feedback

The screenshot is an **Equalizer APO 1.4.2 update-check error**, not a Cruis'n error.
Local installed files identify `C:\Program Files\EqualizerAPO\UpdateChecker.exe`.
The scheduled task `EqualizerAPOUpdateChecker` runs that executable with `-a`; its
last run was September8 at21:06:49 local. No Equalizer/Peace/SourceForge invocation
was found in the launcher or setup/packaging paths. Its update settings were left
alone.

The roadmap now includes distance-based alpha/fog transitions as a post-release
way to soften remaining scenery pop-in. Trace Exotica's actual alpha/depth behavior
as a reference, then test static distant geometry with game-specific adapters.
Acceptance excludes halos, transparent roads, depth/order mistakes, trails and new
stutter. A fade cannot reveal geometry before the renderer has it.
