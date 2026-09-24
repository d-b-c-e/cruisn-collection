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

Two raw trial failures remain part of the record. Trial v1 clipped every
resident fragment because it reused the disabled legacy Margin Fill width;
an independent resident clip uniform fixed that. Trial v2 rendered the
intended pixels, but its journal verifier omitted resident candidates from
the descriptor partition; trial v3 fixed the accounting. A project-regeneration
build attempt also failed on an existing raw-string generator issue; normal
incremental compilation and linking succeeded. None of these failed reports
has been relabeled a pass.

This result is limited to one recorded El Paso turn at physical 1440p. It does
not qualify other Off-Road courses, 4K, physical wheel/force feedback, menu
integration, or the analogous behavior in USA and World. The candidate stays
diagnostic only; the personal UX707 executable, public v0.5.0, launcher
settings and default force profile remain unchanged. A second route and 4K
completed-image review are the next visual gates before considering product
promotion. Independent host-packet reconstruction for the new resident class
would strengthen the harness before broadening the policy.
