# USA Golden Gate: original owner under the early bridge

The [full changed-pixel source check](2026-09-28-usa-bridge-full-indexed-source.md)
identified all 7,058 added bridge indices at completed frame 10476, but the
matched control mirror only said that those pixels previously belonged to the
game. A single bounded original-DMA capture now identifies the exact game
commands below them.

Frozen diagnostic native `f762e01d63b` replayed the saved Golden Gate route
through 10,480 inputs at physical 2560×1440, CRT on, literal FFB0. The raw
capture-mode replay **PASS**es input/native comparison, display watch,
completed-image capture, original indexed mirror and process/capture receipt.
Its completed BMP and all visible-page indexed planes are byte-exact to the
prior ordinary control run. The source's capture-state report does **not**
contain a `vunit_runtime` owned-worker-stop receipt; the separate ordinary
control and candidate reports do. Do not describe source capture shutdown as
an owned-worker-stop qualification.

The completed visible page is page 0; its current original DMA group contains
2,272 quads submitted at frames 10473..10474, selected by the mirror's
consumed-command count. An independent ordered raster of that current DMA
exactly reproduces **7,058/7,058** game-owned indices replaced by the
candidate. All changed control pixels have game tag `1`, all candidate pixels
have host tag `5`; original-only planes and the 4:3 center remain exact.
No changed pixel was previously unowned or host-owned.

| Original DMA ordinal | Replaced pixels | Native rectangle | Repeated band |
| --- | ---: | --- | --- |
| 3 | 4,954 | x −280..−24, y −81..184 | upper 0..10 |
| 18 | 2,104 | x −280..−24, y 184..400 | lower 15..25 |

Both commands are axis-aligned textured rectangles within two consecutive
11-tile panorama-like bands that span the viewport. The older structural
strip screen reported zero USA groups because it expected only one vertex
order; these USA quads store the left edge first and run vertically before
the right edge. The offline detector now accepts either valid perimeter
ordering, while rejecting diagonal crossing. It finds the two USA bands and
retains **exactly the same strip ordinals** in five previously qualified World
source scenes. The source-hashed backdrop gate classifies all 7,058 replaced
game pixels as belonging to those two repeated bands, with zero unclassified.

This narrows an important safety risk: the added bridge geometry at this frame
does not replace a source-qualified road, car or isolated foreground command.
Structural repetition alone does not prove a band is harmless background,
and an isolated current-DMA raster does not prove ordered per-fragment depth,
the shape of the whole bridge, intermediate-frame handover, another course,
physical 4K appearance or release safety. The candidate remains opt-in.

The first invocation of `screen_vunit_margin_overdraw.py` failed before pixel
attribution with `KeyError: 'vunit_runtime'` because capture-state reports omit
that section. The local `usa-bridge-original-overdraw-10476-raw-v1.json`
preserves the failed command and error. The checker now accepts a source
capture only with a passing source report and zero-exit process/capture
receipt; it records that lifecycle distinction explicitly. Its final
`usa-bridge-original-overdraw-10476-v4.json` **PASS**es (SHA-256
`1b0a00d9681eadcc8ecb5e459f538a8bc25c52df191a82545376de7f05094f7d`).
The final strip and backdrop reports are
`usa-bridge-original-strips-10476-v3.json` and
`usa-bridge-backdrop-gate-10476-v4.json` in the same local diagnostics folder;
earlier v1–v3 screens remain intact. Eight focused strip/backdrop/lifecycle
tests pass.
No native code, deployed renderer, personal installation or public release
changed.
