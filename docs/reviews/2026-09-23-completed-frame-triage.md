# Completed-frame visual triage across distance candidates

`harness/gl_frames.py --details` now reports candidate-new and recovered
near-black pixels, the bounds of candidate-new near-black pixels, and changed
pixel counts in a 3×3 screen grid. It still requires completed-frame fence,
dimension and requested-cadence receipts. Intended scenery changes still make
the exact comparison return `passed=false`; the extra fields are **review
hints**, never automatic visual acceptance. A pixel is candidate-new near-black
only if all its candidate RGB channels are at most 8 and at least one reference
channel is at least 32. This excludes small changes among dark tones, but dark
authored scenery can still be flagged. A defect shared by both images is unseen.

Focused completed-capture tests pass, including a two-pixel fixture with one
new and one recovered black pixel while exact comparison remains false. I ran
the updated checker on saved, receipt-validated pairs without launching games:

| Saved pair | Frames | Different | New near-black | Spatial finding |
| --- | ---: | ---: | ---: | --- |
| Exotica Mars 2×→3×, original 4K | 15 | 4 | 0 | All 985 changed pixels in middle-left third; useful outer-scenery addition. |
| World 2.5 Hawaii far-bound correction, 3424×1353 | 12 | 4 | 237 | Changes lie in the middle row; frame5900 has 115 dark pixels within the distant terrain area. |
| Off-Road El Paso 2×→3×, completed 3824×2073 | 66 | 22 | 1,397 | Frame6720 has 375 new dark pixels among 7,734 changes ahead of the car. |

World and Off-Road dark counts are **not** diagnosed black-texture regressions.
The saved World frame shows textured distant terrain, and the sampled Off-Road
frame shows additional distant scenery beyond the building. The checker tells
us exactly where to review; source/motion and adjacent-frame checks still decide
whether an artifact is real. The Exotica count corroborates the earlier narrow
zero-new-black finding without expanding its route acceptance.

Local reports are `mars-appearance-dark-triage.json` under
`results/diagnostics/exotica-open-course-20260916`,
`far-bounds-dark-triage.json` under
`results/diagnostics/world25-roads-20260914`, and
`final-frontier-dark-triage.json` under
`results/diagnostics/offroad-full-20260910`. They preserve requested capture
schedules and source paths. No renderer, installed executable, settings or
release was changed.
