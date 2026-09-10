# Exotica scene layers: projection is not visible benefit

The scene-5000 prototype demonstrates usable future geometry and a workable
isolated depth representation. It does **not** demonstrate a useful extension
in the final picture: existing foreground terrain hides almost all the added
scenery. Broader viewpoints and live resource/lifecycle checks remain necessary.

## Matched source and device state

Two 6,000-frame Hong Kong replays on the separate b3d82b candidate preserve all
4,191 camera samples, 12,573 actual ADC reads/times, 21 completed 4K images from
4990 through 5010, and ten original device/model/resource files. Physical force
is zero. The Stream Deck executable remains v0.5.0/SHA87d04de4.

The bounded source probe passes five independent Python/native checks:

- 4,714 original transforms/setup calls and 4,651 ordinary emissions.
- 257 original models and all 2,202 ordered polygons.
- 222 clock/source/translation joins, including 219 consecutive private contexts.
- 1,079 ordinary allocations and 2,158 initial material bindings from 1,135
  allocations; 56 custom allocations remain excluded.

The source snapshot is at emulated time 87.512356243822. Its camera and view match
222 original CPU/device joins, whose device times span 87.512463699125 through
87.514101965792. This uses actual clocks and operands, not a frame-number-only
join. It is still not a runtime scene-insertion or live ownership contract.

## Future geometry and depth

The private future projection decodes 1,515 instances into 9,596 polygons with
no format errors. Independent native decoding matches every generated Python
polygon. These are generated future expectations, distinct from the original
hardware-submission comparison above.

At the recorded 88-pixel side margin, 1x contributes 1,813 viewport-intersecting
polygons; 2x adds 2,927; 3x adds none in this viewpoint. Of the resulting 4,740
polygons, 2,777 lie wholly beyond the original 24-bit depth ceiling. The 622
visible instances all establish their texture source explicitly before drawing
and use the checked palette load format. Presence in captured WaveRAM does not
establish ownership, completed uploads or continued validity during gameplay.

A hidden real-OpenGL test reproduces order-dependent far surfaces with D24 and
the original depth clamp. D32F with power-of-two scaling preserves all eight
tested near/far orderings, including adjacent representable depths above the
old ceiling. All 18,960 actual future vertex depths round-trip through the
power-of-two scale exactly. The initial test incorrectly selected a bound from
the scene while including a larger synthetic stress input; its bounds failure
is retained. The corrected fixture includes both sources in its bound.

This is a proposed **separate host depth buffer**. It does not change original
hardware depth semantics, and it is not linked into the emulator yet.

## Foreground rejection of the apparent gain

An offline textured layer uses the original setup with a host-only completed-
fade policy. At 1376x800, 2x changes 26,851 pixels over 1x before foreground is
drawn. D32F changes 2,225 pixels relative to the clamped D24 version.

That count is misleading on its own. A second prototype inserts the layer after
this scene's first 14 sky polygons and then draws all remaining original
polygons using their own D24 buffer. Original depth remains byte-identical.
Only 205/206/206 final color pixels differ from control at 1x/2x/3x: **2x adds
just one pixel over 1x**. This scene is therefore insufficient evidence of a
useful visual extension. The insertion boundary is a manually inspected local
prototype, not a generalized runtime guard. There is no renewed 4K acceptance
for this 1376x800 offline composition.

## Broader track coverage is exposing missing checks

Paired Amazon frame-5072 probes preserve the explicit original 1800..5990
camera/ADC interval, 17 completed 4K images and ten original resource files.
The four original transform/setup/state/model checks pass. The section verifier
initially rejects 243 matrices from a later reverse section, while every
predicted object descriptor still matches exactly.

The failure comes from reconstructing the section rotation from an angle
already rounded in RAM. Reconstructing the original arithmetic from its base
heading, section header and direction retains the extended precision used
before that store, and matches all 2,376 captured ordinary matrices. The
existing section decoder already uses this unrounded expression. The reusable
verifier now retains that arithmetic and checks both the stored angle and every
matrix component exactly. It uses the section's ROM direction, including where
third-list placement may clear the object-side direction bit. A synthetic
rounding regression rejects rounded matrices, wrong stored angles and unrelated
direction changes. Amazon, both new Hong Kong snapshots and all six older
Hong Kong snapshots pass. The initial 243 failures remain retained.

The additional Hong Kong frame5990 pair also preserves the original route,
17 completed 4K images and all ten resource files. Its five original native/
Python oracles pass. An additional local study considers earlier ordinary section sources that were
not submitted by the original game. It excludes observed nonfading original
instances, but does not yet establish eligibility for dynamic objects or a
safe live handover. This could address side gaps that increasing far distance
alone cannot fill. No model allowlist is proposed.

The final offline compositions explicitly use the recorded framebuffer page,
initial CPU buffers/clears and separate original/host depth attachments. A page0-
only prototype correctly rejected Amazon's page400. A subsequent prototype
accidentally reused its output as the next initial color buffer; its apparent
10-pixel 3x change was a test bug. Both failures are retained. Version3 uses
immutable initial bytes and repeats the2x and control cases exactly. These are
offline GPU compositions, not comparisons with native full-frame CPU rendering.

| Recorded viewpoint | Sources | 1x changed pixels | 2x changed pixels | 3x changed pixels |
| --- | --- | ---: | ---: | ---: |
| Hong Kong5000 | Future | 205 | 206 | 206 |
| Hong Kong5000 | Earlier unsubmitted + future | 563 | 564 | 564 |
| Amazon5072, ET0:34.94 | Future | 2,562 | 4,352 | 4,352 |
| Amazon5072, ET0:34.94 | Earlier unsubmitted + future | 24,063 | 32,817 | 32,817 |
| Hong Kong5990 | Future | 3,266 | 3,266 | 3,266 |
| Hong Kong5990 | Earlier unsubmitted + future | 7,671 | 7,671 | 7,671 |

Counts compare RGB against each viewpoint's control at1376x800 for Hong Kong
and1368x800 for Amazon. All repeat and original-depth comparisons pass. The
Amazon comparison visibly adds forest ahead. Future-only drawing leaves all1,951
black pixels in the explicit left-margin region x0..171/y400..599 unchanged;
the broader earlier-unsubmitted prototype covers all of them. That is promising,
but does not prove the replacement surfaces are correct. Surface attribution and
motion checks are needed before calling the ground defect fixed. Original/future
handover, source eligibility, animation and live material
ownership are still open. No sampled viewpoint gains from the third distance
band; this is not a nominal3x implementation or a cross-track conclusion.

The full local suite passes291 Python tests without skips,34 native helpers and
96 commands at437-file identity
`433424a28444d6b27c75f60710c060db07dceda0801e2b1cc92d7a8ba780c740`.
Only the future evidence verifier and its test differ from the prior capture-
writer acceptance identity. The native b3d82b build and its seven-default
acceptance remain unchanged; no additional native build is implied.
The [public proof](../../results/proof/2026-09-10-exotica-scenes/README.md)
verifies58 hash-bound receipts; it does not recompute unarchived raw executions,
geometry, pixels, resources or routes.

Raw operands, scripts and images remain local under
`results/diagnostics/exotica-amazon-20260909/scene5000-*`, `scene5072-*`, and
`scene5990-*`. No native deployment, release, menu removal or physical-force
testing occurred.
