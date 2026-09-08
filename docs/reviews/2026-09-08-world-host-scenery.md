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
All 34 are normally drawn starting at frame 5931, with identical model words,
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
