# Off-Road left opening: loaded ground source screen

The El Paso left-margin opening has a stronger source explanation than a
missing future section or a texture that needs copying. In two saved turns,
ordinary section descriptors already loaded by the game project ground into
the blue opening, but those polygons appear in neither the game's captured
original DMA list nor the existing 3× future-scene host list. This is an
**offline source screen**. A subsequent gated live trial is documented in
[the resident-margin review](2026-09-24-offroad-resident-margin-trial.md); it
is not product acceptance.

At source 3116/display 3120, the original near-ground DMA quad 66 matches all
16 reconstructed words from loaded section 9, source `0xec31ed`. A neighboring
loaded source `0xec320e` shares that quad's projected edge exactly. It has the
same ground material (mode `0x100`, palette 18688, texture 10513), matches a
unique allocated RAM object, and is absent from both the 499 original DMA quads
and all 708 existing host packets. Isolated rendering of that one quad covers
5,550 of the 5,841 strict gap pixels. There are 28 loaded, unsubmitted quads
projecting into the left margin in this saved scene. All 28 match allocated
objects; together they cover all
5,841 strict gap pixels and 7,330 ordinary-sky indexed pixels. The existing
708-packet host reconstruction remains byte-exact.

The opening grows later in the same turn. A new bounded resource replay at
source 3132 passes the 3,138-input recorded prefix, original native snapshots,
stable physical 2560×1440 monitor watch, literal `MIDV_FFB=0`, and owned
shutdown. The separately captured source 3132/display 3136 is already joined
to an exact completed image and original DMA list. Reconstructing from the new
RAM matches all 689 host packets. Here 17 loaded, unsubmitted quads enter the
left margin; their isolated GPU draw covers all 7,438 strict gap pixels and
11,649 ordinary-sky indexed pixels. Four nearby ground polygons from loaded
sources `0xec3219`, `0xec31f8` and `0xec323a` use palette 27136/texture 13990.
All 17 eligible margin quads match allocated RAM objects. The earlier
`0xec320e` quad is
already in a draw list at this point, so a policy targeting only that one source
would fail as the gap moves.

The sky-only offline contact previews show a coherent continuation of the
orange terrain in both frames, without the repeated bands from the rejected
pen-copy fill. This visual check is deliberately narrower than a live fix:
the isolated candidate is composited only where the saved original indexed
frame says sky. A native path must preserve original draw order, depth and
material ownership, clip or mask additions outside the affected margin, and
avoid duplicating geometry the game already drew. The offline palette resolve
differs from the saved completed BMP by more than one channel unit at 121 of
3,442,032 pixels at 3120 and 120 at 3136. Therefore neither preview is an
exact completed-image prediction. The later live trial checks motion across
11 views, but broad course behavior remains unchecked.

The gated current-resident ground path now passes its El Paso trial; see the
linked review for exact completed-pixel and shutdown evidence. At least one
other route and 4K visual acceptance remain before promotion. Simply drawing
all loaded geometry would duplicate many original polygons and is not
supported by this evidence. The analogous resident-source question in USA and
World is worth screening, but no cross-game policy is justified yet.

Evidence is local under `results/diagnostics/offroad-full-20260910`:
`left-gap-loaded-ground-screen-v6.json`,
`left-gap-loaded-ground-3136-v6.json`,
`left-gap-loaded-ground-visual-v2/comparison-crop.png`,
`left-gap-loaded-ground-3136-visual-v1/comparison-crop.png`, and
`left-gap-resource-3132-run/report.json`. The first 3120 screen report `v1`
incorrectly flipped the bottom-up GL readback and reported zero overlap; it is
retained as a failed analysis. `v2` corrected orientation, `v3` added the
single-source preview, and `v4` added the all-left comparison. The 3136 `v1`
is the source screen, `v2` adds per-source contributions, `v3` adds a preview,
and `v4` verifies nearby allocated objects. `v5`/`v6` restrict the screen to
loaded descriptors and check all eligible allocated margin quads. Source and material hashes are in the
reports. `harness/offroad_gap_loaded_screen.py` and
`harness/offroad_gap_loaded_temporal.py` reproduce them from saved evidence.
The subsequent native trial changed source, while the installed game, force
setting, launcher and release remain unchanged.
