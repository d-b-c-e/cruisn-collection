# Zeus private wider-original control — September 10

The wider-depth policy is now linked into a separate native candidate. It renders
the original command stream into a private target while the original target
continues to be displayed. No future scenery has been added by this checkpoint.

Native `802714912c919d5394eb7a0eb4699b8926c8bf56` is frozen at
`build/candidates/802714912c9/vunit.exe`, SHA256
`05b132f9147badf5f8ab2e836b77b33fe759aef4e3e4c3b50e964ecbd5cc0a6c`.
The178-patch export reconstructs tree
`562497b3f3aff904326d64214a76d82e80862292`. Personal Stream Deck native87d/v0.5.0
is unchanged. No deployment, release or physical force test occurred.

## What changed

`--zeus-depth-mirror wide` selects the separate wider-depth shader. Existing
`observe` still enforces exact original-color and compatibility-depth equality.
Only actual fast-clear commands receive the new range-initialization tag1024;
direct framebuffer writes retain their separate depth meaning. The original
shader ignores that tag. Old recordings and absent controls retain their behavior.

Wide-mode diagnostics distinguish readback integrity from depth correctness.
They verify finite values in range, native/independent difference counters and
completed snapshots, but explicitly set `pixel_depth_policy_verified` false.
Original D24 data cannot reconstruct a saturated primitive's pre-clamp depth.

## Recorded controls

Three6000-frame Amazon runs—compatibility, wide original and wide repeat—preserve
the original input replay, camera and actual ADC times, all ten original capture
resources and25completed3840×2160 images each. Compatibility still has zero
private color/depth differences at all seven raw snapshots.

Wide mode changes private depth values while all seven private color snapshots
remain exactly equal to original color. Changed depth counts at frames
300/1800/3500/5072/5080/5604/5990 are
6,553,600/29,152/203/179/70/89/0 respectively. These counts describe the changed
mapping, not an image-quality improvement. Repeat preserves all28raw files and
5989ordered frame/vertex/clear/difference counters. GPU batch boundaries may vary.

Full local checks pass342Python tests without skips,47native helpers and132
commands, including the292-case wider-depth and76-case compatibility GPU checks.
The exact source identity and execution receipts are archived in
[public proof](../../results/proof/2026-09-10-zeus-wide-original/README.md).
That verifier recomputes frame coverage, repeat counters and source identity;
raw GPU, route/resource, build and execution results remain hash-bound receipts.

This does not renew the seven-default suite or resolve the earlier USA menu
timing failure. Normal-play performance, complete original-scene depth policy,
future materials, transparency and handover remain open.

## Next diagnostic and drawing work

Existing CPU-side command captures save WaveRAM and palette data at capture end.
Using that final memory image for every earlier draw could miss an intervening
upload. A bounded GPU-consumer journal should capture the initial material image,
every ordered palette/texture update and original command between two completed
frame snapshots. Independently replay that journal and compare both targets.

Then insert owned XWD1 future geometry at the verified early model boundary,
after buffered sky copies have finished. Compare1x/2x/3x, repeat and original-object
handover. Preserve original resources/routes, inspect transparency and performance,
and renew cross-game defaults before deployment or changing product options.
