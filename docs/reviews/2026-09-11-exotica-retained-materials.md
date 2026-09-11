# Retaining proposal materials for the later Exotica draw

The waiting-draw prototype can now keep the exact texture image from its earlier
scene proposal while supplying the later geometry's own palettes. Five actual
completed cohorts pass independent packet comparisons. A captured GPU-command
replay produces identical color and depth with a full second image or the new
retained-image packet. This is a standalone component; it is not yet linked into
MAME and does not change the personal or public build.

## Why the extra contract is needed

Future scenery is inserted early, at proposal P. Waiting scenery must be filtered
at the actual completion boundary R, after the original game's submissions are
known. Reusing the original material packet at R would replay an already-consumed
generation. Taking a fresh live texture image at R could mix proposal geometry
with resources that have since changed.

`native/zeus_retained_materials.h` instead creates a checked continuation of the
owned private image. It increments the material generation with **zero changed
pages**, carries owned palette colors and requires the exact existing image hash.
Palette colors are checked against that image before staging and again before
consumer acceptance. Stale, repeated, changed-page and invalid-palette packets
fail before changing the consumer. Empty geometry cohorts can still complete
their sequence. The caller must separately enforce scene, frame, render page and
one completion per proposal; the helper cannot establish the device fence.

This uses the existing HMT1/XWD1 packet formats. The ordinary game's texture and
palette uploads remain separate. A native implementation must queue the retained
packet before the next future scene advances the private image, preserve intrinsic
transparency and retain the established early-future/late-waiting insertion order.

## Actual snapshot checks

The standalone analyzer reads independently assembled full-image future/waiting
packets, verifies equal proposal images and matching scene metadata, and replaces
the second full image with the retained continuation. The input geometry comes
from the accepted native completion observer. Independent Python construction
matches the complete resulting packet bytes, including ordered geometry, palette
indices, palette colors and the zero-page generation transition.

| Proposal frame | Waiting quads | Palettes | Full-image packet bytes | Retained packet bytes |
|---|---:|---:|---:|---:|
| 3900 | 1,690 | 19 | 17,259,496 | 465,896 |
| 5072 | 849 | 14 | 17,032,312 | 238,712 |
| 5644 | 1,906 | 14 | 17,311,360 | 517,760 |
| 6330 | 338 | 5 | 16,888,120 | 94,520 |
| 7187 | 18 | 1 | 16,799,512 | 5,912 |

Each packet avoids 16,793,600 bytes of duplicate full-image data in this standalone
comparison. This is a packet-size result, **not a measured live speed improvement**.
The original future stream already uses incremental updates. Six malformed-input
cases also fail: wrong scene/page/snapshot state, altered image, trailing data and
truncation. Synthetic tests additionally cover guest-memory mutation, stale
palettes, duplicate continuations, a newer scene image and unchanged state on
failure.

## Ordered GPU comparison and retained failure

An initial comparison with an older offline future packet failed because that
older preparation sorted source addresses. Its primitive/material multiset equals
the actual native stream, but its order differs. The new comparison preserves the
captured native instance order and independently verifies it against the native
XWD1 snapshot. The initial failed expectation and its output remain local.

At CPU5072/GPU5073, the existing future insertion stays at command32 and the
filtered waiting insertion stays at command3358. Four fresh command replays cover
native-order future only, full-image waiting, retained-image waiting and its repeat.
The full/retained/repeat completed color and depth buffers are byte-identical;
other-page and depth-range checks pass. The old sorted-order results happen to
have identical completed pixels in this sample too. This does not establish that
sorting transparent primitives is generally safe.

The compared target is the complete internal2736x4096 buffer, including its
2736x1600 active page. There is no new live4K or temporal acceptance. The earlier
visible trees, unchanged old left black wedge and fade/handover limitations still
apply.

## Next integration

Use this checked continuation in an explicitly gated private waiting draw at R.
Capture palettes from proposal geometry at P, filter their bindings with the
completed ownership cohort, and submit an empty image delta against the already
owned proposal image. Keep the next scene's guest-written page tracking intact.
Renew actual command placement, resource ownership and completed pixels before
adding fade policy or accepting performance. Current native936840, personal87d
and public v0.5.0 remain unchanged.

LOCAL evidence is in `waiting-retained-materials-ordered` and
`waiting-retained5072-render` under the Amazon diagnostic directory. Public
receipts distinguish source/aggregate consistency from raw execution. This work
continues independently while the four-game FFB calibration awaits short matched
drives; it does not defer that near-term milestone.

All424 Python tests (no skips),52 native tests and149 local commands including
the GPU group pass at source identity
`7903ebdf48ccb279eb2a83477c78e4a17db45b873707f3d9edd677139a612d4b`.
The final compiled analyzer renews all five actual packet checks in
`waiting-retained-materials-final`; every output packet is byte-identical to the
GPU-tested preparation. [Public verification](../../results/proof/2026-09-11-exotica-retained-materials/README.md)
checks the associated source hashes and aggregate receipts.
