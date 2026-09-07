# Overnight release hardening

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
