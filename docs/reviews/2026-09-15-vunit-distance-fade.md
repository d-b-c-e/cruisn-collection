# V-Unit distance fade: useful offline prototype

A true color fade can soften the remaining far-plane change in the saved World
Hawaii scene. The standalone shader is now in `gpu/vunit_distance_fade.py`; it is
**not connected to MAME or the launcher**. The native candidate remains `ebe`.

The prototype resolves each original palette-index result to RGBA at its original
draw position, then blends eligible host scenery over the preceding scene. It
retains the existing texture interpolation, transparent-texel rejection, native
translucency coverage and far clipping. Original commands and roads remain opaque.
Disabling the fade reproduces the qualified indexed image exactly.

Opacity uses reciprocal camera-depth interpolation over the original quad's two
triangle fans, followed by a smooth transition over the20,000 units before the
far plane. This is a general depth rule, with no model or track allowlist.

## Saved stationary sweep

The existing scene is held still while the far plane moves from220,000 to240,000
in1,000-unit steps. This measures the boundary itself, not a moving car or an
actual time interval. The largest summed absolute RGB change between steps is:

| Policy | Largest summed channel change |
| --- | ---: |
| Existing coverage clipping | 583,428 |
| Whole-model opacity from its near sphere bound | 597,099 |
| Per-pixel distance opacity, including native translucent coverage | 293,758 |

The per-pixel policy reduces this peak by about49.7%. The whole-model rule does
not improve the peak and is not promoted. Fading changes9,201 pixels at the final
plane, produces no new fully black pixels there, and leaves the entire region
below fine-pixel y1000 unchanged. The authored terrain bottom still looks detached;
fading is not a repair for missing geometry.

An earlier per-pixel version excluded native translucent quads from fading and
exposed two black pixels. A separate indexed ownership render traced both to
host translucent quads that remained at full strength. Multiplying their existing
coverage by distance opacity resolves both pixels without erasing the game's
transparency pattern. Roads remain protected.

## Qualification and limits

Four focused tests pass, including actual OpenGL near/half/far opacity, protected
foreground, preserved translucency and a sloped quad without a fan-diagonal seam.
The first half-opacity assertions required exactly128; reciprocal-depth float
rounding can instead produce127. Tests now permit those two adjacent UNORM8 codes
while requiring untouched channels and foreground to remain exact. The initial
failure is retained.

Four saved renders also qualify the canonical shader. The opaque control and two
peak-transition images are byte-exact. Making the width a runtime uniform changes
one channel by one code in one pixel of the final faded image; an initial strict
comparison failure is retained. The corrected report explicitly bounds that
difference instead of labeling the images exact. No new black pixels or lower
foreground changes result. Initial shader-name and missing pending-descriptor
preflight failures are also retained; neither ran a game.

This is one2736×1600 saved quality scene with static captured palette resources.
It does not prove live palette-update ordering, CRT presentation, smooth ownership
handover, performance or cross-game acceptance. Live V-Unit rendering currently
resolves indices later, so moving color resolution requires an explicit palette
lifetime design. The native dither smoothing and separate host/foreground seam
masks must also survive that integration. Exotica has a different RGBA/depth path
and cannot use this shader unchanged.

Next, prove ordered palette updates and the native post-processing contract in a
bounded replayable renderer fixture before connecting a default-off live policy.
Then evaluate an actual moving-camera boundary and extend the depth adapters to
USA/Off Road. Another whole-game timing run is not justified by this offline shader.

Local evidence under `results/diagnostics/world25-roads-20260914/`:
`distance-fade-v3` (whole-object rule), `distance-fade-v4` (two exposed pixels),
`distance-fade-underlay` (their owners), `distance-fade-v5` (corrected sweep), and
`distance-fade-canonical-v2` (explicit canonical qualification). Raw game data stays
local. Personal Stream Deck/public v0.5.0 are unchanged.
