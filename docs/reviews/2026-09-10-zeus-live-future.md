# Live private Zeus future scenery — September 10

Exotica's future scenery can now be drawn by the native renderer into a separate
wide-depth target while the original game continues to render and display normally.
The first full1x drawing replay preserves the recorded drive and original output;
five independently reconstructed insertions match its private pixels exactly.
The full3x data-only control also passes. Full2x/3x drawing and temporal acceptance
are still in progress at this checkpoint.

Native `e144228a8953e49d36f255826202b8fa8bdf21ca` is built separately and pushed,
frozen at `build/candidates/e144228a895/vunit.exe`, SHA256
`24b18ba8bc22981fedfcfdcec614d0d32dc5adbf1b73fa726513a4d40843e7f4`.
Its181-patch export reconstructs tree `ce147a70f5cc3323af5e56ba8d4312aa7033453b`.
The personal v0.5.0 binary remains SHA87d04de4.

## What changed

`--exotica-host-future observe|draw` extends the existing bounded scene diagnostic.
It requires an explicit candidate, scene interval, private material observation,
live Exotica GL and the wide-depth mirror. Replay disables physical force.
The native queue independently enforces force0. Active margin drawing and the
original-only command journal cannot be combined with this prototype.

The emulation callback prepares an owned XWD1 packet containing ordered polygons,
their palette bindings and the checked material image update. It does not change
guest RAM, activate objects, spend emulated CPU cycles or change hardware DMA.
The GPU consumer finishes the original sky copies, commits pending draws, checks
the packet and uploads its private materials. Draw mode inserts future scenery
only into the private wide-depth target before the corresponding original model.
The original framebuffer remains the displayed image.

Observed mode validates the same ownership and delivery without additional
drawing. Missing controls preserve old recordings. Recorded controls are checked
again, including the completed-frame interval and incompatible diagnostics.

The first live build used the wrong Windows compile guard, causing its queue
entry point to return false at the first scene. That failed run is retained.
The `_WIN32` correction was built and tested in a fresh candidate and run.

## Evidence so far

| Replay | Scenes | Future polygons processed | Original completed4K captures |
| --- | ---: | ---: | ---: |
| 6000-frame1x observation | 4,120 | 835,720 | 25 |
| Full8860-frame1x drawing | 6,953 | 2,312,876 | 117 |
| Full8860-frame3x observation | 6,953 | 19,945,019 | 117 |

All three preserve original input, camera, actual ADC times and ten captured
original resources. The full runs save14 private completed-frame color/depth
snapshots and five immediate insertion snapshots. All14 private control colors
equal original color. Wider-depth values deliberately differ from D24 storage.

At CPUframes3900,5072,5644,6330 and7187, the checker independently prepares scene
geometry in Python, verifies exact packet and palette ownership, then renders
against the saved private state immediately before insertion. It uses a separately
expressed wide-depth shader; material and vertex shader code is shared with the
diagnostic renderer. Full1x drawing and3x observation match every sampled pixel and
depth value exactly. The other framebuffer page is unchanged. This proves these
insertions, not all preceding frames or final visual quality.

All348 Python tests pass without skips, along with47 native helpers and132 local
commands, including the earlier wide-depth GPU cases. The503-file source identity
is `204f28ce496fb6f4eb171aba54852ffc3e53e13b549880f49f9ef7e01b1f217a`.
The [public proof](../../results/proof/2026-09-10-zeus-live-future/README.md)
recomputes identity and selected receipt consistency. Raw game geometry, material
images and framebuffers stay local; actual GPU, route and full pixel comparisons
remain hash-bound execution receipts.

## Why more geometry can still be invisible

Separate offline joins match every original polygon at CPU5072/GPU5073 and
CPU7187/GPU7188. Independent playback of both completed command intervals matches
the original and private targets exactly. The later interval includes a real sky
repeat, extending the earlier journal test that had no sky copies.

At the early sample,1x produces386 future polygons and2x/3x both produce538.
The2x image changes10,127 pixels relative to1x, but the addition is faint because
the source opacity is low. No additional3x geometry survives the bounds at that
specific camera position.

At the later bridge sample,3x produces8,283 polygons. Inserting them changes
131,707 color pixels immediately, but the subsequent original scene covers all
of them. Original final depth is nearer at all131,715 pixels where future depth
changed. Final1x/2x/3x images therefore match there. This is consistent with nearer
bridge/road geometry hiding the distant scene; removing that occlusion would
create incorrect visibility.

## Remaining work

Complete full2x/3x/repeat drawing comparisons and inspect the private images at
multiple points along Amazon. Validate transparency, material lifetime, handover
when original objects activate, and a run without expensive readbacks. Low source
opacity needs investigation; forcing full opacity without a matching handover
could create a new pop when the original object begins its own fade.

The last clean seven-default suite remains the50a milestone. The later USA
6.13-second timing failure is still unresolved and is not erased by these Exotica
passes. No deployment, release, experiment-menu removal or four-game3x acceptance
is implied. World force tuning remains deferred.
