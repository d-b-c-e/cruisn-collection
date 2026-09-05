**Fresh assessment of widescreen, texture artifacts, seams and draw distance — 5 September 2026**

I would retain the expanded-canvas renderer and the proven game-side visibility/sky patches. I would substantially change how remaining artifacts are diagnosed, how patches are composed and validated, and how quality-mode seam repairs are justified. There is no evidence here that a wholesale renderer rewrite is necessary. There is also insufficient evidence to classify the remaining reports as inevitable limitations of the original games.

The project has already demonstrated the right kind of fix: recovering Off Road's actual missing geometry and extending World's actual panorama. Those are more convincing than hiding the resulting holes. The next work should make that distinction explicit for every reported defect.

This is a source/evidence review and proposed investigation, with no implementation changes. I inspected the existing Off Road before/after proof and a saved World New York tunnel frame, in addition to source, patch files and engineering history. I did not reproduce the user's latest visual symptoms in a fresh live session. The [main assessment](E:/Source/cruisn-collection/docs/reviews/2026-09-05-assessment.md) records the native renderer checks; the [replay proposal](E:/Source/cruisn-collection/docs/reviews/2026-09-05-replay-and-testing.md) supplies the needed experimental infrastructure.

The user's clarification is central to acceptance: these defects are often visible only during moving, player-controlled gameplay, not in attract mode. Static proofs can support a particular mechanism but cannot clear those reports. Use recordings that reach the actual level sections, and compare consecutive frames and display timing around the event.

**The wider-canvas approach is geometrically legitimate.**

For a perspective projection, a horizontal screen coordinate can be expressed as `x = focal_scale × X/Z + center`. If focal scale and vertical framing are preserved while the horizontal viewport grows around the old center, more horizontal viewing angle becomes visible. Translating the old coordinates into the middle of a wider canvas implements that expansion, provided the game supplies the geometry and pixel aspect/presentation are consistent.

The current V-Unit path shifts the original screen-space coordinates into a canvas `512 + 2 × margin` pixels wide. At margin 86 it covers game-space approximately −86 through 597. That is a valid route to horizontal expansion. It is not inherently a stretch or a lesser form of widescreen because no single aspect constant was patched inside the game.

A wider viewport and a projection-scale change can be two representations of the same desired view. They can also accidentally compound: reducing horizontal focal scale and expanding the canvas may widen the view twice. Establish the desired projection mathematically, then test stable landmarks, vertical framing and object proportions. Do not select a mechanism based on the label “proper FOV.”

Pixel aspect matters: 512×400 is not square-pixel 4:3. The live V-Unit presentation accounts for this; future resolution/aspect settings should derive the viewport from the same contract, with an explicit rounding policy. HUD placement, menu aspect and the 3D field of view are separate concerns.

The limitation is visibility upstream. A larger framebuffer cannot show a polygon culled by the game, a sky tile never emitted, or a track section not yet instantiated. Conversely, changing a projection constant does not automatically update independent visibility, sky, HUD, or streaming code. Both approaches need those other systems audited.

**What each game currently has**

| Game | Existing widening mechanism | Assessment |
|---|---|---|
| USA | Expanded screen-space canvas; considerable existing offscreen submission; no default game widescreen patch | Keep it, but test unexercised cull paths during crashes/turns. High coverage in a few captures does not prove completeness |
| World 2.5 / 2.4 | Expanded canvas plus version-specific sky and large-polygon cull patches | Mechanism is appropriate; validate panorama wrap, banked views, subdivision and ROM-specific patch completeness |
| Off Road | Expanded canvas plus right-bound change and nine left-reject trampolines | Strong cause-directed fix; preserve the demonstrated geometry recovery and broaden its scenario coverage |
| Exotica | Zeus-side projected geometry and widened raster/scissor treatment, no corresponding game ROM widescreen patch | More geometric information is available than on V-Unit; audit render-state fidelity and remaining game visibility independently |

The [Off Road patch](E:/Source/cruisn-collection/patch/game/offroadc-widescreen.txt) preserves projection and changes visibility: right bound 511→597, left rejects rechecked against −86. The archived [before/after proof](E:/Source/cruisn-collection/results/proof/offroadc-left-edge-FIXED.png) visibly adds the missing left canyon/ground and removes the blue wedges. That supports this particular repair. It does not establish every track/view is artifact-free.

The history's earlier argument that “no entirely off-left quads appear in the DMA stream, therefore none are missing” was invalid: rejected quads cannot appear in that stream. The later fix correctly overturned it. This is the main methodological lesson to retain—observe the decision before rejection, not only the surviving output.

**Missing or black sky: extend the source layer before considering image filling.**

World's [panorama patch](E:/Source/cruisn-collection/patch/game/crusnwld24-widescreen.txt) expands three 256-pixel tiles to five, shifts the starting tile, extends the bank table and scratch storage, and widens the horizon fill. That directly addresses an insufficiently wide emitted layer. I would keep this strategy.

Broaden its proof from a few frames to every bank transition, yaw phase, supported panorama, and the simple/tilted/second-layer paths. The claim that a common bank table makes it correct “for every track by construction” still depends on all of those paths using the same conventions and valid assets. Check tile continuity and resource identity, not only the percentage of black pixels.

For a new sky defect, distinguish these cases:

| Observation at the bad pixel | Likely layer to investigate | Suitable remedy |
|---|---|---|
| No sky draw covers it | Panorama extent, horizon quad, cull/scissor | Emit the missing layer or correct its visibility bounds |
| A draw covers it but samples zero/transparent data | Addressing, texture version, atlas/wrap rules, actual asset | Repair sampling/resource history or asset interpretation |
| It was covered and later became black | Clear/page selection, an overwrite, state loss | Correct ordered framebuffer operations |
| Sky is visible where terrain should be | Missing/rejected terrain, incorrect depth/order | Recover terrain or repair depth/order; painting the sky black just changes the symptom |
| It is a genuine screen-space panel | UI identity/layout | Place or clip the UI according to intended visibility |

“Black texture” describes appearance, not a diagnosis. The current World tunnel proof contains a translucent HUD panel, but explaining that panel does not rule out a different black-margin defect in another frame. Attach each user report to its own interval and region before closing it.

**Seams need a different treatment from missing world geometry.**

The V-Unit GPU path deliberately has two behaviors: native integer/DDA reproduction and scaled continuous coverage/UV interpolation. The exact path's 100.0000% agreement is valuable. The scaled path changes coverage and dithering, so a new seam can arise there even when the reference path is perfect.

Current repairs include a 0.501-coarse-pixel dilation of axis-aligned rectangles with UV extrapolation, a current-scene written mask, and nearest-written-neighbor crack filling. The dilation's UV correction addresses a real previously observed texture squeeze and should not be casually removed. It still needs tests for adjacent tiles, negative UV gradients, transparency, and rectangles that are real 3D surfaces rather than interface tiles.

The [crack-fill shader](E:/Source/cruisn-collection/gpu/renderer.py:283) cannot identify object/material continuity. It finds written pixels on both sides along an axis and copies a nearby sample. At scale 4 its 3D search radius is 16 internal pixels, because the configured radius is `4 × scale`. A four-coarse-pixel search should not be mistaken for a tiny four-output-pixel correction. The dither exception recognizes one checkerboard arrangement; it is not a complete model of intentional transparency.

I would classify seam failures before modifying fill strength:

| Seam class | Diagnostic discriminator | Preferred direction |
|---|---|---|
| Wrong resource/order | The covered pixel has the wrong texture/palette version or later overwrite | Fix command/resource ordering |
| Quality-only coverage | Native reference is filled, scaled continuous path is not | Fix sample/edge rules with minimal adjacent-primitive fixtures |
| Quantized source edges / T-junction | Adjacent surfaces' submitted boundaries are genuinely different | Recover shared geometry/precision where feasible; use tightly scoped reconstruction |
| Original persistent-page crack | Reference also leaves the pixel untouched and shows previous page contents | Keep exact mode; define an explicit enhanced-mode policy with provenance |
| Missing surface | No appropriate terrain/object reaches the rasterizer | Fix game visibility/streaming, not a seam shader |

OpenGL's shared-edge guarantees apply to truly identical transformed polygon edges; they do not repair mismatched edges or arbitrary fragment-shader coverage. The V-Unit shader rasterizes quad coverage inside bounding rectangles, so those hardware guarantees do not automatically cover its custom scanline decisions. See the shared-edge corollary in the [OpenGL specification](https://registry.khronos.org/OpenGL/specs/gl/glspec46.core.pdf#page=686).

A useful next experiment is a seam atlas: retain both contributing primitives, their original and adjusted coordinates/UVs, resource versions, previous page pixels, and native/quality coverage for a small region. This is much more actionable than a red/blue screenshot with no pixel ownership.

If reconstruction remains necessary, constrain it with actual provenance: same surface/object where known, compatible material, bounded gap, and no intentional transparency or silhouette. Screen-space proximity alone can join unrelated objects. V-Unit's current emitted records do not carry full depth/topology, so a sophisticated repair may require an earlier instrumentation hook; that is a real prerequisite, not something a shader can infer reliably.

For long-term 4K quality, investigate retaining pre-quantization positions from the game's transform/emit path. V-Unit has already reduced screen coordinates to integers by the existing DMA interception point. More raster samples cannot restore precision that was discarded earlier. A diagnostic side channel from one verified emit path could test whether higher-precision shared edges materially improve quality before committing to a larger geometry replacement.

Do not apply global vertex welding, polygon inflation, or stronger neighbor filling without topology checks. They can trade cracks for overlaps, altered silhouettes, translucent halos and texture leakage. They also cannot restore original texture detail; higher-resolution geometry and higher-resolution source artwork are separate improvements.

**Margin masking and extension should be secondary, explicit policies.**

Current backdrop tagging recognizes a few low texture-address bytes plus a wide-quad test. Parked UI suppression recognizes untextured quads in a screen band with size/dither conditions. Those are useful local observations, but they are not durable semantic identities. The same address bits or geometry pattern can occur for unrelated draws.

Prefer game-specific emitter/call-site identity, descriptor identity, or verified layer metadata. Retain all original commands in diagnostics and record why a draw was hidden or extended. Make the chosen repair visible in an overlay and in metrics.

The current rig has margin extension disabled, which agrees with the documented edge-smearing regression. Keep it an optional fallback for known content rather than the default cure. A repeated boundary column cannot reconstruct a canyon wall, building or cloud panorama. Suppressing a backdrop without drawing the intended replacement explains why earlier attempts converted blue holes into black ones.

2D/3D classification is also part of correctness. The 70% axis-aligned-rectangle heuristic can change with a menu animation or with batches merged during backlog. A whole scene can then switch crop policy. Prefer explicit phase/layer information where available; otherwise log the classification and test transitions with hysteresis and known exceptions. Do not let a car-selection frame silently change aspect because its primitive mix crosses a threshold.

**Live resource history must be repaired before interpreting intermittent textures.**

The confirmed V-Unit ordering issue from the main review remains central: texture data is updated during queue draining, while earlier quads are rendered afterward. Preserve the resource version used by each draw. Frozen offline captures cannot establish that a running renderer observes the same ordering.

Zeus already flushes queued geometry before waveram updates, which is the right principle. It versions palette rows through a 256-slot ring; stress the case where a slot is reused before all referencing geometry has been flushed. There is no corresponding capacity guard at the palette-update site. This is a conditional reuse hazard, not a reproduced explanation of the Amazon report.

For both renderers, preserve clears, CPU framebuffer writes, display-page changes, texture updates and palette semantics as ordered operations. Avoid dropping individual persistent-state mutations during backlog. Track displayed page and rendered page separately. A full-memory resync must include all relevant framebuffer/depth/resource state, not only textures.

Zeus currently removes the horizontal scissor restriction for all batches while retaining vertical bounds. Verify which horizontal bounds are the normal screen aperture and which, if any, are intentional sub-view or effect clips. A widescreen extension should widen the screen aperture without erasing meaningful per-draw clipping semantics. The review has not established a specific current scene that depends on a narrower clip; it is a focused coverage question.

The available [MAME Zeus documentation](https://wiki.mamedev.org/index.php/Midway_Zeus_2) reflects reverse-engineered hardware behavior. Agreement with MAME is an emulator-reference result. It should not be described as independent proof of real-board accuracy, particularly for newly implemented or uncertain Zeus behavior.

**Patch loading is now part of the rendering architecture.**

The [patcher](E:/Source/mame-src/src/mame/midway/midvunit.cpp:122) checks and applies each word independently. A mismatch skips that word while retaining earlier changes. The documentation's implication that this makes a whole patch inert on an unsupported version is too strong. Multi-instruction trampolines, branch edits, bank tables and relocated scratch arrays must be installed as a coherent unit.

Require a supported ROM identity and validate every expected word and reserved region before modifying any word in a patch group. Reject the whole group on mismatch; expose its failure in the launcher and run manifest. Check branch destinations, overwritten instructions, scratch lifetime and conflicts between groups. Preserve the original words for controlled teardown/reset and diagnostics.

The per-frame “self-healing” mechanism solved the discovery that boot code copied original words back over patches. It is a pragmatic workaround, but an expected old value is not proof of why the game wrote it. A lifecycle hook after the known program-copy step, plus explicit reinitialization handling, is easier to reason about than opportunistic replacement every frame. Revalidation should be atomic for an instruction group.

The [launcher](E:/Source/cruisn-collection/harness/run_rig.py:1264) currently applies a default widescreen patch only for full width, while a configured experimental patch replaces that choice. Thus later distance work for World or Off Road could accidentally remove their widescreen fixes. Partial-width modes still reveal some previously hidden world, yet skip the full-width patch. Environment overrides can also separate the effective margin from the decision used to choose the patch.

Resolve the final aspect first, compose named compatible patch groups, and log their identities and verified application. Generate/choose bounds from the supported viewport contract. Hardcoded ±86 is reasonable for the current fixed mode; it is not automatically a general ultrawide implementation.

**Draw distance: the earlier research found a real lever, but not the whole system.**

The USA investigation is useful. Its negative control lowered the renderer gate and substantially removed geometry. That supports identification of the gate. The later extension producing little difference supports a second bottleneck, but the exact limiting stage should still be attributed object by object.

There are at least six separate distances/policies:

1. Course-section availability: when data becomes available or a segment becomes eligible.
2. Object instantiation/retention: when renderable nodes enter and leave pools/lists.
3. Render visibility: depth/radius and horizontal/vertical rejection.
4. LOD/subdivision: which mesh and polygon partition are selected.
5. Projection/numerical range: valid reciprocal-depth lookup and coordinate representation.
6. Appearance: fog, texture minification, and transitions that make changes conspicuous.

Increasing one does not automatically increase the others. It also need not be appropriate for all classes: traffic activation, collision simulation and render-only scenery may need different policies.

For the reviewed USA ROM, the recorded investigation identifies node LOD choices around depths 8,000 and 15,000, a `depth − radius` rejection against word `0x55` at 80,000, and a reciprocal lookup indexed by depth shifted right four bits with its index capped at 5,000. The experimental patch raises the gate to 160,000 and both LOD thresholds to 32,000.

Two concerns deserve a fresh experiment:

- **The reciprocal lookup still has its old far range.** If newly admitted geometry is projected through the capped index, beyond-range depths may use the last available reciprocal rather than the appropriate reciprocal. Verify which admitted vertices actually take that path. Increasing the gate is not a complete projection-range extension. A deliberate reciprocal calculation or a larger correctly populated table may be needed, with center/near behavior preserved.
- **Both LOD thresholds become identical.** This effectively collapses the medium-distance interval in the described selection path, making the change more than “draw farther.” Separate visibility distance from detail distance, retain ordered thresholds, and compare transitions independently. Extra geometry can cost CPU and GPU time without addressing the distracting pop-in.

These are deductions from the documented code path and current patch, not newly measured artifacts. Check them against a recorded approach and actual branch/lookup observations before implementing a remedy.

**A better next distance experiment**

Choose one named building/terrain section whose appearance is distracting. Record a route approaching it. For frames before and after its first visible appearance, collect:

| Stage | Identity/evidence |
|---|---|
| Track data | Section ID and eligibility/residency changes |
| Node lifetime | Allocation/free, source descriptor, list membership, object class |
| Visibility | Camera-space depth/radius, each rejection reason and branch site |
| Detail | Selected geometry pointer, LOD and subdivision decisions |
| Projection | Input depth, reciprocal index/value, pre-quantized coordinates and wrapped/out-of-range values |
| Output | Emitted primitive count/IDs and actual pixel contribution |

Then change only the first stage shown to suppress that object. Use a lower-distance negative control as well as an extension. Capture the effective patched words at the point of execution so a reverted/inactive patch cannot masquerade as a negative result.

If the object exists but is rejected, widen the relevant render bound. If the object is absent, trace the section/node creation path and extend a bounded forward window. If loading and simulation activation are coupled, decouple render residency where feasible instead of waking every distant opponent or collision object. Track pool capacity, sort-list size, CPU cycles, texture traffic and GPU cost.

If projection caps, repair that stage before interpreting farther geometry. If the object is present at low LOD, address detail selection and transition policy. If geometry is correct but distant texture detail shimmers, investigate minification/LOD as an appearance issue. Fog can reduce visual harshness but should not be counted as a geometry-availability fix.

Start with USA because its path is already partly mapped. Do not transpose its addresses or numerical limits to World, Off Road or Zeus. Share the instrumentation schema and experiment method, not unsupported game constants.

**Alternative long-term directions**

| Approach | Benefit | Cost / limitation | Recommendation |
|---|---|---|---|
| Current interception plus precise game visibility patches | Preserves original game behavior and much existing proof | Continued per-game reverse engineering and transport fidelity work | Primary near-term architecture |
| Earlier transform/emit interception | Can retain precision, object identity and depth/topology needed for better scaling and seams | Must map and validate relevant code paths and ROM revisions | Bounded R&D on one proven problematic path |
| Partial high-level geometry replacement | Direct control of projection, culling, LOD and render residency | Larger correctness burden; game-side creation may still limit objects | Consider after object/transform schemas are demonstrated |
| Full geometry/asset/world replacement | Maximum long-term presentation control | Major project, asset/animation/visibility reconstruction and broad regressions | No current evidence justifies making this the immediate plan |
| More image-space fill or stretching | Cheap reduction of visible holes | Cannot recover correct geometry; introduces smearing/incorrect coverage | Explicit fallback, with bounded scope and measurable repair area |

The appealing staged path is to keep native emulation as the behavioral reference while adding narrowly validated higher-level data at the points where the current screen-space-only interception loses information. This offers a route to better precision and draw-distance control without committing the whole collection to a speculative rewrite.

**What I would implement first, when changes are authorized**

| Order | Deliverable | Definition of done |
|---|---|---|
| 1 | Recorded route and per-pixel/primitive evidence for one current artifact | The same defect can be located automatically at the same game state |
| 2 | Ordered render/resource replay and patch-group verification | Texture rewrites, page changes and partial patch failures have explicit passing/failing tests |
| 3 | One cause-directed repair per defect class | Missing geometry is recovered; sky coverage is continuous; actual seams are narrowed without hiding unrelated surfaces |
| 4 | One USA object-lifetime distance trace | The exact limiter is identified before a new extension is attempted |
| 5 | Independent visibility, projection-range and LOD experiments | Improved appearance is demonstrated on the same route with bounded CPU/GPU costs |
| 6 | Broader game/track/view matrix and optional precision R&D | The fix survives the cases it was not tuned against |

The relevant success measure is correct, stable extra world visible at the intended framing, with fewer unexplained repairs and acceptable timing. Neither “zero black pixels,” “more quads,” nor “native mode remains exact” is sufficient by itself.
