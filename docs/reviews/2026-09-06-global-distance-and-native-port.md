# Global draw distance and native-port reassessment

Follow-up: the [global native trial](2026-09-06-global-distance-trial.md) is now
implemented and measured. The text below records the research before that trial;
its final unbuilt-draft status is historical. Normal launcher preferences remain
unchanged.

Assessment: September 6, 2026 (America/Chicago). Sources inspected September 6–7.
Product baseline: collection `37f698f`, native `e8b8fc3be9c`, deployed executable
SHA256 `d520c414c8bae335abe316695f78ff4794513e97313b000b10b28ff24dfcec47`.

The recommendation is to move from individual scenery exceptions to a shared
engine approach: first measure the combined global limits, then prototype a
separate draw path for distant static scenery. A full native port is a credible
longer-term option, especially for USA, but it is not a prerequisite for that
draw path. The available evidence does not establish that pop-in can be eliminated
everywhere in all four games.

Our previous research was too concentrated on the local implementation. It found
real mechanisms and delivered measured improvements, but a growing list of model
addresses is not a satisfactory long-term architecture. The new findings below
change the recommended direction.

## A directly relevant native port already exists

[Jeff Harris's Cruis'n USA project](https://github.com/jeff-1amstudios/cruisin-usa)
translates the arcade assembly into portable C/SDL2, with AI assistance and MAME
validation. Its README explicitly says the port is not yet fully playable.
The available original source is version 4.4; its source/ROM walker aligns that
source to the 4.5 game, recovering changed code and missing constants. Inspected
commit: `5eeeb65f0c716aa20435286f7d39ea0a99dbc17c`.

The author's [development account](https://1amstudios.com/articles/cruisin-usa/)
reports work beginning in May 2026, reaching the starting line and player input
in August, with gameplay systems still unfinished. It describes two substantial
obstacles: cooperative processes that resume inside functions, and CPU floating
point that cannot be replaced indiscriminately with ordinary host floats. This
is evidence of feasibility and of remaining work, not a schedule for our project.

I inspected its source, mapping files, translation documentation and validation
implementation. I have **not built or independently play-tested that port**.
There are still unimplemented gameplay routines in the inspected tree. We should
evaluate it before commissioning a duplicate USA translation effort. Reuse terms
must be established before importing implementation; this assessment imports no
third-party game code or assets.

For USA, the work is largely source-assisted translation and reconciliation with
the shipped binary. Calling it a completely blind decompilation understates the
head start. Searches in this review did not establish comparable original source
or a working arcade native port for World, Off Road Challenge, or Exotica. That is
an unresolved availability question, not proof that none exists.

## What the USA source explains about our distance problem

The inspected [background system](https://github.com/jeff-1amstudios/cruisin-usa/blob/5eeeb65f0c716aa20435286f7d39ea0a99dbc17c/asm/BACKGRND.ASM)
loads track groups separately from object drawing. It has an 80,000-unit group
activation distance, different removal behavior in attract and gameplay, a track
watcher, and a group loader that checks available object slots. Group records
provide model references and placements. This gives us a concrete route toward
decoding whole sections instead of discovering every mountain separately.

The [object system](https://github.com/jeff-1amstudios/cruisin-usa/blob/5eeeb65f0c716aa20435286f7d39ea0a99dbc17c/asm/OBJ.ASM)
has separate active/inactive lists and thresholds of 75,000 and 80,000. The
[object definitions](https://github.com/jeff-1amstudios/cruisin-usa/blob/5eeeb65f0c716aa20435286f7d39ea0a99dbc17c/asm/OBJ.EQU)
specify 1,100 objects and identify posters, animation, associated processes and
supplemental vehicle/road/ground lists. The
[group definitions](https://github.com/jeff-1amstudios/cruisin-usa/blob/5eeeb65f0c716aa20435286f7d39ea0a99dbc17c/asm/SYS.EQU)
reserve 20 dynamic groups.

These names and structures are useful hypotheses for related games. They are
**not interchangeable layouts**: for example, World's measured compact object
layout differs from this USA definition. Flags, strides, addresses and behavior
must be verified per game/revision. The source's poster bit agrees with a useful
World observation (`2008` pending tree cards), but that alone does not validate
the rest of the structure.

Our local World 2.4 work independently establishes several gates:

| Gate | Current evidence | Consequence |
| --- | --- | --- |
| Object allocation | A returning mountain exists in RAM before it becomes active | Some missing geometry is already available to draw |
| Pending admission | Shared routine at `7B4C`, threshold word `D58C = 11` | Extending the renderer's far limit alone cannot admit these objects |
| Far rejection | Shared comparisons around `A0` and `A8`, original limit 80,000 | Already active objects can still be rejected |
| Projection | Reciprocal indexing originally clamps at 4,999 | A farther object needs valid projection beyond the original table |
| Sorting and frame work | Additional drawing can change list order and execution timing | More quads are not automatically a correct result |
| Section residency | USA source documents a separate loader; World equivalent still needs mapping | A pending-list change cannot draw objects that were never instantiated |

The August feasibility study's broad confidence about free widescreen and all
research risks being retired was not justified by its two successful scenes.
The renderer proof was valuable; it did not establish full gameplay visibility,
scene residency, or timing independence. Preserve that historical study, but use
this narrower assessment for planning.

## What other projects actually do

| Precedent | Verified technique | What carries over; what does not |
| --- | --- | --- |
| [OutRun2006Tweaks](https://github.com/emoose/OutRun2006Tweaks/blob/08e5efb4deea4066c440307ec009c868a30562d3/src/hooks_drawdistance.cpp#L437) | Combines culling-node lists from additional track sections and deduplicates nodes before drawing | Strong racing precedent for a shared section-level solution. Its source also documents conflicting LODs, exposed incomplete track geometry and stage exceptions. It is not a universal, exception-free slider. |
| [OpenMW distant terrain/object paging](https://openmw.readthedocs.io/en/openmw-0.51.0/reference/modding/settings/terrain.html) | Loads and batches distant objects outside the active cell grid; uses terrain LOD and size/distance visibility thresholds | Strong precedent for a visual world larger than the simulated neighborhood. Cruis'n needs its own decoder and object identity model. |
| [Zelda64Recomp culling patch](https://github.com/Zelda64Recomp/Zelda64Recomp/blob/dev/patches/culling.c) | Changes the shared actor culling function for the wider view while retaining distance checks | Shows why a game-level hook can fix an entire class of clipping. This particular patch does not remove all distance limits or load missing rooms. |
| [RT64](https://github.com/rt64/rt64) | Retains untransformed vertices/transforms and matches drawing across frames | Supports moving our capture boundary earlier, before world geometry becomes screen-space quads. RT64 is an N64 renderer, not a V-Unit replacement we can plug in. |
| [Distant Horizons](https://gitlab.com/distant-horizons-team/distant-horizons/-/releases) | Maintains distant LOD data, including explicit handling of that data during replay | Precedent for a separate persistent visual representation. A Cruis'n cache would need source geometry, placements, materials and invalidation rules; saved screenshots cannot provide that. |

The common pattern is controlling scene preparation and data residency as well
as projection. There is no evidence here that a postprocessing filter can recover
arbitrary scenery the game has not submitted.

## New local global experiment: useful, not accepted as a fix

`lua/world_pending_distance.lua` advances the shared pending threshold by up to
eight track sections for a bounded 240-frame window. It applies to every pending
model. The guest performs its normal list transfers; those effects persist after
the diagnostic tap closes. This is an experimental change to game execution.

In the clean comparison with the existing selective scenery feature **off**:

- Both runs completed 201 GL captures, frames 5900–6300 every two frames.
- The zero-lead control reproduces the attended recording through frame 6304.
- Extra-lookahead rendering differs beginning at frame 5910.
- Both traces have 1,263 actual ADC reads with matching frame/value/program-counter
  sequences, but the read timestamps differ.
- All 421 camera samples cover frames 5880–6300; the first camera difference is
  frame 6184. The later captures show differing driving state as well as scenery.

Therefore matching recorded inputs does not prove an unchanged route. This test
does not isolate whether the divergence comes from additional execution time,
simulation activation, or both. Its changed screenshots cannot all be attributed
to improved drawing. It also does not prove a global strategy is impossible.

See [camera/input comparison](../../results/proof/2026-09-06-global-distance/global-motion-comparison.json),
[completed-frame comparison](../../results/proof/2026-09-06-global-distance/global-motion-visible.json)
and [contact sheet](../../results/proof/2026-09-06-global-distance/global-motion-comparison.png).
The previous broader geometry experiment retains its failed geometry/order
checks; unknown additional models and frame-boundary shifts are not silently
classified as defects or successes.

## Recommended global approaches, in order

1. **Measure the complete shared path.** Map section allocation, pending admission,
   far rejection, reciprocal projection, list capacity and sorting. Use the USA
   source as a guide and verify World signatures. Run separate far-only,
   lookahead-only and combined controls. A native diagnostic can remove Lua
   overhead, but must still measure guest execution and actual gameplay state.
   Stop expanding per-model allowlists as the main development strategy.

2. **Prototype a host-side static-scene draw path.** Read existing pending static
   objects without transferring them into the active simulation. Decode their
   original model vertices/materials, apply the current camera and draw them in
   the appropriate scene order. Start with a verified semantic class rather than
   a list of tree addresses. Track identity as allocation/section plus placement,
   not model alone: many trees share one model. Compare the native projection to
   captured original objects before using it for new distant ones.

3. **Extend that path to future track sections.** Decode section/group placement
   records directly from the user's ROM data into host-owned scene storage. That
   avoids consuming the original game's small object pool just to display distant
   scenery. Deduplicate shared instances; resolve LOD alternatives; preserve
   palette/texture lifetime. Dynamic road deformation, animated or destructible
   objects and section scripts need explicit handling, not a guess that every
   pending object is static.

4. **Add perceptual controls after real geometry is available.** Use projected
   pixel size to spend work on visible mountains and trees, keep visibility
   hysteresis to prevent flicker, and consider gentle distance fades or simplified
   far models. Existing checkerboard shadows are a reason to evaluate smooth
   fades carefully rather than introducing another visible dither pattern.
   Fog is optional presentation polish, not evidence that a missing surface was
   reconstructed.

The static-scene path has the best architectural fit for the user's goal. It
could expose one meaningful distance setting across levels while retaining
small, documented exceptions where the original assets are incomplete. It is
also a partial native port: the component that benefits most from modern hardware
moves out of the guest without first rewriting menus, physics, audio and I/O.

A fallback research option is an offline scene cache assembled from isolated
exploration runs. It must store world-space geometry and original placements,
not projected quads, and it cannot claim completeness from one drive. Direct
section decoding is preferable when available. An entire-level renderer may be
practical for these assets, but total unique geometry/material residency has not
yet been measured; the small current per-frame quad count is not that measurement.

## Decompilation, recompilation and a native port are different investments

| Approach | Feasibility assessment | Main limitation |
| --- | --- | --- |
| Shared engine patches inside MAME | Demonstrated in limited forms; continue controlled global experiments | Guest timing, object pools and original scene assumptions remain |
| Native transform/culling/static scenery with MAME retained | Best first substantial investment; concrete source and trace boundaries exist | Need verified model/placement decoding and correct integration with existing scenes |
| TMS320C3x static recompiler or dynamic compiler | Technically plausible, substantial reusable infrastructure | Instruction semantics, control flow, interrupts, memory/I/O and code invalidation all require validation |
| USA source-assisted native port | Credible longer-term project with an existing effort to evaluate | Full gameplay correctness and integration remain unfinished |
| Native World and Off Road ports | Plausible follow-ons, lower confidence until shared routines/data are mapped | Same hardware does not establish identical engines or available source |
| Native Exotica port | Plausible research project, least established of these targets | Related CPU helps, but Zeus2 rendering and game-specific behavior remain separate |

[N64Recomp](https://github.com/N64Recomp/N64Recomp) demonstrates a useful middle
ground: literal binary-to-C translation with symbol metadata and a supporting
runtime, without first reconstructing beautiful high-level source. It targets
N64 MIPS code. We cannot feed our arcade ROMs to it and obtain a working port;
a TMS320C3x backend and arcade runtime would be new work.

Our actual drivers use TMS320C31 for V-Unit and
[TMS320C32 for Zeus2](https://github.com/mamedev/mame/blob/mame0286/src/mame/midway/midzeus.cpp).
The local MAME C3x implementation executes an instruction interpreter. A shared
translation backend could benefit all four games, subject to C31/C32 differences.
It must handle word addressing, CPU floating formats, delayed control flow,
parallel operations, repeat blocks, interrupts and RAM-resident program code.
Our runtime patches also mean translated blocks need correct invalidation.

Two distinctions matter for distance work:

- Faster host execution while preserving guest cycle accounting does not grant
  the original game more work per emulated frame. Overclocking or changing cycle
  accounting is another behavioral change and needs separate testing.
- Faithful recompilation preserves the original culling and loading limits.
  It creates a better place to modify those systems; it does not itself remove
  pop-in. A full native port is not inherently necessary for extended distance.

AI can accelerate source/ROM alignment, function translation, trace analysis and
test generation. It does not provide correctness by producing plausible C.
Jeff's [validation design](https://github.com/jeff-1amstudios/cruisin-usa/blob/5eeeb65f0c716aa20435286f7d39ea0a99dbc17c/docs/debugging.md)
compares ordered function/register/memory events with MAME and stops at a
divergence. Its float assertions have documented tolerances; that is not a
blanket bit-exact certification. We should retain raw comparisons where exact
behavior is required and explicitly distinguish enhanced behavior.

I would plan a full USA port as a sustained effort measured in months, with
substantial uncertainty until we build and exercise the existing project.
There is not enough evidence for an honest four-game completion date. A bounded
native scenery prototype should be the first investment, with continuation based
on measured visual improvement, correctness and portability.

## Milestones and acceptance evidence

1. Produce a verified engine map for USA and World: routine signatures, object
   layouts, section records, capacities and material ownership. At least one
   second World level must exercise the same mechanism without new model IDs.
2. Replay captured transform inputs through a native implementation and compare
   vertices, projected coordinates, texture references and ordering. Exercise
   clipping boundaries and extreme depths, not just normal attract frames.
3. Render an entire pending static class on Germany with the guest lists and
   simulation unchanged. Record earlier appearance time and screen area, plus
   player/camera state, ADC timing, collisions and emulated speed. Completed GL
   receipts and fixed-resolution captures remain mandatory.
4. Extend to section data and a second level. Measure unique model/instance counts,
   host memory, guest work, frame-time percentiles and missing material accesses.
   Test crashes, sharp turns, transmission selection and the late black-road
   window; attractive horizon screenshots alone are insufficient.
5. Repeat enhanced cases against themselves and retain original controls. If a
   deliberate timing change invalidates the old route, create a versioned case
   and preserve the old one. A new recording is not a substitute for investigating
   why a supposedly visual-only change altered gameplay.
6. Validate the three other games with enhancements off, then add verified adapters
   one at a time. Share scene data structures, validation and feature controls;
   keep ROM-specific signatures separate. The wheel toolkit should consume stable
   telemetry/events whether their source is MAME memory or native game logic.

The desired product criterion is no conspicuous scenery appearance during normal
driving across a documented gameplay corpus. Track first-visible projected size,
how early the object appears, missing surfaces, route stability and frame pacing.
Define numeric thresholds from reviewed clips. Do not equate extra submitted
quads, a larger distance number, or perfect reproduction of one recording with
that user-facing outcome.

The experimental native global-distance draft is archived separately, unbuilt and
excluded from production sources. No new distance setting or executable was
deployed as part of this research assessment.
