# Recorded gameplay and diagnostic tests

The recorder saves MAME's effective game inputs, including analog wheel and
pedal interpolation, into an INP file. Playback runs the emulator with those
inputs. It does not physically turn the wheel. **Recording and playback both
disable physical FFB and external telemetry output in this first version.**
An attended FFB evaluation remains a separate drive.

The first verified gameplay case is Cruis'n USA: 6,000 emulated frames with
steering, accelerator, brake, coin, start and gear changes. All recorded inputs,
emulated timestamps and 100 native screenshots matched on playback. The route
was scripted. The user's LA Freeway wheel drive also passed: all 5,012 frames
and 83 native screenshots match, including selection and driving.
World, Off Road and Exotica require independent calibrated cases before claiming
the same coverage.

V-Unit launches now use D3D for MAME's underlying window while retaining the
owned GL widescreen overlay. On this rig, the same LA Freeway recording with raw
capture ran at 78% during car selection and 84% while racing with GDI; D3D held
100% in both intervals. All 83 native images matched. `CRUISN_VUNIT_VIDEO=gdi`
provides a compatibility fallback. This measurement covers USA on this rig;
World/Off Road and physical wheel/menu behavior need their own acceptance.

## Record a drive

From the repository root, using the existing rig configuration:

```powershell
python harness/run_rig.py --rom crusnusa --record-case results/diagnostics/my-drive --record-every 60
```

Insert coins, start, choose a car and drive normally. Quit through the game's
menu so MAME can close the INP and the recorder can validate the final evidence.
The directory must be new. `--record-frames 6000` instead requests a fixed stop
after 6,000 emulated frames, including boot and selection. `--windowed` is
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
```

The first command validates identity against the archived executable. The second
explicitly tests a changed executable. The third uses the recorded presentation
settings, including GL when it was enabled. All create new evidence directories.
`--timeout` bounds the run; partial evidence survives a timeout, which is a failure.

For an older case, explicitly test deferred encoding and capture a defect range:

```powershell
python harness/replay.py results/diagnostics/my-drive --snapshot-mode raw --video d3d --gl-log --gl-capture 3300:3900 --gl-every 60 --gl-max 20
python harness/replay.py results/diagnostics/my-drive --headless --snapshot-mode raw --until-frame 3442 --capture-state
```

Overrides and the replacement diagnostic script hash are retained in the report;
the original case is never edited. `--until-frame` explicitly compares only the
requested prefix, still checking every input/time and sampled image in that
prefix. `--capture-state` retains quads and native RAM at stop-minus-two, matching
the offline renderer's completed-scene convention. Missing dump files fail.
`--native-renderer` is an aspect-preserving windowed control with the replacement
GL disabled. `--gl-scale` and `--no-crackfill` are explicit presentation experiments.

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

## Generate an unattended driving case

```powershell
python harness/run_replay_smoke.py --output results/diagnostics/neutral-seed
python harness/synthesize_input.py results/diagnostics/neutral-seed/case fixtures/scenarios/crusnusa-input-sweep.json
```

The neutral seed verifies the installed INP layout. The USA-only generator then
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

**The stream-frame label is approximate.** A backbuffer is not fenced to that
native frame, and consecutive presents may have the same label. GL images are
retained and fingerprinted, but are not included in the native pass/fail pixel
comparison. Ordered resource replay and explicit scene fences are the next
renderer-harness work. These capture controls currently cover V-Unit, not Zeus.

## Analyze timing, telemetry and force without a wheel

```powershell
python harness/analyze_session.py results/diagnostics/my-drive/record --first 2600 --last 3600 --report results/diagnostics/selection-timing.json
python harness/analyze_ffb.py results/diagnostics/my-drive/record/ffb_trace.csv --profile cruisn-vunit@2 --strength 50
```

The timing report provides emulation speed and host callback p50/p95/p99/worst
intervals. It measures MAME callbacks, not GPU presentation latency or physical
force latency. Separate boot, selection, racing, and capture intervals.

The FFB analyzer compiles a small C++ executable against the same vendored
toolkit headers as MAME. It samples a held motor trace at 4 ms and writes the
shaper stages, impact candidates, peak, RMS and fraction at configured maximum.
It also accepts toolkit motor traces and `fixtures/signals/idle-hit.csv`.
`--compiler` selects a C++11 compiler. It never loads SDL or opens a haptic device.
PASS means the analysis completed; it does not rate subjective force quality.

The new OCR trace fields distinguish unavailable (`speed_status=0`), fresh (1),
and temporarily held (2), alongside `speed_ocr_reading` and `speed_age_frames`.
This metadata currently describes OCR sources. It is not yet a universal
telemetry validity contract or a repair of Off Road's missing OCR implementation.

## Automated checks and source ownership

```powershell
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python harness/sync_native.py
python harness/sync_toolkit.py --ref v0.10.1
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
