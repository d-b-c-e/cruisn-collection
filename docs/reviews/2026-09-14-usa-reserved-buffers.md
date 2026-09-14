# USA extended rendering: reserve model buffers

The USA host renderer can avoid repeated buffer growth while preparing each
model. Two bounded reservations allocate enough space for its projected vertices
and potential output polygons. Model limits remain 256 vertices and 1,024
polygons; geometry, C31 arithmetic, palette lookups, culling and command order
are unchanged. Buffers retain their existing lifetime and failure behavior.

The matching live comparison improves measured 3× driving speed from 96.58% to
97.90%. This is a useful, modest gain; full-speed acceptance remains open.

## Selection and validation

Saved-scene screening compared three approaches before choosing the simplest:
reserving buffers gave a repeatable improvement; caching converted per-vertex
coordinates was slower; reusing projection storage across successive objects
provided little additional benefit and was slightly slower in the lighter
sample. The latter two remain local prototypes and are not in the native build.

A separately frozen baseline and successor reproduce complete ordered output
bytes at 1×/2×/3× for four actual USA scenes (3501, 4001, 4501, 4901). Both cold
and warm model caches are exercised by the analyzer. All counters, object
identities, materials and quad words remain exact. Three focused strict C++11
tests pass: USA model, host and future-section helpers. No unrelated Python or
four-game suite was repeated for two allocation-only lines.

Five alternating rounds, each processing a scene 80 times, give these medians:

| Saved scene | Baseline | Reserved | Reduction |
| --- | ---: | ---: | ---: |
| 3501 | 4.369 ms | 4.020 ms | 7.99% |
| 4001 | 7.484 ms | 6.411 ms | 14.34% |
| 4501 | 2.391 ms | 2.321 ms | 2.92% |
| 4901 | 2.264 ms | 2.106 ms | 6.96% |

These measure future collection, scene assembly and the benchmark's unchanged
output hash, not GPU presentation or game speed. Legacy hash equality screens
the timed repeats; the separate full-byte output comparisons establish geometry
equality. The first qualification compile rejected misleading indentation in
the old local benchmark under strict warnings. Its failure is retained; the
corrected harness puts the independent statement on a separate line.

## Live qualification

The separately built baseline/successor pair preserves all 5,012 recorded inputs,
original native images, 3,211 camera samples and 9,633 actual ADC reads/timestamps.
All 16 completed images are exact on the current 3440×1440 monitor. Every
non-timing scene field matches, including cache misses and ordered quad hashes.
Physical FFB remains disabled.

Over frames 3500–5000, the identical 25.894 seconds of emulated driving take
26.810 seconds on the baseline and 26.450 seconds on the successor: 96.58% and
97.90% respectively. Total scene preparation falls from 3.190 to 2.880 seconds
(9.70%); total measured scene callbacks fall from 3.549 to 3.243 seconds.
Whole-run MAME averages are 98.94% and 99.36%. The boot/menu portion of that
average must not obscure the remaining driving slowdown. This is one matched
A/B, not a confidence interval, uninstrumented measurement or final 4K pass.

Native `c8b350ca75ad3f8330b212c7d459ad28fe700ba1` is frozen at
`build/candidates/c8b350ca75a/vunit.exe`, SHA256
`5f348ed54a8a79274c3577362e948f67505fbee395b6e4abe0f72ee90c3cdd96`.
The 198-patch export reconstructs tree
`0dcd47d9d283f95b4a9bf2f5db53917e514718d2`. The live baseline is nativeb704.

Local evidence: `results/diagnostics/usa-future-render-20260909/`, specifically
`vertex-reuse-screen`, `buffer-reuse-screen`, the retained failed
`reserved-buffers-final`, accepted `reserved-buffers-qualified`,
`reserved-control`, `reserved-candidate`, `reserved-buffers-live.json` and
`reserved-buffers-native-export.json`.
Raw ROM and model resources remain local. Personal native87d and public v0.5.0
remain unchanged; no deployment, hosted CI, menu removal or release occurred.
