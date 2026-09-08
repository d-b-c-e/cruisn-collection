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

Implement a guarded native path that sends additional quads only to the host GL
renderer. It must leave guest RAM, CPU timing, native framebuffer and original DMA
stream intact. Compare its quads against this independent reference, require
repeated completed GL frames and actual camera/ADC equality, and inspect the
handoff when guest drawing takes over. Insertion before the main-object pass is
an occlusion experiment, not a general depth-order solution.

Then broaden static model coverage and decode future track sections outside guest
RAM. Pending-object rendering alone has a finite lead and cannot promise the
removal of every pop-in. USA/Off Road need separate layout/codec adapters; Exotica
also needs a Zeus geometry/material adapter. Shared math, scene evidence and
acceptance checks should carry across those adapters.
