# USA Golden Gate: source of the early red bridge

The continuous 3× candidate shows red bridge pieces at the far-left margin at
completed frame 10500, before the ordinary-distance image does. Three sampled
red pixels now have exact host packet sources. The objects entered the host
submission stream at different times; this helps locate a source-side cause
of uneven appearance, but does not yet prove why the whole bridge looks sparse.

A new bounded replay of the saved 12,212-input Golden Gate drive stopped after
10,502 inputs on the frozen `f762e01d63b` binary, physical 2560×1440 primary
and literal FFB0. It used the same continuous 3× USA controls as the earlier
source capture, but recorded detailed host quads and one completed frame-10500
CRT image. The replay report **PASS**es original input/native comparison,
display watch, detailed host scene validation and owned worker stop. The
completed image SHA-256 is byte-identical to the earlier physical-1440 source
capture (`4d7f4cee…70733`). The earlier source replay's raw report remains
**FAIL** from its since-corrected same-frame host ordering check; its separate
posthoc qualification passes and is not relabeled as a raw pass.

The completed auxiliary prefix selects source frame **10497**, raw page
control **513** (physical page 0). The new 3,710-quad trace and the older
summary share exact ordered fingerprint `6aeaa280929f2a8f`. An independent
isolated raster reproduces the host index of all three screenshot-selected
red pixels over original sky. They belong to three distinct future-list
objects:

| Object | First submitted frame in detailed trace | Packets at 10497 | Exact visible far-left indexed pixels at 10500 |
| --- | ---: | ---: | ---: |
| `0x800a0022` | 9855 | 2 | 649 |
| `0x800a0031` | 10039 | 8 | 2140 |
| `0x800a0040` | 10475 | 3 | 4569 |

All three sampled pixels use palette base 24064 and textured packets. The
individual objects use distinct texture bases. The source object at `0x800a0040`
first submits only 22 emulated frames before the source scene for the saved
10500 image. The other two were already in the host stream earlier, including
before the saved 10200 view where the left ROI gained no new red pixels. The
saved views cannot tell whether those objects were off-screen, occluded by
trees or visually incomplete then. The activation timing is consistent with
staggered future-object availability or admission, **not** proof of a missing
texture or that expanding the far plane alone can make the entire structure
appear at once.

The source-hashed local evidence is under
`results/diagnostics/race-transitions-20260916`:
`usa-bridge-quadtrace-run/report.json`, `usa-bridge-packet-source-v3.json`
and `usa-bridge-activation-v2.json`. Packet-source v1/v2 and activation v1
remain as earlier successful checks; v3 additionally binds the posthoc raw
report, case, binary and completed-image hashes. The first diagnostic source replay and
its raw failure remain under `usa-golden-gate-panel-run`. The prepared-only
plans did not execute a game. The initial one-off activation query failed in
its own print expression after emitting the first object's range; the final
activation report rescanned and verified the entire detailed trace.

These are three selected source objects and one completed 1440p image, not
the full bridge or a motion-quality gate. Other members may be absent, hidden
or authored as sparse distance geometry. The independently found dithered
right-sky panel remains an original game quad. No renderer source, personal
installation or public release changed.
