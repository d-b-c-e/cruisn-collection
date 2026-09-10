# Zeus wider-depth and future-packet contracts — September 10

The wider-depth shader and a separate future-geometry packet now pass standalone
checks. They are not linked into MAME. Native25228 and personal v0.5.0 remain
unchanged; this milestone adds no game-visible drawing-distance feature.

## Why a larger depth target needs explicit clear semantics

The compatibility mirror preserves original depth comparisons, including the
measured D24 quantization ties. It maps saturated geometry and cleared depth to
the same sentinel. That policy cannot order farther geometry correctly.

The separate `wide_fragment` helper preserves the measured D24 codes for ordinary
geometry up to the old limit, then maps actual farther depths into the larger
range. Geometry uses a divisor of2^26, leaving room for the captured3x scenes.
Explicit polygon clears remain at1. Shader saturation is reserved for original
input outside the new range; future packets reject such geometry explicitly.

Original command captures also show fast clears at0xffff00. A test for exactly
0xffffff would miss those. The proposed native producer must tag command type3
explicitly with bit1024. Its depth-range initialization maps by2^24, preserving
relative clear values and zero. Direct type4 depth writes retain actual-depth
meaning. The helper does not infer command type from a game's numeric constant.

The original shader ignores the new bit, but the native producer has not yet
been changed to emit it. This remains a proposed extension of clear semantics,
requiring original-only live controls and complete scene ordering checks.

## Independent checks and their limits

The actual material shader passes292 synthetic cases/636 ordered steps across
internal1x/4x and pages0/400. These include all six orders of three distant
surfaces, near/far occlusion, explicit and range clears, raw depth writes,
depth bias, no depth writes, transparency and boundary values. RGB and stored
depth are checked against an independent CPU calculation. Exact RGBA is checked
against the original material shader with depth admission decided by that CPU
calculation and the reference GPU depth test disabled.

The first run expected alpha255 for a blend but observed254, with exact RGB.
That failed reference is retained. The final check uses the original shader's
actual fixed-function blending, preserving exact RGBA comparison without adding
a pixel tolerance. The promoted helper reproduces every draft result.

`zeus_wide_packet.h` defines XWD1 with owned materials, bounded geometry and
explicit page/multiplier/mode. It excludes raw writes, clears, unsupported
non-depth-tested primitives and depths outside the new range. XMD1 remains the
separate current-margin/D24 contract. Native round-trip and corruption checks
pass, and an independent Python decoder validates the native synthetic packet.
Both implementations accept14,696 previously captured future polygons from five
Amazon/Hong Kong snapshots. This does not certify their real material binding,
insertion order or appearance.

Final local checks pass340Python tests with no skips,47native helpers and132
commands at497-file source identity
`ed1d0b8cac743339a8aab483b37abab4d6b758c0a0087bef8c250e50ce319287`.
[Public proof](../../results/proof/2026-09-10-zeus-wide-depth-contract/README.md)
recomputes source identity and checks hash-bound execution/comparison receipts.
Raw game resources stay local. No native build, live wider-rendering, performance,
default-suite or deployment acceptance is added by these standalone checks.

## Next native work

First add an explicit private wide-original mode and source-tagged range clears,
keeping existing compatibility mode strict and displaying the original target.
Compare original routes, resources and images, and independently inspect the
private page after its clear and original drawing commands.

Then insert XWD1 before the first ordinary original model, after finishing and
flushing buffered sky copies. Three captured joins establish that position only
for those scenes. Compare1x/2x/3x and repeat, including original/future handover,
transparent ordering, lifetime, performance and defaults before any deployment.
Future descriptor opacity often starts low; simply making every object opaque
would need a separate handover solution. Neither that problem nor the original
USA timing stall is resolved here.
