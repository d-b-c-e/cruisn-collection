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
