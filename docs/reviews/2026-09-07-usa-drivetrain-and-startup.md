# USA drivetrain, experiment contexts, and World startup — 2026-09-07

USA v4.5 has a usable internal rev signal and actual gear. The earlier conclusion
that RPM was unavailable was too broad: the old E632 interpretation was wrong,
but that did not establish that a different rev producer was absent.

## The internal source

The read-only palette probe led to the game's tachometer update routine. C31
addresses below are **word addresses**, scoped to USA v4.5 (`crusnusa`):

| Producer | Evidence |
| --- | --- |
| Player pointer | RAM E8A8; observed DE76 in the recorded drive |
| Actual gear | player +38, read by gear glyph code at 9D86..9D89 and palette code at 9E6A..9E75 |
| Rev signal | player +39, C31 floating point, read at 9E54 |
| Tach fill | 9E55 multiplies revs by 0.458251953125; the following code clamps to 0..22 and blanks unused palette entries |
| Simulation/sound connection | 2C4C..2C9B computes/stores this rev field using throttle/speed/gear; one path caps at 47; sound pitch also uses it |

This is stronger than a correlation with a changing RAM address. The code that
presents the player's gear and colored tachometer reads these fields. We followed
that consumer backward and independently sampled the structure in the original
executable before implementing the native reader. The original recording remains
unchanged. E632 remains the packed decimal speed buffer, never RPM.

`native/hud_drivetrain.h` is canonical and synced into MAME. It checks five exact
instructions, the pointer bounds, gear 0..4 and finite bounded revs. Native output
also requires recent numeric HUD submissions and the exact USA revision. It reads
backing RAM without taps or writes in the product path. Other ROMs never enter
this adapter; the helper's C31 decoder correctly treats 80000000 as zero and
00000000 as one. Do not replace it with IEEE float decoding.

For the requested arcade experience, continuous tach fill maps to
`900 + 7100 * clamp(revs * 0.458251953125 / 22, 0, 1)` RPM. These are chosen display
units, not calibrated engine revolutions/minute. The source rev value is real game
state. Gear telemetry now follows automatic shifts instead of the unchanged
shifter input. Neutral/unknown stays zero in JSON; the existing Forza fallback
maps it to first. JSON/CSV identify the RPM estimate and its source. A missing HUD
clears RPM. USA's Forza gauge limits and the launcher keepalive use 8000/900;
current RPM is zero in menus. `MIDV_TELEM_ARCADE_RPM=0` disables the estimated scale
while preserving the real gear producer.

## Verification

Final native commit: `bf8821358d4afb0b3e776c64c0c6d5be1f309218`.
Final executable SHA256: `4d63433b45f492ae7dd6f982c0aca92afdf7d12283d19ee194bf5ec95e55fee4`.
The 118-patch export reconstructs tree `895aabd69d1efcbab19d63039157c076c4396b2e` exactly.

| Check | Result |
| --- | --- |
| Original USA drive, final binary | 5,012 inputs/times and 83 native images match |
| Independent RAM probe vs native producer | All 2,483 active samples match, including player pointer, gear and rev |
| Actual UDP, original drive | 5,012 Forza packets; JSON gear/RPM fields agree across 76,613 packets |
| Independent synthetic USA drive | 6,000 inputs/times and 100 native images match; 6,000 Forza / 90,509 JSON packets validate |
| Shift behavior | All five original-drive and seven independent-drive upshifts have RPM drops within eight frames |
| RPM disabled control | 3,040-frame replay passes; all RPM values zero; gear still exercises 1..4; both UDP formats validate |
| Seven-game regression suite | All pass on the initial telemetry implementation, binary 82203f8f; includes 21 completed Exotica GL references |
| Final-build coverage after gauge-limit adjustment | Both USA drives, disabled control and World scale cycle; the seven-game suite was not silently relabeled as this later binary |
| Hardware-free checks | 108 Python tests and the native drivetrain helper pass; CI34158937631 passed all four jobs before the final analyzer rounding test |

Example: the first 1→2 upshift at native frame 2715 drops estimated RPM from
7205.685 to 4735.147. The corresponding raw game rev changes from about 42.638 to
25.932. Lua's callback labels the same sample frame 2716; the analyzer records
this explicit one-frame numbering conversion. This is not an alignment search.

World 2.4/2.5 and Off Road traces contain no USA game-state samples and no nonzero
RPM, confirming the adapter does not activate there. Exotica uses its separate
path. This work does not establish a new RPM or automatic-gear source for those
games, nor attended dashboard or physical FFB acceptance. No physical force ran
in these checks. An attended USA manual-transmission drive is a useful follow-up;
the current two validated drives exercise automatic shifting.

The first palette probe produced malformed rows because MAME swallowed a tap
callback assertion about the on-chip stack. Its replay PASS described input/pixel
identity, not valid probe output. That run is retained locally and not used as
provenance. The corrected probe rethrows captured tap exceptions on the next frame
callback. A subsequent complete independent memory trace is the reference above.
The packet analyzer also handles CSV decimal rounding: a Forza float of
5675.49951171875 is formatted as 5675.500 in the CSV but correctly sent as integer
5675 in JSON. The test compares against the full-precision wire float.

## Experiment contexts

Shared contains Crack Fill, which still affects only the V-Unit games. USA shows
its supported seams/detail/draw-limit options; World shows only options supported
by its selected revision (global 2x/3x and scenery remain 2.4-only); Off Road shows
its seam option. Exotica has no experiments yet and says so. Hidden settings are
preserved rather than erased. Defaults and the user's saved graphics/force values
were not changed. Six menu previews were inspected, including World 2.5.

## World startup report

The user's screenshot shows MAME's cabinet artwork and lamp panel, indicating
that the replacement presentation was not covering the underlying MAME view.
It does **not** establish that the scale was initialized incorrectly. The failed
World launch log had already been overwritten by a later USA launch; the ordinary
GL log was stale. The reported configuration itself contained a valid scale 4.

The launcher now requests `Screen 0` for every game, so fallback presentation
cannot expose that cabinet panel. Normal launches enable the modest GL logs and
archive the preceding launch's logs/receipt before overwriting them. History is
bounded to eight launches with two-MiB tails per log, with original modification
times and truncation recorded. Support bundles include that history. This makes
the next occurrence diagnosable; it does not claim to repair an unidentified
renderer failure. Startup termination also clears force effects using the
existing cleanup helper if a hung process had to be terminated.

Three final-binary World boots at **4x → 3x → 4x**, CRT on, each pass 1,804 frames
and 30 native-image comparisons. All nine requested completed GL images exist at
3824×2073, with zero dropped messages. The repeated 4x captures match exactly.
The first occurrence of each scale is a reference capture, not an independent
repeat. These are renderer startup checks from the recorded state, not proof of
all launcher configuration paths or artifact-free gameplay. The reported failure
was not reproduced. No shader, draw-distance, crack-fill algorithm, or ROM
rendering patch was changed in this work.

## Evidence and deployment

`results/proof/2026-09-07-usa-drivetrain/evidence.zip` contains 50 checked entries:
reports, native export verification, menu previews, the reported screenshot,
independent RAM samples, actual packet captures and scale-cycle receipts. Its
`files.json` hashes every evidence entry. ROM/program dumps and binaries are not
included. Full local runs are under `results/diagnostics/usa-drivetrain-*`,
`world-scale-cycle-20260907`, and `world-startup-user-20260907`.

The Stream Deck wrapper still launches `harness/collection.py` in this checkout;
`run_rig.VUNIT` resolves to `E:/Source/mame-src/vunit.exe`, now the final binary
above. Restart the launcher to load the menu/keepalive changes. The overnight
release ZIP remains unchanged and predates these fixes. A public release needs
new packaging and the remaining attended release checks.

Next telemetry work should trace the other games' own HUD/engine consumers with
the same method. The newly identified USA player pointer also makes player+26 a
specific speed-source candidate from the engine calculation, but its units have
not been validated against MPH; do not promote that candidate by assumption.
