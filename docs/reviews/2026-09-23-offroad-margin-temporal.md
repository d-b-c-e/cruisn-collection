# Off-Road El Paso margin opening through a turn

The blue left-margin opening is visible through a short moving sequence, not
just the previously analyzed frame 3120. A bounded replay of the existing
attended El Paso drive captures completed frames 3100–3140 every four frames
(about 0.7 seconds). The 3× host range, CRT, 4× internal scale, native candidate
and source recording match the earlier source-joined run. Physical FFB was
disabled. All 3,200 input/time and native-image rows pass, the 11 requested
2544×1353 client captures are present on visible page 1 with zero dropped
messages, the display watch saw no topology change, and the owned worker
stopped cleanly. Frame 3120 is **byte-exact** to the prior capture-mode image.

The local `left-gap-temporal-screen-contact.png` shows the opening changing
shape throughout the sampled turn, including a much wider triangular wedge
near 3132–3140. A fixed client ROI `(40,475)..(400,625)` has a sky-like blue
CRT color signature in all 11 images. Paired-column counts range from 863 to
3,903; these are a review heuristic, **not exact missing-geometry area**. The
mask can include other blue material and omit some sky after CRT distortion.
The visual sequence and the source-joined indexed frame are the stronger
evidence of a persistent surface-continuity problem.

This changes the repair requirement: a proposal needs a coherent moving
surface/material transition across the turn, not a frame-3120 pen substitution.
The [source review](2026-09-23-offroad-left-margin-source.md) shows the two
nearest quads have different palettes/textures, and the [offline fill
screen](2026-09-23-offroad-gap-fill-screen.md) rejects simple copies. A broad
static billboard admission also cannot fill the sampled opening. The current
3× distance remains a diagnostic candidate, not a shipped treatment.

The first prepare-only plan accidentally used the shared preset's Off-Road
host-last frame 2250, which would have disabled host drawing during this turn.
No game ran from it. A second prepare-only attempt correctly rejected an
override because the preset owns that value. The executed explicit plan kept
host drawing through 3150 and matches the previous run's renderer settings
apart from capture/journal policy. These preflight attempts are retained.

Local evidence is under `results/diagnostics/offroad-full-20260910`:
`left-gap-temporal-run/report.json`,
`left-gap-temporal-screen-v2.json`, and
`left-gap-temporal-screen-contact.png`.
`harness/offroad_gap_temporal_screen.py` verifies every completed image against
the replay's pixel receipt, checks the 3120 byte match, and reproduces the
color counts and contact sheet. The v1 screen report is preserved; v2 adds
per-image receipt verification. No native source, installed build, release or
wheel settings changed.
