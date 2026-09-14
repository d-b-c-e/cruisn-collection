# World detailed-road experiment — September 14, 2026

This explicitly gated experiment uses the original detailed road models at
extended distances, bypassing World's simplified distant road templates in the
host renderer. It supports separately mapped World 2.4 and 2.5. The original game
retains its own LOD, allocation, physics and rendering commands.

It follows the [World 2.5 road adapter](2026-09-14-world25-roads.md), whose visible
benefit was small in the inspected coastal scene. In that saved 5900 scene,
replacing simplified templates with original road models increases assembled
quads from 5,702 to 8,294. Hundreds of added quads project into the distant region
under investigation. This motivated a controlled visibility experiment; counts
alone do not establish repair or useful detail.

`--world-host-road-detail full` requires an explicit candidate and host roads on.
`stock` restores the original model-selection policy. Older recordings without
the setting preserve stock selection. The choice is frozen independently of
draw distance. Unknown revisions, unsupported layouts, invalid model/material
spans and existing projection bounds still reject; no geometry guard was relaxed.

Independent Python and native checks pass all four existing 2.4 snapshots and
eleven 2.5 snapshots at 1×/2×/3×, comparing 31,403 and 60,622 future quads
respectively. Descriptor, allocation and binding checks remain active. Two
targeted native tests cover original/full model choice and invalid combinations;
eight Python tests cover options, inherited recordings, required candidate,
road-off rejection and restoring stock selection.

The full 6,000-input 2.5 experiment preserves original native frames, all 4,191
camera samples and 12,573 ADC reads/timestamps. It submits 1,820,814 road quads
across the same 1,666 scenes and 218,655 road-instance visits, versus 185,640 road
quads with stock templates. Average emulation speed is 99.98% in this run.

**The terrain-gap hypothesis is not confirmed.** Four of twelve completed images
change by only 22–197 pixels, mostly near the horizon. The disconnected terrain
remains visibly unchanged. This is a diagnostic option, not a recommended setting
or a release fix. The extra geometry's projected bounds do not establish that it
survives subsequent original drawing. The next investigation traces original
background/ocean commands and host insertion order; their interference is a
hypothesis until measured. No blanket foreground-occlusion bypass is justified.

Native candidate: `679ef586ef7ffc4dfba6665762f4d53b9f9da6d9`, SHA256
`fe397937bd3a151d450c686c1532f772c0c1e632bc0a4802e3857e04593b22f3`.
The separately frozen binary and unchanged force profile are in
`build/candidates/679ef586ef7/`. The 196-patch export reconstructs tree
`487a66d6d302f48468971dc5db28a39beef910b4`, preserving the previous 195 patches.

Local evidence lives under `results/diagnostics/world25-roads-20260914/`:
`full-road-models`, `full-road-detail-checks`, `roads-full-detail`,
`full-detail-comparison.json/png`, and `full-detail-native-export.json`.
No personal deployment, release, hosted CI, physical FFB or menu removal occurred.
