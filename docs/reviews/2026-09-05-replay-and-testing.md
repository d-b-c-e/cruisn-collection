**Recorded driving and a dependable testing harness — proposal, 5 September 2026**

Yes: recording a real wheel-driven session and replaying the game inputs is feasible in principle, and MAME already contains the important input machinery. The proposed first implementation should build on that machinery. Repeatability on these four modified drivers still needs an explicit proof; this review did not run a new recording/playback session.

The desired product experience is simple: choose “Record drive,” play normally, mark an issue if useful, and exit normally. A saved case then lets a developer replay the same route, compare rendering changes, inspect force signals, and measure the car-selection slowdown without asking the user to drive it again each time.

The user specifically reports that most defects appear in motion during actual gameplay, sometimes well into a level. Player-driven recordings are therefore the primary visual regression suite. Attract mode remains a useful narrow control; passing it must not close a gameplay report. The recording has no proposed one-minute reachability limit: retain however much driving is needed to reach the issue, then analyze the marked minute or shorter interval.

This proposal accompanies the [assessment](E:/Source/cruisn-collection/docs/reviews/2026-09-05-assessment.md) and [FFB quality plan](E:/Source/cruisn-collection/docs/reviews/2026-09-05-ffb-quality.md). It describes future interfaces and acceptance criteria; none of the proposed commands or files should be mistaken for an implemented feature.

**What MAME already records**

In the local source, [`record_port`](E:/Source/mame-src/src/emu/ioport.cpp:3246) and adjacent frame-recording functions store emulated frame time, digital/default port state, and each analog field's current accumulator, previous accumulator, sensitivity and reverse setting. [`playback_port`](E:/Source/mame-src/src/emu/ioport.cpp:3109) restores those analog values. This retains the information used for interpolated game-visible steering, rather than merely recording keyboard events or a coarse sequence of left/right commands.

MAME exposes `-record`, `-playback`, `-input_directory`, and `-exit_after_playback`. Its [official command-line documentation](https://docs.mamedev.org/commandline/commandline-all.html#core-state-playback-options) cautions that reliability varies by system and mismatched configuration/NVRAM can cause desynchronization. For this project, use preserved calibrated starting files in an isolated run directory; deleting the user's calibration is unnecessary.

The custom steering curve is applied while accumulating host input, before the analog state is recorded. Playback should therefore reproduce the transformed steering the game received, with that behavior checked against actual game reads. Record the original device samples separately if physical input calibration or alternative steering curves are also being evaluated.

The first proof must include pedals, coin/start, view buttons, manual gears and Exotica's sequential virtual-gear path. Derived/custom port readers and any host-polled controls deserve explicit coverage; not everything in the surrounding application automatically belongs to an INP file.

**Two complementary replay layers**

| Layer | Recorded material | What it can establish | What it cannot establish alone |
|---|---|---|---|
| Full game replay | INP plus exact boot state, configuration and build identity | Route, contacts, game culling/streaming, original motor commands, live renderer behavior | Identical physical wheel feel under a new profile |
| Render transaction replay | Ordered draws and all relevant texture/palette/VRAM/framebuffer mutations, starting state, display boundaries | Fast isolated shader/coverage/order experiments, state corruption and GPU timing | Geometry the game never created or submitted |
| Force-signal replay | Timestamped raw signals, verified events, resolved profile and output-clock schedule | Algorithm comparison, clipping, filtering, event preservation, output protocol checks | Driver adaptation and actual delivered torque without hardware evaluation |

Full game replay is the first milestone. Render transaction replay is the second: it allows many graphics experiments without waiting for boot or running game logic. Force replay can reuse the toolkit's existing conformance work while adding the integration stages it currently misses.

The current quad captures plus final memory dumps are valuable, but they are not yet a complete transaction recording. A later texture snapshot cannot reconstruct which texture bytes an earlier quad used. Both V-Unit and Zeus need an explicit ordered resource history and a complete initial snapshot.

**Capture from boot; analyze the marked minute.**

Record from a reproducible start, even if only the middle minute is interesting. Preserve the inputs leading through calibration bypass, coin/start, car selection and track selection. Let the user mark the interesting interval without discarding the prefix. Replaying the prefix is an acceptable initial cost and avoids guessing how to reconstruct an arbitrary mid-race state.

Save-state checkpoints can accelerate this later, but first prove their equivalence to a boot replay. MAME's saved emulated state does not automatically include custom GL mirrors, pending queues, presentation pages, host-side FFB filter/history, or telemetry globals. A correct checkpoint must restore or rebuild those components and align the recording cursor. Do not advertise “start anywhere” simply because a `.sta` file can be loaded.

Use the same initial NVRAM/config for each replay; never reuse files mutated by the preceding replay. Disable unintended autosave/auto-load behavior for the case. Record startup time/seed inputs and verify anything else with a nondeterministic external dependency.

**A saved case should be self-describing.**

Proposed structure, not existing files:

```text
case-id/
  manifest.json
  inputs/session.inp
  initial/nvram/...
  initial/cfg/...
  initial/controller.cfg
  settings/effective-config.json
  settings/resolved-force-profile.ini
  annotations/events.json
  reference/checkpoints.jsonl
  reference/native-frame-hashes.jsonl
  reference/selected-output-frames/...
  optional/render-commands.bin
  optional/device-inputs.bin
```

Each replay writes into a new result directory referencing the immutable case. Keep local ROMs external and identify them by set/revision and hashes. A manifest should contain:

- Collection, MAME patch/base, toolkit, shader and executable identities; dirty-tree status if applicable. A Git commit alone does not identify an uncommitted binary.
- ROM set/clone, configuration/DIP values, calibration/NVRAM hashes, effective command line/environment, recording format version and starting state.
- Display dimensions, internal render dimensions, visible area/pixel aspect, CRT/repair settings, GPU/driver, and pacing settings.
- Force profile ID and resolved contents/hash, adapter/backend identity and all force settings, even when hardware output is suppressed.
- Case purpose, expected game phases, prefix length, marked analysis interval, expected final frame/event and capture manifest.
- Emulated timestamps/frame numbers alongside host times; do not assume a universal 60 Hz clock.

Store the minimum necessary device identity/configuration for reproducibility. Avoid copying unrelated runtime folders or replacing the user's normal installation state.

**A proof of replay must detect failure, not just finish.**

Start with one 60–90 second actual drive containing meaningful steering, throttle changes, braking, a gear change and a reproducible contact. Replay it twice from isolated copies of the same initial state. Include a separate short car-selection sequence. Once one game passes, repeat the proof for each game and supported ROM revision family.

Compare game-visible input reads and deterministic state checkpoints. For an unchanged executable, also compare native frame hashes and render-command sequence hashes. MAME's existing emulated-time synchronization check is useful but does not establish that the world state is identical: two diverged sessions can still advance time at the same rate.

At the first divergence, retain the preceding input samples, selected CPU/device state, render commands, and surrounding frames. Report a failing/invalid replay, not a visual regression. Never silently continue with live wheel input if playback ends or becomes invalid.

For a shader-only change, game state and original submitted commands should remain unchanged. For a deliberate culling/game patch, some state/commands are expected to change; specify the allowed differences and retain input/route invariants. Do not “fix” tests by accepting arbitrary state drift or by regenerating all baselines automatically.

Suggested initial replay gates:

| Gate | Required result |
|---|---|
| Process completion | Clean expected termination; no timeout, crash, desync or output failure |
| Recording identity | ROM/build/config match declared compatibility rules |
| Input behavior | Same expected digital/analog sequence at declared game-read checkpoints |
| Scenario completion | Correct phases and final marker reached; no calibration/menu stall |
| Artifact completeness | Every requested frame/log present with exact IDs and dimensions |
| Deterministic baseline | Unchanged runs agree on declared state/native-frame/command checks |
| Isolation | Case start remains unchanged; no writes to normal rig calibration/configuration |
| Output policy | Graphics replay does not acquire or actuate a wheel |

**Separate physical output from signal generation.**

Autonomous graphics tests should preserve the game's motor calculations and diagnostic signals while routing force output to a no-device backend. Merely disabling all FFB initialization may currently suppress useful shaping diagnostics too; make output suppression and algorithm evaluation separate switches.

Verify that playback overrides physical steering/pedals at the game boundary. Host-polled overlay commands such as Esc/F9 need a separate policy: record semantic commands with timestamps, or keep them out of deterministic cases. Global physical key polling must not accidentally change the replay. Clean exit should use normal emulator shutdown, not a hard kill with an active effect.

This reproduces the driving trajectory that the game saw. It does not make the wheel physically retrace the user's movements, and it cannot predict how the user would drive differently in response to a changed FFB profile. That distinction enables safe autonomous graphics work while keeping wheel evaluation meaningful.

**Rendering acceptance needs separate contracts.**

| Contract | Checks |
|---|---|
| V-Unit native fidelity | Exact indexed-color agreement on declared reference captures; include Off Road's complete visible area |
| Zeus native semantics | Explicit color/depth tolerances and error maps; distinguish exact CPU reference from approximate GPU coverage/blending |
| Scaled/wide correctness | Coverage, geometry presence, texture/resource provenance, margins, HUD layout and transitions at actual output settings |
| Temporal correctness | No stale state, unexpected frame flashes, page contamination or lost resource updates across consecutive frames |
| Performance | Emulation throughput, CPU/GPU timings, present cadence, backlog and upload cost in named scenarios |

A small average image difference can conceal a glaring seam, and a large acceptable background difference can obscure a missing car. Evaluate labelled regions and contiguous error clusters as well as global statistics. A perceptual score is a triage aid, not a complete oracle. A fixed high-resolution screenshot baseline is also insufficient when the baseline contains the original defect.

For suspect pixels, expose contributing quad/scene/page, texture address and version, palette index, coverage/written mask, and whether a repair changed the pixel. Capture before/after repair views. Record temporal windows around a reported flash instead of one screenshot every several seconds. The custom GL backbuffer must be captured directly; MAME's native snapshot or a black GDI capture is not proof of the displayed overlay.

Within the marked interval, retain every emulated output frame and its relation to displayed presents, subject to an explicit lossless capture design. Detect and report capture drops. Compare matched emulated frames across runs, and also inspect the presented sequence for repeated frames, intermittent stale textures and page flashes. Wall-clock screenshot numbers alone cannot align a moving scene reliably. Preserve a short video/contact sheet for human review alongside the diagnostic sequence; a single still does not represent acceptance of a temporal defect.

Fast-forwarding a long prefix can be a later convenience, but it must preserve full render state and not silently overflow/drop operations. Reproduce pacing-dependent bugs at their recorded timing. First make ordinary boot-to-issue replay trustworthy, then prove any acceleration or checkpoint optimization equivalent for the case.

For draw distance, record objects considered, spawned/streamed, culled, assigned LOD and submitted. A route where an object pops into view should establish which stage withheld it. Offline shader replay cannot extend an object's lifetime in the game's scene graph.

**The initial scenario library**

| Scenario | Main purpose |
|---|---|
| Boot and calibrated entry, each game | Start-state repeatability and no hidden calibration stall |
| Car selection: dwell, cycle through cars, confirm | Reported slowdown; texture churn; 2D/3D transitions |
| Straight approach toward distant landmarks | Streaming, culling and LOD transitions |
| Turns with terrain at both margins | Missing edge geometry, texture validity and wide frustum handling |
| Known red/blue seam route | Consecutive-frame coverage and resource provenance |
| Menu → race → continue → menu | Persistent pages, UI cropping and stale margins |
| Off Road edge/last scanline cases | Its distinct visible-area dimensions and existing edge history |
| Exotica scenes with transparency/texture changes | Zeus blend/depth behavior and resource updates |
| Isolated and repeated car/wall contact | FFB semantics, timing and telemetry |
| Pause/resume, focus changes and clean exit | Lifecycle behavior, with device output evaluated separately |

Do not turn every case into a long full-game run. Retain a few representative whole sessions, then extract short render/force cases for rapid diagnosis and routine CI.

**Car-selection slowdown: a concrete investigation protocol**

The symptom is reported but not measured in this review. First identify the game/ROM, exact selection sequence, output settings and whether the animation, input, audio or whole emulator slows. Preserve that recording as a performance case.

Measure CPU emulation time, software-render time if still active, command packing/queue wait, GL resource uploads, GPU draw/post-processing time, swap/present waits, and host frame intervals. Include queue high-water marks and all dropped-state counters. Use asynchronous GPU timing queries so measurement does not introduce a forced GPU wait each frame.

Run the same case under a small controlled matrix:

| Variant | Question resolved |
|---|---|
| Original/native rendering | Is the slowdown already in the emulated game or base renderer? |
| Replacement at scale 1 | Does the replacement introduce a CPU/order/presentation cost independent of resolution? |
| Replacement at scale 4 | Does GPU work scale with internal pixel count? |
| CRT off/on, then crack fill off/on separately | Which post-processing pass contributes? |
| Light timing instrumentation vs detailed flushed logs | Is diagnostic I/O perturbing the case? |
| Fresh process vs warmed repeat | Is it one-time compilation/resource setup or sustained cost? |

Report median, p95, p99 and worst frame, plus duration below full emulation speed and repeated/dropped presents. Use the actual game's frame period; a 60 fps desktop video cannot by itself prove correct emulation timing. Keep correctness and performance runs separate when expensive snapshots or full state dumps distort timing.

Likely areas to inspect include high projected-area car geometry, overdraw, texture uploads, redundant underlying rendering, and queue waits. These are hypotheses. A low quad count is not evidence of low fragment cost, and average racing FPS cannot clear a car-selection regression.

**Test levels and where they run**

| Level | Scope | Appropriate execution |
|---|---|---|
| Small deterministic checks | Force history/gain/event math, mapping translation, packet bytes, profile resolution | Ordinary change CI, no ROM or wheel required |
| Harness self-checks | Missing frames, mismatch, process failure, invalid baseline and incomplete capture | Ordinary change CI |
| Synthetic render transactions | Texture rewrites, palette boundaries, page persistence, clear/depth/direct writes, queue overflow | Available GPU runners; deterministic fixtures without game assets where possible |
| Recorded real gameplay | Per-game routes, source state, native/quality outputs, car-selection performance | Local/controlled runners with the user's game assets |
| Packaged product | Clean install, upgrade, dependency/cache variants, launch/exit and settings persistence | Disposable install directories, no physical force by default |
| Physical wheel evaluation | Sign, response, stop/recovery, hotplug and driver recognition of contacts | Supervised device sessions |

Fault cases should include a texture update between two draws; a deliberately stalled render consumer; a lost clear/direct write; short force pulses between worker wakes; a disconnected device; a nonzero emulator exit with some valid screenshots; and two runs stuck on the same menu. Each tests a failure mechanism actually present or inadequately covered in the reviewed code.

Performance thresholds should be based on a measured baseline and declared target hardware, with a controlled amount of run-to-run variation. Correctness failures should not be waived because a machine is fast. A failed run should retain a compact bundle with the first divergence and exact reproduction settings.

**Autonomous iteration workflow**

1. Select a known failing recorded case and state its visual or signal acceptance criterion.
2. Verify replay determinism with the baseline build. An invalid replay blocks interpretation of the experiment.
3. Make one scoped implementation change in the future work session.
4. Run the shortest relevant render/force fixture, then the full game case if it passes.
5. Compare defect regions, native invariants, temporal windows and performance; retain both results.
6. Run the affected regression set across games/settings. Request human visual or wheel judgment only for the remaining perception-dependent question.

Baseline acceptance should be explicit and reviewable. The test runner must not overwrite approved references just because two candidate runs agree with each other. Save the previous behavior, proposed behavior and metric changes together.

**First implementation milestone**

Deliver one reliable “Record drive / Replay case” path built around MAME INP, isolated starting files, build/config metadata, expected completion checks, direct overlay capture, and a no-device force backend. Demonstrate one human drive replaying twice and produce a report of exact checkpoints plus selected frames. Include car selection in that first saved session.

Only after that succeeds across the four games should arbitrary checkpoints, broad automatic graphics searches or large benchmark matrices become the focus. A dependable route through the user's actual problem is more valuable than many unattended launches that cannot prove they reached it.
