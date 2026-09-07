# Overnight release hardening


**Final outcome:** the automated release baseline passes. The built candidate is
`CruisnCollection-v0.4.0-rc1-20260907-050908.zip`, packaged from be87237 with native
5bb965763b1. All 100 Python tests, four CI jobs, seven driving cases, five fresh-seed
persistence checks, three menus, 24 GPU quality fixtures and both native-exact
captures pass (100.0000%). Frozen launch/setup/support checks pass for all four
games; the exact ZIP upgrade preserves the fixture's user data and matches all 1,617
packaged files. Windows/Linux/local source hashes agree for all 201 inputs.

The unchanged native renderer also preserves 174 sampled completed GL frames over
three full old/new drives. The final source, native binary and ZIP stayed unchanged
during validation. Configured intervals hold 99.9290..100.0040% emulation; the largest
callback gap is 44.7 ms. This does not certify stutter-free presentation or every
unsampled frame. New proof: [final evidence](../../results/proof/2026-09-07-release-hardening/release-final/README.md).

Public release still needs the [morning checks](../RELEASE-MORNING.md) and a public
hosting decision: the repository is private and anonymous update requests return404.
All 39 human/shared checklist entries remain pending. Physical FFB was never enabled
by automation; scenery pop-in, World collision feel and Exotica polarity remain
open acceptance items. The sections below retain the investigation checkpoints.

2026-09-07. User requested continued autonomous fixes and end-to-end validation
while away, with separate commits and a release candidate ready for attended
checks tomorrow. No public release or unattended physical force output.

## Renderer startup

The previous near-4K World failure remains the starting evidence: a consumer
timeout, native presentation fallback and no requested GL frames. Existing logs
showed more than half a million CPU framebuffer messages during startup.

A first prototype combined adjacent CPU spans. Its 26 captured frames per game
matched the old renderer for USA, World and Off Road, both with the control and
batching enabled. However, World still needed 417,298 upload spans versus 420,693
in the immediate-upload control. Scattered boot writes defeated that approach.
This prototype is retained locally, not credited as a performance fix.

The next implementation uploads the CPU shadow and a mask of actual CPU writes,
then copies only marked pixels into the indexed framebuffer on the GPU. It
flushes before each non-CPU ordered message and before presentation. Untouched
pixels, including prior GPU geometry and margins, remain intact. It does not
change guest memory, simulation, draw admission or the 500-wait stream watchdog.
`MIDV_GL_BATCH_VRAM=0` / replay `--no-vram-batching` retains an immediate control.
Timeout messages now include frame, message type, required/queued bytes, consumer
progress and measured wait duration.

Initial paired runs, 1804-frame prefixes with 26 completed GL frames each:

| Game | Immediate upload spans | Masked GPU copies | Captured images vs old renderer |
|---|---:|---:|---|
| USA | 425,490 | 330 | All 26 match |
| World | 420,693 | 196 | All 26 match |
| Off Road, historical 400-row case | 419,788 | 65 | All 26 match |

These counts are rendering work, not FPS or a guarantee against every timeout.
The new GPU-copy fixtures preserve zero-valued CPU writes, sparse holes, existing
mask tags and margins at scales 1/4 and heights 7/401. All 24 quality fixtures
pass. Both archived exact-mode captures remain 100.0000% bit-exact. No Zeus shader
was changed. Full driving, repeated full-size startup and stall checks follow.

## Diagnostic height correction

The old Off Road synthetic case did not set `MIDV_GL_HEIGHT`, so its historical
GL capture used 400 rows. The launcher already uses the correct 401 rows.
Future smoke/synthetic captures now use the same height mapping; replay has an
explicit `--gl-height` override rather than modifying original recording data.
The new startup harness forces scale 4/CRT on and the game's correct V-Unit height.
The historical images remain useful for their stated 400-row comparison only.

## Release packaging still to address

The tag workflow rebuilds and publishes immediately; candidate artifact promotion
must replace that path before a public tag. Manual workflow ZIP naming also uses
branch names containing slashes. Local freezing and clean-path launches remain
to be tested. `make_release.ps1` advertises bundled art/music and `-NoMedia`, but
currently contains no media-copy stage; inspect the intended packaging history
and verify the actual frozen UI before deciding the appropriate correction.

## Packaging corrections prepared

Git history confirms 5ea8b2d accidentally deleted the media stage while removing
the obsolete FFB plugin. Restore the eight tracked menu images and tracked music
to `art/` and `audio/`, leaving user music in `rig/assets` preferred. `-NoMedia`
now has an effect. Package validation requires media unless explicitly disabled.
The bundled toolkit MIT licence now follows its pinned source tag.

Freezing fails on external-command errors. Source trees copy tracked files only,
excluding loose development bytecode. Exotica fallback BGFX files are required,
and the CI cache retains them alongside the emulator. Timestamped ZIPs preserve
previous candidates. A manifest binds the ZIP, every file, emulator and clean
source identity. Media and third-party sources now affect release identity.

The release workflow builds candidates only; tag pushes no longer publish. The
new dry-run promotion command requires complete current release gates and attended
acceptance containing the exact ZIP hash. Publication is an explicit later action,
using those bytes and their recorded commit. No tag or public release was created.
Frozen-launch and clean-folder validation is still pending at this checkpoint.

## Completed startup, stall and frozen checks

Final renderer executable C925 (native aef6d4465cd) passes12 full-window starts,
3 per game, scale4/CRT and correct native height. All requested completed GL
images exist and each repeat matches its first run. The116-patch export exactly
reconstructs tree de7f57623fc201460b2b6a3b8feed5ac6821eb5c.

The100ms consumer stall recovers and matches3 completed control images. The
1500ms stall with an1804-frame stop finishes emulation before all GL captures,
which the harness correctly rejects. Extending that run to2404 exposes a stream
timeout at1829:16MiB queue,750ms measured wait. A5000ms stall fails at1607, with
zero consumer bytes during a765ms wait. No watchdog threshold was increased.
These are successful negative controls, not successful renderer recovery.

The first extracted frozen package launches all four games using its own copied
ROM/runtime paths with PATH restricted to Windows directories and force off.
Each gives3 completed GL captures and a clean WM_CLOSE exit. The next package
also passes all8 menu/settings images, setup health and actual support output:
3 joystick entries and complete MAME input/binding text. This uses the existing
Windows installation and GPU drivers, not a clean user profile or attended race.
The final source-bound suite follows these component checks.

## Update and support corrections

Importing an older installation previously overwrote existing NVRAM/cfg/ctrlr
files despite claiming preservation. It now fills missing files only; tests retain
newer calibration, scores and bindings. The real Windows updater test covers an
apostrophe in the path, unchanged rig/ROM files and rejection of a ZIP changed
after validation. Corrupt/unsafe/incomplete archives are rejected before copying.
Windows PowerShell initializes its own module path; inherited PowerShell7 paths
previously hid required commands. CI additionally exposed short8.3 paths expanding
to long paths during cleanup. Resolve both compared paths consistently, including
the running-process check. The corrected test passes locally; fresh CI follows.

Frozen GUI executables have no usable standard-output stream for support JSON.
The joystick dump now has an explicit output file. The Lua input dump searches
the packaged source directory too. Support collection disables physical force
and rendering experiments and uses the requested game's controller mapping.
Setup exposes read-only health JSON and an explicit support-output CLI for
repeatable package testing. Full runtime packaging also includes MAME's COPYING
and licence texts, BGFX assets, and the pinned toolkit MIT licence.

## Further force stop-command finding (not implemented at this checkpoint)

Both driver adapters condition signed raw bytes before the output adapter checks
the reserved-128 neutral value. Exotica gain800 can turn it into-127; V-Unit
slew/clamp can similarly turn it into ordinary force. The pinned
[Endprodukt handler](https://github.com/Endprodukt/FFBPluginRacerMAME/blob/7e95f65cab18109cda6b6d0da8ab4c210f3c9c12/Game%20Files/MAMESupermodel.cpp#L1313-L1324)
normalizes neutral before gain. The retained Exotica drive has4616 raw writes,
range-49..36, and zero-128 samples. This source bug is not an observed explanation
for the Fanatec report.

A local draft normalizes-128 before conditioning and resets driver slew history.
ROM-free tests preserve61200 ordinary-command vectors and make240 neutral vectors
zero;216 of those previously yielded nonzero adapted force. It will be integrated
as a separate fix after the currently running renderer/release baseline checks.
No FFB gain, polarity or physical-feel change is inferred from these vectors.

Current CI34102126889 at942d674 passes all four jobs (Windows/Linux harness,
native helpers and Mesa GPU fixtures). The12 startup runs hold99.9777..100.0211%
emulation during frames900..1650 before requested GL captures. Callback p99 is
18.3..25.6ms; worst38.8ms. This bounded interval does not establish display latency
or every driving/selection transition. Renderer proof233 ZIP entries were hashed
and verified on extraction. See `results/proof/2026-09-07-release-hardening/`.


## Complete renderer baseline and subsequent force/upgrade fixes

The C925 candidate at source942d674 completed all automated stages: seven recorded
driving regressions, five fresh-seed boot/replay persistence checks, three V-Unit
pause menus, 24 GPU quality fixtures, both exact captures at100.0000%, and the
frozen package's four game boots/eight UI pages/setup health/support output. Its
ZIP SHA256 is23414805df1bb51c1529257a5463b9d5a386cac209ffd313b87614d6a10fb4be.
The gate remains NOT READY with39 attended/shared items pending. Recorded timing
intervals stay near100% emulation, but one World callback reaches66.73ms; this is
not proof of stutter-free presentation. Full evidence is retained under
`results/proof/2026-09-07-release-hardening/release-942` before subsequent fixes.

Native5bb965763b1 integrates the neutral-byte correction in both driver families.
The same normal-command formula survives61,200 representative vectors; all240
neutral vectors become zero, including216 formerly nonzero outcomes. Driver slew
history resets; downstream smoothing still applies to zero. No default gain,
polarity or force profile changes. Built binary9D8 and the117-patch reconstructed
tree are recorded in AGENTS/session notes; full new runtime validation follows.

Older released ZIPs retained dinput8.dll, which automatically hooks the process.
Copying a current ZIP over such an installation could leave both old and built-in
force implementations present. The updater and first new launch now move only
two verified historical hashes into unique backups under rig/update. Unknown,
redirected or unreadable input DLLs are preserved and block the operation. This
also covers manual ZIP overlay and old updater versions that cannot run new
migration code. Both actual historical binaries were hashed/moved in isolated
folders and backups compared exactly; neither DLL was executed. Real PowerShell
helper tests cover migration and unchanged personal files. Process enumeration
uses typed64-bit handles and canonical image paths, tested against a real Python
child without touching any game. All98 Python tests pass at e4384ec.


## Windows CI correction before final acceptance

The new proxy-retirement check failed on the GitHub Windows runner's short-path
alias: it compared a long install prefix with a short file path. CI34105177890
correctly rejected this at e4384ec. Commit24cc1a2 canonicalizes the ZIP, install
and update-work paths in Python before generating the PowerShell helper. All four
CI34105656916 jobs pass, including the real migration test and native/GPU checks.

The e438 runtime run is explicitly cancelled/superseded after its frozen package,
two USA cases and World2.4 passed. Its Python runner stopped and its owned emulator
received a clean WM_CLOSE; no physical output was active. The remaining partial
Germany data is not accepted. The new clean3720 candidate restarts the complete
suite; both old ZIPs and the actual CI failure remain available. See
[the morning guide](../RELEASE-MORNING.md) for the attended work still needed.


## Confirmed public-access gap

GitHub reports the repository PRIVATE and authenticated access shows latest v0.3.7.
The actual anonymous latest-release endpoint returns404. The updater already reports
this as a private/missing-release error; there is no silent "up to date" claim to
fix. Its public download path cannot make private releases accessible to ordinary
players. Public hosting needs a maintainer decision before release: reviewed public
source repository or a separate public distribution destination with corresponding
client/workflow changes. No visibility change, token distribution or public release
was performed. The read-only response is retained in release-access.json.


## Completed 9D8 baseline and portable source identities

The complete9D8/3720 runtime suite passes, including all174 sampled completed GL
frames in the three full old/new driving comparisons (USA43, Germany78, Off Road53
at401 rows). The actual107MB candidate ZIP also passes the real Windows updater:
all1,616 installed file hashes match, sample existing rig/ROM-directory contents
survive and the recognized historical proxy is preserved exactly in its backup.
No legacy plugin or emulator was executed during that upgrade rehearsal.
The288-entry runtime archive and33 proof files were verified from committed Git
blobs under `results/proof/2026-09-07-release-hardening/release-3720`.

CI34102127057 successfully built the older942 source from upstream plus exported
patches. Its downloaded ZIP and all1,614 file hashes match its manifests. Its
executable is different and was never run or deployed as the final candidate.
Inspection exposed a metadata bug: Git checkout line endings in LICENSE and the
profile example changed the source identity despite the same committed text.

Commit7cb6751 normalizes the remaining known text inputs, including CSV/config/XML,
profile examples and extensionless licence/version files. Binary fixtures preserve
every byte; meaningful licence edits still invalidate identity.100 tests pass.
CI now exports the whole source identity on both Windows and Linux so every input
hash can be compared with the maintainer checkout. Final packaging and standard
release gates will use the corrected identity; prior reports stay unchanged.
The native executable/shaders are unchanged, so the174 binary-bound GL comparisons
remain valid component evidence. Public access and attended acceptance remain open.
