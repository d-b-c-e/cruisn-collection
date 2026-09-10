# Zeus command and material timeline — September 10

A bounded GPU-consumer journal now records the initial WaveRAM/palette image and
every original command and texture upload between two completed-frame snapshots.
Independent offline playback reproduces both the original and private wider-depth
targets exactly for the selected Amazon interval. This closes an important gap in
the earlier captures, which saved texture memory only at the end.

Native `24519f861ba59d0fffe4eedcc059531e6835224e` is built separately and pushed,
frozen at `build/candidates/24519f861ba/vunit.exe`, SHA256
`ebb8602d9bf110a1208294eb28cb110611fadb96bb7ab66f1dfc6f335282a5c4`.
The179-patch export reconstructs tree
`2cd4112e9884bfeaaf623633f9e75e781df74a15`. Personal native87d/v0.5.0 is unchanged.

## Capture and independent playback

`--zeus-depth-stream-frame 5080` requires explicit depth-mirror mode and raw
snapshots at5079 and5080. The consumer owns all captured bytes, limits the journal
to64MiB/131,072commands and writes three files through a bounded writer. The
parser rejects malformed uploads, missing completion and incorrect boundaries.
Ordinary runs leave this diagnostic disabled.

The first replay's parser failed because it assumed all type6 messages were
16-byte completed-frame markers. The actual stream also contains a4-byte legacy
display-address notification, which the current renderer ignores. The corrected
parser handles these distinct formats and still requires a final16-byte marker.
The initial failed report is preserved; a fresh run passes.

Both captured journals are byte-identical. Each contains3,989commands, including
3,799polygons,186palette uploads, one fast clear, one9,192-byte texture update and
both forms of type6 message. Independent playback starts from the prior completed
GPU state and reproduces the entire2736×4096 internal target, with zero color or
depth differences for both the original and wider policies. The material/vertex
shaders are shared with the renderer; wider depth mapping is expressed separately
without importing its native shader generator. Earlier synthetic tests supply the
independent scalar checks of the depth rule.

No additional sky-copy polygon occurs in this specific interval. The checker
implements the independently tested panorama rule, but this sample does not add
live coverage of that branch. Starting from a recorded prior target is also not
an independent reconstruction of all earlier frames.

The fresh6000-frame replay preserves original input/camera/ADC timing, all ten
original capture resources and25completed3840×2160 images. Its eight raw private
color snapshots remain equal to original color. Full local checks pass345Python
tests without skips,47native helpers and132commands at500-file identity
`fba6aafeb463ccc2cc3d5b0c139993e110b7273a2d0608578842e45192e97a1b`.
[Public proof](../../results/proof/2026-09-10-zeus-command-stream/README.md)
recomputes identity, coverage and repeated result hashes; raw resources and actual
GPU/replay/build execution remain hash-bound receipts.

## Next

Match a consumer interval to an existing future-scene snapshot using original
polygon bytes and the model journal. CPU scene-frame labels and completed GPU
frames must be joined explicitly. Then test1x/2x/3x future insertion offline before
linking the same owned packet into the live private target. Continue with material
lifetime, transparency, handover, performance and cross-game defaults.

No future geometry is drawn by this checkpoint. It does not renew the default
suite, resolve the earlier USA timing stall or authorize a deployment/release.
All automated physical force remains zero; World force tuning stays deferred.
