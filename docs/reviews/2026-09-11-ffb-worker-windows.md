# Force normalization: measuring comparable windows on the actual worker

The actual worker traces can now be measured inside game-time windows without
assuming that host time equals emulated time. This matters when comparing force:
the game writes a motor command on one clock, while the output worker wakes,
filters and releases it on another.

`harness/ffb_worker_windows.py` joins both clocks through the captured source
anchors. It measures only the host interval known to be inside each selected
game-time window and reports uncertainty at both edges. It does not interpolate
through a pause or silently stretch a short steering fragment into a longer one.
Duplicate emulated timestamps remain separate host observations. Nanoseconds are
a representation with rounding guards, not a claim of nanosecond timing accuracy.

The measured signal is the actual software sink's held integer output. Repeated
tick records do not add statistical weight. The report includes time-weighted
median/P90, RMS, signed/absolute impulse area and time near the requested ceiling.
This is constant force; mechanical condition effects and rumble response remain
outside the measurement. The script checks the prior stage-verification receipt
and journal hashes; it does not independently execute MAME or re-run those stages.

## Four-game coverage

The existing speed/steering condition intervals use verified World memory speed
and original game-input fields. Adjacent pieces are merged only when they have
the same condition and no time gap. Each game retains the same source/gate/speed
bytes and all deterministic input/time fields as the earlier analysis. The
first attempted whole-frame-CSV hash join failed because host timing and measured
speed-percent columns legitimately change between runs. That failure is retained;
the corrected join excludes exactly those two fields, as the replay comparator
does, and binds both complete file hashes plus every remaining field.

| Game | Merged condition windows | Windows with a known host interior | Measured host time |
|---|---:|---:|---:|
| USA | 840 | 316 | 28.756 s |
| World Germany | 2,290 | 1,004 | 77.745 s |
| Off Road El Paso | 1,907 | 904 | 84.186 s |
| Exotica Amazon | 1,587 | 789 | 61.681 s |

These are unreviewed condition windows, not clean-cornering or contact labels.
Host durations must not be subtracted from the earlier emulated durations as if
they were the same clock. The largest internal source-anchor gaps in retained
windows are 25–70 ms; gaps and edge uncertainty remain visible in each join.

After excluding uncertain edges, only **40–60 m/s, centered, steady input** has
at least two seconds in all four games. No turn bin meets that common coverage.
The negative-medium/slow-input bin retains only 1.337 seconds across30 USA
fragments, 2.107 across55 World fragments, 1.244 across26 Off Road fragments and
0.992 across24 Exotica fragments. Positive-direction and labeled-contact coverage
are still insufficient. These windows cannot accept normalization gains.

## Why matching only RMS would be misleading

The small negative-medium sample has fairly similar RMS between games, but its
shape differs. At nominal50, Exotica's median/P90 requested output are0.399/0.400
of full software range; USA is0.368/0.495. Exotica spends67.1% of this **0.992-second
sample** within1% of its effective40% ceiling, versus9.8% for USA. This is a reason
to inspect clipping and lost detail, not a sufficient sample for a new tune.

An exact-ceiling counter is zero in these samples: smoothing and re-level
hysteresis can stop just below the exact integer ceiling even when the adapter
has already flattened the input. The report therefore distinguishes exact
ceiling time from an explicit1%-near-ceiling measure. Neither alone proves where
clipping occurred. Raw/adapted source evidence remains necessary.

## Using the tool and next calibration drive

```powershell
python harness/ffb_worker_windows.py <accepted-worker-run> <windows.json> `
  --output <new-analysis-directory>
```

The JSON specification has schema1, clock`emulated_nanoseconds`, explicit
`reviewed`, `force_source_sha256`, `frames_sha256` and ordered, disjoint `windows`.
Each window has an `id`, `kind`, `start_ns` and `end_ns`. Reviewed windows also
require a reviewer and visual evidence notes. The report always leaves physical
and normalization acceptance false; declaring a window reviewed does not accept
a calibration.

The useful next recording is a short controlled drive in each game at the same
wheel settings, reference vehicle class and transmission: a straight segment,
several sustained gentle turns in each direction, and clearly identifiable
car/wall contacts with clean driving before and after. Keep existing game steering
sensitivity settings recorded, rather than silently changing them to force a
match. Use currentUSA50 as the provisional feel reference. Exact game-time or
recording-clock markers make contact review much easier. No automatic physical
FFB is authorized by this analysis.

Thirteen new tests cover conservative boundaries, duplicate clocks, delayed sink
acceptance, duration weighting, gaps/overlap, source identity and near-ceiling
semantics. The final complete Python group passes424 tests without skips. Native
and GPU code are unchanged; their previous receipts remain separate.

LOCAL evidence: `ffb-worker-condition-windows-ceiling`, the retained initial
frame-hash failure and intermediate comparisons under the Amazon diagnostic
directory. [Public receipts](../../results/proof/2026-09-11-ffb-worker-windows/README.md)
check source/hash/aggregate consistency; raw traces and their execution stay local.
