# Recorded gameplay and diagnostic tests

Current developer guide. Run ROM-free checks with `python harness/local_checks.py`;
GitHub Actions are disabled. See [local builds](LOCAL-BUILDS.md) and the
[documentation index](README.md) for release/source status. Paths below are
examples or named local references, not recordings included in a downloaded ZIP.

The recorder saves MAME's effective game inputs, including analog wheel and
pedal interpolation, into an INP file. Playback runs the emulator with those
inputs. Playback never physically turns the wheel. Recording defaults to FFB
and external telemetry off; `--record-with-ffb` explicitly retains the configured
force during an attended live recording. Synthetic runs and all playback still
force physical output off, even when the original recording used FFB.

The first verified gameplay case is Cruis'n USA: 6,000 emulated frames with
steering, accelerator, brake, coin, start and gear changes. All recorded inputs,
emulated timestamps and 100 native screenshots matched on playback. The route
was scripted. The user's LA Freeway wheel drive also passed: all 5,012 frames
and 83 native screenshots match, including selection and driving.
World v2.4/v2.5 and Off Road also have 6,000-frame scripted cases with 100
matching native images. Off Road's validated driving case uses H-pattern first
gear; a race entered in neutral is not counted as driving. Exotica now has a
6,000-frame driving case with 21 completed GL reference images. Its live GL path
skips CPU polygons, so matching black native images cannot validate gameplay;
headless/live differences alone do not establish nondeterminism.

V-Unit launches now use D3D for MAME's underlying window while retaining the
owned GL widescreen overlay. On this rig, the same LA Freeway recording with raw
capture ran at 78% during car selection and 84% while racing with GDI; D3D held
100% in both intervals. All 83 native images matched. `CRUISN_VUNIT_VIDEO=gdi`
provides a compatibility fallback. This measurement covers USA on this rig;
World/Off Road and physical wheel/menu behavior need their own acceptance.

## Device-free force-worker diagnostics

An explicit `--candidate` can run the actual native worker with
`--ffb-worker observe --ffb-worker-strength 50`. Physical output stays disabled.
`--ffb-worker-impacts on` selects the enhanced steering-axis mix; default observation
uses the legacy path. The frozen executable needs the shipped `force-profiles.ini`
beside it and no user profile override. See [the worker contract and validation](reviews/2026-09-11-ffb-actual-worker.md)
for required receipts, the current Exotica trim and remaining calibration limits.
Ordinary playback does not enable this observer. Software sink acceptance does
not certify delivered wheel force.

## Isolated Zeus upstream rendering trials

The separate native completion observer is documented in
[the waiting-cohort review](reviews/2026-09-11-exotica-native-completion.md).
`--exotica-host-handover observe` requires the explicit candidate, waiting/lifetime
observers and actual command-fence observation. It records bounded cohorts and
filtered proposal geometry; it does not enable another draw pass. Explicit `off`
verifies that no completion artifacts are produced. This mode is not a launcher
default or a recording requirement.

The newer isolated candidate also accepts `--exotica-host-handover draw`.
It requires those observers plus private future drawing and owned materials,
excludes the active-margin pass, and keeps physical FFB disabled. Waiting geometry
is filtered at the actual completion fence and uses the proposal's retained texture
image. `--exotica-host-future-present extended` displays the private result;
`original` preserves the normal display for regression comparisons. See the
[live waiting-draw checkpoint](reviews/2026-09-13-exotica-waiting-draw.md).

Choose checks according to the change. Start with affected unit tests and a short
recorded integration run. Use a full drive for later-course, reset, or transition
coverage; repeat matrices only when a change or failure warrants them. A verifier
fix can recheck retained captures without another emulator run. Such revalidation
must preserve the original failed report and identify the corrected verifier.
Instrumented captures do not establish normal gameplay performance.

The separate development candidate supports `replay.py --zeus-upstream
legacy|depth|alpha|blend|all`. This is an Exotica 2.4 diagnostic control for the
three changes in [upstream #16094](https://github.com/mamedev/mame/pull/16094),
not a draw-distance setting or a shipped default. Nonlegacy explicit trials
require `--candidate`; physical force remains off. The runner requires the native
candidate's acknowledgment, so an older binary cannot silently ignore the trial.
Absent controls preserve recorded settings. Legacy captures retain their original
format; new-policy model journals explicitly version and record their semantics.

For example, with the named local Amazon case and a built diagnostic candidate:

```powershell
python harness/replay.py results/diagnostics/drive-crusnexo-20260909-203557 --candidate build/candidates/edb517392f8/vunit.exe --zeus-upstream all --gl-capture 1800:8760 --gl-every 120 --gl-max 59
```

Use separate output directories and compare against `legacy`, then repeat the
trial. Counts and changed pixels do not establish visual correctness. See the
[upstream review](reviews/2026-09-09-zeus-upstream.md) and retained Amazon failure.

The newer `f537f74ddbf` candidate also supports `--zeus-palette legacy|guard`.
This independently traces pending GPU palette-row reuse or draws before an
upload would overwrite a referenced row. Both explicit modes require a candidate,
live Exotica GL and native startup/completion acknowledgment. Physical FFB stays0.
Add `--gl-log` for bounded per-frame conflict messages; complete totals appear
under `zeus_palette.result` in the replay report. Absent settings preserve old
recordings. See [palette lifetime](reviews/2026-09-09-zeus-palette-lifetime.md).

## Record a drive

For the next full Off Road and Exotica drives, use the ready
[track coverage presets and acceptance checklist](SCENERY-TRACK-COVERAGE.md).
The current scripted cases cover limited routes; they do not establish that
extended scenery works across tracks.

From the repository root, using the existing rig configuration:

```powershell
python harness/record_drive.py --game world --title "Germany Level" --output results/diagnostics/germany-next --with-ffb
```

This helper preserves the collection's saved resolution, widescreen mode,
steering sensitivity/curve, per-game graphics experiments and wheel bindings.
`--with-ffb` retains the saved force strength for attended driving; omit it for
no physical force. The lower-level `run_rig.py --record-case` remains available,
but its command-line defaults can differ from your saved collection settings.

An external clock opens by default, showing **emulated seconds and frame number**.
It starts at emulator boot, including selection screens. Report, for example,
"125.68 seconds, black road on the left" or the displayed frame number. Pausing
does not advance this clock. It samples the log approximately ten times per
second (a flush every six emulated frames plus a 50 ms UI poll), so a brief defect
should be inspected over neighboring frames too. It does not extrapolate time
while the game stalls. The passive Windows panel does not take focus or intercept
inputs and is excluded from native/GL diagnostic screenshots.

Use `--clock-position 550:80` to position the panel in screen pixels, including on
a second monitor; `--no-clock` disables it and its extra log flushes. The clock
uses Python's Tkinter. It closes when the recording finishes. The original
Germany Level case is `results/diagnostics/world-germany-20260906` (9,269 frames,
160.00815328 emulated seconds, 154 native snapshots); keep it unchanged.

Insert coins, start, choose a car and drive normally. Quit through the game's
menu so MAME can close the INP and the recorder can validate the final evidence.
The directory must be new. With `run_rig.py`, `--record-frames 6000` requests a fixed stop
after 6,000 emulated frames, including boot and selection. Its `--windowed` is
available. Recording currently requires this developer launcher; the packaged
collection's settings screen does not yet expose it.

New recordings save raw native snapshot pixels during play and encode the PNGs
after exit. This removes the measured PNG-compression hitch: on the user's route,
capture-adjacent callback intervals fell from a 79.5 ms median to 18.2 ms, while
all 83 images remained identical. Raw files remain in `record/raw-snap/` with
their own hashes. This uses MAME's `video:snapshot_pixels()`, the same render
target as its PNG snapshots; `screen:pixels()` reads a different buffer.
The raw header is `CRSNRAW1`, little-endian width/height, then BGRX pixels.
Raw disk writes still have a cost; this is not a claim of zero instrumentation.
Older cases retain their frozen PNG capture script unless explicitly overridden.

Record the route leading to a defect, rather than starting a test from attract
mode. Note the location and approximate time of the defect. The saved
`record/snap/frame_*.png` files and `record/frames.csv` locate it precisely in
emulated time. Native screenshots depict MAME's framebuffer, not the GL overlay.

Each case retains:

- `initial/`: initial NVRAM, controller configuration, settings, Lua script and
  any selected game-code patch; replay starts from a fresh copy every time.
- `binary/`: archived emulator and available SDL/profile dependencies. Rebuilding
  the working emulator cannot silently change the reference executable.
- `record/input/session.inp`: the actual effective-input recording.
- `record/frames.csv`, snapshots, motor/OCR trace and launch log.
- `case.json`: source revisions and dirty flags, settings, dependency hashes,
  ROM/container fingerprints, snapshot hashes, input ranges and clean-stop status.

The case includes a local emulator binary and machine configuration; it is
gitignored. ROM containers remain at their original paths and are fingerprinted,
not copied. Moving a case to another computer currently requires deliberately
resolving its ROM paths; there is no portable import wizard yet. Device-ROM
containers visible in MAME's `device_ref` list are fingerprinted when present.

## Replay and compare

```powershell
python harness/replay.py results/diagnostics/my-drive --headless
python harness/replay.py results/diagnostics/my-drive --headless --candidate E:/Source/mame-src/vunit.exe
python harness/replay.py results/diagnostics/my-drive
python harness/replay.py results/diagnostics/world-germany-20260906 --clock --candidate E:/Source/mame-src/vunit.exe
```

The first command validates identity against the archived executable. The second
explicitly tests a changed executable. The third uses the recorded presentation
settings, including GL when it was enabled. All create new evidence directories.
`--timeout` bounds the run; partial evidence survives a timeout, which is a failure.
`--clock` uses the same emulated timestamps during playback. For old cases it
explicitly copies the current diagnostic Lua script into the new replay directory
and records its hash; the archived script and original evidence stay intact.
Without `--clock`, replay does not request the extra clock flushes. Physical
wheel force stays off in either mode. `--small-window` reduces output image size
for dense GL capture while retaining recorded internal resolution; actual capture
dimensions are written to `captures.csv`.

For an older case, explicitly test deferred encoding and capture a defect range:

```powershell
python harness/replay.py results/diagnostics/my-drive --snapshot-mode raw --video d3d --gl-log --gl-capture 3300:3900 --gl-every 60 --gl-max 20
python harness/replay.py results/diagnostics/my-drive --headless --snapshot-mode raw --until-frame 3442 --capture-state
```

Overrides and the replacement diagnostic script hash are retained in the report;
the original case is never edited. `--until-frame` explicitly compares only the
requested prefix, still checking every input/time and sampled image in that
prefix. `--capture-state` retains quads and native RAM at stop-minus-two. The
default offline renderer selects a completed **draw page**, which can differ
from the page displayed onscreen. Missing dump files fail.
New native candidates use a bounded background writer for enhanced-renderer BMPs.
The ordinary path rejects an overflowing capture queue and the harness marks the
run incomplete. For dense offline ranges, explicitly add `--gl-capture-pacing`
together with `--candidate` and `--gl-capture`. It requires physical force zero
and waits at most ten seconds for storage without changing emulated inputs or time.
Older binaries must acknowledge this option; a missing acknowledgment fails.

The writer's512MiB encoded-image budget is separate from the renderer's command
ring. `evidence.capture_writer` reports completed writes, failures, rejected
requests, peak storage and file/drain/pacing times. A started writer without a
final completion receipt fails. Paced wall-clock playback can slow, so benchmark
normal gameplay separately. See [the measured failures and validation](reviews/2026-09-10-async-captures.md).

For live GL capture, leave playback time after the final requested capture so the
consumer can finish before emulator exit. Two frames is a minimum, not a guarantee:
dense near-4K BMP capture can build a much larger backlog. Extend `--until-frame`
within the recording, or use `--small-window` for an explicitly smaller output.
Actual dimensions remain in the receipts. Missing final captures fail even when
every earlier image is present; the report retains missing/unexpected frames and
maximum queued bytes. A requested budget too small for the interval fails before
launch, and legacy asynchronous receipts cannot satisfy a completed-frame request.
`--native-renderer` is an aspect-preserving windowed control with the replacement
GL disabled. `--gl-scale` and `--no-crackfill` are explicit presentation experiments.

`--patch FILE` explicitly replaces the recorded game patch for an experiment.
With `--capture-state`, the report verifies every patched word against actual
program RAM at the dump frame; a reverted, skipped or missing patch cannot pass.
`--patch-at-frame N` instead applies the complete, old-value-checked group at a
late frame, preserving earlier game history. Its application receipt is required.
This helps isolate visibility changes before additional work shifts guest frame
timing. `--probe-script FILE` is an explicit developer Lua frame callback, copied
and hashed into the run; it cannot combine with `--patch-at-frame`.

The product patch loader now validates an entire file before its first reset-time
write, including duplicate addresses and guards. A mismatch rejects the whole
file and logs an error. This prevents a partially installed trampoline on an
unsupported ROM. The existing per-frame self-healing mechanism is still per-word;
it is not yet a general atomic runtime patch-group/lifecycle manager.

The same-state USA visibility check used:

```powershell
python harness/replay.py results/diagnostics/my-drive --headless --snapshot-mode raw --until-frame 3442 --capture-state --patch patch/game/crusnusa-widescreen.txt --patch-at-frame 3436
python harness/verify_scene_extension.py BASELINE_CAPTURE CANDIDATE_CAPTURE --report results/diagnostics/extension.json
python harness/verify_quality.py --report results/diagnostics/quality.json
```

The extension verifier requires unchanged native pages/texture/palette RAM,
preserved original draw order, and additional quads entirely outside the native
x range. It is deliberately stricter than a comparison of unrelated screenshots.
It does not accept an unchanged scene as evidence of an extension. Run the native
GPU verifier on the captures separately. `gpu/renderer.py --buffers output.npz`
exports indices, coverage and transparent-texel-aware polygon ownership.
`--crackfill` and `--marginfill` are independent preview options.

`--object-visibility` on the extension verifier is a separate explicit mode for
new objects that slightly intersect the native edge. It preserves original draws,
order, previous page scene, textures and palette, and attributes each changed VRAM
word to added-quad coverage using the CPU rasterizer. It does not establish route
equivalence. World's wider object bounds pass isolated geometry checks yet change
the subsequent route, so that patch remains experimental and disabled by default.

For World2.4/2.5, compare the actual camera and ADC-read timelines as well:

```powershell
$env:CRUISN_MOTION_FIRST = '1800'
$env:CRUISN_MOTION_LAST = '9200'
python harness/replay.py results/diagnostics/world-germany-20260906 --probe-script lua/world_motion_trace.lua --output results/diagnostics/motion-reference
python harness/replay.py results/diagnostics/world-germany-20260906 --candidate E:/Source/mame-src/vunit.exe --probe-script lua/world_motion_trace.lua --clock --output results/diagnostics/motion-candidate
python harness/compare_world_motion.py results/diagnostics/motion-reference/run results/diagnostics/motion-candidate/run --report results/diagnostics/motion-comparison.json
Remove-Item Env:CRUISN_MOTION_FIRST, Env:CRUISN_MOTION_LAST
```

These environment settings apply only to that bounded probe. A different interval
can be selected, but both traces must have the same contiguous camera samples.
The comparator reports camera state, ADC values/reader PCs and exact read timing
independently and fails if any differ. Camera equality is not a complete physics
checksum. In the rejected visibility case, the input values agree while read
timing changes first and camera position later diverges at frame2732.

`harness/derive_case.py PARENT --candidate EXE --patch FILE --output NEW_DIRECTORY
--title TITLE --clock` creates a separate case by replaying the parent's INP,
checks the parent's initial state/input/ROM/evidence hashes, retains parent pixel
differences, and requires candidate identity replay. Its PASS means repeatability
only. Never use it to turn a failed original-route comparison into a passing
claim. The original Germany case is sufficient; the current normal executable
matches its full route without deriving a replacement recording.

Additional developer probes are bounded and version gated:
`lua/world_object_lifecycle.lua` logs far-gate admission/model selection;
`lua/world_texture_transition.lua` logs the Germany D/A transition and dense
native snapshots; `lua/dma_window.lua` records actual submitted quad provenance.
World often submits15 used DMA words, not16; a no-draw capture fails.
`lua/world_projection_distance.lua` is explicitly **mutating**, restores its
guarded changes, and exists only for short World2.4 distance experiments.
None of these are automatically enabled in a normal launch or replay.

The local `usa-widescreen-candidate-case` was deliberately re-recorded from the
original human INP with the improved executable/patch, retaining that provenance
in its manifest. Its 5,012 frames and 83 native snapshots pass identity replay.
This is a new candidate case: the original `my-drive` reference still fails a
full-run game-patch comparison, as additional guest work changes later history.

`report.json` passes only when the process exits cleanly, every expected frame
and screenshot is present, effective inputs and emulated time match, and all
sampled native images match. Changed references, missing files, truncated traces,
unreadable images, and repeated emulated timestamps cannot pass. Host timing is
recorded but excluded from the deterministic comparison.

This establishes repeatability of the sampled native output. It does not prove
that the recorded scene is correct, compare every displayed pixel between
snapshots, or establish live GL determinism. A candidate that intentionally
changes native output should fail and receive an explicit reviewed reference
update; the harness never blesses it automatically.

## Select the scene actually displayed

For a V-Unit run with both `--capture-state` and a completed
`--vunit-original-mirror-frame` capture, use the same run's renderer receipt to
select the original commands:

```powershell
python harness/vunit_display_scene.py results/diagnostics/my-run/run --report results/diagnostics/my-run/display-scene.json --quads results/diagnostics/my-run/display-scene.npz
```

The selector uses `vunit-mirror.json`'s count of consumed original commands, then
selects its visible physical page. It excludes commands the emulator produced
after that GPU capture, even if a longer recording continued for many seconds.
Do not substitute the final draw buffer or assume a fixed frame offset. The
report records the exact command ranges, their frame stamps, the consumed-prefix
hash and the prior same-page group. Partial journals and inconsistent receipts
fail rather than silently truncating input.

The optional NPZ contains original `current` and `history` DMA arrays; keep it
with the ignored local diagnostic resources. This is scene selection, not a
complete rendering proof. CPU overlays, current palette/texture contents, host
layers, margin clears and older framebuffer history still require their own
reconstruction. The default `gpu/renderer.py` draw-page behavior is unchanged.

The first qualification matches three retained Germany captures at completed
7280/7340, including the exact scene used by the
[road coverage repair](reviews/2026-09-15-world-road-polygon-coverage.md).
No additional game execution is required to select or recheck these saved scenes.

## Generate an unattended driving case

To continue an existing drive through later menus, use
[`harness/extend_input.py`](reviews/2026-09-16-scripted-recording-continuations.md).
It preserves the original INP rows and appends a labeled synthetic tail, including
the actual analog state at the join. The generated stimulus must pass through
MAME recording and prefix validation before becoming a new replay case. A
scripted continuation is not an attended recording of a new track.

`record_continuation.py` performs that recording and prefix check in one command:

```powershell
python harness/record_continuation.py results/diagnostics/my-drive tail.json --candidate build/candidates/COMMIT/vunit.exe --output results/diagnostics/my-drive-continued --title "Recorded drive plus scripted menus"
```

The tail uses the generator's scenario format, with every steering/pedal axis
explicitly set at tail frame0. The command validates the source case, preserves
its frozen settings and cheat actions, and disables physical FFB. Optional
`--display-size 3840:2160 --gl-capture FIRST:LAST --gl-every 300` selects the display
and verifies completed capture frames; frame numbers cover the entire new case.
GL must already be enabled in the parent. Existing capture ranges are cleared.
The output `case` is ready for an explicit candidate replay. No extra full drive
is automatically scheduled, and recording success does not establish route,
second-race or visual acceptance.
Use `--gl-crt on --gl-height 400` when creating a V-Unit control for the current
host renderer; inherited401-line recordings otherwise change pixels across the
whole image. `--probe-script lua/usa_motion_trace.lua` (or the matching game probe)
copies and fingerprints an explicit diagnostic script. Its documented frame
environment still needs to cover the desired interval in control and replay.

### Continuous host scenery candidate preset

```powershell
python harness/replay.py results/diagnostics/my-drive-continued/case --candidate build/candidates/COMMIT/vunit.exe --scenery-preset continuous-3x --output results/diagnostics/my-drive-host3x
```

The exact recorded ROM selects USA, World2.4/2.5, Off-Road or Exotica controls.
The preset combines the existing continuous startup/shutdown and quiet journal
paths with3x host scenery, CRT on and internal scale4. V-Unit uses native height400;
Exotica combines future/waiting/active scenery and marked original replacements,
with routine endpoint snapshots disabled. This requires a current candidate
including the optional endpoint-capture change (nativef0b4db1f25d or a compatible
successor), a GL recording and physical FFB remains disabled.
The preset now selects ordered original-view fallback for a rejected Exotica
future assembly, alongside V-Unit's preparation fallback. Current native5c4da4891a9
also supports bounded Exotica fault injection beyond the old capture window;
that is a separate explicit diagnostic, never a live-recording default.

Capture intervals, motion probes and display selection remain explicit. The
report records the expanded controls. Conflicting manual controls are rejected;
omit the preset when investigating a different policy. Existing ROM, recorded
patch and resource guards still apply. This is a diagnostic convenience, not a
launcher setting, deployment, equal visible3x distance guarantee or release gate.

### Record a fresh drive with the host candidate

First validate a recorded case's initial state and the selected candidate without
starting gameplay:

```powershell
python harness/replay.py results/diagnostics/my-drive --candidate build/candidates/COMMIT/vunit.exe --scenery-preset continuous-3x --display-size 3840:2160 --no-inherited-gl-captures --prepare-only --output results/diagnostics/my-host-plan
```

`launch-plan.json` binds the exact executable, adjacent runtime dependencies,
initial files and parent case. The report says prepared, unexecuted and
`passed=false`; successful preparation is not a replay pass. The explicit
`--no-inherited-gl-captures` clears the old screenshot schedule, while a separately
requested `--gl-capture` still applies to an ordinary replay.

When the driver is ready, start a new isolated recording:

```powershell
python harness/record_prepared.py results/diagnostics/my-host-plan --output results/diagnostics/my-new-drive --title "Open course with host 3x"
```

This uses the parent recording's wheel bindings and initial state, the prepared
candidate, CRT4x and continuous host scenery. **Physical FFB is off.** It removes
playback and finite recording stops, enables the external emulation clock, and
records fresh effective inputs until F12. Wait for recording validation after
closing. Changed dependencies, disabled input devices, old probes and scheduled
captures reject before gameplay. Use an actual driving case as the parent;
synthetic/headless cases can deliberately disable wheel input.

Add `--prepare-only` to the recording command to freeze its private case without
starting gameplay. That mode performs MAME's read-only ROM identity query; it
does not produce a completed recording. Use a new output directory for the
subsequent attended command. Normal completion separately reports input recording
status and native renderer receipt qualification. Deterministic replay, visible
distance quality and physical wheel acceptance remain separate. No launcher
settings, personal NVRAM or installed executable are changed.

```powershell
python harness/run_replay_smoke.py --output results/diagnostics/neutral-seed
python harness/synthesize_input.py results/diagnostics/neutral-seed/case fixtures/scenarios/crusnusa-input-sweep.json
```

The neutral seed verifies the installed INP layout. The generator supports the
five recorded ROM layouts across the four games (including both World revisions), and
constructs explicit digital pulses and analog current/previous values, runs the
stimulus through MAME while recording, and replays the resulting real INP. It
rejects an unexpected ROM, layout, timing or nonneutral seed. This is a synthetic
regression scenario, not a substitute for a skilled human drive or a general
INP editor. Its third coin pulse is necessary to start a game with the fixture's
credit settings; input changes alone do not prove that a test entered gameplay.

For bounded live renderer evidence on the same route:

```powershell
python harness/synthesize_input.py results/diagnostics/neutral-seed/case fixtures/scenarios/crusnusa-input-sweep.json --candidate E:/Source/mame-src/vunit.exe --gl --gl-capture 4000:4030
```

This uses V-Unit GL at internal scale 4 in a window. The requested resolution is
1280x720; actual window/backbuffer dimensions are recorded and can differ under
MAME's aspect/window sizing. It is not a 4K output acceptance test.
`--patch path/to/patch.txt` explicitly selects a game-code patch for a new case;
there is no implicit draw-distance experiment.

`record/gl-snap/captures.csv` identifies each BMP, presentation count, most
recently consumed stream frame, actual dimensions, visible page, queued bytes
and dropped-message count. Captures use the GL backbuffer, avoiding black GDI
screenshots. The bounded interval is limited to 240 stream frames and 180 BMPs.
Capturing can itself stall rendering; compare timing outside the capture interval.

New V-Unit builds fence GL captures after a completed visible frame and include
`completed_frame` in `captures.csv`. Legacy asynchronous captures remain labelled
as such and cannot be used by the strict GL comparator. Capture short consecutive
intervals with `--gl-every 1`, then compare actual pixels:

```powershell
python harness/gl_frames.py FIRST_RUN/run/gl-snap SECOND_RUN/run/gl-snap --frames 3000:3030 --report results/diagnostics/gl-identity.json
```

The validator rejects missing/duplicate frames, dimension changes and dropped
render commands. `--gl-stall 2995:100 --gl-queue-mb 16` exercises bounded consumer
stalls; a persistent stream failure makes the replay fail even if native video
continues. GL pixel comparison is separate from the native-image pass/fail.
Completed-frame captures and `--compare-gl` cover V-Unit and Zeus. Queue capacity,
stall, margin-fill and geometry-join controls are V-Unit-specific. Full-size GL BMP capture can
stall presentation and should not be used as a clean timing benchmark.

For Zeus comparisons, the harness selects a monitor whose dimensions match the
recorded completed frames. This prevents automatic placement on a 1080p secondary
display from invalidating a 4K reference. The report records the chosen device;
when no matching display exists, the comparison fails before launching. It never
resizes the reference to manufacture equality.

New cheat-enabled recordings retain the imported XML, selected choices, current
loader and native state-change log. Replay rejects changed cheat files or state
even when input samples match. See [the cheat guide](CHEATS.md).

`--no-marginfill` reproduces the new default: render submitted backdrop polygons
without suppressing them or copying native-boundary columns. Set
`MIDV_GL_MARGINFILL=1` only for the legacy experiment. `--no-crackfill` controls
the separate local coverage-based cosmetic pass.

## Analyze timing, telemetry and force without a wheel

```powershell
python harness/analyze_session.py results/diagnostics/my-drive/record --first 2600 --last 3600 --report results/diagnostics/selection-timing.json
python harness/analyze_ffb.py results/diagnostics/my-drive/record/force-source.csv --profile cruisn-vunit@2 --strength 50 --frames results/diagnostics/my-drive/record/frames.csv
```

The timing report provides emulation speed and host callback p50/p95/p99/worst
intervals. It measures MAME callbacks, not GPU presentation latency or physical
force latency. Separate boot, selection, racing, and capture intervals.

The FFB analyzer compiles a small C++ executable against the same vendored
toolkit headers as MAME. It samples a held motor trace at 4 ms and writes the
shaper stages, impact candidates, peak, RMS and fraction at configured maximum.
It also accepts toolkit motor traces and `fixtures/signals/idle-hit.csv`.
`--compiler` selects a C++11 compiler. It never loads SDL or opens a haptic device.
New recordings also have `force-source.csv` with emulated seconds/frame and raw
versus driver-adapted bytes. Prefer this clock for contacts and video alignment.
`ffb_trace.csv` uses host milliseconds and must not be treated as emulated time.
`--frames` adds each candidate's first completed game frame to the JSON report,
using the emulated clock even when host playback stalls. Out-of-range events
remain unanchored. Both `--frames` and `--labels` reject host-time input traces
instead of silently comparing incompatible clocks. Candidate anchors are review
targets, not automatic collision labels.

```powershell
python harness/analyze_ffb.py CASE/record/force-source.csv --impacts --labels contacts.json
python harness/run_rig.py --rom crusnusa --record-case results/diagnostics/attended-drive --record-with-ffb
```

`--impacts` evaluates the optional explicit steering torque envelope. Enable it
for attended product testing through **Settings → Force Feedback → Impact Cues**,
or with `[collection] ffb_impact=1` / `ffb_impact_<rom>=1`. A revision override
(including `0`) wins over its family and global settings. The World menu writes
the selected revision, normally `ffb_impact_crusnwld24`. It reserves 25% of the constant-force budget; independent
condition effects are outside that budget. Defaults and existing profiles remain
unchanged until this option is selected.
The enhanced detector reads raw force before driver gain/clamp/slew; the
structural component retains those adaptations. `raw_byte` and `detector_input`
in the offline stage CSV make that distinction inspectable. The clamped-hit
fixture verifies that reducing wheel output does not conceal the raw pulse.

Labels use this structure, with manually reviewed intervals and non-overlapping
contact windows. Times below are an illustrative schema, not labels for a drive:

```json
{"schema":1,"clock":"emulated_ms","coverage":[[1000,5000]],"events":[{"kind":"car_contact","start_ms":2000,"end_ms":2100}]}
```

The score ignores candidates outside reviewed coverage, reports missed contacts,
and counts duplicate candidates separately rather than inflating recall.
PASS means the analysis completed; it does not rate subjective force quality.

The new OCR trace fields distinguish unavailable (`speed_status=0`), fresh (1),
and temporarily held (2), alongside `speed_ocr_reading` and `speed_age_frames`.
Those fields describe the OCR fallback. USA v4.5 now decodes the actual guarded
numeric HUD text first; `MIDV_SPEED_NUMERIC=0` restores OCR-only comparison.
`speed_numeric_hud` and `speed_source` expose selection. `signals.csv` uses the
shared schema for sample time/frame, source, quality and speed in metres/second.
A held sample retains its original timestamp. Other games need their own numeric
producer research; this does not repair all telemetry readers.

## Automated checks and source ownership

```powershell
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python harness/sync_native.py
python harness/sync_toolkit.py --ref v0.11.1
python gpu/renderer.py results/capture-8000 --no-png --report results/diagnostics/native.json
```

The first two synchronization commands check without modifying files; add
`--write` to update the MAME copy from canonical sources. Toolkit synchronization
checks a committed Git ref and prior contents rather than blindly copying a
dirty checkout. `native/hud_speed_filter.h` belongs to this collection; force
shaping and rise detection belong to `dbce-wheel-mod-toolkit`.

GitHub CI runs the harness tests on Windows/Linux and the native HUD helper and
FFB analyzer on Linux without ROMs or hardware. Local GPU checks still require
OpenGL, moderngl and captured reference data. Exact native V-Unit mismatches now
return exit code 1. Zeus requires explicit tolerances and pixel budgets; its
known approximate rendering must not be described as native bit exact.

## Object and detail-distance investigation

```powershell
python harness/replay.py CASE --headless --until-frame 3840 --probe-script lua/usa_object_lifecycle.lua
python harness/replay.py CASE --headless --until-frame 3060 --capture-state --patch patch/game/crusnusa-lod-experiment.txt --patch-at-frame 3054
```

The USA v4.5 probe verifies instruction signatures and traces an explicit bounded
interval. The experimental LOD patch changes detailed/medium model thresholds,
not the far plane or scene-object creation. Its native screenshot differences
are expected and retained; they must not be silently blessed as identity passes.
See [the follow-through review](reviews/2026-09-06-follow-through.md) for the
specific model transition and cross-game coverage.

```powershell
python harness/analyze_distance.py RUN/run/lifecycle.csv --report distance.json
python harness/run_regressions.py --candidate E:/Source/mame-src/vunit.exe
```

The suite manifest is `fixtures/regressions/collection.json`. Local recordings
and ROMs are required; missing cases fail explicitly. Use `--only usa-widescreen`
for a recorded subset. Each case preserves its own input/native/GL coverage and
timing windows. The candidate's displayed Exotica frames are compared with
`--compare-gl`: its default live path skips CPU polygons, so native screenshot
equality alone cannot certify the displayed race. A uniform final visual reference
is rejected. This basic guard does not judge the correctness of nonblank images.

`--zeus-native` enables CPU and GL rasterization together for diagnostic comparison;
it is slower and expected to differ from a case whose native race images were
black. `--zeus-stop-frame 5500` deliberately stops the GL consumer to exercise
CPU fallback. Fallback makes the replay fail even if CPU presentation recovers.

For pixel attribution, render with `gpu/renderer.py CAPTURE --wide --scale 4
--buffers buffers.npz --output-dir PREVIEW` and inspect with
`python harness/inspect_pixel.py buffers.npz 291 1108 --report pixel.json`.
`--align-tjunctions` is an opt-in geometry experiment in both offline renderer and
live replay. It matches closed three-polygon joins with consistent material/UVs;
it never applies to native exact rendering. See the
[latest rendering review](reviews/2026-09-06-seams-distance.md) for its limits.

For V-Unit pause/menu regression checks:

```powershell
python harness/check_menu.py results/diagnostics/world-germany-20260906 --candidate E:/Source/mame-src/vunit.exe --frame 1800
```

This explicitly drives menu key-handler edges inside the emulator while physical
force is disabled. It requires visible menu text and selection changes, stable
paused frames, a working CRT toggle, resumed frames and clean Exit. Menu images
are recorded separately from completed gameplay captures. It tests the overlay
path; it does not exercise OS keyboard routing or the collection's shell itself.

## Transmission assets and diagnostic failures

Enhanced World 2.4 keeps the outgoing transmission atlas in GL uploads until
its UI models leave the actual render list. `replay.py --no-ui-assets` explicitly
disables that display fix for a control. Capture through the transition with
`--gl-capture 1200:1400 --gl-every 10 --gl-max 30 --until-frame 1442` on the
Germany recording; allow frames after the final requested GL image for shutdown.
Native snapshots retain the game's original atlas reuse, so use completed GL
images to judge the display fix. No production behavior depends on these frames.

`lua/world_asset_jobs.lua` and `lua/world_ui_models.lua` trace the loader and
outgoing models through bounded, revision-guarded `--probe-script` experiments.
Probe load/callback errors now request clean exit instead of bypassing the stop
frame until timeout. The evidence validator rejects `[LUA ERROR]`, explicit probe
failures and snapshot errors even when MAME exits with code zero. Errors in a
memory tap are also rejected; the callback wrapper alone cannot guarantee an
immediate stop for errors raised inside MAME's separate tap dispatcher.

## Selective scenery distance

`replay.py --scenery off|mountains|trees|all` selects the native World2.4 candidate
and records its setting plus per-frame `scenery.csv` counts. `derive_case.py`
accepts the same option and archives it for identity replay. Parent pictures can
legitimately differ; derivation retains those differences rather than replacing
the parent recording. See the [native scenery evidence](reviews/2026-09-06-native-scenery.md).

`compare_scenery.py CONTROL.csv CANDIDATE.csv --allow-added-model ca57f3
--max-added-extent 32 --report geometry.json` checks matched-frame provenance,
including duplicate quads and ordering. The extent limit is optional and intended
for small distant-tree additions. It does not judge visible pixels, whether a
tree is occluded, or driving-route equivalence. Unknown models remain explicit.

Use `--alignment scene` to compare complete nonempty page-control runs when guest
drawing work spans a frame boundary. It drops incomplete edge runs, preserves
duplicates and original order, and records both runs' frame ranges. Keep the
strict frame comparison too: a scene match does not erase a timing difference.

For completed GL images sampled every few frames:

```powershell
python harness/gl_frames.py CONTROL/run/gl-snap CANDIDATE/run/gl-snap --frames 1980:2240 --every 2 --details --contact-sheet comparison.png --report visible.json
```

This checks the requested capture sequence, reports changed pixels and bounds,
and creates an overview of the first/largest/last changes. Bounds use exclusive
right/bottom coordinates. Different-sized images are identified separately.
`--every N` uses global frame multiples, matching the native capture producer.
Reused filenames, missing frames and dropped stream messages are rejected.
Expected visual changes still fail pixel identity; inspect `error` and the
completed evidence before interpreting FAIL as a failed launch or timeout.

`lua/world_scenery_events.lua` and `harness/analyze_scenery_events.py` locate
candidate appearance windows from complete drawing scenes. Submitted bounds are
not visible pixels; slot reuse is not proof of LOD. The read-only activation probe
can then trace a specific object's fields, model assignment and call stack.
Literal `CRUISN_*` probe parameters are archived beside the script hash in replay
reports. Mutating probes are explicitly labeled and remain separate from product
options; their effects can outlive the bounded callback interval.

`world_scenery_activation.lua` also has an explicit
`CRUISN_ACTIVATION_WATCH_EXISTING=1` mode for a slot allocated before the capture
window. It verifies the initial model, requires observed writes, and fails if
the slot changes to another model. The default still requires an actual model
assignment; missing allocation evidence is not silently accepted. This mode
cannot be combined with assignments-only capture.

`world_pending_distance.lua` tests shared World 2.4 pending admission over at most
240 frames, with `CRUISN_PENDING_FIRST`, `CRUISN_PENDING_LAST` and
`CRUISN_PENDING_LEAD` (0..8). It requires `--scenery-lead 0`. Use `--scenery off`
to isolate it from the selective distance feature. It changes game execution;
objects transferred during the experiment remain transferred after it ends.
The archived `world_tree_activation.lua` probe is a selective comparison, not
the planned global solution. See the [global assessment and measured route
divergence](reviews/2026-09-06-global-distance-and-native-port.md).

## Exotica far distance and submission timing

Before scheduling another distance replay, check the saved future and waiting
packets for geometry in the band being changed:

```powershell
python harness/exotica_distance_samples.py results/diagnostics/my-comparison/run --frames 5072 5644 --require-third-band --report results/diagnostics/distance-samples.json
```

Choose actual saved snapshot frames. This command validates ordered instance
spans and quad counts; it does not render or establish completed visibility.
The strict option fails selection if all selected samples have zero third-band
polygons. Earlier admissions may still affect later original replacements.
See [the sample-selection findings](reviews/2026-09-15-exotica-distance-sample-selection.md)
before repeating the existing Amazon windows.

For Exotica far-distance diagnostics, `run_exotica_distance_trials.py` runs a
bounded stock/coherent/2x/3x/repeat matrix. `compare_exotica_distance.py` compares
actual branch outcomes at equal poses while excluding only the requested far
value. These tools do not grant visual acceptance; use completed GL and actual
Zeus submissions. The current trial found extra admissions but no sampled pixel
benefit. See [the far-distance evidence](reviews/2026-09-08-exotica-far-distance.md).

`compare_zeus_capture.py` defaults to strict frame-stamped submission equality.
Its explicit `--alignment scene` excludes only quad frame stamps and enumerates
each excluded change, preserving order, geometry and effective palettes. Retain
both reports: a scene PASS must never replace a strict timing FAIL.

`run_exotica_admission_trials.py` holds coherent sphere projection/bounds fixed
while testing two earlier admission-limit consumers at160000/190000.
`analyze_exotica_streaming.py` validates the independent second comparison after
each pass and the loader's actual threshold/cursor. The interval is bounded;
admitted objects can remain active after the taps are removed. The current
candidate repeats but fails strict scene-state/order checks; see
[the admission review](reviews/2026-09-08-exotica-admission.md).

## Host preparation failure trials

For candidate V-Unit host drawing, `--vunit-host-failure original` latches extra
scenery off if read-only preparation fails before submission. Add
`--vunit-host-inject-failure-frame N` to exercise the first qualified scene at or
after N. The explicit `strict` policy retains fatal diagnostic behavior. These
controls require physical FFB0, live GL and a scene interval ending before the
replay drain. They do not apply to Exotica or recover device/transport failures.

A degraded run intentionally returns FAIL even when its independent original
input/image comparison passes. Inspect `vunit_host_failure.result`, including
actual frame, stage and fallback decision; do not accept it as rendering parity.
`--vunit-original-mirror-frame N` now supports USA, both World revisions and Off
Road, with split/tagged host ownership. World fade controls remain World-only.
See [the actual fallback qualification](reviews/2026-09-15-vunit-preparation-fallback.md).

Exotica has a separate `--exotica-host-failure original|strict` and
`--exotica-host-inject-failure-frame N`. This only covers future-assembly
rejection in the combined private pipeline. Already owned work must finish, CPU
and GPU retirement receipts must agree, and the renderer switches to the original
target. Source snapshots must precede injection. A recovered run remains an
explicit degraded FAIL. See [the ordered recovery qualification](reviews/2026-09-15-exotica-retirement.md);
resource/ownership/transport failures are still fatal.

`python harness/analyze_exotica_runtime_budget.py PATH/TO/run --report NEW.json`
measures admission-ledger occupancy from saved lifecycle/packet watermarks and
compares completed journal totals to current diagnostic caps. It does not launch
the game or estimate process memory. See [the continuous-runtime audit](reviews/2026-09-15-continuous-runtime-budget.md).

## Drivetrain and actual telemetry packets

USA v4.5, World2.4/2.5, Off Road and Exotica have separate verified rev and gear
producers reading the player structures used by their HUDs, with ROM-instruction,
pointer, value-range and HUD-lifetime guards. `drivetrain.csv`
records native frames, emulated seconds, source, raw rev units, normalized tach
fill and estimated RPM. The 900–8,000 RPM scale is a presentation choice.
`gear_source=3` means game state; `=1` means the legacy shifter-input fallback.
`rpm_estimated=1` identifies the game-derived arcade scale; zero RPM outside the
HUD is unavailable, not a measured stopped engine. `MIDV_TELEM_ARCADE_RPM=0`
disables the scale without disabling actual gear telemetry.

```powershell
python harness/replay.py results/diagnostics/my-drive --candidate E:/Source/mame-src/vunit.exe --headless --telemetry-loopback --output results/diagnostics/usa-wire-new
python harness/analyze_drivetrain.py results/diagnostics/usa-wire-new/run --require-drive --output results/diagnostics/usa-wire-new/drivetrain-report.json
```

Loopback uses fresh private localhost ports and captures Forza and JSON packets;
it never sends to the user's SimHub ports or enables physical force. The analyzer
requires packet/sample agreement, a complete Forza sequence and valid values.
`--require-drive` additionally requires all four gears and RPM drops within eight
frames of every upshift. That strict diagnostic passes the accepted USA drive;
World has real countdown/rapid shifts that do not drop revs, so the normal suite
compares its actual memory values without imposing artificial drops. A control replay
can add `--no-arcade-rpm` (analyze without `--require-drive`).

`lua/usa_drivetrain_memory.lua` independently reads the guarded player structure
over a bounded interval. Pass its CSV with analyzer `--memory FILE`. The report
explicitly accounts for Lua's one-based frame number versus the native zero-based
counter. `lua/usa_tach_probe.lua` traces the palette/texture writers; tap errors
are retained and rethrown from the next frame callback because MAME can otherwise
swallow a tap-callback exception. A replay PASS alone doesn't validate arbitrary
probe contents. See [the provenance and verification report](reviews/2026-09-07-usa-drivetrain-and-startup.md).

The regular seven-case suite captures UDP and runs independent probes for every
game, requiring at least500 active samples and10MPH. World2.4 uses
`lua/world_drivetrain_memory.lua`; World2.5, Off Road and Exotica use
`lua/drivetrain_memory.lua`. Off Road/Exotica's existing synthetic cases cover
first gear only. A passing suite cannot certify their all-gear behavior or tactile output.

`force-gate.csv` retains enabled state, raw motor command and requested host level
separately from the unchanged four-column `force-source.csv`. Exotica releases
force outside verified active driving. World forwards menu/race-end requests
after the user's regression report. `analyze_force_gate.py DIRECTORY --memory CSV
--game ROM --output JSON` checks the driving gate; add `--policy passthrough` for
current World builds to require nonzero menu requests and no gated writes.
Physical output stays disabled; requested levels are not wheel torque measurements.
Current `force-gate.csv` also includes `game_invert` and `device_invert`.
`--check-polarity` validates these against `frames.csv` DIP values and recomputes
the requested signed level from `force-source.csv`. Exotica normalizes its cabinet
motor switch; World keeps game polarity0. Device inversion remains separate.
See [the all-game findings and final validation](reviews/2026-09-07-release-feedback.md).

For synthetic course-selection and short sightline scouting, `synthesize_input.py`
accepts `--record-only` to retain a MAME-written input case without automatically
running it a second time. The resulting report explicitly says `passed: false`
and `identity_replayed: false`; recording completion is not repeatability or
rendering acceptance. Use this only when the next planned candidate comparison
answers a concrete question, rather than repeating an unchanged scouting run.

`--gl-capture FIRST:LAST --gl-every N` allows sparse images over a longer scenario,
with a maximum of241 images and time left for presentation before stopping.
Cadence follows global native frame multiples: `3060:5460 --gl-every 400` captures
3200,3600,4000,4400,4800,5200. It does not start its cadence at3060.

For source attribution in saved Exotica geometry:

```powershell
python harness/exotica_fragment_sources.py RUN_DIRECTORY --frame 5200 --band 3 --require-visible --output NEW_REPORT_DIRECTORY
```

This performs no game execution. It first requires exact saved insertion color
and depth, then labels the last surviving fragment against completed depth.
`--save-labels` retains local per-pixel arrays. Blended contributions and actual
final-screen visibility require separate checks; see the
[Mars qualification](reviews/2026-09-16-exotica-mars-distance.md).

Scheduled emulator resets are retained separately from MAME INP, which records
game inputs. `record_continuation.py --soft-reset-frame N` adds a reset after the
preserved parent input prefix; repeat the option for up to16ordered resets.
The frame is relative to the entire case, and at least two frames must remain
before stopping. Existing parent schedules are retained by continuation and
derivation. `Recording.prepare(..., session_actions=[{'frame': N,
'action': 'soft_reset'}])` exposes the same bounded mechanism to local harnesses.

New cases freeze the schedule and Lua loader with their initial hashes. Normal
`replay.py` executes the same schedule automatically and requires matching actual
request/completion receipts and timing. Physical FFB is disabled. Missing,
duplicate, unexpected or delayed resets fail evidence validation; successful
recovery still does not establish scenery parity. This currently supports complete
scheduled cases, not cutting a replay before a later scheduled action. Manually
pressing MAME reset is not automatically converted into a replayable schedule.
See [recorder reset continuity](reviews/2026-09-16-session-soft-reset.md).

The continuous Exotica candidate now has an explicit quiescent reset path.
`replay.py` verifies its CPU/GPU material boundary and separate fresh-start
proofs against the scheduled action. An interrupted-work reset remains a strict
failure. A successful reboot with no marked scenery is not accepted as full
extended-renderer workload coverage. See the [reset assessment](reviews/2026-09-16-exotica-quiescent-reset.md).

New case manifests identify MAME source only from a build receipt matching the
archived executable bytes. A missing receipt leaves source identity unknown;
the enclosing Git checkout is labeled separately. See [build provenance](reviews/2026-09-16-binary-provenance.md)
for attaching a verified native export before recording. Historical manifests
remain intact; their old emulator_source field alone does not prove a native revision.

## Observe USA distance opacity without applying a fade

The candidate-only --usa-host-fade-metadata transports all USA host depths with
3x future drawing, far coverage and an explicit --vunit-original-mirror-frame.
Add --usa-host-opacity-observer to record the hypothetical20k outer envelope
in both completed pages without changing displayed colors. Physical FFB must
remain off. This is a visibility diagnostic, not a road policy or launcher option.
See [the qualified measurement](reviews/2026-09-16-usa-opacity-observer.md).

## Off-Road opacity observation

--offroad-host-fade-metadata and --offroad-host-opacity-observer use the same
bounded original-mirror workflow with explicit3x future drawing, stock sphere
admission and physical FFB0. Projection remains bounded below191040; the observer
measures an11824-unit envelope below141888 without applying a fade or clipping
existing geometry. See [the completed-frame result](reviews/2026-09-16-offroad-opacity-observer.md).

Exotica continuous candidates now distinguish a reset before any pool/scene
ownership from an active quiescent reset. The former retains the first startup
proof and has no GPU-reseed receipt; mixed schedules preserve both kinds of proof.
Interrupted bootstrap, pending work and degraded resets still reject. See
[the startup-reset qualification](reviews/2026-09-16-exotica-startup-reset.md).

### Screen Off-Road fade candidates before replay

Use harness/offroad_fade_screen.py SAVED_RUN --frame N --report NEW_REPORT.json on a scene from offroad_scene_resources.lua. This checks ordered2x/3x geometry and decodes C31 camera depths. A zero envelope avoids an unnecessary capture; a positive result is not completed visibility or fade acceptance. See [the actual early/late El Paso checks](reviews/2026-09-16-offroad-visible-boundary.md).

### Original Off-Road billboard capture

The read-only offroad_billboard_capture.lua probe uses CRUISN_OFFROAD_BILLBOARD_FIRST/LAST (default2500..2520, maximum121frames). Verify its local output with verify_offroad_billboard.py RUN --native ANALYZER --report NEW_REPORT. This checks actual current-basis matrices and four-vertex XYZ only; it does not accept future sources, materials or displayed geometry. See [the foundation review](reviews/2026-09-16-offroad-billboard-foundation.md).


## Match host preparation to its displayed frame

A mirror frame can display an older scene. The completed renderer's auxiliary
count now binds each physical page to its last submitted host preparation.
Check host_completion in the mirror result; a captured preparation is not
automatically the visible scene. This is submission alignment, not a substitute
for checking original geometry, materials, CPU writes and completed pixels.

For a new V-Unit candidate capture, --vunit-host-metadata-frame S separates
the saved depth operands from --vunit-original-mirror-frame P. S must be within
the host preparation interval and no later than P. Explicit selection requires
the completed visible page to contain the complete S scene; a mismatch fails
verification. The existing behavior remains available when the option is omitted,
but the report explicitly states whether its source matches the visible page.
The option requires the game's existing depth-metadata mode and physical FFB0.

For a source-aware screen of blue margin openings, use
`python harness/screen_vunit_sky_gaps.py PASSING_REPLAY_DIR --report NEW_REPORT.json`.
The replay must contain both a completed `vunit-mirror.json` and same-run
`capture/quads.bin`; the screen verifies their receipts and never launches a
game. Its short backdrop-between-surfaces regions are diagnostic candidates,
not an accepted fill or a substitute for temporal/visual review. See
[the saved ten-image screen](reviews/2026-09-23-vunit-sky-gap-screen.md).
The default maximum gap is now 32 coarse pixels, which catches the longer
El Paso 3136 opening; the report also shows ordinary sky runs connected to a
host-bounded seed. Disconnected ordinary sky remains unclassified.
