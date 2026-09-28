# World 2.4 New York: one-frame wall handover at 6303 and 6311

The [five-frame-cadence turn check](2026-09-28-world-new-york-late-wall-temporal.md)
showed a large change near 6305 in both modes. I narrowed that transition
with one matched 15-frame control/candidate pair at every completed frame
6298..6312, using the saved New York drive and frozen `f762e01d63b` native.
Both 6,320-input raw replays **PASS** recorded input/native comparison,
physical 2560×1440 display watch, literal FFB0 and owned worker shutdown.
The candidate alone enabled active non-road margins. No native build or
product renderer changed.

The paired report **PASS**es preservation: all 15 completed 2544×1353 CRT
images differ intentionally, and every changed pixel lies in the right
third; center and left are exact. The 625,537 accumulated changed
frame-pixels are repeated screen positions over time, not a defect area.
Adjacent captures occur in identical pairs for most of this window, matching
the game's roughly two-frame visible update cadence.

The change at **6302→6303** is a handover in the inspected right-side views.
At 6302, the candidate already shows a distant tower and wall where control
still shows sky. At 6303, control draws much of that tower; the candidate
keeps a road-edge/shoulder continuation. The between-mode difference footprint
falls from 71,586 to 19,309 pixels, with 53,632 previously different locations
becoming equal and 1,355 newly different locations. This does not show the
candidate tower disappearing from the user-facing scene; the ordinary game
has largely caught up at that camera step.

At **6310→6311**, the between-mode footprint grows from 19,018 to 61,100
pixels, with 44,559 newly different locations. In the inspected control image,
a blue sky opening reappears beneath/beyond the road edge; the candidate
continues a textured wall/shoulder and road edge. That is a positive
visibility observation in this short turn, not source or depth attribution
for frame 6311. The existing source-qualified 6300 check remains the only
exact packet/original-DMA attribution within this dense interval.

The reusable `harness/screen_paired_completed_steps.py` verifies both raw
reports, capture indexes and decoded RGB image signatures, then records
adjacent raw motion and turnover of the *between-mode difference footprint*.
Raw adjacent image changes exceed 2.8 million pixels at most game update
steps because the CRT treatment changes across much of the screen; they
must not be read as geometry motion. The first offline invocation failed
before analysis because it compared a BMP file hash with the report's
decoded-image hash. Its command/error are preserved as
`active-nonroads-6305-dense-steps-raw-v1.json`; corrected source-hashed
`active-nonroads-6305-dense-steps-v3.json` **PASS**es 14 adjacent steps.
Three focused metric tests pass. The v2 raw-motion report is preserved but
superseded by v3's paired-footprint fields.

The three missing explicit-option preflights (`...control-prepared`, `-v2`,
`-v3`) are retained as pre-launch **FAIL**es; control `-v4` and trial
preflights passed before the two GPU runs. Local paired evidence and a
right-side contact sheet are
`active-nonroads-6305-dense-paired-v1.json` and
`active-nonroads-6305-dense-contact-v1.png` under
`results/diagnostics/world-new-york-20260927-live-1`. The contact sheet is a
visual aid; completed BMPs and reports are the evidence. This interval
does not prove full-course foreground safety, eliminate all pop-in, qualify
physical 4K or validate an attended wheel. Keep active non-road margins
diagnostic.
