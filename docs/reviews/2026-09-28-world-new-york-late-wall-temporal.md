# World 2.4 New York: late-wall turn sequence

The [single-frame 6300 check](2026-09-28-world-new-york-late-wall.md)
showed a right-side wall/building continuation over the game's upper panorama.
I used the same saved New York drive to test whether that appearance persists
through the adjacent turn rather than treating one image as a transition pass.

Frozen diagnostic native `f762e01d63b` ran matched control and active
non-road-margin candidate prefixes through 6,340 inputs on the physical
2560×1440 primary, CRT on, literal FFB0. Both raw replay reports **PASS**
original input/native comparison, stable display watch and owned shutdown.
Nine completed 2544×1353 images at frames 6280..6320, every five frames,
were compared. The candidate submitted 334,478 additional quads over the
prefix; that is workload, not visible gain.

All nine completed images differ, with **395,233 changed RGB frame-pixels**
in total. Every change lies in the right third; the center and left thirds
are pixel-exact. Per-frame changed counts are 52,149, 50,513, 50,640,
66,689, 70,605, 19,194, 19,018, 44,703 and 21,722 in chronological
order. The frame-6300 control and candidate BMPs are individually byte-exact
to the earlier one-frame pair. In the inspected contact sheet, the candidate
wall and roadside scenery remain visible through the sampled turn. At 6315
and 6320, the control has conspicuous sky/dark openings at the outer road
edge that the candidate covers. The 6305 appearance changes abruptly in
both modes as the view rounds the turn; this nine-view sample cannot establish
every intermediate frame or a fade.

The loose RGB near-black heuristic counts 90 candidate-new and 23,142
candidate-recovered pixels across the nine frames, but these are review hints,
not exact texture-defect areas. Only frame 6300 has the separate indexed and
original-DMA attribution: its 98,129 replaced original pixels belong to one
upper panorama quad, with no measured unowned-gap fill. This temporal run
does not identify the candidate packets/depth for the other eight frames,
prove foreground safety through the full route, fix the older finish crash,
or qualify 4K, physical wheel output, product deployment or release.

No native code, renderer deployment, personal installation or public release
changed. Local evidence under
`results/diagnostics/world-new-york-20260927-live-1`:
`active-nonroads-6300-temporal-{control,trial}-run/report.json`,
`active-nonroads-6300-temporal-paired-v1.json`, and
`active-nonroads-6300-temporal-contact-v1.png`. Both prepare-only plans passed
before gameplay. The paired report hashes the two raw reports and capture
indexes; the contact sheet is a local visual aid.
