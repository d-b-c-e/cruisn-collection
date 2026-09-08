# World host scenery: independent projection and pending-object drawing

The user authorized the host scenery approach after the morning checkpoint.
The existing overnight heartbeat remains paused. This work does not change the
published v0.4.0 package or personal settings; all automated physical force is off.

## Verified foundation

World 2.4's main packed-model path can now be reconstructed on the PC, without
executing game instructions or activating guest objects. `scenery_c31.py` preserves
the DSP's extended register precision, 24-bit multiply operands, store/reload
boundaries and negative FIX rounding. The reference agrees with the actual MAME
CPU helper bodies on 10,081 vectors across six arithmetic/conversion operations.
The ROM-free vectors are checked in the normal Python test suite.

`lua/world_transform_capture.lua` records object placement, camera matrices,
packed models, material words, projected vertices and actual DMA submissions.
`verify_world_transform.py` independently reconstructs camera-relative centers,
ordinary object rotations, both packed vertex formats and unclipped polygons.
The shared billboard camera basis is a captured adapter input, like the view
matrix. Clipped polygons and alternate road/car codecs remain explicit exclusions.

The Germany control at frames 5900–5910 passes the original input/native-image
replay and seven completed GL captures. All 596 projections and 1,680 unclipped
polygons reproduce exactly. The original captured scene independently rasterizes
to all 204,800 native framebuffer pixels exactly. A longer read-only 5900–6020
probe passes the original replay and all 10,299 projections; it does not claim
complete reconstruction of the other draw paths.

`preview_world_pending.py` draws pending scenery offline, before the main-object
pass, preserving every original DMA command and its order. It admits whole objects
within the original 80,000 far bound and excludes unsupported codecs/near clipping.
Frame 5909 adds 78 polygons from 34 objects, changing 9,310 pixels in the 2736×1600
quality preview. This is an offline visibility result, not live GL acceptance.
All 34 are normally drawn at frames 5921 (18 objects) or 5931 (16), with identical model words,
materials, position, rotation and palette/texture selectors. No model allowlist
is used: selection follows the pending list and supported geometry codecs.

Evidence is local under `results/diagnostics/world-host-transform-20260908`.
`control-v1` retains a rejected object-allocation assumption; `control-v3` retains
a rejected GL capture budget. `control-v2` is the projection-only control;
`control-v4` adds the pending snapshot and GPU evidence. `transition-v1` checks the
longer interval. `math-v1` retains the compiler PATH failure, corrected in `math-v2`.
173 Python tests pass. The source emulator remains native `12e9ea6a374` at this
checkpoint, with unchanged release/tag/configuration.

## Next acceptance work

The guarded native prototype is now built as `480206c670c`, SHA256
`33670b9dae672725851a0e177bb58be6eee29402512c41ac8d1875e9e890accd`.
Its 131-patch export exactly reconstructs tree
`95c99e6b11ac61756c3fa55761f7eb6bcc676cf0`. The first native commit `7ffdd42ad02`
was followed by a separate guard restricting geometry/material reads to ROM,
so a bad resource pointer cannot reach side-effecting I/O.

The option is diagnostic CLI only, bounded explicitly:

```text
python harness/replay.py results/diagnostics/world-germany-20260906 --candidate E:/Source/mame-src/vunit.exe --world-host-scenery draw --world-host-first 5900 --world-host-last 6020 --gl-capture 5900:6020 --gl-every 2 --gl-max 61 --small-window --output NEW_DIRECTORY
```

`observe` computes/logs the same host quads without submitting them. `off` and an
unset `MIDV_WORLD_HOST_SCENERY` install no hooks. Native modes are 0/1/2 and require
World 2.4, stock guest far/activation and, for drawing, the GL renderer. The
prototype writes neither guest RAM nor VRAM and adds nothing to the hardware DMA
stream. Shared C31 math is canonical in `native/scenery_c31.h`; the World adapter
is `native/world_host_scenery.h`. The source launcher has no new menu/default.

`native-observe-v1` and `native-draw-v1` both pass the original 6023-frame input/
native-image replay. Their complete camera and actual ADC logs, original quad
capture, native framebuffer and texture/palette RAM are byte-identical. 59/61
completed 512×451 GL images change, with extra distant scenery. The observation
cost was at most 0.630 ms per scene in this bounded sample; that is not a whole-game
performance claim. The GL equality report intentionally says FAIL for this
intervention and retains each changed-frame count/bounds.

`native-draw-v2`, on the tighter-guard final binary, repeats all 61 completed GL
images exactly. Its simultaneous read-only Lua capture independently reconstructs
every logged host quad across all 61 scenes. The capture now stores both session
callback count and actual emulator frame: they differ by one in this recording.
Runtime comparisons use the measured emulator clock, without guessed alignment.
The heavy Lua capture costs wall time and is excluded from native-cost claims.
174 Python tests and the ROM-free C++ geometry/I/O-guard/cycle tests pass.

Full-route observe/draw, default cross-game regressions and larger completed images
are the next acceptance checks. Insertion before the main-object pass remains an
occlusion experiment, not a general depth-order solution.

## Separate host distance limits

Native `cfba021b59e` adds `--world-host-far 80000|160000|240000` to the bounded
diagnostic interface. This changes only host culling/projection: the game still
uses its original far limit, reciprocal table and section activation. Original
table words are read unchanged; extra reciprocals are calculated in host memory.
The native binary SHA256 is
`f320ecef22d8974772e89580b0cdba15d239c84d42d3f641c1737cd163aa7398`;
132 exported patches reconstruct tree `51bd79f93b6d37b7c2f07e88fee94eed8e9e8449`.
Both larger limits match independent Python projection across the 60 captured
pending scenes. This checks geometry, not final visibility or correct occlusion.

`analyze_world_host.py` compares full original input values/times, camera and actual
ADC logs, native replay results and completed GL images. Its explicitly chosen
GL expectation distinguishes an intended image change from a repeatability check.
A changed image is never itself a visual-quality PASS. Scene counts must agree
with actual logged host quads, and missing messages/dimension changes fail.

The user restored the 3840×2160 monitor during testing. The earlier ultrawide run
is retained with a display-transition notice. The fresh 4K-monitor observe control
passes all 9,269 original inputs and 154 native snapshots and captures 31 completed
GL frames at the actual 3824×2073 client size. Full candidate trials and default
regressions on the new native binary are still pending at this source checkpoint.

Then broaden static model coverage and decode future track sections outside guest
RAM. Pending-object rendering alone has a finite lead and cannot promise the
removal of every pop-in. USA/Off Road need separate layout/codec adapters; Exotica
also needs a Zeus geometry/material adapter. Shared math, scene evidence and
acceptance checks should carry across those adapters.

## Full-route 4K-monitor results

The final native pointer hardening is `d52b8f95d92`, SHA256
`e0cf8a8b498d4499f81228b2fbb3e40367d29fd25e1c86edb9c95ee500c689d1`.
It guards preceding LOD metadata at the bottom of ROM and rejects overflowing
object links. Its 133-patch export reconstructs tree
`8502d3368438573facb5fb8edaaa5d487fe074df`. All settings remain unchanged; the
host path is still a bounded CLI diagnostic, not a new launcher default.

All full Germany trials complete 9,269 frames and retain the original 154 native
snapshots. Camera samples and actual ADC reads, including their timestamps, are
byte-identical. Completed GL captures use 31 frames from 1920 through 9120, every
240 frames, at 3824×2073 on the restored 3840×2160 monitor.

| Trial | Host quads across 3,731 scenes | Completed images | Interpretation |
|---|---:|---|---|
| Observe, 80,000 | 219,528 prepared, none submitted | Control | All guest work stays original |
| Draw, 80,000 | 219,528 | 18/31 change vs observe | Earlier trees are visible |
| Draw, 160,000 | 662,946 | 20/31 change beyond host 80,000 | More distant terrain, buildings and trees are visible |
| Draw, 240,000 | 663,078 | 31/31 equal to 160,000 | No additional visible gain in these samples |
| Repeat 160,000 on final binary | 662,946 | 31/31 exactly repeat | Input, camera, ADC and host quads also repeat |

The largest sampled 80,000→160,000 change is 144,921 pixels at frame 7680:
distant hillside/building geometry appears behind the foreground scenery. Changes
are not automatically correct occlusion or a whole-game visual acceptance result.
The 3× run preserves all 2× host quads in order and adds only 132 quads at frames
3666–3678. Its original expectation-of-change FAIL is retained; sparse image
equality must not be described as proof that every intervening frame is equal.
The targeted 3650–3690 comparison confirms a short 3× gain: 6/21 completed images
change at frames 3672–3682, with 2,125–24,047 changed pixels. Distant mountain
geometry appears earlier. Both prefixes preserve original inputs/native images
and identical camera/ADC data. This is a brief extension, not a large 3× gain
throughout the track; the sparse-image negative result remains intact.

The final 2× instrumented run independently reproduces every one of 13,215 host
quads across 61 scenes. Its original hardware DMA capture, native framebuffer,
texture RAM and palette RAM are byte-identical to the 80,000 control, as are its
camera/ADC traces. This directly separates the host drawing from guest rendering
and simulation. The first 80,000 oracle likewise reproduces all 5,157 host quads.

Full-route callback timing is approximately 99.887%–100.006% emulation speed.
Individual callback stalls reach 147.9 ms with instrumentation/captures; this is
not a presentation-latency or stutter-free claim. Heavy Lua projection captures
are excluded from native performance claims. No physical force was tested.
The 2× host callback's 99th percentile is about 1.54 ms, but the repeat has one
120.4 ms outlier. These outliers do **not** align with the requested screenshot
frames. The current counter includes model preparation, CSV logging and GL
submission, so their cause is unresolved. Split those phases and benchmark with
per-quad logging disabled before promoting this path for everyday play.

## Future section decoding

The read-only `world_section_capture.lua` and `verify_world_sections.py` begin
checking the source definition→object placement boundary. Section record AR7
contains base XYZ, heading and model-list pointers; World advances D575 by 8 words,
or 12 when flag 8 supplies an extra placement offset. Each main object definition
has model pointer, integer XYZ, C31 heading and metadata. The 7B9A allocator copies
these through the section matrix, then initializes palette/dynamic/list state.

The probe captures the source at read D580/PC7B9E and the initialized object at
D58D/PC7C1C. The independent reference preserves integer→float stores and 90C5's
operation order, including its differently scheduled last matrix row. Section
matrix/trig were initially captured inputs; palette setup, dynamic initialization
and list membership remain unverified effects. This probe does not create a host
future-section loader.

Both completed read-only probes pass the original 6,023-frame replay and preserve
the camera/ADC logs. The first independently reproduces XYZ and heading for 180
allocated objects across two section records. The second additionally reads the
seven actual polynomial constants and independently reproduces all 180 object
and section yaw matrices. There are only **two distinct observed angles** and no
flag-8 offset sections in this window; broader angular/offset coverage is still
needed. The two guest-observed numerical vectors are frozen in the test suite.
The source contains no copied model or texture assets.

Next, broaden placement/orientation coverage and reproduce palette/texture
bindings for eligible static definitions. Only then draw future
sections from PC-owned storage and test handover to the original guest renderer.
Keep alternate road/car codecs and special dynamic classes explicit; never infer
static eligibility merely from a model name or introduce a level/model allowlist.

## Default regression and source binding

All seven default cases pass on final native `d52b8f95d92`, including actual UDP
versus independent memory, World force passthrough, Exotica polarity and all 21
completed 3840×2160 Exotica reference images. The suite uses source identity
`411697739e64f832e5f819a2995a55f47e74dabd28849a3f88d4ddae6161eb7e`.
Later changes are confined to the read-only section/yaw diagnostic and its test
vectors; the archive explicitly verifies these four changed files and confirms
none is a default-suite probe. No product/native/default-test input changed.
The suite is retained as evidence on that exact source snapshot, not relabeled.
Final validation is 180 Python tests and all four CI jobs in run 34286683257.
All 287 source hashes match on local, Linux and Windows checkouts, identity
`89efc97dcda1a5f2a14f73ddca5a4d4475511866ce2c588ae809e75cb6438203`.
The 279-file derived archive and verifier are in
`results/proof/2026-09-08-world-host-scenery`. Native/root deployment, Stream Deck
script, personal config and the original v0.4.0 tag/ZIP hashes are recorded there.
