# Conservative Exotica model bounds

The standalone native and independent Python bounds implementations now use
actual packed model vertices. Outward-rounded float intervals carry the bounds
through the original matrix and perspective projection. A bound crossing the
near plane, or an uncertain/nonfinite calculation, stays with the full polygon
projector. The game's CPU sphere radius is not used for this rejection.

This component is not yet linked into the live scene assembler or MAME. It
does not draw extra scenery or establish material ownership, scene ordering or
a gameplay performance improvement.

## Verification

The canonical comparison decodes every polygon independently, checks that a
rejected model has no polygon intersecting the viewport, and compares every
C++ rejection decision with Python. Three earlier standalone snapshots pass:

| Snapshot | Rejected objects | Projected quads avoided | Visible quads retained |
| --- | ---: | ---: | ---: |
| Hong Kong5000 |725/1,515|4,741/9,596|4,740|
| Amazon5072 |1,535/1,622|15,881/16,408|382|
| Hong Kong5990 |740/818|4,598/5,478|457|

All3,955 decisions agree, with zero false rejections. Margins are the recorded
88 pixels for Hong Kong and86 for Amazon. These counts belong to the older
standalone snapshots, not the later f49 live observer snapshots.

The reproducible synthetic suite also passes5,000 random-transform, screen-edge
and near-plane cases:808 rejections,3,307 visible polygons, zero false
rejections. Its right edge is598 at margin86. Earlier local draft tests used
a600 right edge and different synthetic inputs; their receipts are retained
but are not the canonical result. The native unit additionally compares16,214
transforms against the native polygon projector, retaining all10,223 visible
polygons while rejecting5,871 objects. Four malformed batch cases must fail
without publishing partial output.

The complete local suite passes305 Python tests without skips,36 native helpers
and103 commands. Its454-file source identity is
`3a342df2214ecbd1d8a71e8a19bde2e5ec203bd3eb77d1dd08da2864be37e78f`.
The standalone analyzer SHA256 is
`11579692674e424625898959030cffc76eff29fcf5d875b1b9808eccdf67869c`.
Raw operands and generated geometry remain local under
`results/diagnostics/exotica-amazon-20260909`.

## Integration next

Cache bounds with each owned model and make their use explicit, default-off and
recordable. Keep old context bytes unchanged when off; version captures when
on. Bounds must not bypass malformed-model or projection checks. Compare all
remaining ordered visible quads against unfiltered scenes, then measure live
cost, repeatability, route, original resources and4K images.

The accepted live observer and seven-default milestone remains nativef49,
SHA9c7dcd27. Personal Stream Deck remainsv0.5.0/SHA87d04de4. No new native
build, deployment, release, physical-force test or hosted workflow occurred.
