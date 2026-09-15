# World depth and road metadata for distance fading

The next native appearance step needs camera depth for every host quad. The old
coverage transport describes only quads that cross the far plane. Reusing it for
wholly inside quads would violate its existing validation contract.

The new64-byte packet retains that60-byte prefix and adds an authored road flag.
Its separate decoder accepts wholly inside or crossing quads, requires positive
bounded C31 depths and exact host-layer ownership, and rejects wholly outside
quads. The old crossing-only decoder is unchanged. Roads are identified from the
original object flag, not from shape, texture color or screen position.

Standalone qualification decodes8,597 actual saved World2.5 quads exactly against
independent Python float/policy bytes:3,038 road quads,81 crossing quads and8,516
wholly inside quads. Separately, saved World2.4 frame6000 and World2.5 frame5900
checks preserve all ordered quad/depth output against the frozen helper. Their
1,260/3,038 protected-road flags match captured descriptors across2,814/8,597
quads. The first local analyzer failed strict compilation because an appended
print statement shared an unbraced conditional line; that failure is retained,
and the corrected analyzer passes. No game rerun was needed for that correction.

Native candidate `e1a93e3589e` connects this as an explicit transport diagnostic,
not a fade. Both producer and consumer validate every packet. Wholly inside quads
rejoin the existing unclipped path; crossing quads retain their existing coverage
metadata. Producer and consumer save the exact packet sequence at the requested
mirror frame. The replay verifier checks byte equality, independent depth bounds,
page/road counts and per-scene ordered quad fingerprints. It also requires the
consumer totals to cover every logged host scene, draining beyond the host window.

The local replay option is `--world-host-fade-metadata`, requiring the original
mirror, future host draw, coverage clipping and physical FFB off. The native run passes6,000 inputs and original native images. All4,119,775 host
packets and193,125 road quads reach the consumer through the full host window.
At frame5900, both sides save the same5,922 packets, including363 protected-road
and60 crossing quads. The independent verifier matches depths, pages, scene
fingerprints and road counts. This live case uses stock road detail; the8,597-quad
offline fixture above uses full road detail.

All eight indexed/mask planes and the completed1280×720 presentation at5900 are
byte-exact to the previous mirror candidate. All1,666 host-scene rows match after
excluding the same eight named duration fields. The consumer drains through5999;
this is full packet-coverage evidence, not just the one saved frame. No appearance
or launcher setting changed, and no final4K or performance acceptance is claimed.
Evidence: `fade-metadata-live-qualified.json`.

## Next appearance integration

Add an opacity texture to each extended page. Ordinary and dirty CPU writes set
opacity to one; auxiliary draws calculate the distance envelope, with roads kept
opaque. The original index/mask pair remains untouched by auxiliary draws. Both
views resolve using the presentation-time palette before the existing CRT pass.

Opacity belongs to persistent indexed pixels. A mask-only scene reset must not
reset opacity: it has not changed the underlying indices. Pixel clears must clear
the corresponding opacity coherently, and ordinary/CPU overwrites must replace it.
This avoids turning retained old host pixels fully opaque between scenes.

Only after a matched native image check should the fade be enabled, then examined
through a short moving-camera window. Native alpha ownership, temporal handover,
performance and other-game adapters remain open. The earlier stationary image
metric is not gameplay acceptance, and fading does not repair missing terrain.

Local evidence: `fade-metadata`, `road-provenance-v2`, `fade-metadata-live` and
`fade-metadata-native-export.json`, under the World2.5 road diagnostics directory.
Native225-patch tree `e2baf89da3bfa2370f7166a161ee59f5f23372ee`; frozen SHA256
`dbe5f5126c5159536b67b11ab208f71e70004f0191013213193c69e722bf24d8`.
Personal87d/publicv0.5.0 remain unchanged.
