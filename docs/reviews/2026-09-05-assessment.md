**Cruis'n Collection: independent engineering assessment — 5 September 2026**

The project has a sound core and valuable reverse-engineering work worth preserving. Its largest weakness is the gap between what the existing checks prove and what the live product now does. A native-resolution shader comparison cannot establish that widescreen gameplay, asynchronous texture updates, wheel behavior, telemetry, or upgrades are correct. Several current problems have concrete software explanations that should be resolved before further subjective tuning.

The highest-value next investment is a reproducible recorded-drive harness, accompanied by repairs to the existing tests' pass/fail behavior and the force-feedback integration. This would turn a report such as “the left margin flashes on this turn” into an independently repeatable engineering case.

The user emphasizes that most rendering defects need moving, player-controlled gameplay, sometimes deep into a level. That is the primary acceptance workload proposed here. Attract-mode equality and isolated screenshots remain supporting controls, not substitutes for reproducing those gameplay intervals.

This is an assessment, not an implementation. This review only added or revised review documents. It launched no game, issued no wheel force, and changed no product source, runtime configuration, NVRAM, generated shader, or deployment. A separate session advanced the repositories during the review, as recorded below.

Companion documents: [fresh widescreen and draw-distance assessment](E:/Source/cruisn-collection/docs/reviews/2026-09-05-widescreen-and-distance.md), [recording and test-harness proposal](E:/Source/cruisn-collection/docs/reviews/2026-09-05-replay-and-testing.md), [FFB quality and collision proposal](E:/Source/cruisn-collection/docs/reviews/2026-09-05-ffb-quality.md), and [speed telemetry reassessment](E:/Source/cruisn-collection/docs/reviews/2026-09-05-speed-telemetry.md).

**Scope and evidence**

Reviewed the project instructions, engineering chronology, session notes, roadmap, feasibility study, launcher, wheel mapping, diagnostics, renderer/reference code, release/update path, exported patch relationship, modified MAME sources, and relevant parts of the shared wheel toolkit. Checked relevant upstream MAME and SDL material. The actual immediate notes are under `.claude/`; the instructions' `.Codex/session-notes.md` path does not exist in this checkout.

| Component | Reviewed revision / state |
|---|---|
| Cruis'n Collection | `master`, `c27dd4f87f5cbf57c8a6d954af3b8a0aa250f8d8` |
| Modified MAME | `poc/quadlog`, `e309c3c777b72d17d43e238d578f1762786ef37a` |
| Wheel toolkit checkout | `d170e0403aee67e4dd82685b87156377553e8ee1` |
| Vendored toolkit marker | `v0.9.0`; inspected force headers match toolkit source |
| SDL beside local emulator | File/product version `2.32.10.0` |
| Initial user changes | Untracked root `AGENTS.md`; untouched by this review |

The other session subsequently committed Collection `8035c120c519537e705009d6c74f1b60a4c888e4` and MAME `58203bb13f7b4a5997b4f6dceed1e36a8fd631d8`. I inspected the intervening changes: MAME's executable logic was unchanged; comments added World's three-digit OCR verification and clarified that Off Road's OCR box has never worked. The collection commit also picked up `AGENTS.md` and two draft review documents already written by this review. I made no commits and did not undo that work. The completed documents incorporate the final telemetry clarification. Original line references below are based on the initial reviewed revisions; the added MAME comments shift later lines by eleven.

“Confirmed” below means established from source or a specifically described check. It does not mean the corresponding visual or physical symptom was reproduced. “Hypothesis” identifies an experiment still needed. Source line references refer to these revisions and will move as implementation changes.

**Verification performed during this review**

Replayed six existing V-Unit captures in an offscreen OpenGL context on the RTX 5080, using the current Python renderer's exact/native path. Compared integer framebuffer indices against archived MAME videoram entirely in memory, without replacing reference images or writing new captures.

| Existing capture | Pixels compared | Exact agreement |
|---|---:|---:|
| `results/capture` | 204,800 | 100.0000% |
| `results/capture-8000` | 204,800 | 100.0000% |
| `results/capture-continue` | 204,800 | 100.0000% |
| `results/capture-crusnwld-rig` | 204,800 | 100.0000% |
| `results/capture-offroadc-rig` | 205,312 | 100.0000% |
| `results/capture-ny` | 204,800 | 100.0000% |

The scalar and fast Python vertex builders also agreed on these inputs. Reconstructed both generated shader headers in memory and verified they match the current source. Compared the vendored force-model/profile headers with the shared toolkit checkout. Small in-memory calculations reproduced the collision detector edge cases described in the FFB document.

These are meaningful positive results. They cover archived native V-Unit scenes on one GPU. They do not cover fresh full-game replay, the live C++ command timeline, widescreen quality mode, all Zeus rendering, actual wheel torque, car-selection performance, or installed-package behavior. No new hardware-playtest or car-selection timing result is claimed.

**Findings in recommended priority order**

| ID | Priority | Finding | Evidence level |
|---|---|---|---|
| F01 | P1 | Emergency FFB cleanup has an incorrect pointer-return ABI | Confirmed source defect |
| F02 | P1 | Collision cue detection and output scaling are inconsistent after toolkit migration | Confirmed source behavior and calculations |
| F03 | P1 | Exotica gain clips away force distinctions before shaping | Confirmed source behavior |
| G01 | P1 | Deferred V-Unit draws can use later texture contents | Confirmed ordering defect; symptom attribution unproven |
| T01 | P1 | Existing renderer/oracle tools can report success without a complete passing case | Confirmed source defect |
| G02 | P1 | Renderer queue overflow can lose persistent state | Confirmed failure path; overflow not reproduced here |
| F04 | P2 | Worker timing, event signaling, and output verification lag the shared shaper integration | Confirmed integration gaps |
| G03 | P2 | Widescreen repairs and distance experiments lack broad gameplay validation | Confirmed coverage gap |
| G04 | P1 | Multiword game patches can be partially applied; experimental patches replace widescreen defaults | Confirmed source behavior |
| P01 | P2 | Car-selection slowdown needs a dedicated timing case | User observation; cause unresolved |
| W01 | P2 | Wizard can save a binding that the game mapping silently drops | Confirmed current configuration example |
| D01 | P2 | Speed's missing-read counter is cumulative instead of consecutive | Confirmed source defect |
| D02 | P2 | Telemetry and diagnostics do not adequately express validity or provenance | Confirmed design gap |
| R01 | P2 | Overlay-style upgrades retain files removed from newer releases | Confirmed updater behavior |
| A01 | P2 | Reuse is promising but the integration contract remains incomplete | Architecture assessment |

P1 means address before relying on the affected subsystem for tuning or unattended regression work. P2 means a substantive reliability or product improvement. Priorities do not assert that every failure occurs in normal play.

**F01 — emergency force release is not a reliable fallback yet.**

[`release_ffb`](E:/Source/cruisn-collection/harness/run_rig.py:192) calls `SDL_HapticOpen` through `ctypes` without declaring its pointer return type, then wraps the already returned value in `c_void_p`. The default return is a C integer: a 64-bit pointer may already have been truncated. Wrapping afterward cannot recover it. The helper also counts a device as stopped without checking `SDL_HapticStopAll`'s result. This undermines the fallback specifically intended to recover stranded force after a failed shutdown. Python documents the default return convention and explicit `restype` mechanism in its [ctypes reference](https://docs.python.org/3/library/ctypes.html#return-types).

Declare and test the complete ABI, distinguish attempted from successful stop, and exercise the lifecycle through a fake backend before supervised wheel checks. A process-side watchdog cannot stop a force after that process has died; device-side duration or a proven independent recovery path deserves explicit treatment. The current infinite effect and previously observed stranded torque make this an existing product issue, not a hypothetical warning.

**F02/F03 — collision feel needs signal repairs before another smoothing preset.**

The current path forwards a signed motor command through a shared shaper and adds a heuristic rumble cue. It does not know whether a force represents a car collision, a wall scrape, or ordinary steering resistance. The detector omits zero and unchanged samples, and its thresholds still assume that global strength has already scaled the input. That assumption is no longer true. The supplementary rumble amplitude also bypasses the shaper's global strength scaling. Details and worked cases are in the [FFB review](E:/Source/cruisn-collection/docs/reviews/2026-09-05-ffb-quality.md).

For Exotica, [the launcher requests 800% motor gain](E:/Source/cruisn-collection/harness/run_rig.py:1323), and [the driver clamps the result back to a signed byte](E:/Source/mame-src/src/mame/midway/midzeus.cpp:739). Raw magnitudes 16, 30, and 46 all become 127. Reducing force afterward cannot recover the distinction. The old gain/strength combination and the new one are equivalent only below clipping. This is especially relevant to the report that impacts do not stand out against the ordinary force.

Keep the original motor signal observable, repair the detector and common output scaling, measure clipping/headroom, and introduce an explicit impact event path where reliable game evidence supports it. Do not assume every high motor command is a crash.

**G01 — live draw ordering is a stronger concern than another texture-filter adjustment.**

In the [V-Unit consumer](E:/Source/mame-src/src/mame/midway/midvunit_v.cpp:1302), incoming quads accumulate into pending runs. Texture messages immediately overwrite the single GL texture-memory mirror, but pending scenes are rendered only after draining the queue. Consequently, an ordered sequence `texture A → draw A → texture B → draw B` can draw both batches using B. Texture changes can cross both scene boundaries and queued work.

That violates the emulated device's command ordering even if every individual shader calculation is correct. The present frozen-state oracle does not test it. It is a plausible source of incorrect textures during resource changes or backlog, but no claim is made that it explains every currently reported artifact.

Preserve resource versions at draw time: either flush affected batches before texture mutations or retain versioned resources/ordered commands. Add a minimal transaction fixture with a texture rewritten between two draws. Treat palette scanout semantics separately; palette and texture timing are not automatically identical on an indexed framebuffer.

The pending-run “skip to latest” policy also needs a proof of complete repaint before discarding older operations. The implementation itself relies on persistent page contents. Later draws cannot be assumed to overwrite everything lost from an earlier run.

**T01 — tests currently permit false confidence.**

The [V-Unit renderer](E:/Source/cruisn-collection/gpu/renderer.py:830) prints differing-pixel counts but ultimately returns zero even when they are nonzero. The [Zeus renderer](E:/Source/cruisn-collection/gpu/zeus_renderer.py:497) likewise reports color comparison statistics and returns zero; its final comparison is not a full color-and-depth acceptance gate.

The [determinism oracle](E:/Source/cruisn-collection/harness/run_oracle.py:75) logs an emulator failure but still returns available screenshots. It requires two equal, nonempty snapshot counts, not the requested count and exact frame identities. Two equally truncated/crashed runs, or two identical runs stuck on calibration, can therefore become a “PASS.” Successful comparison also replaces reference frames automatically. Capture helpers similarly need explicit failure for missing expected dumps.

Require successful execution, the full expected artifact manifest, correct frame IDs and game phases, and declared comparison thresholds. Keep baseline creation separate from regression acceptance. Add failure-injection checks proving that one wrong pixel, one missing frame, and one nonzero emulator exit produce a failing result. These tests validate the harness, not merely the renderer.

**G02 — backpressure must preserve persistent state.**

The [V-Unit ring](E:/Source/mame-src/src/mame/midway/midvunit_v.cpp:133) drops messages when full. `flush_span` clears the pending CPU videoram span even when its write failed. Palette/texture dirty retry does not recover that lost span or every other operation. Its shared positions are `volatile`, without a proper C++ acquire/release publication protocol; an x86 comment is not a language-level synchronization guarantee. The fixed `Local\\MIDV_LIVE` mapping also makes simultaneous instances a collision risk.

The [Zeus ring](E:/Source/mame-src/src/devices/video/zeus2.cpp:406) improves synchronization with atomics, but classifies only palette, waveram and display tick as essential. Clear and direct framebuffer-write operations can be dropped with ordinary quads. After a bounded wait, only a lost waveram update requests full resynchronization. Losing framebuffer/depth state can outlast a single displayed frame. The wait loop can also stall emulation while a slow renderer catches up.

Define a complete state-recovery boundary, instrument all dropped operation types, and test overflow deliberately. Prefer skipping presentation while maintaining the state history; if that is impossible, discard a whole transaction and rebuild from a complete authoritative snapshot. Never report a corrupted run as a passing visual test.

**G03 — widescreen has several independent problem classes.**

| Symptom | Distinct mechanisms to investigate | Evidence needed |
|---|---|---|
| Distant pop-in | Object creation/streaming, game culling, LOD selection, subdivision/projection limits | Follow the same object's lifecycle and submitted geometry over a recorded approach |
| Black or missing margins | Original frustum clipping, geometry never submitted, parked UI heuristics, page clearing, lost commands | Per-pixel ownership and command provenance; native vs wide paired frames |
| Red/blue seams | Stale page contents, coverage mismatch, wrong texture version, actual geometry gaps | Coverage/written masks, raw indexed color, texture version and contributing quad IDs |
| Intermittent flashing | Queue ordering/overflow, incomplete page updates, scene classification changes | Consecutive frames and queue history, not isolated screenshots |

The history already found a genuine USA distance gate at word `0x55`, but extending it did not make the course streamer create missing distant nodes. LOD and the reciprocal-depth lookup have their own limits. Raising a far-distance value is insufficient. A renderer receiving already projected screen-space geometry cannot reconstruct objects the game never supplied. The next distance experiment should trace creation, rejection, LOD, and projection separately and compare a fixed route.

The renderer contains useful but game-specific rules for backdrops, offscreen UI, 2D cropping, and crack filling. The [quality shader](E:/Source/cruisn-collection/gpu/renderer.py:213) and [live scene classification](E:/Source/mame-src/src/mame/midway/midvunit_v.cpp:1372) depend on thresholds and geometric patterns. They need fixtures for every exception, including legitimate small polygons and transitions between menu and 3D scenes.

Crack filling operates on unwritten coverage. A sky pixel already written behind absent terrain is a different problem. A local repair can also hide evidence or fill intended gaps. Retain diagnostic views both before and after repair, and measure the number and location of repaired pixels. Do not equate “all holes filled” with correct geometry.

At scale 4 a 400-line V-Unit image has 1,600 internal vertical samples before presentation to a 2,160-line display; Off Road's 401-line mode has 1,604. Describe this accurately as 4K output with selectable internal scale. Native exactness and the scaled quality path are separate contracts. Preserve the exact path as a reference while testing quality at the actual output settings.

**G04 — game patches need coherent validation and composition.**

The [patcher](E:/Source/mame-src/src/mame/midway/midvunit.cpp:122) applies each word as soon as its individual old-value guard passes. A later mismatch leaves earlier words changed. For trampolines and relocated sky tables, that does not guarantee an unsupported ROM remains untouched. Verify ROM identity and all expected words before applying a whole patch group. The launcher also lets a configured experiment replace the default widescreen patch; future distance patches for World or Off Road need explicit composition so they do not disable the existing geometry fixes. The [dedicated widescreen review](E:/Source/cruisn-collection/docs/reviews/2026-09-05-widescreen-and-distance.md) reassesses these mechanisms and proposes a staged alternative for extending distance and precision.

**P01 — car-selection slowdown is an explicit unresolved issue.**

The user reports noticeable slowdown during car selection; the affected game(s), duration, and bottleneck were not established in this review. Keep it in the regression corpus as a named case, rather than absorbing it into average racing FPS.

Measure emulation speed, emulated frame interval, CPU submission time, GPU time per pass, present interval, queue occupancy, and texture-upload volume during the exact selection sequence. Compare native MAME, replacement scale 1, replacement scale 4, and individual CRT/crack-fill variants using the same input recording. Separate intended animation speed from emulation slowdown and presentation stutter.

Close-up cars can be expensive through projected area/overdraw even when quad counts are modest. Other hypotheses include CPU/software-render work, texture churn, a producer blocked on the renderer, and synchronous logging. The current rig has FFB diagnostics enabled, and several paths flush logs per write. All are experiment candidates, not established causes. See the [timing protocol](E:/Source/cruisn-collection/docs/reviews/2026-09-05-replay-and-testing.md).

**W01 — robust wheels require end-to-end binding validation.**

The [mapping translator](E:/Source/cruisn-collection/harness/run_rig.py:1087) supports buttons 1–32 and additional-switch tokens for 33–48; larger values return `None`. The current rig contains `voldn = MOZA R12 Base|btn:48`, a zero-based button 49 binding. It can be captured and saved but cannot become a working game token through this path.

Validate a binding through the complete wizard → stored value → generated controller → actual MAME input-port chain. Reject unsupported inputs visibly or extend the emulator's addressable items; silently saving an unusable binding is poor product behavior. A raw API exposing 128 buttons does not establish that the whole product supports them.

Device display names are also insufficient identities when multiple logical devices or identical peripherals exist. Record stable instance identity plus vendor/product and capabilities, handle ambiguity explicitly, and show which device actually owns steering and FFB. Test sparse axes, combined/separate pedals, initially untouched pedals, duplicate names, replug, split shifters, high button numbers, and missing-wheel fallback. Keep physical steering calibration separate from each game's response curve.

**D01/D02 — telemetry needs correctness and confidence, not just an available packet.**

The [HUD OCR fallback](E:/Source/mame-src/src/mame/midway/midvunit_v.cpp:2996) increments `s_absent` on failed reads but never clears it on successful reads. “180 absent frames” therefore means 180 cumulative failures, not three consecutive seconds without a HUD. It can insert a false zero into an otherwise valid long drive. The speedometer's corrected hundreds-digit window does not fix this separate counter defect.

Other limits remain: the other session's final notes verify World's three-digit OCR reads and identify Off Road's speed box as wrong and never working; RPM is not equally established across all titles; the Forza adapter advances time by a fixed 17 ms and reports race-on unconditionally. A zero can mean stationary, menu, unsupported, or unreadable. These are materially different states for SimHub and for automated tests.

I would reopen the source investigation by tracing backward from CPU writes to the HUD digits, through glyph selection to the numeric formatter or player structure. A transient register value is still observable inside the emulator; failure to find a stable RAM address does not close that route. The [speed telemetry proposal](E:/Source/cruisn-collection/docs/reviews/2026-09-05-speed-telemetry.md) separates displayed speed, physical velocity and OCR fallback, with acceptance criteria for each.

Introduce a versioned internal telemetry contract with units, source, validity, age, emulated timestamp/frame, and measured versus estimated status. Emit protocol-specific packets as adapters from that contract. Avoid deriving collision or acceleration truth from noisy OCR differences. Preserve pre-gain motor commands as well as post-processing outputs.

The [support bundle](E:/Source/cruisn-collection/harness/support_bundle.py:71) prepares/runs a diagnostic configuration before copying the original logs, potentially changing the state being investigated. Preserve evidence first and run probes in a separate directory. Add Zeus logs, resolved profile contents/hashes, executable identity, and a shared timeline. A “shaped” trace row currently records intended output before the device call; it is not proof of accepted force or measured torque.

**R01 — upgrades need removal and rollback semantics.**

The [updater](E:/Source/cruisn-collection/harness/updater.py:126) copies a release over the existing install using `robocopy /E`. Files absent from the new release remain. An old hook DLL such as `dinput8.dll` can therefore survive removal from the current package and keep affecting the emulator. This is a conditional upgrade defect; the review did not claim such a DLL is currently active on this rig.

Use a manifest of application-owned files, remove obsolete application files through that manifest, preserve user data, and stage/verify an update before swapping it into service. Include rollback on partial copy failure. The generated PowerShell also needs correct literal escaping for apostrophes in paths and fail-fast handling of expansion errors. Test an old-plugin install upgrading to a plugin-free release, not only clean installs.

The only current workflow is release-oriented. Add ordinary change validation, pin build dependencies, and make packaged runtime assets reproducible on both cache hits and clean builds. A cached executable alone is not a complete emulator distribution. Record the emulator, patch, shaders, toolkit and package identities in the artifact manifest.

**A01 — keep the reusable core, strengthen its boundaries.**

The relevant abstraction is `E:\Source\dbce-wheel-mod-toolkit`. It already offers reusable native force math, profiles, a native output library with managed bindings, telemetry encoders, and conformance tests. This is valuable existing work.

Cruis'n currently vendors the C++ shaper/profile headers. It does not use the shared `WheelFfb.dll` device lifecycle or the shared game-force model: its SDL worker and heuristic rumble remain local. Calling the project a complete consumer of the shared assembly would overstate the extraction. Header-only sharing is a reasonable integration strategy for MAME; there is no reason to introduce a managed runtime merely for architectural uniformity.

Keep game memory addresses, ROM patches, collision interpretation, and hardware-specific render semantics in game adapters. Share normalized force conditioning, profile parsing/versioning, device capability/lifecycle contracts, telemetry primitives, capture formats, and replay evaluators. Where different backends remain necessary, run the same contract fixtures against each.

Version the engine behavior as well as the profile name. The same immutable profile can feel different after gain order, scheduling, or event handling changes. Store toolkit revision, resolved profile hash, adapter version, backend, device calibration, and user settings together. Separate game semantics, device calibration, and user preference; one increasingly large per-game preset cannot substitute for those distinctions.

The launcher and modified video files now own many unrelated responsibilities. After tests exist, extract small lifecycle-owned components for render transport, overlay presentation, FFB output, telemetry, and diagnostics. Keep the MAME patch surface understandable and independently backportable. A large rewrite before replay coverage would increase uncertainty.

**Upstream and documentation discipline**

Continue taking upstream Zeus improvements, but associate each backport with the exact issue and regression case. Recent changes include Exotica clock/framebuffer work and continuing Zeus fixes. A same-day [open upstream DIP clarification](https://github.com/mamedev/mame/pull/16057) says the old “Wheel Invert” label concerns FFB and shifter polarity, rather than steering direction. That is reason to recheck the local manual-transmission workaround against actual input, motor, and shifter behavior; an open PR alone is not reason to remove a rig-verified workaround.

Keep the append-only engineering log. Add a compact current-state record whose claims identify game, ROM revision, render mode, scenario, build, and evidence. Older “artifact-free,” “solved,” and “all games verified” statements should not serve as current acceptance criteria when later play reports contradict them. The player's observation should become a tracked reproducible case, even when its cause is unknown.

**Suggested sequence and completion criteria**

| Stage | Work | Evidence required before moving on |
|---|---|---|
| 1. Trust the measurements | Correct harness failures, preserve support evidence, repair FFB cleanup ABI, add output-stage diagnostics | Deliberately broken cases fail; successful cleanup is distinguished from an attempt |
| 2. Replay a real drive | MAME INP recording from a pinned start, immutable run bundle, replay without physical output | The same human drive replays twice with matching game inputs/state checkpoints and expected end markers |
| 3. Establish rendering order | Transaction capture/replay, texture versioning, persistent-state overflow recovery | Adversarial resource-update and queue-stall cases agree with the reference |
| 4. Fix reported graphics | Curated margin/seam/pop-in routes plus car-selection timing | Named defects disappear on the same routes without native regressions or timing regressions |
| 5. Establish FFB quality | Correct gain/event path; labelled contact cases; device calibration and supervised comparisons | Collision detection metrics and output traces pass; drivers can distinguish impact classes across supported wheel classes |
| 6. Harden the product | Validated bindings, telemetry validity, installed-package/upgrade tests, modular ownership | Replug, stale telemetry, missing dependencies, old releases, and shutdown paths behave predictably |

Recording/playback is the central enabling feature. It makes much of graphics iteration autonomous and makes force-signal comparisons repeatable. Physical wheel feel still needs controlled human evaluation, but far less of that evaluation should be spent diagnosing preventable signal and integration defects.
