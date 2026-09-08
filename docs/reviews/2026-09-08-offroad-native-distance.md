# Off Road native global distance — 2026-09-08

Off Road 1.63 now has an opt-in native global distance adapter. It preserves the
earlier Lua trial's modest visible gain while removing its expensive per-read
Lua tracing. This is a coherent far/clip/perspective extension, without model or
level allowlists. It does not eliminate pop-in.

Native `12e9ea6a3742643f5bbc57e7dc07073177594cd6`, root `vunit.exe` SHA256
`9936c7160ddb708949d9e776c9197d833e868ffc921fd679153a72ab99735275`.
The 129-patch export reconstructs tree `85f158eccb5f11308144513e77b8678f45a0317b`.
The published v0.4.0 tag and package remain the rollback baseline.

## Implementation

`MIDV_OFFROAD_DISTANCE=0` or unset installs no hooks. `1` observes the original
limits; `2` and `3` extend them. Recording, replay and candidate derivation accept
`--offroad-distance`. An explicit choice is frozen in the recording settings.

| Multiplier | Sphere far limit | Vertex clip limit | Last reciprocal index |
|---|---:|---:|---:|
| 1 | 47,296 | 63,680 | 63,679 |
| 2 | 94,592 | 127,360 | 127,359 |
| 3 | 141,888 | 191,040 | 191,039 |

The sphere comparison reads active far word `1B724` at PC `1C36`. Two verified
consumers read clip word `1B725`; twelve compare/conditional-load consumers read
ceiling `111A8`. Native read taps substitute only those consumers' results.
The stored limits, their initializers and all ROM/resource bytes remain intact.
This naturally survives the race-transition resets that defeated the first
active-word-only Lua experiment. No additional game patch is required.

The canonical `native/offroad_distance.h` verifies the exact program profile,
including all 59 known projection instructions. Reciprocal reads additionally
require `AR0=CB0FC8` and the actual address to equal `AR0 + signed IR0`. The
previously misattributed resource read at PC `1EA8` is explicitly excluded: a
stale base register does not establish a perspective lookup. Unsupported
consumers or out-of-range qualified reads stop the trial.

All original table entries are left untouched. The host tail uses the measured
eight-decimal rational generator with ties rounded to even. Recomputing its
entire original range, including indices −4096 through 63679, matches **67,776
ROM entries exactly**. Two rounding-sensitive entries are permanent helper
test vectors. Synthetic and captured-program guards also pass.

Buffered per-frame and per-consumer CSVs record far decisions, clip/ceiling reads,
extended lookups and index ranges. `analyze_offroad_native.py` rejects incomplete
coverage, changing configuration, unknown instructions, inconsistent counters,
bad ranges and duplicate rows. `run_offroad_native_trials.py` serializes the
native matrix; the existing Lua trial runner remains available independently.

The first native build (`781af835091`) completed the original and 2× drives, but
its CSV duplicated the startup frame 822 when MAME requested a partial screen
update. The analyzer rejected that log. The final native emits one row per
frame; the failed initial logs remain in the diagnostic directory.

## Completed small-window matrix

The final stock control matches all 6000 inputs and 100 native snapshots. Native
2× matches all 42 completed GL samples from the older Lua 2× trial. It changes
five of those samples against stock (4000, 4100, 4200, 4400 and 4600), the same
small changes previously observed. Native 2× and 3× match each other's 42 GL
samples exactly. These matrix captures are 512×451, not a 4K acceptance test.

| Trial | Extra far admissions | Table reads | Extended reads | Largest index | Upper clamps | Emulation rate |
|---|---:|---:|---:|---:|---:|---:|
| Stock | 0 | 6,884,206 | 0 | 63,679 | 581 | 100.0040% |
| 2× | 16,995 | 7,322,497 | 55,113 | 95,085 | 0 | 100.0050% |
| 3× | 17,005 | 7,322,517 | 55,133 | 96,264 | 0 | 99.8321% |
| 2× repeat | 16,995 | 7,322,497 | 55,113 | 95,085 | 0 | 100.0044% |

Counters cover all 6000 frames; timing covers 1800…5990. Counts differ slightly
from the earlier bounded Lua trial because the native option is active from boot.
These are emulation throughput measurements, not presentation-latency results.
The repeat has identical native CSVs, all 4191 camera samples and actual ADC
events including their timestamps, plus all 42 completed GL samples.

Camera observations cover 1800…5990. Stock, 2× and 3× retain the same camera and
actual ADC frame/value/PC sequences in that interval; ADC timestamps differ
with added drawing work. Strict timing equality therefore remains a FAIL for
the extended trials. Camera equality does not prove equal traffic state or
rendering phase. Each trial retains its original-image FAIL independently of
its completion and counter checks.

The existing synthetic El Paso drive runs off course and slows down. It is useful
for repeatable diagnostics but cannot stand in for a fresh attended full race.
The previous Lua geometry comparison also retained a changed original quad;
neither the new adapter nor these images erase that strict geometry failure.

Evidence is being completed under `results/diagnostics/offroad-native-20260908`:
candidate repeatability, larger-display captures and disabled-feature regressions
are separate checks, not implied by the results above. Physical force stays off.

The harness now accepts `--display-size WIDTH:HEIGHT` in replay and derivation.
It selects an actual matching monitor and records that selection, or fails if
none exists. V-Unit's maximized client area can be smaller than the monitor due
to borders; completed-capture dimensions remain the evidence, not the requested
display size. A derived case freezes its selected screen and resolution for its
identity replay. Existing original recordings are never edited for this purpose.
