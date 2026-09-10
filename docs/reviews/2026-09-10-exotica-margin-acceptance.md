# Exotica current-distance margin acceptance — September 10, 2026

The separate candidate repairs missing margin geometry in the recorded Amazon
drive and passes the existing seven-game regression cases. It is **not deployed**
and does **not increase far drawing distance**. Broader foreground ordering,
material lifetime, other tracks and normal-play performance still need work.

## Accepted candidate and coverage

Native `50a6eaa3d1f233f51d1c0174b6858a09487e9120` is separately built and pushed.
Frozen `build/candidates/50a6eaa3d1f/vunit.exe` has SHA256
`a4e4cd4dc060e068ae4e4f3c29f9c8abc853bdc28420958ee797f924742581de`.
The 176-patch export reconstructs tree
`0bf35ca188db56a9a90166f13763af39df28fbfd`.
The personal Stream Deck binary remains v0.5.0 / SHA256
`87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8`.

| Check | Observed result |
|---|---|
| Full Amazon, 8,860 recorded inputs | 5,290 completed scenes / 970,889 ordered added quads |
| Full Amazon repeat | Same scene fields, geometry fingerprints and all 117 completed 4K images |
| Optimization versus preceding candidate | Full, repeat, Hong Kong and observe runs match all 51 / 51 / 17 / 51 owned raw snapshot files |
| Observe-only control | All 117 images match the preceding observe control, which matches the original |
| Hong Kong, 6,000 inputs | 21 completed 4K images, route and original resources match |
| Amazon motion | 7,060 camera samples and 21,180 actual ADC read times match the original control |
| Original sampled resources | Ten command/model/palette/texture/framebuffer files match per comparison |
| Independent final geometry | Amazon 6330: 24 instances / 165 quads; 7187 and 8760: 0 / 0; Hong Kong 5000: 4 / 9 |
| Seven defaults | All pass, including actual UDP/memory telemetry and four software force-policy checks |
| Local suite | 332 Python tests, no skips; 46 native tests; 127 commands pass |

Final local/default source identity:
`a3d78d50fb5a045fa77c0b19657c3f209970eaac2ab08aa197c0c1e94bc541f2`.
Default-case presentation follows each existing fixture; the 4K claims above
refer to the separate Exotica comparisons, not every default fixture.
All automated physical force remained zero.

The earlier full candidate changes 48 of 117 sampled images from the original;
the optimized candidate preserves those images exactly. Inspected game-time
44.89s and 57.50s comparisons replace black edge ground with textured geometry.
Earlier dense 5072/5080 raw comparisons repair 6,459 / 4,231 black margin pixels
without creating newly black pixels. These samples do not certify every frame.

## Resource ownership and cost

The game can advance camera, animation and model pointers while earlier commands
are still draining. The implementation owns scene-end RAM and rendering state,
then checks that the old model bytes, palettes and required texture pages are
still valid at actual command completion. It does not substitute the new scene's
camera or accept a reused material merely because its address is unchanged.

CPU scene sealing now has its own dirty-page bitmap. GPU uploads cannot consume
that bitmap. Initialization and save-state restoration require a complete copy.
The 6,000-frame verification run compares all 2,457 reconstructed 16 MiB images
against independent complete copies: all pass. It copies 11,499 pages including
4,096 at initialization; no later scene needs more than four pages. The 25 images,
ordered geometry and 85 raw snapshot files remain identical to the prior build.

In the full instrumented drive, average sealing cost falls from 1.354 ms to
0.200 ms; repeat is 0.201 ms. Overall measured emulation speed rises from 89.29%
to 92.37%, with 92.04% on repeat. The corresponding original control is 93.67%.
These runs include expensive diagnostic captures. The subsequent
[runs without heavy captures](2026-09-10-zeus-depth-domain.md#performance-without-heavy-captures)
measure99.99% baseline,94.90% future observer and93.06% observer plus margins.
**Normal-play smoothness is not accepted yet**; geometry assembly and diagnostic
hashing still cost measurable CPU time.

## Remaining limits and retained failures

- The private pass uses the original D24 depth range and current-distance objects.
  The parent future observer's multiplier does not turn this into 3x drawing.
- Fifty-five instances remain excluded by the raster contract across Amazon.
  A generated RAM descriptor at frame 5604 now decodes correctly, but its one
  non-depth-tested quad remains excluded. Zero RAM-descriptor models are rendered
  in this drive. Parsing it successfully is not an ordering fix.
- Snapshot checks protect the entire original depth target and outside-margin
  color. They do not establish correct ordering against every transparent or
  non-depth-writing foreground object, nor general handover into original draws.
- Initial synchronous-capture watchdog, camera advancement at 3510, animation
  pointer advancement at 4131 and generated-descriptor rejection at 5604 remain
  retained failures. See the [implementation history](2026-09-10-exotica-live-margins.md).

Public [proof](../../results/proof/2026-09-10-exotica-live-margins/README.md)
recomputes scene/copy counters, completion, ordered fingerprints and source identity.
Full pixels, geometry, original resources, route, native build and default outcomes
remain hash-bound receipts. Raw game data stays local.

Next: measure capture-free overhead, then prototype an original-only private
renderer with wider depth storage and prove image/ordering equivalence before
inserting farther scenery. No release, deployment, menu removal or World FFB change.
