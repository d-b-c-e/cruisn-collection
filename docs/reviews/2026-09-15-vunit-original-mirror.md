# Native original-only V-Unit mirror

The distance-fade prototype needs an original-only image to blend against while
resolving both views with the latest palette. The first native step implements
that image separately from the appearance policy. It does not enable fading or
change launcher settings.

Candidate `0f3b4b51f5a` adds two private integer textures per framebuffer page.
Ordinary geometry writes normal and private indices/masks in one GPU traversal;
auxiliary geometry writes only the extended view. Original scene resets follow
original commands independently, so an earlier auxiliary batch cannot clear the
private history. Batched CPU writes update both views only at dirty pixels.
Unbatched CPU upload mode is explicitly unsupported by this diagnostic.

The replay option `--vunit-original-mirror-frame` requires a candidate, World GL,
physical FFB off, and a capture before the replay drain. Added scenery requires
both tagged coverage and split batches. Native code also rejects unknown layer
ownership. The mode is off by default and the normal presentation shader remains
unchanged. USA/Off Road are not admitted by this first harness gate.

At the requested completed frame, the diagnostic saves both pages of extended
and original indices/masks: eight bounded binary planes plus a receipt. The
harness checks dimensions, counts, sizes, exact file inventory and hashes. In an
original-only run it also requires each private plane to equal its ordinary
counterpart. A separate comparator checks all four private planes between runs;
input and resource qualification remain separate requirements.

The first control passes 6,000 recorded World2.5 inputs. At frame5900 both pages
match exactly, after 2,965,204 ordinary quads, 195 CPU blits and 2,639 original
scene resets. The host-enabled counterpart also passes 6,000 inputs. All four original-only
planes remain byte-exact with 3,839,110 auxiliary quads submitted. The original
quad count, page selection and reset count also match the control.

A single matched run of the previous frozen `ebe10e87c33` binary confirms that
the completed frame5900 image is byte-exact with the new mirror enabled. All1,666
host-scene rows match after excluding exactly eight named timing fields. Both
runs pass the original input/time and native-image comparisons. Older cached
images used different road-detail and batch settings, so they were not treated
as valid matched controls.

The completed presentation is1280×720; the private index buffers are2736×1600.
This is not renewed final4K presentation acceptance. Three targeted harness tests
cover configuration gates, missing/corrupted captures, exact original-only pages
and cross-run original-plane/reset mismatches. Evidence additionally includes
`original-mirror-pair.json` and `original-mirror-presentation.json`.
No fade, moving-camera appearance, cross-game or release-performance acceptance
is claimed by this control.

The224-patch export reconstructs `86382b9844028b248eeb891c56e69e9b9d207216`.
Frozen binary SHA256:
`e56e68b5e79b59846bfd052a9f439d699296e1532d219191c733914cdecdd8ad`.
Local evidence lives under `results/diagnostics/world25-roads-20260914/`:
`original-mirror-control`, `original-mirror-host`, `original-mirror-build.log`
and `original-mirror-native-export.json`. Personal87d/publicv0.5.0 are unchanged.
