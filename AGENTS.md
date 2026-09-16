# Cruis'n Collection — agent instructions

## Current work: release parity, September 16

Continue autonomously through useful parity work. Commit completed changes
separately and start the next item; do not stop at a milestone or wait for the
heartbeat. Stop only for a real user-dependent roadblock or a user pause.
The recovery heartbeat is a backup, not the work cadence.

Read these current references first:

- [Remaining release work](docs/reviews/2026-09-15-parity-remaining-work.md)
- [USA race transition](docs/reviews/2026-09-16-usa-race-transition.md)
- [Continuous3x preset](docs/reviews/2026-09-16-scenery-presets.md)
- [Optional Exotica endpoint capture](docs/reviews/2026-09-16-exotica-optional-endpoint-capture.md)
- [Quiet continuous V-Unit](docs/reviews/2026-09-16-vunit-quiet-runtime.md)
- [Off-Road 3x race transition](docs/reviews/2026-09-16-offroad-race-transition.md)
- [World 3x race transition](docs/reviews/2026-09-16-world-race-transition.md)
- [Exotica 3x race transition](docs/reviews/2026-09-16-exotica-race-transition.md)
- [Scripted recording continuations](docs/reviews/2026-09-16-scripted-recording-continuations.md)

**Current checkpoint:** World2.4 and Off-Road continuous quiet3x race/menu
continuations qualify, alongside Exotica. World12,669 inputs; Off-Road13,044;
original motion and owned shutdown exact. Both add distant terrain after menus.
Off-Road initially compared inherited401-line control against400-line candidate;
that raw comparison is NOT visual acceptance. A matching400-line control passes,
with10/14 images exact and4 changing only distant geometry above y838. The
candidate was not rerun. See their dated reviews for actual course/scope limits.

**Current checkpoint:** Exotica snapshot0 under explicit continuous quiet mode
passes one5300-input check.170 prior non-endpoint files and4 completed4K images
are exact, original input/camera/ADC unchanged,9842 endpoints prepared/0reject,
joined shutdown. Initial checker failed on scheduling-dependent depth batch count;
source-guided qualified-v2 preserves vertices/resources/pixels and separates that
count. No game rerun. Native first-rejection selection remains tested and lazy
operand capture retained. Read the optional endpoint capture review below.
USA also now passes12,212 inputs,10,412 camera/31,236 ADC,6,336 scenes,
14,903,983 quads and joined shutdown. Continue8400/startGoldenGate9000/bridge12000
at0:54.41 observed.2/13 menu images exact,11 gameplay changes all above y1142;
start-letter gap detail retained, not blanket overlay acceptance. No full second
race claim. The reusable recording command ran live and preserves all5012 source
inputs; probe/CRT/height controls are explicit.

The new diagnostic --scenery-preset continuous-3x centralizes all5 ROM profiles.
Three targeted parser/conflict tests PASS; saved controls match executed plans
(Exotica only changes snapshot5219->0, separately qualified). No redundant game
replay for argument spelling. No game/build/test active. Next investigate actual
user-requested close/interruption semantics with owned workers, using existing
check_frozen_package.py WM_CLOSE helper and FFB0; inspect native shutdown contracts
before selecting a bounded run. Keep ordinary input/capture completion distinct
from an intentionally interrupted test. Product/attended/distance gates remain.

Current frozen native: `f0b4db1f25d869d010d396997bb1839c412a4b23`,
`build/candidates/f0b4db1f25d/vunit.exe`, SHA256
`435123cf0e1026fbdda94a8069a59f025a3d8b98fc2d1cebda0146b871fd95c1`.
253 patches reconstruct `476814a23a6864416d95e564830a464b0e4672c3`.
`endpoint-routine-capture-native-export.json` under
`results/diagnostics/world25-roads-20260914` is the current export receipt.
**All existing export scripts have already run. Never rerun an export against
its appended patch baseline.** Create a new export for a new native commit.

Recent verified results:

- V-Unit scene bootstrap, continuous operation and owned GPU shutdown qualify
  USA, World2.4/2.5 and Off-Road. Quiet journals qualify USA/World2.5/Off-Road;
  World2.4 retains a matching capture-mode regression. Recorded inputs, motion,
  geometry and actual post-reference-end4K images match retained controls.
- Exotica continuous3x completes Amazon plus scripted name entry/loading/new
  race start:11,260 inputs,9,460 camera records,28,380 ADC reads,9,734 scenes,
  ten native pool epochs,32,221 marked commands with zero rejection, and joined
  quiescent shutdown. Eight menu/loading images are exact. Frame11100 changes
  only far-right foliage;941 new dark pixels there are retained, foreground
  rectangle exact. Not a complete second race or proof of outer3x visibility.
- `harness/extend_input.py` preserves the entire recorded INP prefix and joins
  a labeled scripted tail with correct analog interpolation. New stimuli must
  pass through MAME's writer and actual prefix checks before use as new cases.

Exotica's first transition plan failed **before launch** because the endpoint
snapshot is mandatory. Corrected `exotica-menu-tail-3x-v2` retains5219 and passes;
keep the original failure. Earlier USA/World analyzer corrections and Off-Road
bootstrap receipt failures remain documented. Never turn old failed reports
into successes or rerun games merely to fix an analyzer.

Open work includes broader track/temporal quality, World Hawaii's authored
terrain gap, New York's artifacts/crash, useful outer Exotica distance/fade
coverage, remaining performance and final product gates. Prior World custom
handlers/no-op and adjacent terrain searches are already completed: consult
their reviews rather than reopening obsolete NEXT instructions. A two-race,
open-course Exotica recording was requested; availability is unanswered. Do not
start an attended recording without a reply. Independent work still remains.

## Constraints and efficient validation

- No deployment, release publication, hosted CI, physical FFB, or menu removal
  during this parity work. The personal Stream Deck copy and publicv0.5.0 remain
  unchanged. Personal `E:/Source/mame-src/vunit.exe` SHA256 is
  `87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8`.
- Serialize the rig, GPU and builds. No builds, patch exports or broad scans
  during a timed game. Use exact known result directories; the full diagnostics
  tree is enormous. Use `rg --files --no-ignore` for ignored case artifacts.
  Do not guess case or capture filenames: manifests are usually `case.json`
  and completed capture indexes `captures.csv`.
- Use existing evidence before new gameplay. Run targeted checks for changed
  behavior. Do not repeat full drives for favorable timing or broad suites by
  habit. The previous seven-case default suite passed; repeat only for a new
  shared risk. Performance comparisons need matched conditions and clear scope.
- Preserve original cases, failed reports, source/ROM/settings identity and
  exact frozen binaries. Save substantive diagnostic scripts. Python text I/O
  must specify `encoding='utf-8'`; Windows default encoding previously corrupted
  a source comment. Keep corrected analysis in new reports.
- Separate input identity, camera/ADC equality, scene/resource/ownership proof,
  completed pixels, timing and attended feel. None alone proves a good game.
  Zeus GL skips CPU polygons: matching black native images do not validate
  its visible output. Attract mode does not substitute for gameplay.
- Exact renderer claims require zero differing pixels (100.0000%, four decimal
  places). Never assume a scene occurs on every frame or is always nonempty.
  Do not accept missing requested work just because native execution returned0.
- Current monitor selection is DISPLAY2,3840×2160 primary; DISPLAY1,3440×1440
  secondary. Verify actual completed dimensions. V-Unit maximized client is
 3824×2073; Zeus covers3840×2160. Do not describe older3440 tests as final4K.

## Source, build and export

The collection is `E:/Source/cruisn-collection`, branch `master`, remote `origin`.
Native MAME is `E:/Source/mame-src`, branch `poc/quadlog`, remote `fork`, based on
MAME0.286. Commit/push them separately and keep the complete exported patch
series in sync, including the DIJOYSTATE2 base patch from `mame0286`.

Canonical C++ helpers live in `native/`; check/sync with
`python harness/sync_native.py [--write]`. The toolkit pin is
`lib/toolkit/VERSION` (v0.11.1); `harness/sync_toolkit.py` checks consumers.
Shader source is `gpu/renderer.py`; regenerate with `harness/gen_shaders.py`.
Never hand-edit generated `midvunit_gl_shaders.h` or introduce raw C++ shader
strings that MAME's source scanner cannot parse.

Build locally with MSYS2 at `E:/msys64`, not C:. Export `OS=Windows_NT` inside
the login shell because its profile clears the inherited value:

```powershell
$env:MSYSTEM='MINGW64'
& E:/msys64/usr/bin/bash.exe -lc 'export OS=Windows_NT; cd /e/Source/mame-src && make SUBTARGET=vunit SOURCES=src/mame/midway/midvunit.cpp,src/mame/midway/midzeus.cpp NOWERROR=1 TOOLS=0 SEPARATE_BIN=1 -j18'
```

The isolated output is `build/mingw-gcc/bin/x64/Release/vunit.exe` in mame-src.
Freeze it under collection `build/candidates/<commit>/` with profile and SHA
receipts. Never overwrite the personal root `vunit.exe` during candidate work.
Never touch `Launchbox-Racing/Emulators/mame286/mame.exe`; only read its ROMs,
controller inputs and fixtures as needed. Add REGENIE only for relevant build
project changes. Use `git -c core.safecrlf=false` for native commits/exports.

Export once per committed native successor. Verify prior patch SHA, clean native
HEAD, expected commit count, actual built binary age, reconstructed Git tree,
profile SHA and unchanged personal binary before appending. Preserve patch
bytes; do not rely on PowerShell text redirection for a binary-safe export.

## Architecture and product boundaries

This is still emulated game code with replacement renderers and host scenery,
not a native port. Never reuse unverified memory addresses across ROM revisions.
Explicit MIDV_PATCH overrides normal selection; conflicting experiments must
fail. The launcher menus still use older guest-distance experiments; the new
continuous host prototypes are explicit CLI candidates, not shipped features.

| Path | Responsibility |
| --- | --- |
| `harness/collection.py`, `run_rig.py` | Launcher, saved rig preferences, common launch/input path |
| `harness/record_drive.py`, `replay.py`, `derive_case.py`, `extend_input.py` | Attended recordings, isolated replay, derived cases and scripted continuation |
| `harness/local_checks.py`, `release_gate.py`, `promote_release.py` | Local evidence and exact accepted ZIP promotion |
| `harness/cheats.py`, `lua/cheats.lua` | Exact-revision cheat import and live bridge |
| `native/`, `gpu/`, `lua/` | Canonical C++ helpers, renderer/shaders and read-only probes |
| `tests/`, `fixtures/` | Focused contracts, native tests, scenarios and calibrated NVRAM |
| `patch/`, `lib/toolkit/`, `profiles/` | Native patch series, pinned reusable wheel code and profiles |
| `docs/`, `results/` | Current guides, dated evidence, ignored large diagnostics |
| `rig/`, `build/`, `media/`, `third_party/` | Personal state/candidates, menu assets and notices |

Release preparation is local; workflows are disabled and tag pushes do not
authorize publication. Follow `docs/LOCAL-BUILDS.md` and the full release checklist
only when publication is authorized. Keep personal preferences separate from
fresh-install defaults. Defaults include CRT on,4x, full widescreen and free play.
Launcher-path tests remain necessary before release; replay success does not
prove the shell launches correctly.

## Rendering, controls and FFB facts

- V-Unit page_control bit2 selects render target, bit0 the visible page. Pages
  persist; native cracks may expose prior-frame content. Margin ownership,
  painter/depth order and intrinsic transparency must remain correct.
- After shader/pipeline changes, preserve exact-mode reference output with
  `python gpu/renderer.py results/capture-8000`; original native captures require
  seeded NVRAM. Use completed GL fences for displayed scenes, not quad-count
  thresholds or legacy asynchronous external-viewer captures.
- GL uses an owned top-level popup, not a child window. Keep input focus on MAME;
  never activate the overlay or use SwitchToThisWindow. GDI captures can show GL
  as black; prefer native completed-frame captures. Rawinput may reject injected
  keyboard events. Normal Esc opens the in-game menu; F9 CRT, F12 exits game,
  Shift+F12 exits both game and launcher. See INSTALL for bindings/calibration.
- FFB is built into MAME through SDL2 and the pinned toolkit; retired input/FFB
  plugins must not return. Preserve World's user-requested menu/race-end pass
  through; no unattended strength retuning or restoration of its rejected gate.
  Motor polarity, input direction, native source, conditioning and wheel torque
  are distinct. Full normalization and physical feel remain unaccepted.
- Never hard-kill with physical FFB active: stranded constant torque is possible.
  Use normal exit/WM_CLOSE; the Stream Deck Stop FFB control is available for a
  stuck wheel. Unattended runs require literal MIDV_FFB=0 and no actuator tests.
  FFB time joins require force-source/emulated clocks, not an assumed wall clock.
- User-observed defects and complete gameplay recordings are valuable evidence.
  Do not call crashes harmless based on old teardown hypotheses; preserve logs
  and distinguish guest, renderer and shutdown failures.

## Documentation maintenance

Update this current checkpoint in place. Do not prepend another full history.
Put detailed outcomes in dated reviews and link them here. Keep `results/RESULTS.md`
append-only and original failures intact. The previous361KB AGENTS file is
preserved verbatim in
[the checkpoint archive](docs/reviews/archive/2026-09-16-agent-checkpoints.md).
It contains obsolete NEXT tasks, old private-repository status, superseded RPM
claims and unsafe-for-current-work build destinations. It is historical evidence,
not active instructions; read only a relevant dated section when needed.
