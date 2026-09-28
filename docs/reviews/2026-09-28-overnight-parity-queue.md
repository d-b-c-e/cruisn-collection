# Rendering-parity queue after the September 28 bounded checks

The diagnostic 3× paths run on all four games, but graphical parity is still
route-specific. The personal Stream Deck renderer and public v0.5.0 remain on
their accepted baselines. The World active non-road margin path in frozen
native `f762e01d63b` and the Off-Road resident-ground path remain opt-in
diagnostics. No tested multiplier eliminates guest scene-list pop-in globally.
For a compact cross-game comparison of **visible** returns rather than
submitted geometry, read the
[four-game visibility triage](2026-09-28-four-game-visibility-triage.md).

## What the new recorded drives establish

- **World 2.4 New York:** the active non-road path recovers both measured
  unowned wedges at frame 6000 and all but ten indexed edge pixels at 3600.
  Source-time packets explain every 3600 indexed change, including 25,631
  pixels previously drawn by the game. The corrected mask-tag check shows
  zero changed pixels previously belonged to host geometry; all 25,631
  trace to one original backdrop strip in this scene. Nine matched
  frames on each side of 3600 and 6000
  preserve the center and show moving margin repair. The older finish crash did
  not recur on this recorded drive; its old 3×/+12 or intermittent cause is
  still open. A separate [late wall sample](2026-09-28-world-new-york-late-wall.md)
  at 6300 replaces 98,129 original upper-panorama indexed pixels with a
  visually continuous right wall/building; it fills no unowned pixel. A
  [nine-frame turn sequence](2026-09-28-world-new-york-late-wall-temporal.md)
  at 6280..6320 shows right-margin-only changes and an apparent continuation
  through the turn, with exact center and repeatable 6300 images. Candidate
  [source-packet attribution](2026-09-28-world-new-york-late-wall-source.md)
  now accounts for all 98,129 changed indexed pixels at 6300. Full ordered
  depth and intermediate-frame safety remain open. The same short callback
  window has 21/41 intervals above 25 ms in both modes; this is not a GPU or
  full-course pacing pass.
- **World 2.4 Germany:** nine matched early turn frames add left-edge scenery
  with exact center. The saved black-road report and distant mountain/tree
  activation are separate problems. An original-DMA-qualified 7280 check
  shows the building replaces only two upper panorama strips, with zero
  newly owned or prior host-owned changed pixels; it is not proof that those
  separate problems are fixed. A saved-trace
  [packet screen](2026-09-28-world24-germany-packet-source.md) now identifies
  230 added packets and reproduces every changed candidate index at 7280.
- **World 2.5 Hawaii:** six of nine matched frames add only left-edge foliage;
  the known authored terrain rectangle at frame 5900 is exact in both modes.
  The source-checked 5775 image adds trees over authored sky/ocean panorama
  strips and 972 prior host pixels; it fills no unowned gap. The rejected
  generic skirt and missing ordinary mesh neighbor remain relevant. A new
  [five-frame-cadence transition check](2026-09-28-world25-hawaii-dense-transition.md)
  finds a visually coherent right guardrail extension at 5760 and then
  left-edge foliage through 5800; eleven matched completed views preserve the
  center. Its [5760 ownership check](2026-09-28-world25-hawaii-guardrail-ownership.md)
  traces all 8,209 replaced indexed pixels to the game's lower panorama strip;
  the exact source scene and two added objects explain all candidate indices
  there. Cross-course safety remains open.
- **Off-Road Pike's Peak:** ten sparse resident/control views are exact despite
  extra work. A focused 19-frame control-only sharp-turn survey found no clear
  El Paso-like opening. A second
  [snowy left-turn survey](2026-09-28-offroad-pikes-snow-turn-screen.md)
  at 6340..6520 also finds no clear positive margin gap. El Paso remains the
  positive resident-ground example; Pike's Peak supplies no demonstrated
  benefit yet.
- **USA and Exotica:** earlier continuous 3×, motion, completed-image and owned
  shutdown gates remain. A new USA 1440p original-DMA source capture attributes
  the unchanged right-sky panel to a game-drawn dithered quad; the saved 4K
  pair shows an earlier but skeletal-looking left bridge under 3×. See the
  [Golden Gate source check](2026-09-28-usa-golden-gate-panel-source.md).
  Exotica's stable physical 1440p Mars/Amazon receipts and old merged-display
  failures must both remain visible in decisions.

## Highest-value independent steps

1. **World active non-road admission:** use saved source/packet evidence to
   search for a concrete case where new policy-2 geometry incorrectly covers
   previously correct game scenery. Source-time New York 3600 is an attribution
   pass, not a universal occlusion test. A negative screen of a distinct scene
   or course is more useful than another full New York drive. The new
   [panorama safety screen](2026-09-28-world-panorama-safety-screen.md) shows
   why the existing `0xc5` sky heuristic would reject 550 legitimate-looking
   Hawaii lower-band overdraw pixels; structural backdrop recognition remains
   diagnostic. The [source-attributed backdrop gate](2026-09-28-world-panorama-safety-screen.md)
   now checks that all previously game-owned changed pixels in five saved
   source-qualified samples belong to repeated panorama strips; it finds no
   unclassified foreground overwrite there. Hawaii's 972 prior host pixels
   now have [exact old/new packet attribution](2026-09-28-world25-hawaii-prior-host-source.md)
   at one frame, with all new logged depths nearer. The denser Hawaii check
   narrows the transition, and its separate right-side guardrail extension at
   5760 replaces only a source-qualified original lower panorama strip. That
   frame's added packets reproduce every changed indexed pixel, but the
   isolated raster does not establish full per-fragment depth or
   full-course occlusion safety. The New York 6300 wall sample adds another
   source-qualified upper-panorama replacement, and its nine-frame turn
   screen shows a moving right-side change. Exact source-time native packets
   account for the candidate indices at 6300, while full ordered depth and
   intervening-frame handover remain open. Keep any raw failures and do
   not promote the option from changed-pixel counts alone.
2. **Off-Road resident margins:** find a visibly positive defect interval on a
   second course before running another resident/control pair. The saved Pike's
   Peak wheel trace and original snapshots can choose turns cheaply, but native
   snapshots omit widened margins; completed GL views must confirm a target.
   If no target emerges, record this as a coverage limit rather than repeating
   entire races.
3. **World 2.5 authored Hawaii gap:** preserve the original edge/resource
   reconstruction. Test any new explanation offline against the saved indexed
   scene first. A credible candidate must retain terrain silhouette/material
   and beat the rejected skirt's visible wall; more global distance cannot
   create a lower mesh edge already within the 3× plane.
4. **USA useful distance:** the saved completed-frame interval now locates
   candidate-only red bridge appearance at 10500/10800/11100, absent in the
   sampled left ROI by 11400. The new
   [source packet check](2026-09-28-usa-bridge-object-activation.md) attributes
   three red pixels to three textured future-list objects first submitted at
   frames 9855, 10039 and 10475. Center depths lie near the 240,000-unit 3×
   far boundary, but ROM radii show each already passes the sphere cutoff by
   10k–28k units; the far rule is not isolated. Confirm pre-admission vertex,
   descriptor and material evidence before trying a larger global limit.
   A new [matched partial-coverage trial](2026-09-28-usa-bridge-farcoverage-trial.md)
   shows a ready bridge source projection-rejected in saved end-of-frame RAM;
   the already gated mode brings far-left red structure into view earlier in
   all 11 completed 1440p interval images, with center/right exact. An
   [exact source-time tap](2026-09-28-usa-bridge-source-projection.md) at 10473
   reproduces the full 3,706-quad ordinary scene and confirms projection
   rejection of ready object `0x800a0040`; partial coverage adds its three
   quads, preserving every old ordered quad. A matched native candidate source
   replay agrees on all 3,782 quads and its ordered fingerprint.
   [Completed frame 10476](2026-09-28-usa-bridge-pixel-source.md) now has
   selected center samples from two new bridge objects: 1,779 red points from
   `0x800a0040` and 779 from `0x800a0042`, source/page/packet/index matched.
   A [control-coverage screen](2026-09-28-usa-bridge-red-coverage.md)
   separates those 2,558 genuinely new isolated host samples from 2,304
   candidate-only red CRT samples whose ordinary source packets already
   produce the same index. Screenshot redness is not new-geometry area.
   A [matched control indexed mirror](2026-09-28-usa-bridge-control-indexed.md)
   confirms 7,058 left-margin game-to-host pixel changes at 10476, exact
   original-only/4:3 center, and identical completed index/tag for 2,348
   of the 4,906 candidate-only red CRT centers. The 2,558 genuinely new
   red centers trace to the two earlier identified source objects.
   The [saved-trace timing census](2026-09-28-usa-bridge-member-timing.md)
   puts the first member's auxiliary submission 294 frames earlier with the
   gated option; the second is absent from ordinary auxiliary output through
   source10499. This is not first visible time.
   This does not qualify the full silhouette or smooth handover.
   A fixed-ROI red-color screen of those saved images stays candidate-positive
   in every sample; its count narrows as control scenery appears. This is a
   visibility hint, not bridge-object segmentation or smoothness proof.
   Other members, object completeness and intervening occlusion still require
   a targeted gate before any policy change.
   A [bounded cost screen](2026-09-28-usa-bridge-cost-screen.md) finds about
   +203 µs mean native host-scene work over 235 matched scenes near the bridge,
   while the synchronized host interval remains near 8.1 seconds in both
   runs. This is not a GPU/stutter/4K benchmark.
   The dark right panel is original game output, a separate issue.
5. **Exotica useful distance:** find a saved open-sightline interval with an
   actual completed outer-boundary change. Measure source activation and
   transition cadence before another broad 3× run.
6. **Promotion gates after a candidate survives:** independent clean native
   build/patch receipt, 4K matched captures, another course per game, overlay
   and menu/race transition appearance, frame pacing, and attended wheel/FFB.
   The current rig has a stable physical 1440p primary but no connected 4K
   display. Product/default settings and release validation come after the
   diagnostic renderer decision.

Use source-hashed reports, completed-image receipts, original input/native
comparisons, and explicit worker drain/join. A screenshot color heuristic is a
review hint, not an exact texture or coverage oracle. The replay harness should
keep live GPU/native runs serialized and literal FFB0. Do not change the
personal installation or public release during this diagnostic queue.

For a specific V-Unit black/colored pixel in a saved original-mirror capture,
the new [indexed-pixel provenance probe](2026-09-28-vunit-pixel-provenance.md)
reports original, auxiliary and current-DMA status without another game run.
It accepts bottom-up indexed coordinates or calibrated top-down points in a
2544×1353 completed CRT screenshot. The latter requires a near-exact full-image
palette reconstruction and returns a center sample, not every CRT blur/dither
contributor. It does not attribute the auxiliary source.

The September 28 detailed reviews are the [New York source overlap](2026-09-28-world-new-york-overlap-source.md),
[New York turn sequence](2026-09-28-world-new-york-overlap-temporal.md),
[Germany appearance](2026-09-28-world-germany-margin-onset.md),
[Germany ownership](2026-09-28-world24-germany-overdraw.md),
[Pike's Peak turn](2026-09-28-offroad-pikes-sharp-turn-screen.md), and
[World 2.5 Hawaii interval](2026-09-28-world25-active-margin-interval.md),
plus the [Hawaii ownership check](2026-09-28-world25-hawaii-overdraw.md).
