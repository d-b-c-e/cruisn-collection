# Off-Road resident-ground margin trial — September 24

The El Paso sharp-turn blue opening has a promising **opt-in native fix**. The
game has already loaded ground polygons that extend across the missing left
margin, but neither its original draw list nor the existing 3× future-scene
host path submits them. The new candidate verifies a unique allocated object
for each loaded descriptor, accepts only opaque textured ground crossing the
original 4:3 edge, and clips those extra fragments to the widescreen margins.
It does not enable retired Margin Fill or alter the game's framebuffer.

The source-backed offline screens at preparation/display 3116/3120 and
3132/3136 find 28 and 17 eligible margin quads, respectively. **Every** one
matches an allocated object; together they cover all 5,841 and 7,438 strict
indexed gap pixels in isolated GPU screens. The older report versions lacked
the all-candidate allocation count. Current reports are
`left-gap-loaded-ground-screen-v6.json` and
`left-gap-loaded-ground-3136-v6.json` under
`results/diagnostics/offroad-full-20260910`.

The live candidate passes one bounded 3,138-input El Paso replay on the
physical 2560×1440 primary display with `MIDV_FFB=0`, stable display watch,
original input/native snapshots, an original indexed mirror at 3136, and
owned graphics-worker shutdown. The two completed 2544×1353 images at 3120
and 3136 are byte-exact to the earlier passing trial. Their SHA-256 values
are `3fc6bad2…f9de0b6` and `9c5cfbf3…79b23a6d2`; all eight original mirror
plane hashes match the prior source-joined control. Source commit
`03123d5b27202d96045ecdd8f67f16986ff062fb` is frozen as
`build/candidates/03123d5b272/vunit.exe`, SHA-256
`cb6a4697528e27b492f65b023c60dac66a83798fbdbd7465dd1c30f0c484f24a`.
The 280-patch export and binary attestation are in
`resident-native-export.json` and the candidate's `.build.json` file.

The independent Python scene projector was extended to reconstruct the
resident selection and margin pruning from saved RAM/ROM. A standalone native
CLI using the shipped helper produces **exactly the same ordered 876 and 795
quads**, counters and objects on cold and warm caches at source 3116 and
3132. Its ordered quad fingerprints, `bd235ef2e6f97f0d` and
`c2b6df8a213d9853`, also equal the committed candidate's live scene journal
at those frames. This joins the independent source calculation to the live
producer receipt without another game replay. The saved resource captures
come from matching recorded-input runs; the final run did not save a fresh
RAM snapshot. This is exact ordered-scene evidence at two frames, not a
byte-for-byte comparison of every graphics packet in the full course. The
qualified report is `resident-independent-v4.json`. Its v1 failed on a
Python-only synthetic object owner, and v2 failed to locate the CLI's MSYS2
runtime DLLs; both raw reports remain saved.

An additional single 3,142-input trial captured 11 completed frames from
3100 through 3140, every four frames. Compared with the saved 3× control,
each changes 6,192–16,894 pixels, all left of completed x370; the center and
right are exact. The contact sheet shows the blue opening replaced by
continuous ground as it moves through the turn. A simple near-black threshold
finds 1,997 newly dark pixels across those frames, alongside dark pixels
removed by the change. That threshold is a review hint, not evidence of a
texture defect or visual acceptance. The frozen committed binary received
only the focused 3120/3136 replay; the 11-frame run used the same source
before its build-revision string changed. Reports and contact sheet are
`left-gap-resident-final-run/report.json`,
`left-gap-resident-temporal-run/report.json`,
`left-gap-resident-temporal-compare-v1.json`, and
`left-gap-resident-temporal-contact-v1.png` in the same local directory.

A later offline pass applied the common completed-frame triage threshold to
those exact 11 saved pairs. It counts only pixels whose candidate RGB channels
are all at most 8 while a reference channel is at least 32. **Three** pixels
qualify, all within completed `(72,528)..(73,538)` at frame 3140; the other
ten frames have zero. Seven pixels meet the inverse recovered criterion. This
explains why the earlier 1,997 count under a loose `<40` threshold should not
be read as 1,997 new black artifacts. The common checker correctly returns
`passed=false` for all 11 intentionally different images, with no size or
capture-cadence mismatch. Its first invocation pointed at the case directory
instead of its `run` directory and failed before reading images; the corrected
capture-validated result is local `resident-dark-triage-v2.json` (v1 retained).
Neither threshold sees a defect shared by both images or establishes temporal
quality between the eleven samples.

The same 11 pairs now also use the exact CRT-blue signature and fixed left ROI
from the earlier no-host comparison. The new analysis verifies every control
BMP hash and reproduces its saved blue count before comparing the resident
candidate. Control counts span 863–3,903 paired-column pixels; the resident
candidate has 0–16 in those frames. The reduction is positive in all 11,
between 861 and 3,903 paired pixels; frames 3128, 3132, 3136 and 3140 have
zero remaining pixels under this signature. Local
`left-gap-resident-temporal-compare-v3.json` contains the per-frame counts and
source hash for the earlier screen. This is a paired CRT-color heuristic, not
an exact sky/ground area or a guarantee against other texture artifacts.

The committed candidate's source-joined 3136 capture now has a repeatable
indexed-page check, `harness/verify_vunit_resident_gap.py`. It first validates
the passing control's same-run original DMA and backdrop command, both replay
input comparisons and indexed-mirror receipts, and all four original-only
plane hashes across both pages. The original planes are byte-identical between
control and resident candidate. The control has 7,438 strict backdrop-gap
pixels within an 11,649-pixel connected sky envelope. In the candidate, **all
7,438 strict pixels and all 11,649 connected pixels have auxiliary ownership**;
the strict pixels all carry tag 5 and none has index zero. The candidate
changes 24,346 displayed indexed colors and 11,649 ownership tags, with zero
changes inside the native center; all ownership-tag changes are within that
connected envelope. Local `resident-indexed-gap-3136-v2.json` preserves hashes
and counts. The first v1 report passed before an added connected-envelope
equality assertion; both are retained. This is an exact single-frame native
indexed result, not physical 4K, post-CRT, full-course or texture-quality
acceptance. The existing completed-image pair supplies the separate display
view.

The frozen committed binary also completes the **full 9,644-input El Paso
recording** with quiet scene journals, all original input/native comparisons,
stable physical 1440p display watch, literal force zero and owned shutdown.
It prepares 4,249 host scenes / 3,931,158 quads through frame 9642 and drains
the graphics worker at 9643. The sparse capture request yielded completed
frames 4000, 6000 and 8000 (the recorder aligns to its frame modulus), all
at 2544×1353 on visible page 1. A matched 8,002-input control using the same
frozen binary and 3× settings without resident margins also passes. At 4000
the candidate changes 20 pixels in completed x2318–2323, inside the **right**
widescreen margin; the 6000 and 8000 images are byte-exact to control. None
of those three frames changes center pixels. The images show no obvious new
defect on inspection, but three still frames are not whole-course visual
acceptance. The saved reports are `resident-full-elpaso-run/report.json`,
`resident-late-control-run/report.json` and `resident-late-compare-v2.json`.
The first late comparison failed because its predicate required a positive
**left** margin change in every frame; it remains a raw analyzer failure,
not a failed game replay.

Two raw trial failures remain part of the record. Trial v1 clipped every
resident fragment because it reused the disabled legacy Margin Fill width;
an independent resident clip uniform fixed that. Trial v2 rendered the
intended pixels, but its journal verifier omitted resident candidates from
the descriptor partition; trial v3 fixed the accounting. A project-regeneration
build attempt also failed on an existing raw-string generator issue; normal
incremental compilation and linking succeeded. None of these failed reports
has been relabeled a pass.

The live candidate completes one recorded El Paso course at physical 1440p;
its detailed visual gain is demonstrated for the sharp turn. It does not
qualify other Off-Road courses, 4K, physical wheel/force feedback, menu
integration, or the analogous behavior in USA and World. The candidate stays
diagnostic only; the personal UX707 executable, public v0.5.0, launcher
settings and default force profile remain unchanged. A second route and 4K
completed-image review are the next visual gates before considering product
promotion. A detailed live packet comparison over a second route would
strengthen the harness before broadening the policy.
