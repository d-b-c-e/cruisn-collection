# Verified startup across V-Unit games

The explicit `--vunit-bootstrap scenes` candidate policy now supports USA,
World2.4/2.5 and Off-Road. It starts preparation at each game's actual checked
scene boundary, retains the finite capture end and requires future drawing,
both rendering layers, live GL and physical FFB disabled.

World2.4 gains an opt-in recognition of the independently captured empty track
state. Both its section pointer and pending limit must be zero, and the scene
instructions must still match. Such a state clears the future cache and skips
drawing. Default World2.4 capture behavior is unchanged. Once ready, the complete
existing code/source/model/material and guest-cycle checks still run.

## Live evidence

Three2,502-input prefixes cover startup through initial driving/attract scenes.
Original inputs, timing and native images pass in all three. Activation operands
exactly match the original-only snapshots qualified earlier.

| Game | First prepared scene | Scenes before1800 | Earlier submitted quads | Exact later scene rows |
| --- | ---: | ---: | ---: | ---: |
| World2.4 | 1675 | 62 | 83,558 | 351 |
| World2.5 | 1206 | 297 | 724,301 | 351 |
| Off-Road | 1045 | 378 | 0 | 300 |

Later comparison covers1800–2500 against the accepted road-polygon/partial-source
controls. All semantic fields and ordered quad fingerprints match; only named
timing fields and cache-miss counts are excluded. Each run matches701 camera
samples and2,103 World or2,804 Off-Road actual ADC reads. No preparation fallback
occurred. Quads are cumulative submissions, not newly visible object counts.

One completed CRT image at2400 per game was inspected on the4K monitor
(3824×2073 client captures). World2.4 shows early Germany driving, World2.5 shows
London attract driving, and Off-Road shows the El Paso start. These are inspection
samples, not paired proof of every early frame or all tracks. USA's separate
5,012-input/later-image qualification remains documented in
[the USA review](2026-09-16-usa-scene-bootstrap.md).

## Failures retained and corrected

The first World2.5 comparison used a control from before the accepted near-crossing
road-polygon fix. Its geometry mismatch is retained. Comparison against the
correct accepted control passes; the game was not repeated.

The first Off-Road run's overall harness report fails because the native activation
receipt incorrectly used the shared World revision field, whose default is24.
The saved Off-Road scene, operands, original replay and overlapping geometry are
independently qualified separately; its malformed receipt is not relabeled valid.
The same lookup would also misreport USA. A separate native commit replaces it
with a game-name profile and restores one accidentally re-encoded comment.

The corrected profile passes a focused native test for all four V-Unit ROM names
and unknown/null rejection. Short1,102-input Off-Road and802-input USA smoke runs
exercise the actual corrected receipts without repeating full drives. Both must
pass their normal harness activation checks; both first operands also match the
original observer byte-for-byte (`bootstrap-receipt-smokes-qualified.json`).

Three focused native checks cover the World empty-state rules, existing World
host behavior and receipt profiles. Five Python checks cover bootstrap gates,
cross-game receipts, malformed evidence and preparation fallback. Native45f0
contains the adapter expansion; native6cc8a1869d3 is its receipt-only successor.
The latter freezes SHA256
08d7fe4985ac5aec6d82c5a0880e11bffb87eb34bdf1b5b1aed0dce1ad860660,
with250 patches reconstructing cff2f9f92c53369d8f8327f07a6994926d173c03.

Local evidence under `results/diagnostics/world25-roads-20260914` includes the
three `*-bootstrap-live` runs, World `*-bootstrap-qualified-v2.json`, separate
`offroad-bootstrap-render-qualified.json`, the two `*-bootstrap-receipt-smoke`
runs, and `vunit-bootstrap-receipt-native-export.json`. Both
`export-vunit-bootstrap.py` and `export-vunit-bootstrap-receipt.py` have already
run and must not be rerun.

## Next

Finite end windows still prevent normal continuous operation. The next work is
an explicit session lifetime and shutdown policy, preserving fallback and
bounded caches. The earlier audit's thread-join reference needs correction:
the join at `midvunit_v.cpp` belonged to the FFB worker. The graphics worker is
detached, with `s_stop`/`s_done` and a bounded shutdown wait. Reaching a screenshot
frame does not establish queue exhaustion or graphics-thread ownership at exit.

Continuous runtime, multi-race transitions, full early-frame appearance and
performance remain open. No deployment, release, physical FFB or hosted CI ran.
The personal Stream Deck build and publicv0.5.0 remain unchanged.
