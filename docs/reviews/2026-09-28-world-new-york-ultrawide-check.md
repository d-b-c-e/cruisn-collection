# World 2.4 New York: 3440×1440 display check

After the primary monitor changed to a single 3440×1440 ultrawide, I used the
saved New York drive to recheck the diagnostic active-nonroad margin path at
the source-qualified frame-3600 right-side gap. This is a display-topology
check, not a claim that the game now renders native 21:9 world content.

The frozen `f762e01d63b` control and candidate both passed prepare-only
preflight, then 3,608 recorded inputs/native comparison, literal FFB0,
physical 3440×1440 display watch, explicit CRT on/4×/height 400, and owned
shutdown. The only renderer option difference is active non-road margins.
The paired comparator **PASS**es seven completed frames 3598..3604:
all seven change in the right third only, with an exact center and left.
The candidate adds 116,872 quads over this prefix; the seven completed
changes range 32,222..35,990 RGB pixels. Those are frame-pixels, not a
quality score. The inspected frame-3600 candidate carries the right wall
into the control's dark opening.

The completed BMPs are 3424×1353, although the physical monitor is
3440×1440. At frame 3600, **both** new BMPs equal their previously qualified
2544×1353 captures pixel for pixel after a 440-pixel centered horizontal
offset. Every pixel in the new 440-pixel left and right side bars is black.
The old and new completed images use the same saved drive and frozen native
binary, and each replay independently passes its input/native gate. This
strongly shows that this sampled 3440×1440 presentation centers the same
16:9 rendered image; it does **not** show a wider game camera or additional
ultrawide view. Other frames or games are not covered by the cross-display
exact-pixel check.

`harness/check_centered_display_capture.py` records image hashes, exact
center equality and both black-bar checks for the control and candidate.
Two synthetic positive/negative tests and Python compilation pass. Local
raw receipts and source-hashed reports are under
`results/diagnostics/world-new-york-20260927-live-1` as
`new-york-3600-ultrawide-{control,trial}-{prepared,run}`,
`new-york-3600-ultrawide-paired-v1.json`, and
`new-york-3600-ultrawide-{control,trial}-centered-v1.json`. The paired
report's generic exact-image comparison correctly says **FAIL** for the
intended right-margin differences while its route and center gates **PASS**.
No native product change, renderer deployment, personal Stream Deck update
or public release occurred. Physical 4K, other courses, physical FFB and
GPU pacing remain separate gates.
