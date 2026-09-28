# World 2.5 Hawaii active-margin interval — September 28

The shared World active non-road margin option had only a single exact
World 2.5 Hawaii view at completed frame 5900. I compared a bounded nine-frame
interval from 5750 through 5950 at 25-frame spacing, where the existing 3×
terrain candidate is known to add distant mountains. Both control and opt-in
replay the same saved 5,970-input Hawaii drive on frozen native `f762e01d63b`,
stable physical 2560×1440 display, literal FFB0 and identical completed-frame
requests. Both pass original input/native checks and owned shutdown.

The option submits 107,824 more host quads over the same scenes. Six of nine
2544×1353 completed images differ: 5775 by 24,339 pixels, 5800 by 10,189,
and 5825/5850/5875/5925 by 28/177/549/922. Frames 5750, 5900 and 5950
remain exact. All 36,204 changed frame-pixels lie in the left third; the center
is exact throughout. The inspected 5775 pair shows extra trees at the extreme
left edge, with no change to the road, car or distant ocean. This is visible
cross-revision execution, not proof of a substantial draw-distance gain. The
small near-black heuristic counts (176 candidate-new, 95 recovered across
the differing images) are not texture-defect measurements.

Most importantly, the conspicuous Hawaii dark rectangle/terrain edge at 5900
is exact on both sides. The prior source analysis found its authored lower
mesh edge already within the 3× plane; the rejected generic skirt produced a
wall. This active-object margin policy does not solve that separate coverage
problem. The exact-pixel comparator returns **FAIL** because six completed
images intentionally differ, while the paired route/preservation comparator
passes. Neither result authorizes renderer promotion, 4K acceptance or a claim
that distant pop-in is eliminated.

Local evidence is under `results/diagnostics/world-new-york-20260927-live-1`:
`world25-5750-{control,nonroads}-run/report.json`,
`world25-5750-paired-v1.json`, the expected exact-difference
`world25-5750-gl-v1.json`, and `world25-5750-contact.png`. Related source
analysis is in `2026-09-14-world-terrain-boundary.md` and the rejected skirt
trial in `2026-09-23-world-hawaii-skirt-trial.md`. No source code, native build,
release or personal installation changed.
