# Graphics experiments in the launcher

The user asked why Crack Fill was a regular Display setting and why the tested
World 3x limit was unavailable for manual trials. Source launcher changes:

- Crack Fill moved to Display → Graphics Experiments as **Crack Fill (Shared)**.
  Its existing global preference and ON default are preserved. The hint explains
  that it borrows nearby pixels and can smear them. It does not repair missing
  geometry or texture resources. Margin Fill remains retired.
- World 2.4 now offers **World Draw Distance: Off / 2x / 3x**, and independent
  **Scenery Lookahead: +0 / +8 / +12**. Lookahead is inactive until distance is
  enabled; +8 is the initial trial value. Widescreen and internal scale >1 are
  required. World 2.5 and the other games cannot activate these native hooks.
- Global distance and the older selective Distant Scenery path are mutually
  exclusive. The most recent menu choice turns the other off. Conflicting edited
  INI preferences resolve to global distance. Widescreen Terrain can compose with
  either. Expected-word checks remain mandatory; the CPU stays at 100%.
- Saved options reach ordinary launches and recordings. Explicit recording CLI
  trials override the saved distance without composing two conflicting limits.
  An explicit developer MIDV_PATCH still replaces the configured patch group.
  The launcher log now includes the effective distance, lookahead and Crack Fill.

## Why 3x did not improve the measured mountain

The [controlled Germany investigation](2026-09-07-world-3x-and-release.md) found
an earlier gate: pending objects become active according to track section.
Increasing the far limit does not make inactive scenery available for submission.
At equal lookahead, 2x and 3x first submitted the traced mountain at the same frame,
and all 201 bounded completed GPU images matched. +12 versus +8 lookahead advanced
the submission 56 frames but also changed later replay history. That is evidence
for section activation limiting these mountains, not a universal diagnosis of
every pop-in or proof of 56 frames of extra visible mountain pixels.

The next engine direction remains drawing future static scenery on the host
without activating guest gameplay objects. No new distance algorithm or native
executable was introduced by this menu change.

## Validation and release scope

Code commits: c753f4b (Crack Fill placement), 9ae9231 (distance controls).
All 104 Python tests pass. Tests cover every 2x/3x × +0/+8/+12 combination,
guarded patch composition with terrain/widescreen, resetting the limit to Off,
preference persistence, left/right adjustment, revision/display gates, exclusive
scenery paths, and explicit patch/recording overrides.

Actual native integration used the shared launcher resolver with 3x/+8 and
Widescreen Terrain, then recorded/replayed a separate 2,404-frame prefix from the
preserved extended Germany inputs. All inputs/times, 40 native snapshots and three
completed GPU images repeat exactly. Actual capture size was 512×451 with internal
scale4/CRT, not a new 4K acceptance test. Native CSV verifies far240000, lead8,
CPU100%, profile accepted, 1,022,175 extended projection reads and 378 pending
comparisons. These counters are operations, not visible objects. Physical FFB was
off. This short derived case does not establish original-route or human acceptance.

The 1920×1080 offscreen shell previews were visually inspected: all ten experiment
rows and the selected hints fit. Native remains 5bb965763b1 / SHA256
9d8a8c14998777a15190ca76edd318380baec05e6dac6086d54929dcd2c62a86.
Evidence is retained in results/proof/2026-09-07-graphics-menu.

Restart the source launcher to see these controls through the Stream Deck path.
Saved personal settings were not edited. The overnight 050908 ZIP is preserved
unchanged and predates this UI; shipping the UI requires a newly packaged candidate
with matching source/package acceptance. The earlier complete release suite must
not be relabelled as a full pass for this newer source. No public release was made.
