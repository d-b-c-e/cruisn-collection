# Four-game normalization: actual force-worker observation

The next strength-50 calibration needs the output after conditioning, not only
the game's raw motor writes. The separate native93684035c6c candidate now runs
the existing worker with an explicit device-free sink. It records the inputs
and clocks actually consumed by the worker and verifies every detector, shaping,
mixing and integer-output stage independently after the drive.

This is measurement infrastructure for the near-term calibration. It does not
change the shipped gains, Exotica trim, World menu passthrough or cabinet polarity.
The Stream Deck copy and public v0.5.0 remain unchanged.

## Why this closes a measurement gap

The older analyzer samples held source writes every 4 ms. The real worker also
wakes on motor updates, coalesces writes and can run late. Its watchdog uses
host time; game source writes use emulated time. Gate cancellation resets the
shaper, detector and mixer, while watchdog expiry resets the detector/mixer but
retains the shaper's existing release behavior. Those distinctions affect force.

The new journal records each actual atomic read and each clock used, rather than
pretending all inputs were one simultaneous snapshot. In enhanced mode, raw
detector input is read after the watchdog and can reflect a newer CPU write.
The verifier deliberately preserves that possibility. It reproduces conditioning
from observed inputs; it does not yet prove every asynchronous mailbox read's
causal relationship to source writes.

Source records carry both host and emulated timestamps. They join independently
to the existing emulated force-source trace. Tick records distinguish a requested
value accepted by the software sink from an SDL command accepted by a driver.
The final receipt requires a completed worker shutdown and a zero sink value.

## Explicit diagnostic contract

Use a separately frozen candidate with the unmodified shipped
`force-profiles.ini` beside its executable and no user profile override:

```powershell
python harness/replay.py <recorded-case> --candidate <candidate-vunit.exe> `
  --ffb-worker observe --ffb-worker-strength 50 --ffb-worker-impacts off `
  --output <new-evidence-directory>
```

`--ffb-worker-impacts on` measures the enhanced steering-axis mix. Observation
requires literal `MIDV_FFB=0` and rejects native sign-test mode. SDL haptic loading,
enumeration and delivery are skipped; attempting its loader in this mode is fatal.
Ordinary playback leaves observation disabled, and inherited observation requires
an explicit CLI choice. Strength zero still exercises the diagnostic worker.

The harness chooses the existing `cruisn-vunit@2` profile and removes inherited
smoothing overrides. Nominal50 is effective50 for V-Unit and effective40 for
Exotica, preserving its current explicit 0.8 trim. Recorded polarity, menu gate
and condition/rumble preferences remain in the invocation. No calibration values
are inferred from a recording's peak or whole-drive RMS.

Each of the two buffered journals is bounded by 131,072 records and 64 MiB.
Missing profiles, incomplete shutdown, malformed records, changed profile files,
stage mismatches and unexpected observer output in disabled mode fail validation.
The native build is frozen separately; 188 exported patches reconstruct its tree.

## Validation checkpoint

All four complete recorded input comparisons pass on the same candidate. Every
source/gate/speed/drivetrain CSV remains byte-for-byte equal to the earlier
native795fc controls, and all 61,713 actual worker ticks reproduce exactly.

| Game | Inputs | Source writes | Worker ticks | Legacy waveform candidates | Gate cancellations |
|---|---:|---:|---:|---:|---:|
| USA | 5,012 | 4,569 | 9,947 | 2 | 0 |
| World Germany | 9,269 | 8,803 | 17,565 | 29 | 0 |
| Off Road El Paso | 9,644 | 8,820 | 18,006 | 45 | 0 |
| Exotica Amazon | 8,860 | 7,476 | 16,195 | 46 | 2 |

These waveform candidates are not labeled collisions. The Exotica column is its
legacy adapted-motor detector; the enhanced raw-motor threshold finding remains
separate. None of these four runs expires the watchdog; synthetic schedules test
that branch. Every shutdown clears the software sink.

All V-Unit native images match. Exotica's CPU polygons are disabled in its live
GL path, so native images do not establish gameplay rendering. Its 21 completed
3840×2160/CRT samples at frames4650..4750 additionally match the earlier control's
decoded pixels and BMP files exactly. This is sampled presentation evidence,
not renewed camera/ADC or whole-route pixel coverage.

The first aggregate comparison mistakenly compared a BMP-file hash to the
receipt's decoded-RGB hash. That assertion failure is retained. The corrected
comparison independently verifies both equal file bytes and equal decoded pixels.

Fifteen hand-calculated schedules cover five strengths in legacy/enhanced modes,
same-millisecond observations, positive/negative force, cancellation, watchdog
expiry, the positive/negative impact envelope and zero strength. Fourteen
corrupted-journal cases fail validation. Six new Python tests cover the diagnostic
gate, explicit Exotica trim, profile identity, source bounds and disabled-mode
rejection. The complete Python suite passes 411 tests without skips; all 135 native
commands, including 51 standalone native tests, pass on the same source identity.
GPU test groups were not rerun for this force-only change; the four actual game
comparisons above remain separate evidence. This is not a release-gate renewal.

Three additional live USA controls pass. Disabled observation preserves a
1,200-input/20-image prefix and writes no observer artifacts. At strength0, a
2,400-input/40-image prefix contains 2,352 nonzero requested-input ticks, but all
4,458 outputs are zero and no sink change occurs. Enhanced strength50 preserves
the full 5,012-input/83-image drive and exactly verifies 9,943 ticks, two waveform
events and 22 samples with a nonzero impact-envelope contribution. This actual
event count differs from the earlier idealized four-event result; host timing and
consumed inputs must be considered before attributing that difference to contacts.

The native/Python checked-source identity is
`135ee3fbb11a4dd5f6d68718303f65b2ce4945f96080c07d37d534809fce952b`.
[Public receipts](../../results/proof/2026-09-11-ffb-actual-worker/README.md) bind
the current code and aggregate results. Their verifier does not execute private
recordings, rebuild MAME, rerun GPU captures or accept a wheel's physical feel.

An initial negative test incorrectly expected removing a cancellation to fail
even though that particular zero-output schedule still has identical resulting
stages. It was removed from the corruption set: a different valid input is not
itself corrupted evidence. The retained test failure does not represent a native
worker failure.

## Remaining acceptance

Measured host timing includes this diagnostic's logging cost and software sink.
It is not an uninstrumented hardware-driver performance result. Desired rumble
amplitude and condition settings are recorded; their mechanical effects are not
simulated. No physical wheel output occurs in these automated runs.

Next compare time-weighted output in reviewed clean left/right turns and labeled
car/wall contacts, with source-to-host timing uncertainty shown. Existing drives
still lack sufficient common turn/contact labels. A short targeted same-wheel
drive per game may be needed before choosing a versioned calibration. Separately
calibrate Exotica's enhanced detector source units, whose current Amazon range
cannot reach the common arrival threshold.

The target remains comparable strength50 steering weight, preserved impact
contrast and headroom, and monotonic 0/25/50/80/100 behavior. Attended feel and
stability checks accept the candidate after software validation.
