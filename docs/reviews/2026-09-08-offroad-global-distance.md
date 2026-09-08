# Off Road: global far and projection trials

The bounded2× and3× trials run through the full6,000-frame recording with the
original camera path. They produce a small visible extension in this El Paso
sample;3× adds no sampled pixels beyond2×. These are diagnostic Lua experiments,
not launcher options or an accepted native renderer change.

## What changes

The1.25× checked patch changes only the initialized far culler47,296→59,120.
It preserves the63,680 clipping plane and63,679 projection-table ceiling.

The larger trial keeps three limits coherent: object far distance, geometry
clipping and the reciprocal-table ceiling. It modifies the two initializers,
their two active copies and the ceiling during frames1800..5990, then restores
them.2× uses94,592 /127,360 /127,359;3× uses141,888 /191,040 /191,039.
The reciprocal tail is supplied by guarded reads, leaving ROM/resource bytes
untouched. It uses the exact eight-decimal rational generator documented in
[the adapter notes](2026-09-08-distance-next-adapters.md). No model/level allowlist
is involved.

All candidate projection instructions are checked, and a replacement requires
the expected PC, table-base register and actual indexed address. The first broad
ROM-tail probe mistakenly attributed a resource read atPC1EA8 because AR0 still
held the table base; checking the effective indexed address separates that read.
The failed run is retained. A second stopped when the game reinitialized its
active limits at a menu/race transition. Including the guarded initializer words
fixes this lifecycle requirement; write logs independently identify the original
1821/1823 store instructions at frames1988,2648,2650 and3905.

## Full-run evidence

| Trial | Extra far admissions | Projection reads | Upper clamps | Sampled GL changes |
|---|---:|---:|---:|---|
| Original | 0 | 6,553,303 | 581 | 0/42 |
|1.25× culler only | 9,011 | 6,852,864 | 581 | 15 pixels in3/42 |
|2× coherent | 16,971 | 6,991,546 | 0 | 220 pixels in5/42 |
|3× coherent | 16,977 | 6,991,558 | 0 | same42 images as2× |

The maximum observed projection index is95,085 at2× and95,782 at3×. Eleven
verified consumer PCs use the extended table at2×. The extra3× admissions therefore
do not establish useful extra rendering. Completed captures are512×451 and are
sparse100-frame samples; they do not establish4K quality or eliminate pop-in.
The most noticeable difference is distant scenery near the center at frame4400.

All trials keep recorded frame inputs/emulated time and all4,191 camera samples
equal to the original. Actual ADC frame/value/PC events also match; their
timestamps differ, so the stricter motion verdict remains FAIL. Changed original
native-image comparisons also remain FAIL. The recording contains menu setup and
a short synthetic El Paso drive that leaves the course and slows; it is not a
complete attended race or broad level coverage. A fresh drive remains useful.

The1.25× read-only profile runs near100% emulation. The more expensive full Lua
trials measure94.2059% for the unchanged control,54.2028% at2× and53.1330% at3×.
Those figures include instrumentation on millions of reads, including a guarded
ROM tail. They are not acceptable product-performance results, and do not show
what a native adapter would cost. No option is being promoted on this evidence.

Three focused tests validate patch composition, explicit bounded trial settings
and rejection of inconsistent/truncated counter traces. The full147-test Python
suite passes. Native8b151aa9c2f/SHA638 remains unchanged. Runtime evidence is in
`results/diagnostics/offroad-global-20260908`, including original failed trials.

## Remaining checks

Matched captures at frame4400 are being collected to compare original geometry,
draw order and texture/palette resources. Candidate repeatability, a low-overhead
implementation and broader attended driving are still required before launcher
promotion. Do not describe the extra admissions alone as corrected scenery.
