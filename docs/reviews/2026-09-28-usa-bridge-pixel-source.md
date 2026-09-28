# USA Golden Gate: new bridge packets reach completed pixels

One earlier red bridge appearance is now joined from exact source state through
native packets, indexed ownership and a completed CRT image. At completed
frame **10476**, 1,779 screenshot-selected red center samples trace to new
packets from ready future object `0x800a0040`; 779 more trace to neighboring
new object `0x800a0042`. The former was absent from ordinary 3× host output
at source frame 10473 and first appeared in the ordinary detailed trace at
10475. This establishes a real early-visibility mechanism for two members,
not a complete bridge, smooth transition or global pop-in solution.

## Matched source and presentation

A detailed coverage-on replay on frozen `f762e01d63b` **PASS**es 10,480
recorded input/native frames, stable physical 2560×1440 display, literal FFB0,
original indexed mirror and owned worker shutdown. Its source-frame 10473
program RAM, C31 RAM, textures and palettes are byte-exact to the qualified
read-only control tap. The native 3,782-quad scene has the independently
predicted ordered fingerprint `cad18ecde19865f8`. The completed visible-page
receipt selects precisely this source scene: page 0, 3,782 consumed quads and
the same fingerprint. Its completed 10476 CRT BMP is **byte-exact** to the
earlier continuous coverage-on trial. Thus this detailed replay can identify
packets behind that already qualified visible image.

The control and coverage-on completed images differ by 7,627 RGB pixels at
10476, entirely on the far left. The fixed bridge ROI `(70,450)..(290,710)`
contains 4,906 candidate-only red screenshot pixels under the explicit
predicate `R>110`, `100R>135G`, `100R>125B`. A calibrated center mapping gives
4,906 unique indexed points; 4,862 agree with the isolated host raster and
captured auxiliary index/tag. Of those, 2,558 are last-written by one of the
76 new source packets: 1,779 by object `0x800a0040` and 779 by `0x800a0042`.
The other red screenshot points are not attributed to a new packet here;
CRT filtering, existing packets and foreground composition can contribute.
This is **not** a claim that 2,558 distinct game objects or whole-screen pixels
were repaired. The full indexed/palette reconstruction differs by more than
one channel unit at 123 of 3,442,032 completed pixels; the center mapping is
therefore usable but does not decompose the CRT footprint of every pixel.

For one concrete point, screenshot `(178,506)` maps to bottom-up indexed
`(123,1009)`. The candidate mirror has auxiliary index/tag `(24283,5)` over
original-only sky `(7931,1)`. The isolated source raster matches that index
and identifies object `0x800a0040`, model `0xc4794f`, depth 236,352. The
matched control image at that screen point has a different color. The native
candidate source scene and all 3,782 detailed quads match independent
projection from source RAM; this point is not a color-only object guess.

## Scope and cost of the diagnostic

The original DMA snapshot in this run is from a later frame, so this check
does not assign an original DMA ordinal to frame-10476 pixels. The captured
original-only mirror plane supplies their underlay. One frame and a fixed
far-left red predicate cannot assess the full bridge silhouette, overlap at
handover, 4K, another course, frame pacing or physical FFB. No renderer,
personal installation or release changed.

The replay was prepared with `--usa-host-first 10450` to try to bound detailed
logging. **Continuous bootstrap starts at the first actual scene despite that
capture reference bound**, so the run produced a 1.5 GB detailed quad journal.
The raw run nevertheless passed and the packet evidence is useful. Do not
repeat this approach expecting a short log; the harness should state the
effective continuous journal scope in its preflight. The prepared-only plan
and raw run stay separate.

Source-hashed local evidence under
`results/diagnostics/race-transitions-20260916/`:
`usa-bridge-coverage-pixel-prepared` (preflight),
`usa-bridge-coverage-pixel-run` (raw replay PASS), and
`usa-bridge-candidate-pixels-v1.json` (source/packet/indexed/CRT PASS).
The reusable checker is `harness/screen_usa_bridge_candidate_pixels.py`.
Read the [exact source projection](2026-09-28-usa-bridge-source-projection.md)
and [matched appearance interval](2026-09-28-usa-bridge-farcoverage-trial.md)
for the separate source and temporal gates.

Next inspect the other bridge members and a denser handover interval before
any default-policy change. The currently demonstrated benefit remains
game/route-specific and the partial-coverage option remains gated.
