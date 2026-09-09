# v0.5.0 release evidence

Published September 8, 2026, following the maintainer's acceptance of the watched
Cheats testing and explicit request for a new release. The repository remains private.

- Release/tag commit: `96006e725d370e7222fe1fb97d751c9cd31cd122`.
- ZIP: `CruisnCollection-v0.5.0-20260908-221432.zip`, SHA256
  `20d1cf67cc7db82fa6cebf494369117e25bf5cf6eae0e8b7d717a55c830d3734`.
  Uploaded asset was downloaded and verified byte-for-byte.
- Native: `4ac6a84b51b4ae549399c81ffe1b9346e2c04758`, SHA256
  `87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8`.
  Its 134-patch export exactly reconstructs tree `007c6ac1f1b6471237241d07275fd57024c19d01`.
- All 297 source inputs: `f4d17d053cbc511b5644abe5f2cc707998a8ca83cae895663d2b427ce6376295`.
- Personal Stream Deck emulator matches the candidate. Previous d52 binary is
  backed up; all 26 inspected personal preference/state files remained unchanged.
  Published v0.4.0 and original recordings remain intact.

## Completed checks

196 Python tests without skips, 14 native helper tests, 10,081 C31 math vectors,
force/T-junction analyzers and 24 GPU fixtures pass in 39 local commands. Hosted
workflows stayed disabled. All seven driving regressions pass, including the full
Germany recording and Exotica's 21 completed GL images, actual UDP versus independent
memory and four force policy/polarity checks. Physical force remained disabled.

All five fresh-seed boot/replay persistence checks pass. Five 4K native-menu cases
open Cheats, stage one action, return, resume, reopen and exit; their input/state/
action traces and sampled completed GL images replay. Native screenshots show the
queue before Resume. The initial 512×451 USA test failed a text-pixel threshold;
that receipt remains. The harness now targets the actual 4K monitor. No emulator
change was needed after this visible-test failure.

The exact 1,726-file package passes factory defaults (CRT on, full widescreen,
scale4, World2.4, force50/CRISP, per-game experiments off), no personal config/ROM/
cheat-database checks, nine frozen pages, setup/support, four default launches,
saved and live World cheats, and 18 completed GL captures. The actual frozen
launcher invokes the new live menu successfully. Windows upgrade, rollback and
re-upgrade match 1,726/1,637/1,726 packaged files and preserve seven synthetic user
fixtures. This is the current Windows installation with development paths removed,
not a newly tested Windows profile or physical wheel setup.

The gate is ready under explicit current-state release authorization. **41 human
coverage waivers remain waivers**, with their limits recorded individually. They
are not new observed passes. World force oscillation/normalization, wider hardware
coverage, New York distance artifacts/crash and broader cheat-effect validation
remain documented limitations.

## Reproduce the numerical checks

```powershell
python results/proof/2026-09-08-v0.5.0-release/verify_archive.py
```

The 183-file, 21,209,662-byte archive includes derived telemetry/memory/force data
and immutable reports/images. The verifier recomputes all seven drivetrain and
four force verdicts, then checks menu/replay, fresh/frozen, upgrade, deployment,
package and downloaded-asset receipts. Native compilation, GPU rerendering and
full emulator playback are not repeated by this archive verifier.

The hashed companion `../2026-09-08-live-cheats/evidence.zip` recomputes five timer,
instruction-restoration and action-journal checks on the same native binary.
Its pending-deployment text is historical. Named finish checks establish timer
writes, not every resulting race-end effect. No ROMs, cheat XML, raw resource dumps,
private configuration contents or emulator binaries are included here.
