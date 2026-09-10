# Exotica private margin drawing — September 10, 2026

An offline GPU composition repairs the black left-hand ground in the captured
Amazon scene at game elapsed0:34.96. It draws63 current objects/522 quads selected
by the original horizontal culling decision and the expanded viewport. The added
geometry uses a private copy of original D24 depth and writes only the two
widescreen margins. No individual model or track is allowlisted.

The insertion follows original quad3219 of3349, at the actual final command
completion verified by the native observer. The remaining original polygons
are then drawn in their original order.8,416 margin pixels change; completely
black margin pixels fall6,459 to zero. The original center image, complete
original depth buffer and original GPU material textures remain byte-identical.
The repeated result matches exactly. Visual inspection confirms the black
triangle becomes textured ground.

This is an offline native4x framebuffer composition:2736x4096 target, with a
2736x1600 page image. It omits CRT, live sky-repeat and previous margin retention;
it is not a new live4K gameplay acceptance. Materials come from the captured
first-model state. Their validity at the later live fence still needs checking.

The repository now includes three reusable parts:

- `native/exotica_active_capture.h` owns31 rendering words per current list
  member, checks list order and duplicates, and rechecks membership, rendering
  fields and projection factors before selecting the final objects. Original
  scratch word20 is excluded; neighboring word31 is never captured. Actual
  original submissions can be excluded explicitly. The caller must additionally
  check live camera/view/setup dependencies and the device fence.
- `native/zeus_margin_packet.h` owns materials and clipped geometry in one
  bounded packet. It validates private palette rows, page, vertices and the
  original D24 range, including depth bias. It does not silently clamp farther
  geometry into that range. Whole-instance eligibility remains the producer's
  responsibility. A clipped polygon may contain eight vertices/eighteen triangle
  vertices. Empty scenes and malformed packets are covered.
- `harness/verify_zeus_margin_depth.py` tests real OpenGL D24 copies, foreground
  occlusion, private depth ordering, original depth/center/other-page isolation,
  original drawing after the private pass, and repeatability. Its16 synthetic
  cases cover both pages, zero/86/88/120pixel margins and1x/3x/4x scale.

The canonical capture helper reproduces13 actual list-start/end journals:
4,591 objects,814 margin candidates and4,318 scratch changes. This comparison
ends at CPU ordinary_end; it is not a new live end-fence ownership observation.
The canonical packet checks all1,238 actual quads from seven snapshots. All
324Python tests/no skips,45native tests and125local commands pass at source
identity`412c67e1db0662d41592a9200eba51ab34d8036744447780982eadd994df8496`.
Public proof at `results/proof/2026-09-10-exotica-private-margins` contains
hash-bound receipts; raw models, textures, images and journals stay local.

Next, integrate the owned capture and late material/geometry packet at the
accepted command fence in a separate native candidate. Reuse the private texture
image with an explicit late-scene phase; preserve generation/order checks and
distinguish early and late snapshots. Check current slot/binding ownership,
page/camera/setup, material readiness, original center/depth/resources and repeated
gameplay around the reported times. Then broaden to the full Amazon/Hong Kong
drives and all seven defaults.

This margin experiment retains original draw distance. General farther depth,
transparent foreground ordering, fade and handover remain open. A post-ordinary
depth copy alone cannot recover every earlier non-depth-writing shadow or alpha
contribution; inspect this explicitly before wider use.

A separate original-renderer concern was identified in code: texture dirty spans
are queued at screen updates, after earlier polygon records. The GPU flushes
those earlier polygons before uploading the new bytes. Whether any affected
polygon needed a newer texture is unproven. Measure write/consumer versions or
actual texture footprints before changing this timing; resource equality only
proves preservation, not correct material age.

No MAME build or deployment is added by these standalone helpers. Native2eac
remains the last candidate with seven-default acceptance; personal Stream Deck
remains v0.5.0/SHA87d04de4. No release, hosted workflow, physical FFB, World force
tuning or experiment removal.
