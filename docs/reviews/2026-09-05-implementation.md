# Assessment follow-through: diagnostic foundation

This records implementation after the independent assessment. The five original
review documents remain a dated description of the baseline, including defects
subsequently fixed here. The [workflow guide](../DIAGNOSTIC-REPLAY.md) contains
commands and file formats. The shared toolkit's separate review is
[`docs/REVIEW-2026-09-05.md`](https://github.com/d-b-c-e/dbce-wheel-mod-toolkit/blob/master/docs/REVIEW-2026-09-05.md).

## Return points and scope

Before implementation, the collection assessment was committed as `d099c2f`
and pushed on master with annotated tag `assessment-2026-09-05`. MAME baseline
`58203bb13f7b4a5997b4f6dceed1e36a8fd631d8` was pushed to the private fork's
`poc/quadlog`. The toolkit assessment baseline is `4e99136`, also pushed with
`assessment-2026-09-05`. These remain return points after the improvements.

The first implementation deliberately establishes trustworthy experiments and
repairs bounded signal/diagnostic defects. It does not mark the rendering or
subjective crash-feedback complaints resolved. No physical wheel output was
requested during the tests. No deployed racing MAME executable was modified.

## Changes completed

### Effective-input recording and replay

`run_rig.py --record-case` records actual MAME INP input state rather than a
sequence of host keyboard events. This includes analog current and previous
values, sensitivity and reverse state, allowing the emulator's interpolation to
recur during playback. An isolated initial configuration/NVRAM copy, archived
executable and dependencies, input hash, native screenshot hashes, emulated-time
trace and source identity are retained. Replays validate these before launching.
Every run has a new directory; no diagnostic command silently replaces its
reference or a failed run's output.

A 6,000-frame USA synthetic scenario inserts three coins, selects a race, and
changes steering, accelerator, brake and gear. It reaches actual Golden Gate
Park gameplay, with about 36 seconds of racing visible at the end. It is an input
sweep, not a well-driven lap. A neutral seed and strict INP-layout validation
make the synthetic provenance explicit. MAME records the synthetic playback;
the resulting recording is then independently replayed.

The live GL capture path now supports a bounded stream-frame interval and a
CSV index containing presentation count, stream frame, backbuffer dimensions,
visible page and queue/drop counts. Native screenshots and asynchronous GL
captures have distinct acceptance scopes. The latter are retained evidence, not
a falsely claimed deterministic pixel oracle.

### Tests that fail on defective evidence

The attract oracle and instrumented capture require successful process exit,
all scheduled snapshot receipts, expected nonempty files and matching image
dimensions/content. They retain stderr, stdout, invocation and error details on
failure or timeout. Reference publication is explicit and refuses an existing
destination. A frame-600 capture with no polygon stream now fails correctly;
the later frame-2400 capture produced the complete required artifact set.

The V-Unit GPU CLI returns failure for any exact/native mismatch and writes
machine-readable comparison metrics. Quality previews carry `passed: null`.
Zeus has explicit color/depth tolerance and mismatch budgets; a permissive
threshold cannot silently become an exactness claim. CI adds Windows/Linux
Python tests plus Linux native HUD-filter and offline-force builds.

### Force events, telemetry and shared ownership

Toolkit v0.10.0 (`47b06f08cd6b3044e5167821f48f024882ef035f`) supplies the same
source-force rise detector in C++ and C#. It consumes every sample, including
silence, uses elapsed time rather than a fixed sample-count history, and tests
arrival/rise before strength scaling. MAME now uses it, runs the smoothing
worker at the profile's intended cadence, scales the supplemental cue with
global strength, and records candidate decisions and SDL rumble results.
Normal zero writes no longer truncate a cue immediately; watchdog/exit do stop
output. A candidate remains a waveform heuristic, not a decoded collision flag.

The toolkit also fixes directionless impacts at exactly centered steering,
resets public model diagnostics with the model, and supports the chosen IPv4 or
IPv6 UDP endpoint family. Previously absent @3/@4 conformance vectors were
added without changing the older vectors. Tests now run in CI with MSVC/GCC and
.NET. Cruis'n is registered as an actual source consumer. Its synchronization
tool reads a committed ref, checks old copies, updates both native consumers,
and verifies version markers and a source-content manifest. Existing feel
profiles and runtime user overrides were not retuned.

The first collection CI run then exposed a native profile-loader portability
defect: it joined directory/file names with a Windows-only separator. Fixed
canonically in toolkit **v0.10.1** (`c9b76b72087579ffd3b58734f22704e0fc078ecb`),
with actual file-loading checks on Windows and Linux. Both Cruis'n consumers
now pin v0.10.1. This follow-up changes no force math or feel profile.

The project-owned OCR filter now expires speed after **180 consecutive** missed
reads, rather than an accumulation of unrelated misses. Valid reads reset that
counter; an invalid frame cannot help confirm a large outlier. Fresh, held and
unavailable states have explicit trace fields, including raw reading and age.
File-only diagnostics now initialize the speed/RPM source tables without
requiring an external UDP destination. This repaired the diagnostic runs that
previously logged zero speed despite a readable USA HUD. It does not find a
native speed address or repair Off Road's unimplemented OCR box.

Emergency SDL cleanup now declares the complete ctypes ABI, preserves 64-bit
handles, checks the stop result, and unwinds resources after partial failure.
Mocked success/failure cases validate this code; no physical lifecycle test is
claimed.

## Measured results

Compact numeric evidence is committed in
[`results/proof/2026-09-05-diagnostic-milestone.json`](../../results/proof/2026-09-05-diagnostic-milestone.json).
Full cases remain under gitignored `results/diagnostics/`; their local paths
are included below and in the compact evidence. They contain local executable
copies and are intentionally not part of a public release.

| Check | Observed result | Boundary |
|---|---|---|
| Six archived V-Unit scenes, assessment | **100.0000%** exact native indices | Archived scenes, one NVIDIA GPU |
| Current CLI, capture-8000 | **100.0000%**, zero differences | Exact/native path; no shader change |
| Deliberately alter one reference pixel in a separate copy | **99.9995%**, exactly one difference, exit 1 | Original reference preserved |
| Zeus strict native comparison | Color **93.6313%**, depth **75.6636%**, exit 1 | Existing approximate renderer; known failure |
| Native attract oracle | Two runs, required frames 300/600 identical | Boot/attract repeatability only |
| USA effective-input gameplay replay | 6,000 frames, 100 native images identical | Synthetic route; not human-wheel certification |
| USA gameplay against the rebuilt MAME candidate | Same input/time and all 100 native images | Native output unaffected by the bounded fixes |
| USA live GL record followed by headless identity replay | 6,000 frames, 100 native images identical | GL images excluded from deterministic comparison |
| Bounded live GL evidence, source frames 4000..4030 | 32 BMPs, zero reported drops during captures | Async labels; 817x720 actual backbuffer, scale 4 |
| Harness regression tests | 21 pass locally | Mock failures plus pure comparisons, no wheel |
| Toolkit managed tests | 105 pass | 41 telemetry, 64 FFB |
| Toolkit native tests | Semantic tests at 30/60/250/1000 Hz; 10 profiles x 200 ticks match | MSVC and MinGW local; CI also passed |
| MAME incremental build | Successful with GCC 16.2 | Known device_t compiler warning remains |

The full exported MAME patch was also applied to the upstream `mame0286` files
in an isolated repository; all 23 changed paths reproduced the committed MAME
source exactly. Format-patch context whitespace is preserved deliberately.
The final MAME source is `1a2bb35f8ad58e2f0960c1d8b15bd361725a7a51`.
Toolkit CI for v0.10.1 passed on Windows and Linux
([run](https://github.com/d-b-c-e/dbce-wheel-mod-toolkit/actions/runs/33998611172)).
The final collection implementation `1131dc2` passed Windows/Linux harness and
native helper CI ([run](https://github.com/d-b-c-e/cruisn-collection/actions/runs/33998673255)).

Useful retained cases:

- `scenario-20260905T224940Z-knuxy44n/case`: native USA gameplay reference.
  Identity replay: `replay-20260905T225207Z-z7aqiwxr`; changed executable replay:
  `replay-20260905T225637Z-20cqcj_y`.
- `scenario-20260905T231026Z-s1l7_egt/case`: live scale-4 GL gameplay recording;
  its sibling `replay/` passes native/input comparison. The bounded capture
  shows actual race start. Some dark stippled areas also appear in native
  screenshots; that observation alone is not evidence of a widening defect.
- `replay-smoke-20260905T224001Z-vop1s2s_/case`: archived neutral USA seed for
  the synthetic generator. Earlier prototype recordings used intermediate
  metadata/layout handling and are not the supported schema-1 references.

### Car selection timing

In this USA scenario's selection interval, frames 2600..3600, headless/native
execution ran at **336.60%** real time. Live GL averaged **99.99%**, with host
frame p50 **17.20 ms**, p95 **25.31 ms**, p99 **77.64 ms**, and worst **124.41 ms**.
The GL capture interval came later, so its BMP writes do not explain these
selection measurements. Lua still captured a native PNG every 60 frames; both
that instrumentation and shader/resource processing need separate measurements.

This demonstrates uneven callback timing under the instrumented live path,
not a proven GPU bottleneck. The user's slow-selection game was not specified,
and average emulation speed can conceal poor pacing. The next experiment should
record the affected game's selection screen, distinguish decode/upload/scene/
present work, and repeat with screenshots disabled after validation.

### Collision-event analysis

The same archived motor trace (1,491 motor rows, 19,655 held-sample ticks) produced
**13 candidate arrivals at identical times** for strengths 25/50/100. Shaped
peaks were **0.24 / 0.50 / 1.00**, RMS **0.08030 / 0.16749 / 0.33498**. The 25%
peak reflects MAME's existing integer percent-to-toolkit conversion. Fraction
at configured maximum was **0.1323%** in each run.

These data verify source-event invariance and strength scaling. They do not
mean 13 actual crashes occurred, establish event precision/recall, or measure
torque at the rim. The analyzer uses 4 ms held samples and cannot reproduce
actual worker scheduling or the driver's response to force. Motor saturation,
supplemental rumble and condition effects still need a combined output budget.

## Next work, in order

1. **Acquire human driving references.** Record the routes and exact intervals
   exposing margin loss, sky failure, seams and collision events; establish
   identity replay separately for each game/revision. Include an unaffected
   control interval and the wheel/settings identity for attended FFB studies.
2. **Make live resource order testable and correct.** V-Unit can render retained
   quads after newer texture uploads; skip-to-latest loses persistent-page
   operations. Zeus has palette-slot and dropped-clear risks. Introduce ordered
   scene/resource replay, explicit fences and overflow failure before blaming
   UVs or painting over stale pixels. Use the recorded route to quantify each
   change. The current volatile ring still needs proper synchronization.
3. **Reassess widescreen by pipeline stage.** Distinguish absent guest geometry,
   clipped submitted geometry, missing sky/background coverage, wrong texture
   state, and raster edge rules. Expand guest visibility/frustum consistently
   with projection, and preserve native mode as a control. Crack fill should
   remain an explicit visual heuristic, not substitute for shared-edge rules.
4. **Increase distance in the game, with cost measurements.** A screen-space
   renderer cannot draw geometry the guest culled. Trace the guest visibility,
   LOD and track-resource decisions for one verified ROM; vary one boundary at
   a time and count submitted geometry, missing resources and frame cost.
   Validate all words in each ROM-specific patch group before writing any.
   No speculative new draw-distance constants were deployed in this milestone.
5. **Give crashes a measurable and physical identity.** Label real wall/car
   contacts, compare detector precision and onset, decode event state where
   possible, and implement an explicit steering-axis supplemental waveform.
   SDL 2.32 generic rumble's waveform/axis behavior remains a concern; simply
   raising its strength is not a proven remedy. Evaluate multiple wheel classes
   with normalized, bounded settings. Exotica's early gain/clipping is still open.
6. **Finish reusable contracts in the toolkit.** Add validity, age, units and
   provenance independent of the Forza packet; fix VID/PID selection/fallback,
   nonfinite inputs and time-weighted shift-pulse balance; add a fake output
   backend and lifecycle tests. Then ship a small native/managed new-game
   adapter template with explicit capability gaps and deterministic signal
   replay. Avoid copying Cruis'n's MAME-specific OCR into that shared layer.

Other reviewed open issues include Off Road speed, native speed-source discovery,
Forza clock/race-state semantics, unsupported high wheel buttons, updater handling
of obsolete plugin DLLs, and diagnostic bundle evidence preservation. This
milestone provides a stronger way to investigate them; it does not close them.
