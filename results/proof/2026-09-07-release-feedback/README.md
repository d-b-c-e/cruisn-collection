# September7 release-feedback evidence

The final source/native checks pass. Physical output was disabled throughout.
This does not certify physical steering direction, comfortable torque, all-gear
Off Road/Exotica behavior or SimHub/Buttkicker response. All43 attended/shared
release requirements remain pending; no public release was created.

Native f2e5b63dd72, SHA256:
`80688f753070bffe5e55654fed1fd7ffdbd1158acd978e44c9a2a660b40fba57`.
Source identity:
`9eeaefe1defee4ac06ea198a1ea192499ab6785abe0c684774a9b504f642d7cd`.
Local package at clean commit bb62a22:
`CruisnCollection-v0.4.0-rc2-20260907-170505.zip`, SHA256:
`e8847b70fc9436a23aa38ffdb2f2756009c040c6acbaf7bff577a42a947224f8`.
Later documentation/evidence commits do not change that product source identity.

- Seven complete replay cases pass inputs/images and live UDP plus independent
  memory probes. World/Exotica force gating matches the independent state samples.
- Five fresh1800-frame boot/replay cases preserve free play, including Off Road's checksum.
- The actual frozen settings reader confirms CRT on, full widescreen, scale4,
  per-game experiments off and no personal rig. The ZIP contains1632 checked files.
- The extracted ZIP passes four neutral game boots with12 completed GL captures,
  eight launcher pages, setup health and support diagnostics. This used the current
  Windows installation; it is not clean-profile or attended gameplay acceptance.
- 113 Python tests and all four CI jobs pass. CI34164817060's Windows/Linux identities
  match every217 local input hashes. The121-patch series reconstructs the native tree exactly.

`derived-evidence.zip` holds160 derived files, including CSV/UDP captures, bounded
probe scripts, original reports, CI receipts, packaging manifests and the preserved
New York3x/+12 guest-fatal log. Its exact bytes are indexed in `archive.json`.
No ROMs, program/RAM dumps, NVRAM or personal controller configuration are included.
Original recorded drives and the complete screenshot sets remain local. The archived
replay reports record their comparisons; this archive alone cannot rerun gameplay
or independently recreate the pixel comparisons.

Run `python results/proof/2026-09-07-release-feedback/verify_archive.py` from the
repository to verify every archive hash and recompute all seven telemetry and four
force-gate verdicts using only the archived data/analyzers. No emulator or wheel is used.

The New York experiment's crash cause remains unresolved. Nonzero World motor
commands after race end are independently reproduced with distance disabled; the
new force gate suppresses them, but the original observed oscillation's lost trace
cannot establish that this was its only cause.
