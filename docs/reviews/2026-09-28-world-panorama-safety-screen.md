# World non-road margin overdraw: panorama safety screen

The World active non-road candidate currently passes the four source-qualified
indexed samples, but a general foreground-preservation rule needs a way to
distinguish backdrop from real road, scenery and HUD output in the widescreen
margins. I tested a deliberately simple rule offline: permit a new non-road
pixel only over an unowned pixel, a prior auxiliary pixel or an original DMA
quad caught by the existing low-byte `0xc5` sky classifier. This is arithmetic
on saved source reports, **not** a renderer change or a completed composite.

| Saved completed frame | Unowned pixels changed | Prior auxiliary pixels changed | Original backdrop pixels changed | Rejected by simple `0xc5` rule |
| --- | ---: | ---: | ---: | ---: |
| World 2.4 New York 3600 | 24,759 | 0 | 25,631 from upper `0xc5` strip | 0 |
| World 2.4 New York 6000 | 20,954 | 0 | 0 | 0 |
| World 2.4 Germany 7280 | 0 | 0 | 19,471 from two upper `0xc5` strips | 0 |
| World 2.5 Hawaii 5775 | 0 | 972 | 34,116 from upper `0xc5`, **550 from lower `0x60`** | **550** |

The four selected frames have 126,453 changed indexed frame-pixels. The simple
rule would reject Hawaii's 550 lower-band pixels even though the source shows
five consecutive, axis-aligned ocean panorama tiles spanning the viewport at original
DMA ordinals 5–9 with the same palette base and `0xb60` texture base. Ordinal 6
owns the 550 changed pixels. The existing `gpu/renderer.py` backdrop heuristic
was intentionally scoped to the upper sky texture and cannot simply be reused
as a universal World foreground veto. Widening it to every `0x60` material from
this one view would be equally unjustified.

The new `harness/screen_vunit_panorama_strips.py` tests a structural candidate:
at least three consecutive, adjacent 200–300-unit textured rectangles with
matching height, palette base and texture low byte, spanning at least 512
native units. It identifies one five-tile upper band in each of New York
3600/6000 and Germany 7280/7340, plus both five-tile upper and lower bands
in Hawaii 5775. All five source runs have passing replay reports. A USA Golden
Gate and Off-Road El Paso contrast yielded zero such strips; the USA raw replay
status is still FAIL, with its separate posthoc qualification documented in
the [Golden Gate review](2026-09-28-usa-golden-gate-panel-source.md). These are
selected scenes, not a false-positive rate across games or courses.

Local source-hashed evidence is
`results/diagnostics/world-new-york-20260927-live-1/world-nonroad-c5-veto-screen-v1.json`,
`world-panorama-strips-v1.json`, and `cross-game-panorama-contrast-v1.json`.
The original source reports and DMA files remain unchanged. The helper compiled
and screened seven saved scenes without a new MAME run, native build, renderer
deployment or 4K claim.

This establishes a concrete obstacle to an easy safety policy: original game
pixels can be safe-to-overdraw panorama without sharing one texture identifier.
A next opt-in trial needs an explicit provenance mark for structurally qualified
backdrop pixels, an unchanged original-only view, and matched completed images
at transition frames. The structural screen alone does not establish that a
tile is sky/ocean, that host depth order is correct, or that foreground is safe
throughout either World revision. Do not promote the active non-road candidate
from these five scenes.

## Source-attributed foreground gate

`harness/check_vunit_backdrop_overdraw.py` now joins an existing qualified
original-DMA overdraw report to that frame's saved source DMA. It verifies the
source hash and completed frame, then requires the count of attributed game
pixels to be complete. It reports each game-owned pixel that the candidate
replaces whose source ordinal is **not** in a structurally repeated backdrop
strip. This is a reusable negative screen; a zero count is not permission to
turn on the renderer policy.

The three available source-qualified positive-overdraw frames all have zero
unclassified game pixels: New York 3600 has 25,631/25,631 in the upper strip;
Germany 7280 has 19,471/19,471 in the upper strip; Hawaii 5775 has
34,666/34,666 across the upper and lower strips. Hawaii separately replaces
972 prior auxiliary pixels whose packet identity this screen does not resolve.
New York 6000 adds only formerly unowned pixels, so it is not a foreground
overdraw test. The local source-hashed
`world-backdrop-overdraw-screen-v2.json` contains the three joins. The v1
screen is preserved but superseded by v2's explicit source-report hash check;
the overlap report's separate source-time tap must not be mistaken for its
matched original-DMA replay. Four focused
tests include a foreground-ordinal negative and reject incomplete/failed
source attribution; no new game replay or native build was used.

This gate catches a source-attributed foreground overlap if a later scene
shows one. Its structural rule can still misclassify a repeated foreground
pattern, and the present samples do not cover transitions, other courses,
depth correctness or completed 4K appearance. Prior host overdraw needs a
separate source/order test. Keep the active non-road option diagnostic.

The later [Hawaii 5760 guardrail check](2026-09-28-world25-hawaii-guardrail-ownership.md)
adds a fourth source-qualified positive-overdraw frame. It replaces 8,209
original game pixels, all from lower panorama ordinal 9. A new source-hashed
`world-backdrop-overdraw-screen-v3.json` joins all four samples: 87,977
replaced game pixels across the sampled frames, all structurally classified
as backdrop, zero unclassified. This is still a selected-sample negative
screen, not a measured foreground false-negative rate or an acceptance of
the candidate renderer.

The later [New York 6300 wall check](2026-09-28-world-new-york-late-wall.md)
adds a fifth positive-overdraw view. All 98,129 changed game pixels in that
view trace to upper panorama ordinal 3. Combined source-hashed
`world-backdrop-overdraw-screen-v4.json` now has 186,106/186,106 changed
game pixels in structural panorama strips across the five selected frames,
zero unclassified. This remains a selected-sample screen, not a general
foreground-preservation or depth guarantee.
