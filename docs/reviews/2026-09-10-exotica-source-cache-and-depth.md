# Exotica source caching and early depth — September 10, 2026

Two separate opt-in optimizations reduce repeated CPU work in the diagnostic
future-scene path. Neither draws extra scenery or changes product defaults.

`--exotica-host-source-cache off|on|verify` reuses the immutable-ROM descriptor
result while checking every RAM dependency and the current loader frontier.
RAM material-bank changes rebuild it. Current texture/palette colors and model
bytes remain outside the cache. Each machine instance and ROM bank owns its
cache identity; external ROM mutation requires invalidation and is unsupported
in the live diagnostic mode. Partial-loader exclusion and terminal states are
checked explicitly. Verify mode compares every declared source/section field
against a fresh full build on every scene, without relying on fingerprints.

`--exotica-host-early-depth off|on|verify` computes exact C31 camera depth before
the full rotation matrix. Objects beyond the existing chosen distance limit
skip the matrix calculation. Verify mode still prepares every selected supported
object and checks the depth, including objects subsequently rejected. It does
not increase the distance limit. Recording environment values preserve both
choices; absent controls retain the earlier algorithms. Geometry context bytes
remain unchanged because these strategies have identical intended outputs.

Native commits `d19f1531313` (cache) and `7b432126ffe` (depth) are separately
reviewable. The combined candidate is separately built and pushed at
`7b432126ffed9c15fbdf7356a9ad8b6625d74231`, frozen in
`build/candidates/7b432126ffe/vunit.exe`, SHA256
`d16e8b7a7c4f4ed377402017c4a7814d2c87d953f9def0872ff95b37d0fd964e`.
The166-patch export reconstructs tree`0920fde0921f9791e881dbe5b5c532532919f9c1`.
Final321 Python tests/no skips,41 native programs and115 local commands pass at
source identity`6f8fdd5380d255bbcf0a064e769d2b61b707fa3db57a6422a0a89a919655dbab`.

Canonical helper checks pass35,724 descriptors across seven captured snapshots,
686 synthetic ordinary/partial frontiers,693 rejected mutations and seven valid
changed material bindings. Actual snapshots are bank0 and not partial; synthetic
coverage is not a live observation. Early depth matches70,000 arbitrary C31/flag
cases. Both early modes match45,340 ordered quads and all instance bytes across
14 checks at seven independently verified3x viewpoints. Runtime performance,
full-route resource/image equality and seven defaults are still pending.

The previous local cache benchmark suggested useful savings, but is not a live
runtime measurement. Fifteen planned serial trials isolate cache-only, depth-only,
both, off, verify and repeat modes, cover1/2/3x, Hong Kong and full Amazon, then
run all seven defaults. Source is frozen during these checks. Keep failures and
separate reference intervals; all full original-context captures use7187–7188.

Last accepted defaults remain nativeac10/SHA9daeb048. Personal Stream Deck stays
v0.5.0/SHA87d04de4. No deployment, release, hosted workflow, physical FFB, World
tuning or experiment removal. Next work remains initialization, private depth and
scene insertion, occlusion/handover, and active unsubmitted ground eligibility.
