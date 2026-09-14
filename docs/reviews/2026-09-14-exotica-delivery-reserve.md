# Exotica: reserve outgoing future geometry

The native future-packet builder knows the exact quad count after scene assembly.
It now reserves that capacity before copying the polygons into their owned
delivery packet. This avoids repeated allocation and copying of large polygon
arrays. The existing scene bound still limits the allocation; object selection,
materials, validation, serialization and queue/producer order are unchanged.

## Why this change

The local delivery benchmark recreates the native caller's material encoding,
packet construction and final encoding from four actual Amazon packets. Five
alternating rounds of 100 assemblies each produce these medians:

| Captured frame | Existing delivery | Reserved delivery | Reduction |
| --- | ---: | ---: | ---: |
| 5644 | 1,631.90 µs | 1,093.80 µs | 32.97% |
| 6330 | 92.04 µs | 66.69 µs | 27.55% |
| 7187 | 2,426.28 µs | 1,458.61 µs | 39.88% |
| 8760, empty geometry | 0.477 µs | 0.474 µs | effectively unchanged |

Every complete XWD packet and embedded material byte sequence matches its
captured source. Qualification uses the unchanged canonical encoders. This
measures CPU delivery work, not GPU execution or equivalent game-speed gains.

Screening also tried exporting the already encoded materials instead of encoding
them twice, and omitting a redundant outer depth check already repeated by the
encoder. Their additional gains were smaller. Neither the alternate encoder API
nor either behavioral refactor was promoted. All existing validations remain.

## Live qualification

The frozen candidate is native `0cc78ba648402f1f63e6b6a73e100ecb26ba143e`, at
`build/candidates/0cc78ba6484/vunit.exe`, SHA256
`8a2c95d8552043b0b48bdde52e507b3f5e75efb4db7fba13863429e1fbab09a2`.
The 199-patch export reconstructs tree
`aefd4adc578adc5980a2cd5ef1b428f9168e689c`.

A fresh baseline/successor pair on the same current monitor passes all 8,860
inputs, original native images, 7,060 camera samples and 21,180 actual ADC reads
and timestamps. All non-timing fields match in 6,953 early scenes, 6,953 active
scenes and 20,859 material stages. Lifetime, handover/cohort and composition files
are byte-identical. These source checks also renew equality with the prior
nativef6 packet-storage run.

The main material/delivery stage falls from 5.331 to 4.390 seconds, a 17.66%
reduction. The finer queue timing overlaps that stage and is not an additional
saving. Scene assembly and hashing remain essentially unchanged. Over frames
3501–8859, measured emulation speed improves from 95.29% to 96.15%; the busiest
5001–7000 interval improves from 93.43% to 94.54%. Whole-run MAME averages are
94.97% and 95.56%. The fresh baseline is itself faster than the older f6 run,
which is why the improvement is stated against this matching pair.

This is a modest end-to-end gain, not full-speed acceptance. Physical FFB remains
disabled, and no heavy GL readbacks were added solely for this allocation change.
The prior completed-image composition evidence remains separate. Temporal
visibility, remaining performance and final 4K acceptance are still open.

Local evidence lives under `results/diagnostics/exotica-amazon-20260909/` in
`delivery-screen`, `delivery-reserve-qualified`, `delivery-reserve-control`,
`delivery-reserve-live`, `delivery-reserve-live-acceptance.json` and
`delivery-reserve-native-export.json`.
Raw game resources remain local. Personal native87d and public v0.5.0 are unchanged.
