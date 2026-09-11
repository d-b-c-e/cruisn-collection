# Four-game force condition coverage

The first time-weighted comparison is now reproducible, and it identifies why
the existing recordings are not yet enough to choose normalization gains. This
is analysis only: no MAME binary, force tune, menu policy or deployed settings
changed. Strength 50 equivalence remains a near-term goal.

## Method and checks

`harness/force_segments.py` consumes the four accepted native795fc replay runs
listed in [the normalization plan](../FFB-NORMALIZATION.md). Each has physical
FFB disabled. It validates source/gate pairing and signed requested levels,
reserved neutral handling, contiguous input frames, speed-sample frame/time
joins and original sample age. It rejects differing native executables,
unaccepted replays, malformed rows, nonfinite values and invalid clocks.

The source motor command is held between observed writes, bounded by the first
and last captured samples. Intersections with speed and recorded wheel-port
intervals provide exact duration weights. Motor age above 500 ms and speed age
above 100 ms are excluded. These are evidence-selection limits in **emulated
time**, not an emulation of the physical worker's host-time watchdog. Source
requests include gate/polarity at writes; asynchronous gate transitions, SDL
effects and shaper/worker timing are outside this report.

Conditions retain speed bands, signed wheel-port deflection and absolute input
velocity. The wheel-port scale is `(byte - 128) / 112`, matching the supported
16..240 range. It is not physical wheel angle or proof of equal actual ADC
samples. Different steering sensitivity/curve settings are retained in receipts.
No interval is labeled contact-free solely from a waveform.

## Results

| Game | Selected time with numeric/memory speed only | Why it does not establish calibration |
|---|---:|---|
| USA | 40.136 s | Short original recording, unreviewed contacts |
| World Germany | 0 s | All available valid speed samples are OCR |
| Off Road El Paso | 117.076 s | Rough track, unreviewed contacts |
| Exotica Amazon | 89.298 s | Unreviewed contacts and substantial adapter clipping |

The selected Exotica intervals spend **36.95%** of their duration at the
adapter's full normalized level (absolute byte >=126). USA spends 2.71%; Off
Road spends 0%. These are different routes/conditions and unshaped commands;
they cannot be used as a force-normalization target or physical saturation claim.
This denominator differs from the earlier whole-trace and event-count metrics.

A second explicitly exploratory run permits OCR speed with the same age cap.
Only two condition bins contain at least two seconds in **each** game:

| Condition | USA | World | Off Road | Exotica |
|---|---:|---:|---:|---:|
| 40–60 m/s, center, steady input | 7.665 s | 18.660 s | 21.751 s | 15.437 s |
| 40–60 m/s, negative medium input, slow movement | 2.728 s | 2.941 s | 2.279 s | 2.013 s |

In the turn bin the longest continuous pieces are only 0.104–0.207 seconds.
There is no corresponding positive-direction bin with two seconds in all four.
These totals are therefore candidate review coverage, not matched clean turns.
No gain fit or claim of comparable strength is justified by this result.

## Validation and next work

Ten new tests cover duration-weight invariance under repeated writes, unknown
ends, stale speed's original timestamp, OCR opt-in, same-time last-write order,
gate exclusion, bin boundaries, fragmented intervals, source identity and malformed
input rejection. The complete Python group passes **368 tests, no skips** at
source identity `b3110f9b2e2b944aaec696562f8bd181c80d896b295b72497ca3354ee2ee8652`.
Native/GPU checks were not rerun for this Python-only change; their earlier
checkpoint remains separate.

1. Validate World speed independently. The existing Germany probe already logs
   guarded player `speed_raw`; its units and lifetime must be verified before use.
2. Relate recorded port values to effective steering/actual ADC sampling, retaining
   per-game sensitivity and curves. Do not treat equal port bytes as equal rim angle.
3. Review windows and contacts, then reproduce final conditioning and delivery
   timing with device output disabled. Keep impact contrast separate from steering
   weight, and select versioned calibration from adequately covered conditions.
4. Verify the strength-50 candidate with an attended common-wheel comparison;
   fill recording gaps only after using the existing evidence.

LOCAL full intervals and reports are under `results/diagnostics/exotica-amazon-20260909/`
in `ffb-condition-final`, `ffb-condition-final-ocr` and `ffb-condition-python-checks`.
[Public receipts](../../results/proof/2026-09-10-ffb-condition-coverage/README.md)
bind source and reported coverage. They do not contain raw game traces or rerun
the games, force worker or physical wheel.
