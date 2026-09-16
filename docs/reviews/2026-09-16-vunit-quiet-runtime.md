# Quiet continuous scenery

`--vunit-journals quiet` explicitly removes persistent host scene journals and
first-activation RAM snapshots from continuous V-Unit operation. USA, both World
revisions and Off-Road share the policy. It requires the continuous candidate,
scene bootstrap, live GL, physical FFB disabled and summary geometry. Detailed
quad, mirror and fade captures are rejected. Capture remains the default.

The existing checked `DiagnosticJournal` separates enabled rendering from an
open file. Quiet mode does not open a null-device file or format scene rows.
Capture still checks buffering, writes and closure. Off-Road's per-scene partial
frontier announcements are also suppressed in quiet mode; preparation failure
and final CPU/GPU receipts remain visible.

An ordered 64-bit FNV fingerprint folds each submitted scene's frame, page, quad
count and existing ordered-quad hash as fixed little-endian words. It permits
comparison against retained captured geometry without writing every scene.
It is not a cryptographic identity or proof of every source/material field.
Quiet bootstrap reports explicitly say that operand capture was disabled;
missing snapshots are never described as independently verified operands.

The GPU exit path additionally avoids drawing a remaining partial batch after
the persistent stream has already failed. It still waits for issued GPU work
and reports unfinished/failure state. The healthy path is unchanged; no new
injected stream-corruption acceptance is claimed for this guard.

## Validation

Three native tests pass: policy selection, the checked capture/quiet journal,
and continuous frame bounds. The compiled fingerprint matches an independent
Python fold of all saved continuous scene rows for all four V-Unit profiles.
Nine focused Python tests cover bootstrap, runtime and preparation fallback.

| Profile | Policy | Inputs | Scenes | Quads | Geometry fingerprint |
| --- | --- | ---: | ---: | ---: | --- |
| USA | Quiet | 4,002 | 2,267 | 4,020,633 | `49880c7a3803b6c9` |
| World 2.5 | Quiet | 2,502 | 648 | 1,419,058 | `5ec6d16a0d8ccc12` |
| Off-Road | Quiet | 2,502 | 678 | 251,021 | `59db737e6b3fa91d` |
| World 2.4 | Capture regression | 2,502 | 413 | 672,298 | Saved scene rows match |

The three quiet runs match the captured controls' entire ordered geometry folds,
first/last prepared frames and counts, and produce no host journals or bootstrap
RAM files. World 2.4 retains matching scene semantic fields and first operands,
excluding named timing/cache-miss counters. All four preserve original recorded
inputs, native images, camera/ADC samples and the actual completed image after
the old reference end (USA3750, others2400). Images remain3824×2073 CRT on the4K
monitor. All four stop with joined graphics workers, equal ring positions and
no pending quads, drops, stream failures or observed GL errors.

These short runs validate the changed I/O path. They are not a new performance
benchmark, full-route visual acceptance or multi-race test. The earlier journal
size audit did not establish a major performance problem; no speed gain is
claimed here. World 2.4 and2.5 use the same journal implementation, so one checks
capture and the other quiet instead of repeating both policies for both sets.

Native `1a1b7e0ff6b`, SHA256
`a9e5b5734347033c5d5f28387761bf2f76ebbdd50f295a1bba24055de401109a`.
252 patches reconstruct `ad2774cd1d5286a9424413a75384b725719ac1e0`.
Local evidence: `results/diagnostics/world25-roads-20260914/vunit-quiet-checks`,
`*-quiet-live`, `*-quiet-qualified.json`, and `vunit-quiet-native-export.json`.
`export-vunit-quiet.py` already ran; never rerun an export against its appended
patch baseline. Personal Stream Deck copy and publicv0.5.0 remain unchanged.

Next: recorded race/menu/track transitions. A labeled scripted extension of an
existing drive can exercise lifetime behavior autonomously; it must retain the
human prefix exactly and must not be presented as a second human-driven race.
Open-sightline visual distance validation still benefits from the requested
attended Exotica recording.
