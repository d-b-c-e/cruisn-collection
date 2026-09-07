# Four tree variants and gameplay appearance tracing

The second native scenery build covers four verified tree cards. It improves
small horizon details, but does not establish a cure for the large forest and
mountain pop-in. The new gameplay trace identifies larger candidates and separates
distance rejection from objects that have not reached the drawing list.

## Four-tree build

Native commit `5ca501570a5`, executable SHA256
`2e3ac3f32e791516a7b0f8d0339cf7cf98c120e90a02b14b94ce0f34acc09f56`.
The World 2.4-only Distant Scenery option remains OFF by default. The original
three-mountain policy is unchanged. Tree additions are CA5833 (mirrored conifer,
radius1950), CA5863 (broadleaf,818), and CA5896 (broadleaf,1252), alongside CA57F3.
Exact model/radius/flags and bounded projection checks remain in force.

- The bounded Lua experiment adds289 quads across21 drawing frames. No original
  quad changes, disappears or changes relative order. Every new quad fits within
  32 native pixels. The native implementation matches that geometry exactly.
- A full8783-frame Germany candidate and its repeat match all input/time rows and
  146 native screenshots. Ten parent screenshots differ; the remaining136 match.
  Derivation proves repeatability, not exact original route or attended acceptance.
- Each full run reports371 mountain admissions,3964 tree admissions and31712
  extended reciprocal reads, with maximum index8120 of the supported10000.
  Both average about100.005% emulation during frames1800..8780.
- A completed201-image GL run (1600..2400 every4), with only the tree extension
  enabled, differs from scenery-OFF in109 images. The largest difference is49 pixels at2168,
  within X301..327/Y221..228 of the captured viewport. Last difference:2192.
  This is a measured but small visual benefit.
- All seven original default-build regression cases pass, including their timing
  gates and Exotica's21 completed GL captures. Shaders and toolkit are unchanged.

Proof: [four-tree evidence](../../results/proof/2026-09-06-four-trees/).

The long Lua GL run **timed out at frame2252**, with164 completed images. It is
retained as a failed run, not accepted as a complete capture. Its164 shared images
match the native run, which completed all201 requested images. No Lua error was
logged; the timeout's cause is unconfirmed. Full native candidate/repeat runs also
completed normally. The proof records this limitation explicitly.

## Appearance trace

`lua/world_scenery_events.lua` observes the World 2.4 far test and joins it to
submitted DMA geometry in the same frame. It aggregates consecutive raw page-control
runs, dropping the incomplete leading/trailing runs. It records appearance events
and per-scene counts instead of millions of individual polygon rows.

The full read-only run matches the attended baseline:8783 input/time rows and146
native images. It records3584 completed runs,4578059 attributed quads,6700 unjoined
shared-path calls and16323 appearance events in about1.77MB of CSV. Shared polygon
paths also serve HUD/other geometry; an unjoined call is not necessarily missing3D.

`harness/analyze_scenery_events.py` ranks clipped submitted bounds and proposes
capture windows. Bounds area is not visible pixel area. A reused object slot or
model change is not by itself a LOD transition. A first far-gate observation is
not proof that the model was created or loaded at that instant. Results are
candidate findings, not an automated assertion that every appearance is a bug.

The trace recovers the known CB1A8B mountain crossing at2027. It also finds two
more mountains (CB2314/CB21A2) and a grouped forest strip (CB2375), verified by
isolating their submitted geometry against the captured texture atlas. Their
original crossings occur at2143/2181/2175 respectively. These need separate
bounded admission and completed-GL validation before native coverage expands.

Another large appearance, CCF288 at3019, is already inside the original far range
(depth-minus-radius53996). A read-only object-write trace finds allocation at2991
and a pending-to-active flag change at3017. This is evidence of a separate
activation limit; its precise policy and safe earlier activation remain under
investigation. Raising the global far value alone cannot alter this earlier stage.

Proof: [appearance trace](../../results/proof/2026-09-06-scenery-events/).
Probe reports now archive literal `CRUISN_*` environment inputs alongside the
script hash. An unset value means the archived script's default. No physical FFB
is enabled during these automated tests.
