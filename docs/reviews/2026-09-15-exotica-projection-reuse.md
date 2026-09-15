# Exotica projection reuse: verified CPU saving, modest live gain

Follow-up: the [covered-window correction](2026-09-15-exotica-owner-window.md)
restores approximately full speed in all three measured windows on this same
candidate. The low absolute speeds below include a replay harness window-sizing
regression. The matched CPU assembly saving remains valid.

The model decoder invalidated prepared projection constants on every texture
command. These commands change texture/mode and the UV exponent, but only the
exponent changes projection constants. Retain prepared values when that exponent
is unchanged; still refresh them on exponent changes and at the first polygon
of each model. Texture selection, UV offsets, material state and vertices are
always processed from the current command.

The change is confined to `native/zeus_model.h`, used by host scenery and private
model endpoints. It changes no game memory, rendering policy, draw distance,
FFB or release defaults. Original MAME device rendering is unchanged.

## Saved-data qualification

Three alternating rounds of200 complete assemblies compare frozen pre-change
headers with the candidate, using current saved operands. Every ordered instance
and quad byte, and every non-timing counter, matches the saved actual output.

| Native scene | Reference median us | Candidate median us | CPU reduction |
| --- | ---: | ---: | ---: |
| 5072 | 1988.870 | 1953.180 | 1.79% |
| 5644 | 2359.770 | 1961.040 | 16.90% |
| 7187 | 2687.070 | 2327.210 | 13.39% |

These are complete CPU assembly measurements, not game-speed improvements.
The two busy scenes benefit more because their decoded models contain more
texture commands. The source copies, compilation output and all individual
measurements remain in local `projection-reuse-screen`.

Three focused native tests pass: model decoding, original-model endpoint and
scene endpoint. New cases compare same-exponent texture/material changes and
changed-exponent projection against independent fresh projection calls; an
invalid exponent must still reject after a valid polygon. Existing near-plane,
material, unsupported-input and state-reset checks remain.

The canonical compiled analyzer additionally matches240 original models and
3,255 ordered original quads against the independent Python decoder and actual
native command bytes; all11 original/replacement endpoint pairs are byte-exact;
and three complete scene instance/quad outputs match their saved actual bytes.
No geometry cache crosses models, frames or resource updates.

## Native candidate

`f0cfbd005c87f4f40b81381227785acfbfb6485c` is separately built and frozen,
SHA256 `30d3472d471f77b5cd1ff6cb1a30cf0cc91e58e32d64d1e491816644960a5fa4`.
The219-patch export reconstructs `8e15b541e2d88d2c67b16e49062d50034f1f86ac`.
The personal87d executable, force profile and publicv0.5.0 remain unchanged.

The fresh same-settings pair completed8,860 Amazon inputs at3840x2160.
Both runs omit large resource/color/depth readbacks. All camera/ADC, lifetime,
admission, original-model and GPU endpoint receipts match exactly, including
30,308 accepted marked preparations with zero rejections and282,036 GPU pairs.
All22 saved original/replacement model binaries match. Every deterministic
scene/material/GPU field matches, including geometry fingerprints. The two
completed3840x2160 CRT frames6538/6545 are byte-identical.

Summed future assembly falls16.5483 to15.2928 seconds (7.59%); active assembly
falls1.9954 to1.9022 seconds (4.67%). The fixed noncapture windows show modest
improvement, while absolute performance remains well below full speed:

| Native frames | Control speed | Candidate speed | Host-time reduction |
| --- | ---: | ---: | ---: |
| 3501-5000 | 80.79% | 81.56% | 0.94% |
| 5701-6400 | 71.99% | 72.89% | 1.23% |
| 7001-8848 | 78.71% | 79.14% | 0.55% |

This is one matched pair, with correctness journals still enabled. It supports
the measured CPU saving, not precise causal FPS predictions, full-speed parity
or an uninstrumented/physicalFFB release verdict. The remaining bottleneck needs
attribution rather than another identical timing run.

The initial local checker assumed cadence relative to the first requested frame
and copied VUnit's window dimensions. Actual Zeus captures use global multiples
of7 and full3840x2160 output. The corrected checker calls canonical
`requested_frames` and qualifies the two actual requested frames. The failed
checker is retained; no game was repeated to fix the analysis. Prior prose and
local plan described three frames; two is the completed and accepted scope.

Local evidence under `results/diagnostics/exotica-amazon-20260909`:
`projection-reuse-screen`, `projection-reuse-checks`, `projection-reuse-actual`,
`projection-reuse-export.json` and the `projection-reuse-live-*` pair.

Final local reports: `projection-reuse-live-qualified-v2.json` and
`projection-reuse-live-cost.json`. No deployment or release was performed.
