# USA Golden Gate: full changed-pixel source attribution at 10476

The [matched control indexed capture](2026-09-28-usa-bridge-control-indexed.md)
established 7,058 changed pixels in the left margin of completed frame 10476.
This saved-evidence check asks whether the exact 76 packets newly admitted by
partial far coverage can account for **every** one of those indexed changes,
rather than just the red CRT center samples.

The checker first revalidates the 10,480-input control/candidate receipts:
same diagnostic binary, case and physical 1440p target; literal FFB0; exact
recorded input/native comparison and owned worker shutdown. The candidate
BMP remains byte-exact to the earlier continuous on run, the control BMP to
the earlier off run. Source-time RAM, fast RAM, texture and palette are equal
between the exact source tap and detailed candidate trace. All 3,782
candidate packet words/order match the source projection; the 3,706 ordinary
packets match within the candidate multiset, leaving 76 new packets. The
visible-page original-only indexed
planes and 4:3 center remain exact.

The newly admitted packets were rasterized **alone**, in their source order,
using the captured texture. Their raster covers and exactly reproduces all
**7,058/7,058 changed completed indices**. None is uncovered or mismatched.
All changed control tags are game-owned `1`, and all candidate tags are
host-owned `5`; the changed footprint is x=45..183, y=792..1023 in the
2736×1600 indexed page. Nineteen of the 76 added packets contribute to
these changes, from five source objects:

| Source object | Exact changed indexed pixels |
| --- | ---: |
| `0x800a0040` | 4,936 |
| `0x800a0042` | 1,377 |
| `0x800a0044` | 4 |
| `0x800a0051` | 565 |
| `0x800a0056` | 176 |

This closes the earlier attribution gap in the red-color screen: at this one
frame, all completed indexed changes come from newly admitted textured source
packets. It does **not** mean all candidate-only red CRT pixels represent new
coverage: 2,348 of 4,906 red center samples have the same completed index/tag
in both modes, consistent with neighboring CRT or presentation influence.
Nor does the isolated raster prove full ordered per-fragment depth safety,
correct bridge shape through intermediate frames, smooth activation, another
course, 4K appearance, GPU pacing or release readiness. The option stays
diagnostic.

`harness/screen_usa_bridge_candidate_pixels.py` now has an opt-in
`--require-full-added-coverage` mode that requires the matched control mirror
and records covered, exact, mismatched and uncovered changed pixels plus
source-packet IDs. The source-hashed local
`results/diagnostics/race-transitions-20260916/usa-bridge-candidate-pixels-v6.json`
**PASS**es with 7,058 exact, zero mismatched and zero uncovered (SHA-256
`1b6eb07189ac036076a91f22010b0dae85395b33ee385630bf68bef5233d822d`).
Python compilation passed. Prior v1–v5 reports are preserved. No game replay,
native build, renderer deployment or release resulted from this screen.
