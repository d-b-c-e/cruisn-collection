# Exotica far-distance experiment — 2026-09-08

A coherent 2× far-plane extension admits more objects but produces **no changed
pixels in the fifteen sampled completed gameplay images**. A matched scene shows
why: the added geometry reaches Zeus, but existing geometry occludes it. This is
not evidence of eliminated pop-in, and no new far-distance launcher option is
being promoted from this result.

The deployed native build remains `12e9ea6a374`, SHA256
`9936c7160ddb708949d9e776c9197d833e868ffc921fd679153a72ab99735275`.
The new tools are committed as `dc1f07d`. No native code, shader, force behavior,
saved preference or released v0.4.0 package changed during this investigation.

## Global trial and controls

`run_exotica_distance_trials.py` serializes five 6000-frame replays of the
existing Exotica case. The bounded Lua probe intervenes only during frames
4500–5990, drains the last observation and removes its taps. Exact instructions,
CPU consumers, object pointers and table operands are checked. The extended
reciprocal is supplied through read substitutions; guest RAM and ROM stay intact.
Physical force is disabled throughout.

| Trial | Far limit | Actual sphere admissions | Actual far rejects | Completed GL versus coherent stock-far control | Instrumented emulation speed |
|---|---:|---:|---:|---:|---:|
| Original projection/bounds | 204800 | 321668 | 3669 | Different | 98.9389% |
| Coherent projection, wide bounds | 204800 | 387144 | 3732 | 15/15 identical | 98.2979% |
| Coherent 2× | 409600 | 390179 | 0 | 15/15 identical | 98.2337% |
| Coherent 3× | 614400 | 390179 | 0 | 15/15 identical | 97.4147% |
| Coherent 2× repeat | 409600 | 390179 | 0 | 15/15 identical | 97.9221% |

Each far trial matches **515968 captured object poses** from the coherent
stock-far control. The comparison excludes only the requested far value, keeps
the original reciprocal and all pose fields, and independently validates actual
branch operands and acceptance. There are 3035 additional admissions, no lost
admissions and no pose mismatches. These are repeated visits, not unique objects.
The 2× repeat also has an identical complete raw sphere trace.

All original frame inputs and emulated timestamps match. Exotica's unchanged
live CPU framebuffers are **not** a gameplay visual oracle; the separate completed
1920×1080 GL captures provide the pixel evidence. The Lua observation overhead
reduces emulation speed slightly. These figures do not predict an unbuilt native
far adapter's performance or measure presentation latency.

All additional admissions belong to the `BBB7` render-list consumer. Seven model
identifiers account for the original control's far rejects. Their object slots,
flags and specialized drawing path are consistent with vehicles; model identity
has not been independently named. No per-model allowlist is used. This sample
does not establish a far-plane rejection of mountains or trees.

## Actual Zeus submissions and occlusion

Independent prefix runs capture submissions around frame 4864, where eight extra
objects pass the CPU sphere tests. The candidate adds **199 quads and eight palette
loads**. Texture wave RAM and initial palette match the control.

The default, strict comparator reports **FAIL**: 438 original quads are stamped
4864 instead of 4863 after the extra guest drawing work. This failure is retained.
The new explicit `--alignment scene` diagnostic excludes only quad frame stamps;
it preserves all **2606 original records**, their order and effective palettes,
with one insertion of 207 records. All geometry/state bytes match in the original
quads. This narrower PASS does not cancel the strict timing failure. Completed
GL images at both 4863 and 4864 are identical between the two runs.

The new quads project into native x=456.27…552.26, y=209.85…214.21, toward the
hillside in the captured view. Their depth values range from approximately
16.70 million to21.92 million; some exceed the renderer's 24-bit depth range.

A separate offline GPU query replays the preceding captured submissions with the
same shader, textures, palettes and wide scissor at scale4. The added polygons
cover **173 samples with depth testing disabled and zero with depth testing
enabled**. A second diagnostic doubles the shader's depth range for the geometry;
the result remains zero versus173. Prior geometry therefore explains invisibility
in this captured scene; extending depth range alone does not reveal these objects.

The query starts at farthest depth, omitting uncaptured prior occluders. It uses
the capture's resource snapshot, not a chronological texture-upload stream. It
is a bounded diagnostic, not a whole-frame live oracle or a proposed shader fix.
There is no suggestion to disable depth testing in the product.

## Harness and follow-up

- `compare_exotica_distance.py` checks coherent trials at matching poses and
  rejects malformed operands, changed configurations or missing rows.
- `compare_zeus_capture.py` keeps strict frame comparison as its default. The
  optional scene alignment records every excluded frame change and still checks
  geometry, effective palettes, duplicate records and ordering.
- All166 Python tests and all four CI jobs pass at `dc1f07d`
  ([run34223306424](https://github.com/d-b-c-e/cruisn-collection/actions/runs/34223306424)).
  Local, Windows and Linux source identities agree:
  `54c2b421df9a39bc29c94bf493f2b2805dd8d3a5336d8cd47f0848bb87a10b4b`.
- The prior native build's complete seven-game-case regression remains the
  deployed product baseline; it was not rerun merely for these analysis tools.

Next, investigate static-scenery activation/residency and model-detail selection
before raising another advertised multiplier. Exotica has distinct generic and
vehicle LOD branches, and the current slow synthetic Hong Kong drive provides
limited visibility coverage. A fresh attended drive on an open level, with a
clear example of scenery appearing suddenly, would materially improve targeting.
Continue read-only loader/list diagnostics independently; do not wait for or
invent that human evidence. A future useful far extension also needs an explicit
depth-range study, resource checks and native performance/repeatability tests.

Local evidence: `results/diagnostics/exotica-distance-20260908`. The derived archive
in `results/proof/2026-09-08-exotica-far-distance` recomputes the full CPU branch,
pose, input and timing results with the standard library. Its reconstructed 3×
and repeat traces must match the actual captured byte hashes. Completed images,
raw Zeus resources and GPU query results remain hash-bound receipts; the archive
verifier does not claim to reproduce those pixels without their local inputs.
