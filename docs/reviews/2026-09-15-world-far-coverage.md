# World: clipping coverage instead of rejecting whole models

A saved-scene prototype reduces abrupt far-boundary changes while preserving
the original texture mapping. It is not yet connected to MAME or accepted for
release. The separate authored terrain gap remains visible.

The current World host renderer rejects an entire model when any vertex is
beyond the far plane. The prototype projects crossing models within a bounded
480,000-unit diagnostic range, retains their original quads and clips only
pixel coverage at 240,000. It interpolates reciprocal depth along projected
edges. It does not create new textured triangles, change the original game's
commands or alter UV interpolation. This is an approximation to clipping after
the game's quantized projection, not a reconstruction of its clipping routine.

## Saved Hawaii result

All 8,403 previously accepted ordered quads remain exact. The prototype adds
194 quads from 36 objects; 81 polygons cross the far plane. In the completed
2736×1600 offline quality render:

| Variant | Changed pixels against accepted baseline |
| --- | ---: |
| Whole in-range polygons only, prior screening | 682 |
| Crossing polygons with coverage clipping | 1,619 |
| Entire crossing polygons, without a mask | 3,757 |

Original command ordering and resources are retained. The original baseline
image is checked byte-for-byte. The visible benefit is modest; the floating
terrain bottom is still present and must not be described as repaired.

## Boundary movement

A stationary-camera sweep moves only the far plane from 220,000 to 240,000 in
1,000-unit steps. Across its 20 transitions, the largest changed-pixel count is
13,020 with whole-model rejection and 1,348 with coverage clipping. This
supports further investigation of smoother partial admission. It does not
establish live camera motion, smooth handover, texture lifetime or performance.
The final whole-model and clipped images exactly reproduce the two prior
offline baseline images.

`native/vunit_far_coverage.h` is a standalone shared helper for this calculation,
with a 64-byte shader-mask layout and explicit unchanged/rejected/clipped states.
Invalid inputs clear the result and return failure. Its focused native test
covers perspective fractions, alternating crossings, equality, duplicate triangle
vertices, invalid depths and invalid screen coordinates. An independent Python
comparison checks all 180,537 quad/plane operations from the saved scene:
11,554,368 mask bytes match exactly, including 1,547 clipped operations.
The analyzer is included in the local native build inventory. It is not synced
or linked into the emulator yet.

The first local prototype compile incorrectly assumed the native C31 type had
the Python reference's `value()` method. The failed compile is retained; the
corrected capture emits original C31 words for independent conversion. No game
replay or MAME build was used for this investigation.

Next: connect bounded per-quad depth metadata to the private World rendering
path behind an explicit test gate. Verify original resources, unclipped pixels,
actual moving-camera admission and cost before applying the approach to USA
or Off-Road. Exotica already has a separate depth renderer and needs its own
far-boundary policy. This does not justify a shared release-ready 3× claim.

Local evidence is under `results/diagnostics/world25-roads-20260914/`:
`far-coverage` (initial compile failure), `far-coverage-v2`, `far-sweep`, and
`far-coverage-qualified`. Raw meshes and images stay local. Frozen nativef2e,
personal native87d and public v0.5.0 remain unchanged.
