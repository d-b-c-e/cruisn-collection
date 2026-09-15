# USA first scene and first track frontier

USA's actual scene hook begins at native frame739 in the retained recording,
well before the previous host-renderer test window starting at3500. The first
track frontier appears at1480. Six saved snapshots now qualify code and source
readiness at these two stages without changing guest state or enabling early
host rendering.

`lua/vunit_startup_observer.lua` observes the actual scene read atPC0x81. It reads
ordinary RAM through the memory share, bypassing cycle-eating handlers, and
captures fast RAM separately. The probe changes no input, memory, guest
allocation or draw submission. It has a4096-row bound and at most eight explicitly
selected snapshot sequence numbers. It checks write/close results and removes
its tap at the declared end. Profiles for World and Off-Road exist in the probe,
but have not yet been exercised or accepted by these runs.

## First scene

One original-only, headless2,101-input prefix passes the existing input/native
image comparison. It records1,301 actual scene calls from native739 through2098.
The first, second and sixteenth calls save complete RAM/fast-RAM operands at739,
740 and755. All three pass the canonical full USA host-code and future-code
guards. Native preparation at3× matches the independent Python reconstruction:
the track is not initialized and both pending/future output are empty.

The row stream reveals the first nonzero frontier at scene706/native1480. A
nonzero pointer alone is not accepted as readiness evidence. The first capture
did not include its full RAM state, so one shorter1,552-input prefix saves scene
706,710 and730, corresponding to native1480,1484 and1504. Its775 scene records
match the original prefix exactly, excluding only the requested snapshot flag.
Inputs and native images pass again. This second prefix supplies missing state;
it is not a timing repeat or a full-drive rerun.

## First initialized frontier

The already-built guarded native analyzer and independent Python implementation
agree at all three initialized snapshots:

- 64 upcoming sections and5,382 definitions.
- 52 special definitions and3,381 currently unbound definitions remain excluded.
- 1,949 ready definitions, no queued uploads.
- All1,949 ready candidates fail the near-distance test; output is correctly empty.

The complete native output, including counters and ordered geometry, matches
Python. The analyzer also runs cold/warm native model-cache passes. No scene
guards, material ownership tests, projection tests or unsupported-source rules
were relaxed to obtain these results.

This establishes readiness for the captured startup states. It does not qualify
every intervening scene, actual early rendering, later track transitions or
continuous product operation. The next candidate should activate from a verified
scene/code boundary, retain per-call readiness and material checks, and preserve
the established preparation fallback. It should not hardcode frame739 or1480.

Local evidence under `results/diagnostics/world25-roads-20260914`:
`usa-startup-observer`, `usa-startup-qualified`, `usa-startup-frontier`, and
`usa-startup-frontier-qualified`. Both runs use frozen native71c8339c8c7 with
host rendering off and physical FFB disabled. The raw game data remains local.
No GPU performance, renewed4K presentation, deployment or release claim follows
from these headless observation prefixes.
