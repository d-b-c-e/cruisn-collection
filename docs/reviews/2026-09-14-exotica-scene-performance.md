# Exotica extended scenery: less repeated assembly work

The isolated candidate reduces scene assembly cost while preserving the prior
waiting-scenery candidate's output. This improves the path toward release-ready
distance parity; it does not establish parity or normal-speed acceptance.

## Changes

Projection constants are prepared once per model texture-format interval instead
of per polygon. Format changes invalidate them, and each decode starts with fresh
context. Scene assembly reuses bounded decode scratch storage, reserves result
capacity and validates each cached model/format combination once per scene.
Neither geometry nor texture state is cached across scenes. Math ordering, guest
execution, drawing order, resource ownership and full diagnostic hashing remain
unchanged. The changes affect the Exotica host scene path, not V-Unit drawing.

## Evidence and limits

Two focused native test executables pass, including projection-format changes,
successive decode calls and malformed projection inputs. Five saved native scenes
were compared through old and new compiled helpers, with three alternating timing
rounds of 80 assemblies each. Complete ordered geometry and instance bytes match
each other and the captured native artifacts. The two most improved scenes reduce
median assembly time by 20.2% and 25.5%; the other three are effectively unchanged
(one is 1.2% slower). This is workload-dependent, not a uniform speedup.

One full Amazon replay on the rebuilt candidate passes all 8,860 recorded inputs,
7,060 camera samples and 21,180 ADC records. All 6,953 waiting batches complete;
five insertion samples pass geometry/material checks. Early scenery and original
resources remain unchanged. All 33 selected completed 4K/CRT images match the
previous waiting-draw candidate exactly. These sampled images do not prove that
every intervening frame is identical or that the existing artifacts are fixed.

Logged early scene assembly falls from 20.471s to 17.572s, a 14.2% reduction.
Diagnostic geometry hashing stays effectively unchanged at 4.453s. Instrumented
emulation speed rises from 81.85% to 83.51%. These single-run figures include
capture/observer overhead and host scheduling; they are not a clean real-time
performance benchmark. No timing spans from different threads are added together.

Full hashing was retained deliberately. A sampled audit could reduce diagnostic
cost, but should be a separate explicitly scoped experiment, not a silent change
to the evidence used here. No broad four-game regression matrix was repeated for
this isolated optimization. Combined product regressions remain a deployment gate.

## Remaining release work

Exotica still needs verified fade/handover through object admission, a solution
for the left ground margin that composes with extended scenery, and sustained
performance. Next test a specific transition window or changed implementation;
do not repeat this accepted full replay without a new reason. World, USA and
Off-Road retain their earlier coverage and limitations; this checkpoint makes no
new cross-game or cross-track acceptance claim. FFB normalization still requires
the requested attended calibration coverage.

## Reproduction

Native commit: `1d5af5a09287dc71a2c06ea2bc8ddf605310d329`.
Frozen candidate: `build/candidates/1d5af5a0928/vunit.exe`, SHA256
`f18591de69456916b1434fe1d4cbafbee135fd32729d34d9350288c12c5889bc`.
The 190-patch export preserves the verified prior 189-patch bytes; the appended
commit reconstructs tree `2c3511d125d6341cf40011ca5032b6995c36c020`.

Local evidence:

- `build/scenery-perf-20260914/comparison.json`, benchmark sources, old/new
  executables, outputs, native test executables and native build log.
- `results/diagnostics/exotica-amazon-20260909/waiting-draw-perf-full/report.json`
  and `waiting-draw-perf-full-acceptance.json`.
- `waiting-draw-trial.py --full --present extended --candidate
  build/candidates/1d5af5a0928/vunit.exe --pixel-reference
  results/diagnostics/exotica-amazon-20260909/waiting-draw-full/run`, with output
  name `waiting-draw-perf-full`.
- `waiting-draw-perf-native-export.json` binds export and executable hashes.

No deployment, release, hosted CI or physical FFB was performed. Personal
Stream Deck executable and public v0.5.0 are unchanged.
