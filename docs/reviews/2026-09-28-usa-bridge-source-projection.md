# USA Golden Gate: exact pre-admission source projection

The far-left red bridge has a source-qualified projection limitation before one
of its members joins ordinary continuous 3× drawing. At the actual USA C31
host-scene read for frame **10473**, future object `0x800a0040` is ready, but
the ordinary 240,000-unit projection rejects it. The existing gated partial
far-coverage path reconstructs three of its quads without changing any of the
ordinary ordered quad words. This is stronger than the earlier end-of-frame
10470 inference. It remains one object and one source scene, and does not
prove that all bridge pop-in is caused by this projection limit.

## Exact-hook qualification

A read-only Lua tap observes program read address `0x40` at C31 PC `0x81`,
the same guarded scene hook used by frozen native `f762e01d63b`. The replay
uses the same Golden Gate recording, stops after 10,477 inputs, physical
2560×1440, CRT on, literal FFB0 and continuous 3×. Its raw report **PASS**es
input/native, display watch and owned worker shutdown. The tap receipt names
frame 10473, PC `81`, address `40` and USA. Source-time program RAM, C31
internal RAM, textures and palette have checked extents and hashes.

The captured frame-10473 native host scene has the same time, page 513,
3,706 quads and ordered fingerprint `df956ddad1403f87` as the prior detailed
trace replay. Independent reconstruction from this exact source RAM and the
saved immutable ROM reproduces all six counters, every quad count and that
fingerprint. The first counter is **264 resident pending + 4,204 ready future
= 4,468 total candidates**; the native journal labels only the resident part
`pending`. An initial checker incorrectly compared 4,468 to 264 and failed;
its raw `usa-bridge-source-tap-raw-v1.json` is retained. Corrected v2 **PASS**es.

At this exact scene the target is one ready future descriptor among 4,204,
with zero unbound/deferred definitions and zero new uploads. The earlier
detail trace first submits its quads at frame 10475. Ordinary projection has
72 whole-object projection rejections in the full scene and emits no target
quads. Partial coverage reduces that counter to zero and emits 76 additional
quads in the full scene, including three from the target at native
x −61..−42, y 144..185. All 3,706 ordinary 16-word quads remain byte-identical
and in their original relative order. This initially was an **offline
counterfactual** from exact source operands. A separate, matched 10,477-input
live replay with the gated option on now **PASS**es input/native, stable
physical1440 display and owned shutdown. At source10473 its native scene
submits **3,782** quads with fingerprint `cad18ecde19865f8`; independent
source reconstruction matches the full count, all six counters and ordered
fingerprint exactly. The original and candidate frame clocks and inputs match.
This qualifies the native candidate geometry at this source scene, not a
candidate packet-to-completed-pixel attribution or a visual acceptance.

The separate [matched completed-image trial](2026-09-28-usa-bridge-farcoverage-trial.md)
shows earlier red structure in 11 far-left 1440p views with center/right
unchanged. Its color screen finds candidate-only red at every sampled point.
Those live pixels and this source-time object are not yet joined one-to-one.
Other bridge members have different admission histories, and trees or authored
composition may still determine the sparse appearance. Neither 4K, another
USA route, frame pacing nor physical FFB has been qualified for this option.
No native/product renderer, personal installation or release changed.

The source-hashed local evidence is under
`results/diagnostics/race-transitions-20260916/`:
`usa-bridge-source-10473-prepared` (preflight only),
`usa-bridge-source-10473-run` (raw replay PASS),
`usa-bridge-source-tap-raw-v1.json` (counter-label checker failure),
`usa-bridge-source-tap-v2.json` (corrected exact-source PASS),
`usa-bridge-coverage-10473-prepared` (preflight only),
`usa-bridge-coverage-10473-run` (raw replay PASS), and
`usa-bridge-candidate-scene-v1.json` (native/offline candidate PASS). The tap is
`lua/usa_source_scene_capture.lua` and the checker is
`harness/screen_usa_bridge_source_tap.py`; candidate matching uses
`harness/qualify_usa_bridge_candidate_scene.py`. The existing 1.5 GB detailed quad
trace was source-hashed by the earlier activation report and was not rescanned
for this gate.

Next, attribute a candidate completed pixel to its new source packet in a
bounded interval, then assess member-by-member visual transitions and cost.
Do not broaden the global limit on the basis of a single projected member.
