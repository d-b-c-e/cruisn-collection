# Recorded steering for four-game FFB normalization

The force comparison now has an independently checked reconstruction of recorded
steering. All **32,785** frame samples match across USA, World, Off Road and
Exotica. On Exotica, all **7,060 actual steering ADC reads** also match at their
captured emulated times. This advances the strength-50 calibration milestone;
it does not change deployed force or establish equal physical strength.

## Why this matters

The native795fc `src/emu/ioport.cpp` path applies the custom gain/curve when it
reads a live absolute PADDLE input. MAME then records the resulting accumulator,
its previous value, sensitivity and reversal. Playback restores those fields
after the live port update. Reapplying the gain/curve during offline analysis
would therefore apply the curve twice.

The game can read steering between frame snapshots. MAME interpolates the stored
accumulators using emulated nanoseconds before applying sensitivity, reversal,
fixed-point scaling and rounding. `harness/steering_reconstruction.py` implements
that arithmetic independently for the supported 16..240, center-128 racing ports.
It reads INP; it never synthesizes or changes input. It rejects unsupported
identity/layout, malformed clocks, incomplete/compression-overflow data, unknown
input lifetimes and ambiguous rounded timestamps.

INP timestamps retain exact attoseconds. Twelve-place CSV clocks include a
conservative formatting/double uncertainty. Frame evidence must contain the exact
corresponding INP update time within that interval. Sub-frame evidence must give
one unambiguous predicted byte across the entire uncertainty interval; the
analyzer cannot pick a side merely because it matches the observed byte.

## Current evidence

All four accepted replays use frozen native
`795fc77b68e40c88ec328be49a03bedd27300c04`, executable SHA256
`97cd738c6b89f59a7523c9494285c5ee625e9f5041622f542983d94173b37d7a`,
with physical force disabled.

| Game | Frame samples reconstructed exactly | Recorded MAME sensitivity | Actual steering ADC checked here |
|---|---:|---:|---|
| USA | 5,012 | 25 | Pending |
| World Germany | 9,269 | 20 | Pending |
| Off Road El Paso | 9,644 | 25 | Pending |
| Exotica Amazon | 8,860 | 25 | 7,060 reads, frames 1800..8859 |

All recorded reversal fields are zero. The sensitivity values are internal MAME
settings, not calibrated steering-angle ratios or FFB gains.

Exotica's captured reads come from address `9c000b`, consumer PC `856c`, and join
the corresponding INP time interval. Twenty-five reads differ from the preceding
frame snapshot by one byte; reconstruction matches the actual game read in all
cases. That small sampling difference does not explain the large reported force
imbalance. It demonstrates why a frame snapshot and a game read should remain
distinct measurements.

The other three drivers use an ADC that samples the selected port at conversion
completion and returns a latched value later. The inspected ADC0844 conversion
delay is 40 microseconds. A CPU read timestamp alone is not its sampling time;
validate the actual conversion/channel sequence before claiming the equivalent
V-Unit sub-frame coverage. No such new runtime capture was made in this step.

## Validation and next work

The complete Python group passes **390 tests, no skips**, including seven new
tests covering supported layouts, signed interpolation, rounding/clamping,
sensitivity/reversal, no repeated live curve, malformed input, clock ambiguity
and independent ADC/evidence rejection. No MAME build, GPU test, device output or
native suite was needed for this analysis-only change.

Run the bounded analyzer with:

```powershell
python harness/steering_reconstruction.py RUN_DIRECTORY --rom crusnexo --exotica-adc --output NEW_DIRECTORY
```

For the V-Unit frame checks use the relevant ROM and omit `--exotica-adc`.
The report hashes the input/evidence and keeps physical-angle and normalization
acceptance explicitly false. This is an input reconstruction check, not a new
replay-acceptance gate or full physical force model.

Next verify the V-Unit sampling joins, review matched clean turns and contacts,
then compare complete force conditioning at strength 50. Use current USA as the
initial reference while retaining impact headroom. Missing comparable drive
coverage should prompt targeted recordings rather than a whole-race RMS tune.
The [first candidate milestone](../FFB-NORMALIZATION.md#first-candidate-milestone)
is independent of completing the extended-drawing project.

LOCAL evidence is under `results/diagnostics/exotica-amazon-20260909/` in
`ffb-steering-reconstruction` and `ffb-steering-python-checks`.
[Public receipts](../../results/proof/2026-09-11-ffb-steering/README.md) check
source/hash and reported-count consistency; they do not rerun the private INP,
actual game reads or physical wheel tests.
