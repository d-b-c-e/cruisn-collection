# Live Exotica waiting-scenery drawing

The isolated renderer now draws allocated scenery during the gap before the game
first submits it. A full Amazon replay completes with additional visible trees.
This is an integration milestone, not release-ready four-game distance parity.
The personal Stream Deck executable and public v0.5.0 remain unchanged.

## Implementation

Native `88803dabb212f776e2e8e62ff3e58cd903a2efa2` adds an explicit
`--exotica-host-handover draw` path. It captures geometry and palettes at the
proposal, filters out objects already submitted by the original game at the actual
device completion fence, then draws the remaining copies with the retained private
texture image. The renderer enforces scene/frame/page and image-generation order.
Original texture uploads and guest dirty-page tracking remain separate. Existing
future scenery stays at its earlier insertion point; intrinsic alpha is preserved.

The harness verifies late packets separately from early future packets, including
material generation, zero changed texture pages, palette bindings, ordered geometry,
completed GPU delivery, and unchanged other-page pixels in sampled insertions.
Active-margin drawing is excluded; physical FFB is disabled. The helper is now
in the MAME synchronization manifest. No new launcher setting is exposed.

## Focused validation

- **Short original-display run:** 6,000 inputs, original camera/actual steering
  timing, 21 completed 4K images, and existing future geometry/resources match.
  All 4,120 waiting batches reach the GPU; three sampled insertions pass texture,
  geometry and depth/page checks.
- **Full extended-display run:** all 8,860 inputs, 7,060 camera samples and 21,180
  actual ADC records match the original drive. All 6,953 batches complete through
  the post-race reset, drawing 5,528,581 waiting quads in total. Five sampled
  insertions pass; original future geometry and sampled resources remain unchanged.
- **Visible comparison:** 17 of 33 selected completed 4K/CRT frames differ from the
  previously accepted future-only 3x baseline. Inspection at frames 5100, 5550 and
  7950 shows added vegetation; the village and downhill views make the addition
  easiest to see. Pixel counts alone do not establish correct transitions.
- **Targeted regression tests:** 37 tests across handover, waiting selection,
  future GPU receipts, materials and scene options pass. Native helper sync passes.
  The previously verified 188-patch export is unchanged; applying the appended
  commit to its verified tree reconstructs the new tree exactly.

The short run initially failed an old observer artifact glob that also matched
the new drawing files. The verifier now separates those namespaces. Its original
failure report remains; the saved capture was revalidated without another drive.
The full emulator run passed; a separate image analysis initially requested exact
33-frame coverage from a 233-frame reference. The corrected analysis compares the
explicit 33-frame subset, again without rerunning gameplay.

## Limits and next decision

The existing left-edge ground defect remains visible. Temporal fade/handover,
broader tracks, a repeat of this new draw mode, and normal-speed acceptance remain
open. This work does not change the other three games or renew the combined default
suite. That suite remains required before deployment, rather than at every isolated
experimental milestone.

This instrumented full run reports 81.85% speed, including geometry logging and
large GPU captures. It is not a clean performance benchmark. Existing timing
columns identify useful optimization targets: early scene assembly totals 20.471s
and diagnostic geometry hashing 4.452s; future GPU processing totals 22.230s and
waiting GPU processing 6.969s. These spans overlap across threads and contain
instrumentation, so they must not be added into a frame-time budget. Material
encoding alone totals only 0.533s. Prioritize unnecessary assembly/hash/packet work
and smooth object handover over further texture-image copying optimizations.

The next useful test should target a changed optimization or a concrete transition
window. Do not repeat the whole matrix merely to collect more passing receipts.

## Reproduction and local evidence

Frozen binary: `build/candidates/88803dabb21/vunit.exe`, SHA256
`a165370e9cb776082acbdc7be4045db6d0bc938dc78c576dca576ca2827d62e2`.
The full 189-patch export reconstructs tree
`55df7333c515b3bac1d2c516ecf2acb6959c1826`.

Under local `results/diagnostics/exotica-amazon-20260909/`:

- `waiting-draw-short/report.json` retains the original verifier failure;
  `revalidated.json` and `waiting-draw-short-acceptance.json` hold corrected checks.
- `waiting-draw-full/report.json` and `waiting-draw-full-acceptance.json` hold
  the complete integration and selected-image comparison results.
- `waiting-draw-trial.py` records exact commands and supports `--verify-existing`.
- `waiting-draw-native-export.json` binds the baseline export and successor tree.

Raw game geometry, memory, recordings and images remain local. No new standalone
proof package or broad test campaign was needed for this checkpoint.
