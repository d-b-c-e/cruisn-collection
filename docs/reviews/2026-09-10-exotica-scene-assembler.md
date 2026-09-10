# Exotica scene assembler: reusable geometry before live integration

The future-scene prototype is now a bounded C++ component with an independent
capture-driven Python verifier. It reconstructs complete private render state,
model selection and every projected polygon. It remains separate from MAME;
this checkpoint does not draw additional scenery in the personal game.

`native/exotica_scene.h` joins the existing section, transform, CPU setup and
Zeus state/model components. It copies model words into a cache owned by each
call. It rejects duplicate sources, unsupported transforms, out-of-bounds model
reads, excessive work, nonfinite values, unsupported palette formats and models
that would inherit texture state from an unrelated original draw. No guest
memory, hardware FIFO or GPU state is changed. Source eligibility is an explicit
caller policy; this first analyzer selects ordinary future sources only.

The limit is 32,768 source descriptors, 4,096 selected instances, 131,072 quads
and four million copied model words. Failed assembly returns an empty result.
Model LOD follows the existing checked game rule. The optional completed-fade
policy changes private flags only; it does not advance the game's fade state.
Palette loads remain resource requests. Explicit addresses and captured bytes
do not establish live ownership, completed uploads or safe handover.

## Verification

`harness/verify_exotica_scene.py` rebuilds the source/context join from original
CPU and device captures. It verifies the original ordered polygons and
consecutive private contexts, requires the snapshot camera and setup operands
to match, then compares every generated native instance and quad byte against
independent Python at 1x, 2x and 3x. Both original and completed fade policies
include a repeated 3x case: 24 complete comparisons across three scenes.

| Captured scene | Original ordered quads | Original state pairs | Generated instances, 1/2/3x | Generated quads, 1/2/3x | Viewport quads, 1/2/3x |
| --- | ---: | ---: | --- | --- | --- |
| Hong Kong5000 | 2,202 | 219 | 913 / 1,515 / 1,515 | 5,291 / 9,596 / 9,596 | 1,813 / 4,740 / 4,740 |
| Amazon5072 | 3,255 | 132 | 632 / 1,296 / 1,622 | 5,656 / 13,345 / 16,408 | 330 / 382 / 382 |
| Hong Kong5990 | 2,012 | 183 | 730 / 818 / 818 | 4,800 / 5,478 / 5,478 | 457 / 457 / 457 |

All comparisons and repeats pass. Fade changes the expected rendering state,
but not these geometry counts. Amazon's third band contains 326 additional
instances and 3,063 polygons; none intersects this viewport. This is an explicit
example of why increased admissions alone are not useful rendering acceptance.
The earlier scene-layer review documents the corresponding visible differences.

The final analyzer comes from the standard local-check build, SHA256
`4f595c8fd2402708619be51e54c52516aeac98fb0e0c885133fa58b073aea5be`.
The initial explicit `-ffp-contract=off` build was separately compared before
renewing the same checks on the standard compiler invocation. Offline assembly
cost is approximately 3–9ms, plus 1–2ms to reconstruct source descriptors in
these trials. This includes offscreen geometry; it is not a live frame-time
benchmark or a guarantee at 4K.

The complete local suite passes 295 Python tests without skips, 35 native test
helpers and 99 commands at 442-file source identity
`0ad4af67d712be6a4e19a90698f3e22968b1cd01ed7c5636791b18d43701e855`.
Focused guards cover ambiguous camera/time joins, changing billboard rotations,
inherited textures, empty third bands, exact instance offsets, invalid bounds,
source duplication and private-state isolation. An initial synthetic test
accidentally aliased view and alternate arrays; separating those fixture arrays
exercised the intended changing-billboard rejection. No game failure was hidden
by that test correction.

## Next work

Connect the assembler to a guarded live observation point using direct RAM and
zero emulated CPU cycles. Compare its exact clock, camera, original route and
resource results before enabling submissions. Then provide owned material data,
an isolated depth attachment, a verified sky/foreground insertion point and
source handover rules. Earlier unsubmitted sources need separate eligibility
checks to address the black ground patch without freezing moving objects.

The public [proof receipts](../../results/proof/2026-09-10-exotica-assembler/README.md)
verify archived hashes and result consistency. They do not rerun local resources
or recompute unarchived geometry. Raw game data stays under ignored
`results/diagnostics/exotica-amazon-20260909/assembler*` and `scene*-source`.
The native MAME candidate remains b3d82b/SHAe7780a7a with its prior seven-default
acceptance. Personal Stream Deck remains v0.5.0/SHA87d04de4. No release,
deployment, menu removal, hosted workflow or physical-force test occurred.
