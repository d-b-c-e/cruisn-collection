# World terrain visibility and conservative distance bounds

The World 2.5 Hawaii terrain gap is **not fixed**. A captured scene rules out
later ocean/background drawing as its cause. It also identifies a smaller,
general correction: the host renderer was rejecting some models whose bounding
spheres cross the far plane even though their actual vertices remain inside it.
The correction keeps the same configured distance and rejects complete models
with any vertex outside the supported depth interval. It is not polygon clipping.

## Actual drawing order

One bounded, headless observation on frozen native `679ef586ef7` preserves all
5,904 recorded inputs and the accepted original native images. The observed
1800–5901 motion interval preserves 4,102 camera samples and 12,306 actual ADC
reads/timestamps. Physical FFB is disabled.

The new local command observer captures 2,854 original DMA quads across two
scene starts. All 16 words, frame, page and ordering match a unique contiguous
interval in the native quad journal. The completed scene starting at native
frame 5900 contains 1,419 original quads. Its first ten are five sky tiles from
PC `0x967f` and five ocean tiles from PC `0x97fa`. Both groups precede the
`0x6a` scene-list call where the host inserts extended scenery. Thus moving the
host after the background cannot repair this sample: it is already there.

The offline GPU renderer reproduces all 204,800 native framebuffer indices
exactly with the captured resources and prior same-page history. Its separate
4× quality preview is a static diagnostic, not a renewed live or 4K acceptance.
The original ordered 8,294 host quads match the saved snapshot reconstruction.
They cover 238,468 quality pixels; 172,390 are subsequently covered by original
geometry, while 66,078 survive and change the final image. The leading covering
polygons are ordinary scene geometry, not a later background layer. Bypassing
that coverage indiscriminately would put distant scenery over foreground objects.

## Other screened explanations

These local prototypes were not integrated into the emulator:

- Adding templates from all four active lists inspects 354 objects and projects
  1,380 quads from 238 of them. The old host geometry remains ordered-byte exact.
  Only 1,531 final pixels change, away from the conspicuous terrain gap. This
  does not validate active-object lifetime or justify drawing them unconditionally.
- The 244 excluded future definitions are all class A custom allocations,
  spread over 17 model pointers. None has a matching later allocation in the
  available World 2.5 capture. Their custom initializer dispatch is confirmed
  at `0x58ec`; treating them as ordinary static objects remains unsupported.
- Relaxing the near-sphere test in addition to the far test adds eight more
  quads but no additional completed pixels in this sample. Near clipping remains
  excluded from the promoted correction.

## Far-bound correction

`native/world_host_scenery.h` now rejects a sphere wholly beyond the far plane
using its nearest extent. Every transformed vertex must still have integer depth
at least 1000 and strictly below the requested far limit. An out-of-range vertex
rejects its whole model; it is never clamped into a distorted polygon. The
original conservative near-sphere check, reciprocal-table bounds, signed screen
coordinate checks, source order and original guest rendering remain intact.

On the saved 5900 scene, this admits 109 additional quads, removes none and
changes 4,866 completed quality pixels. Visual inspection shows additional
distant mountain geometry; the conspicuous gap underneath remains. The change
does not extend the configured 3× plane or promise elimination of pop-in.

The independent Python oracle now applies the same depth contract through its
separately reconstructed vertex buffers. All four World 2.4 snapshots and eleven
World 2.5 snapshots pass at 1×/2×/3× using full-detail road models: 32,128 and
61,898 future quads respectively. Three strict native tests pass, including new
sphere-overlap and exact/beyond-plane rejection cases. The relevant Python groups
pass 19 tests. No broad default-game suite was repeated for this isolated helper.

## Evidence and remaining work

Local evidence is under `results/diagnostics/world25-roads-20260914/`:
`background-order`, `background-order-join.json`, `background-control.json`,
`background-coverage`, `special-catalog.json`, `active-coverage`, `bounds-far`,
`bounds-vertices` and `far-bounds-checks`. Raw game resources stay local. Initial
inspection commands referencing absent filenames are not acceptance evidence.

The separate native candidate `b7048961cd385639836f0f6662cf0705db4c83a3` builds
and passes the matching 6,000-input replay, original native images, 4,191 camera
samples and 12,573 actual ADC reads/timestamps. Its 1,666 host scenes submit
5,688,298 quads. Four of twelve completed images change by 952, 2,945, 4,022 and
880 pixels (frames 5800–5950); the other eight remain exact. Visual inspection
confirms additional distant mountains and the persisting terrain gap. The
comparison's image-equality field is deliberately false for these expected
changes; its route and motion acceptance pass. MAME reports 99.98% average speed.
These are 3424×1353 captures on the current 3440×1440 monitor, not final 4K checks.

The frozen executable is `build/candidates/b7048961cd3/vunit.exe`, SHA256
`3a79167363b57a81843b544313522b0471354635a12664114b6b68084b9d478f`.
The 197-patch export reconstructs tree
`0b97a05cd907c0c791ef1f536942bd6d374ed317`. Additional local evidence is
`roads-far-bounds`, `far-bounds-live-comparison.json/png` and
`far-bounds-native-export.json`. No unrelated default suite was rerun.

The larger terrain gap still needs a source-level explanation; custom allocation,
authored model coverage and true partial-polygon clipping are separate questions.
Temporal pop-in/fade, Exotica full-speed rendering and final 4K cross-game
acceptance remain open. Personal native87d and public v0.5.0 are unchanged.
