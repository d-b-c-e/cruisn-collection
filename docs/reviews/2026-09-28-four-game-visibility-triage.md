# Four-game extended-rendering visibility triage — September 28

The current opt-in distance and margin paths execute across all four games,
but their visible returns differ sharply. The table uses saved matched reports;
each row names its own control and capture regime. Pixel totals are accumulated
**frame-pixels**, not unique screen area. They are not comparable quality
scores across routes, resolutions or different interventions.

| Saved comparison | Completed images with a difference | Changed frame-pixels | What is actually established |
| --- | ---: | ---: | --- |
| USA Golden Gate continuation, original case vs continuous 3×, 3824×2073 CRT | 11/13; the two Continue/menu views are exact | 377,941 | Same 12,212 inputs, camera and ADC trace; extra distant bridge/roadside geometry appears, but some sampled new dark pixels and start-letter overlap remain to inspect. |
| World 2.4 New York turn, control vs active non-road margins on top of 3×, 2544×1353 CRT | 9/9 | 258,118 | Moving right-edge wall/shoulder gap is visibly reduced. Source-joined frame 3600 fills 24,759 formerly unowned pixels and replaces 25,631 original backdrop pixels; ten indexed edge pixels remain unowned. |
| World 2.4 Germany early turn, same margin toggle, 2544×1353 CRT | 9/9 | 67,482 | Distant left-edge scenery appears. At source-checked frame 7280, the building replaces only upper panorama strips and fills no gap. It does not address mountain activation or reported road holes. |
| World 2.5 Hawaii, same margin toggle, 2544×1353 CRT | 6/9 | 36,204 | Extra far-left foliage. At source-checked frame 5775, changes replace sky/ocean panorama and 972 prior host pixels, with no newly owned gap. The dark authored rectangle at 5900 is exact in both modes. |
| Off-Road Pike's Peak, control vs resident ground margins over 3×, 2544×1353 CRT | 0/10 | 0 | 268,381 extra submitted quads but no visible gain in sparse samples. A denser fast-turn control screen also found no clear El Paso-like gap; no reason yet for another resident pair. |
| Exotica Mars, 2× vs 3×, 3840×2160 CRT | 4/15 | 985 | A small far-left extra-scene appearance with identical saved camera/ADC traces and original resources. The equal intervening 5220 frame and zero visible fragments at 5300 prevent any claim of smooth fade or eliminated pop-in. |

The sample sizes and baselines differ. In particular, USA compares the recorded
control to continuous 3×, Exotica compares 2× to 3×, and the World/Off-Road
rows test additional margin policies **on top of** an existing 3× control.
One screenshot may change because of replacement or overlap rather than an
earlier object activation. The original-DMA-qualified World checks make that
distinction visible: Hawaii and Germany gains are largely backdrop
replacement, while New York has a measured unowned black wedge. More
submitted quads are therefore a poor success metric.

The next evidence gates should target different uncertainties:

1. **USA:** the Golden Gate frame-10500 source screen now distinguishes an
   unchanged original-game dithered right-sky panel from an earlier auxiliary
   red bridge at the left. See the [source check](2026-09-28-usa-golden-gate-panel-source.md).
   The later [packet check](2026-09-28-usa-bridge-object-activation.md)
   finds three sampled future objects entering the host stream at staggered
   frames 9855/10039/10475. Its skeletal appearance remains a potential 3×
   quality regression despite more visible geometry. Preserve the raw USA
   verifier FAIL and separate posthoc pass.
2. **World:** keep active non-road margins gated. The New York gap is a real
   positive case, but source/ordered ownership and transitions on another
   defect-bearing course remain before promotion. Do not use Hawaii/Germany
   backdrop replacement as proof that mountains appear earlier.
3. **Off-Road:** retain El Paso as the positive resident-ground route. Seek a
   precise second-course gap or owner timestamp before another Pike's Peak
   resident replay. Sparse exact frames do not qualify the whole course.
4. **Exotica:** use a saved open-sightline scene with completed depth and source
   identity, or an attended contrasting course, before another full 3× run.
   Amazon's existing occluded third-band scenes are weak quality samples.

Sources are the local `usa-menu-tail-3x-qualified.json` under
`results/diagnostics/race-transitions-20260916`,
`mars-appearance-qualified.json` under
`results/diagnostics/exotica-open-course-20260916`,
`paired-safety-v2.json` under
`results/diagnostics/offroad-pikes-peak-20260927-live-1`, and the New York,
Germany and Hawaii paired/source-hashed reports under
`results/diagnostics/world-new-york-20260927-live-1`. See the September 28
per-course reviews for input/native, original-resource, completed-image and
shutdown qualifications. No native build, release, deployment or additional
game replay was made for this synthesis.
