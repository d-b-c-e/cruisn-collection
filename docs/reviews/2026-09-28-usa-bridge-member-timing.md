# USA Golden Gate: admission timing of two visible bridge members

The two objects independently identified in completed frame 10476 have
different source-admission histories. In the existing detailed quad traces,
the gated partial-far-coverage path first submits object `0x800a0040` at
source frame **10181**, while ordinary continuous 3× first submits it at
**10475**: a 294-frame submission lead. The gated path first submits
`0x800a0042` at **10281**; that object is absent from the ordinary *auxiliary*
trace through its last prepared source frame **10499**. This is a lower bound
of more than 218 source frames for the second object's admission difference,
not proof that the game's original renderer never draws it.

At source frame 10473, the gated path submits three quads from `0x800a0040`
and 25 from `0x800a0042`; the ordinary auxiliary path submits neither.
The [source/packet/pixel screen](2026-09-28-usa-bridge-pixel-source.md)
attributes 1,779 and 779 candidate-only red CRT center samples at completed
10476 to those respective new packets. Thus the early submission has a
measured visible consequence at that frame. It does **not** establish when
either object first became visible during the prior several seconds: trees,
depth, original scene composition and CRT filtering can hide earlier submitted
quads. Nor does it establish a smooth handover or quantify overall pop-in.

The offline census streams the saved 1.5 GB ordinary and candidate detailed
traces once, validates each full-file hash against the prior activation/pixel
reports, and retains the same recording/binary identity. No new game replay,
GPU render or native build was needed. The first checker incorrectly required
both objects to appear in the ordinary trace and **FAILed**. The raw
`usa-bridge-member-timing-raw-v1.json` is kept; corrected
`usa-bridge-member-timing-v2.json` **PASS**es and explicitly represents the
second object's absence through 10499. Both are local under
`results/diagnostics/race-transitions-20260916/`. The source-hashed checker
is `harness/screen_usa_bridge_member_timing.py`.

This strengthens the case that partial far coverage helps the Golden Gate
approach, while the bridge's sparse-looking composition remains a separate
visual question. Keep the option gated until transition, cost, other-course
and physical 4K checks are complete. No installed renderer or release changed.
