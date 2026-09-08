# v0.4.0 release evidence

[Published release](https://github.com/d-b-c-e/cruisn-collection/releases/tag/v0.4.0)
on September 8, 2026. The repository remains private.

- Tag/source commit: `c098290aeaa1f19ca37d7bee56c747cbf51350b5`.
- Native commit: `97600e9597e46ae3c926164e01c1926340fc759d`.
- Native SHA256: `b5ba0021a51a1f9ec50e105dde9c8112cb3c7e4ce71009ce4294841296383ee2`.
- Product source identity: `4c9dd0a3d246f9bfa1160360ad551e3af841da3ecf837200626def487d7eb30d`.
- ZIP: `CruisnCollection-v0.4.0-20260908-000947.zip`, 111,918,111 bytes.
- ZIP SHA256: `fd292b0d4ba4d2a97147c6ffc1fb95407e3891495dfb68fada2f899e3c31ba4a`.
- Proof archive SHA256: `ccd2d8d81680626187dafffd10b2cd57616724148c5731609d1c9cade9a67be2`.

The published ZIP was downloaded again; its bytes match the local tested ZIP and
GitHub asset digest. The release tag resolves to the packaged source commit.
Its companion SHA256SUMS and package manifest are also attached to the release.

## Validation

117 Python tests and all four CI jobs pass at the tagged source revision.
CI Linux, Windows and local identities match across all 217 product source files.
The current native executable passes all seven gameplay regressions, actual UDP
and independent drivetrain-memory checks, World force passthrough and Exotica
cabinet-polarity checks. This includes Exotica's 21 completed GL references.
Measured replay intervals range from 99.9726% to 100.0069% emulation speed;
this is not a certification of GPU presentation pacing on every wheel setup.

All five fresh-save boot/replay checks preserve free play. The frozen ZIP passes
eight menu-page captures, setup health, support diagnostics and four launches
with 12 completed GL captures, using a new folder and no development paths.
Actual update-helper rehearsal preserves user-state fixtures and backs up the
recognized obsolete DLL; all 1,637 packaged file hashes match after update.
GPU quality fixtures and all three V-Unit pause-menu tests pass. Both archived
native renderer comparisons remain **100.0000%** exact (zero differing pixels).
The frozen Display and game-selection screenshots were visually inspected.

The maintainer explicitly signs off the current alpha state. The acceptance
ledger has two reviewed shared checks and **41 explicit maintainer waivers**;
`all_checks_passed` remains false. Unperformed attended tests are not relabeled
PASS. Physical force remained disabled throughout automation. Known World
oscillation/normalization, distance artifacts and incomplete broader hardware/
track/soak coverage remain documented in the release notes.

## Archive and reproduction

`release-evidence.zip` contains 61 derived reports, logs, frozen menu images,
CI source identities, package manifests, acceptance records and the upstream
inspection. It excludes ROMs, RAM dumps, NVRAM, personal rig configuration and
executables. `manifest.json` hashes every entry; run `python verify_archive.py`
from any directory to check the archive and recorded release identity.

This archive preserves receipts, not a substitute for rerunning a game. The full
local runs are in `results/diagnostics/release-v040-20260908`; original recordings
remain unchanged. Reproduce using the archived pipeline commands and your own
ROMs/recordings. The recorded acceptance paths resolve against the original local
run directory; moving the ledger alone does not create portable attended proof.
Older force and telemetry traces are linked from the September 7 proof folders.
