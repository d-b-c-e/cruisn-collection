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
14 checks at seven independently verified3x viewpoints.

All fifteen serial trials and all seven defaults now pass on this candidate.
The trials isolate cache-only, depth-only, both, off, verify and repeat modes,
cover 1/2/3x, Hong Kong and three full Amazon runs. Across 45,354 scenes, all
542 paired 4K images, ordered geometry/material identities, sampled original
resources and camera/actual ADC times match their declared controls. Verify mode
compares 10,204 complete source results and 29,794,639 exact depth decisions.
Full original-context captures cover 7187–7188; earlier failures remain retained.

In the same-candidate Amazon comparison, mean scene CPU work falls from 3.448 ms
with both strategies off to 2.585 ms with both on (repeat 2.602 ms). Measured
emulation speed rises from 87.67% to 91.89% (repeat 91.32%). Without GL captures,
the prior written-page control measures 88.42%, versus 92.45% with both strategies.
Regular raw snapshots every 60 frames remain enabled in these measurements.
The initial roughly 49 ms CPU/25 ms GPU material upload is still unresolved;
these figures do not establish smooth or full-speed gameplay.

The public proof at `results/proof/2026-09-10-exotica-cached-depth` recomputes
selected CPU/clock measurements and validates the hash-bound build, coverage
and seven-default receipts. Full raw geometry, resources, routes and images
remain local; the published verifier does not independently reconstruct them.

Accepted defaults now belong to native7b432/SHAd16e8b7a. Personal Stream Deck stays
v0.5.0/SHA87d04de4. No deployment, release, hosted workflow, physical FFB, World
tuning or experiment removal. Next work remains initialization, private depth and
scene insertion, occlusion/handover, and active unsubmitted ground eligibility.
