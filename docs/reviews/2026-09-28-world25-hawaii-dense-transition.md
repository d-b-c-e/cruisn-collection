# World 2.5 Hawaii: dense margin transition near frame 5775

The nine-frame active non-road margin comparison sampled Hawaii every 25
frames. Its largest change at completed frame 5775 had source-qualified
panorama and prior-host overlap, but the sparse cadence could not describe
how the added scenery entered the view. I replayed the same saved World 2.5
drive to input frame 5820 with eleven completed CRT captures at 5750..5800,
every five frames. Frozen diagnostic native `f762e01d63b` and the existing
3× World host settings were identical except for active non-road margins.
Both runs used the physical 2560×1440 primary and literal FFB0.

Both raw replay reports **PASS** 5,820 recorded inputs, native comparison,
display-watch stability and owned worker shutdown. The paired comparator
**PASS**es same case, binary, presentation and 1,877 host scenes. The candidate
submits 105,071 additional quads over that prefix. This is work performed,
not itself a visible benefit. All eleven completed images are present without
dropped persistent state. Frames 5775 and 5800 in each arm are byte-identical
to the corresponding earlier 25-frame-cadence capture.

| Completed frame | Changed RGB pixels | Location | Visual check |
| ---: | ---: | --- | --- |
| 5750, 5755, 5765 | 0 | — | Exact control/candidate images. |
| 5760 | 5,656 | Right third, x=2328..2474 | The candidate continues a guardrail farther toward the right edge. |
| 5770 | 673 | Left third, x=156..314 | Small extra foliage at the margin. |
| 5775 | 24,339 | Left third, x=67..319 | Trees appear at the outer left, including the previously source-attributed overlap. |
| 5780..5800 | 6,576..10,189 each | Left third, x=67..322 | The extra foliage remains in sampled views. |

The eight differing images total 74,557 changed RGB frame-pixels. **No
center-third pixel changes** in any of the eleven frames. The right-side
guardrail extension at 5760 looks spatially coherent in the inspected
control/candidate crop. The subsequent
[indexed ownership check](2026-09-28-world25-hawaii-guardrail-ownership.md)
finds that this change replaces only one original lower panorama strip at
its sampled frame. The left tree at 5775 follows a view where a nearer
cliff/tree occupies much of that edge, which is consistent with an occlusion
transition; five-frame sampling does not establish a fade or prove that the
object never pops. The exact old/new packet and depth attribution from the
[5775 source check](2026-09-28-world25-hawaii-prior-host-source.md) applies
only to that completed view. A later check attributes all 5760 changes to
two added active objects from the exact source scene. The candidate-new
near-black color count across the eight differing images is 454, but dark
scenery is not automatically a texture defect.

This pair expands World 2.5 transition evidence without demonstrating a
mountain draw-distance gain or repairing the authored dark rectangle at 5900.
It is one route at physical 1440p, with 5-frame sampling and no physical FFB.
Before any policy promotion, search for a concrete harmful overdraw and
retain 4K/other-course gates.
No native source, binary, renderer deployment, personal installation or
public release changed.

Local evidence: `results/diagnostics/world-new-york-20260927-live-1/`
`world25-5750-dense-{control,nonroads}-run/report.json`,
`world25-5750-dense-paired-v1.json`, `world25-5750-dense-contact.png`,
and `world25-5760-right-crop.png`. The two prepare-only plans and all raw
run reports remain separate.
