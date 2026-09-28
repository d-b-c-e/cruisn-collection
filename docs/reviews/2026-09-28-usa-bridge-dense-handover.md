# USA Golden Gate: one-frame bridge handover around 10478

The [source timing check](2026-09-28-usa-bridge-member-timing.md) found the
first ordinary auxiliary submission of bridge object `0x800a0040` at source
frame 10475. The prior completed interval was four frames apart, leaving the
visible handover unclear. A matched control/partial-coverage pair now captures
every completed frame 10468..10484 on the saved drive.

Frozen diagnostic native `f762e01d63b` replayed 10,488 inputs in each mode,
continuous 3×, CRT on, physical 2560×1440, literal FFB0. Both raw reports
**PASS** recorded input/native comparison, display watch and owned worker
shutdown. The only scenery option difference is USA partial far coverage
off/on. The new reusable `harness/compare_usa_farcoverage_course.py` checks
case/binary/display/presentation, exact recorded frame clocks, mode delta,
all completed images, center/right preservation and source hashes. Its
`usa-bridge-10475-dense-paired-v1.json` **PASS**es 17 images; all differ only
in the far-left third. There are 92,614 accumulated changed frame-pixels,
which are not a unique bridge area or quality score.

The completed 10476 control and candidate BMPs are each byte-exact to their
previous indexed-mirror/source-attributed counterparts. The reviewed
right-left crop shows the candidate's main red tower present at 10476 while
the control has only the lower piece and scattered distant red fragments.
At **10478**, the control draws the main tower and the candidate keeps it.
The between-mode difference footprint contracts from 7,627 to 2,504 pixels:
5,169 previously different locations become equal and 46 new differences
appear. Through 10484 the candidate and control both retain the main tower;
their small remaining far-left differences total 2,505–2,616 pixels per
sample. This is a visually continuous *main-tower* handover in this short
interval, not proof that every bridge member or distant piece fades smoothly.

The one-frame RGB pair changes roughly every two completed frames, so the
10475 source submission should not be equated mechanically with a completed
10475 appearance. The existing exact source/pixel attribution is at 10476;
the 10478 control appearance is observed in completed pixels, not joined to
an exact 10478 original-DMA/auxiliary packet trace. The scattered distant
red elements below and to the right of the main tower remain a visible
composition question in both modes. This check cannot establish a complete
bridge silhouette, another course, physical 4K appearance, GPU pacing or
release safety. Partial coverage remains opt-in.

The generic exact-image comparator correctly returns **FAIL** for 17
intentional differences; its raw `usa-bridge-10475-dense-gl-v1.json` is
retained separately from the passing paired qualifier. The source-hashed
`usa-bridge-10475-dense-steps-v1.json` measures 16 adjacent difference-mask
turnovers. The local aspect-preserving visual aid is
`usa-bridge-10475-dense-contact-v2.png`; v1 is retained but has a distorted
crop and must not be used to judge appearance. Both preflights were prepared
successfully before GPU runs. No native code, renderer deployment, personal
installation or public release changed.
