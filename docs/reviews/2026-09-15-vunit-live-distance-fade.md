# First native World distance fade

Candidate `e5344546a8e` connects the qualified indexed fade and palette shaders
behind `--world-host-distance-fade`. It requires the explicit World metadata and
original mirror diagnostics. The outer20,000 units of the240,000-unit host range
fade toward the original-only view. Authored roads and ordinary game drawing
remain opaque. This is not a launcher feature or a new release default.

Opacity now has a persistent float texture on each extended page. Ordinary and
CPU writes set it to one; auxiliary draws use per-quad depth and protected-road
metadata in batches matching the existing primitive order. A mask-only reset
preserves opacity, while pixel clears reset it coherently. The original-only
image is independently preserved. Palette updates remain shared and resolve at
presentation; blending precedes the existing CRT pass.2D presentation skips the
fade. The native snapshot includes finite0..1 opacity from both pages.

The first same-candidate World2.5 off/on pair passes6,000 inputs each. All4,119,775
metadata packets, all1,666 host-scene rows excluding named duration fields, and
all eight indexed/mask planes at5900 remain exact. Only the palette-stage image
changes. At5900 the pages contain8,618/9,068 partially opaque pixels, plus one
zero-opacity pixel each; all remaining pixels are opaque.

Across21 completed frames5880..5900, the fade changes17..1,855 output pixels per
frame. It introduces zero newly fully black pixels and preserves the lower third
of every image exactly. Paired5900 images were inspected: the visible difference
is small, with the known detached terrain still present. This proves an active,
bounded live effect, not elimination of pop-in or a measured perceptual benefit.
The presentation is1280×720, internal buffers2736×1600. This is not final4K,
all-track, long temporal handover or release-performance acceptance.

Next use the existing World2.4 Germany recording for a longer moving-camera
window, including the known left-road issue near the game's1:37 timer. Confirm
current4K display targeting before that pair; then adapt the metadata and road
policy to the other engines using their own verified formats. No additional
whole-game default suite is justified merely by this gated World prototype.

Evidence under `results/diagnostics/world25-roads-20260914/`:
`distance-fade-control`, `distance-fade-on`, `distance-fade-live-qualified.json`,
`distance-fade-native-export.json` and `distance-fade-build.log`.
Native226-patch tree `328a24ba413237814e8aae6b8e035992e1013baf`; frozen SHA256
`8e09bf779f582adcfbfbcfb18ce41304e5eedd2e82aad9a787f5205ca484699d`.
Personal87d/publicv0.5.0 remain unchanged.
