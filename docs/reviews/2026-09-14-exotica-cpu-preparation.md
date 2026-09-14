# Exotica CPU preparation: exact arithmetic and identity lookup

Three bounded changes reduce saved-scene preparation cost while retaining the
same ordered instances and polygon bytes. The GPU batching experiment is
reverted in a separate native commit because its full-drive test showed no
speed benefit. Full Amazon correctness passes; improved whole-game speed is not
demonstrated.

## Changes

- Convert normal-range C31 values directly into their exactly representable
  IEEE float bits. Subnormal values and the one overflowing negative encoding
  retain the previous arithmetic, including rounding and error behavior.
- Step between adjacent normal IEEE values with integer bits for conservative
  bounding intervals. Zero, subnormals, extreme normals, infinities and NaNs
  retain `std::nextafter`. This does not widen acceptance or relax clipping.
- Reserve a per-scene hash set for the exact 64-bit `(entry, source)` identity.
  Source traversal, callbacks, duplicate rejection and output order stay the
  same. There is no cross-scene geometry or resource cache.

The numeric and lookup changes have separate collection and native commits.
They affect Exotica's host preparation; they do not change other games' geometry
codecs, game simulation, FFB or release defaults.

## Offline evidence

The reference headers are frozen copies from before these three changes. Three
alternating rounds of 200 assemblies compare full ordered instance and quad
bytes with both that reference and saved native scene output. All non-timing
statistics also match.

| Saved native frame | Reference median µs | Candidate median µs | Reduction |
| --- | ---: | ---: | ---: |
| 5,072 | 2,204.455 | 2,004.145 | 9.09% |
| 5,644 | 2,386.915 | 2,245.870 | 5.91% |
| 7,187 | 2,647.630 | 2,547.340 | 3.79% |

These are CPU assembly measurements on saved data, not whole-game FPS gains.
The earlier isolated trials and their source copies remain available.

Seven targeted test executions pass: numeric tests under ordinary optimization
and `-frounding-math`, plus state, model bounds, scene, model endpoint and scene
endpoint tests. Numeric coverage includes 16,384 C31 boundary cases, 208 IEEE
neighbor cases across four rounding modes, and one million deterministic words.
Boundary checks compare output bits, error numbers and floating exception flags.

## Candidate and remaining validation

Native `f2e08e49d9eeff082b88ca675fcbaff0b1ff6811` is separately built and frozen,
SHA256 `680f1cbf6f8314abf9023209caba4ca6e4472027846f3f3b3b4c74862864173b`.
The 214-patch export reconstructs tree
`ddba53361125d38bc5e3bf85d5976a307c9b665d`. It includes the batching revert and
three independently committed CPU changes. Personal native87d is unchanged.

The full Amazon validation passes all 8,860 original inputs, camera/ADC/lifetime
and admission records, all 30,308 marked endpoint preparations with zero
rejections, and byte-exact endpoint inputs/model/GPU journals against accepted
pre-batching `080f78a2358`. Ordered early geometry and all non-timing scene fields
match. Original/private completed color/depth pages at 5,073/5,645 and all fifteen
completed CRT bitmaps at 6,536–6,550 match exactly.

Summed future preparation falls from 17.456 to 17.026 seconds, and active
preparation from 2.516 to 2.071 seconds. These are instrumented CPU measurements.
The fixed noncapture windows do **not** demonstrate an end-to-end gain:

| Native frames | Baseline speed | CPU candidate speed |
| --- | ---: | ---: |
| 3,501–5,000 | 97.13% | 95.85% |
| 5,701–6,400 | 85.86% | 79.46% |
| 7,001–8,848 | 92.24% | 90.57% |

One pair includes host scheduling, instrumentation and asynchronous capture
costs; this does not establish a causal regression magnitude. Retain the exact
CPU savings without describing them as a gameplay smoothness fix. Do not repeat
full drives simply to seek a favorable timing. Remaining submission/diagnostic
cost needs attribution. Final 4K and broader track acceptance remain open; the
current monitor is 3440×1440.

Local evidence under `results/diagnostics/exotica-amazon-20260909`:
`current-cpu-checks`, `current-cpu-benchmark`, `current-cpu-build.log`,
`current-cpu-export.json`, `full-current-cpu`, `full-current-cpu-qualified`, and
`current-cpu-cost-v2.json`. The initial timing summary rejected fractional
microsecond strings as integers; its failed report is retained, and the corrected
summary uses their actual fractional values without rerunning the game.
Raw game resources remain local.
No deployment, public release, hosted CI or physical FFB was performed.
