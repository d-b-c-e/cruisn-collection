# Exotica Mars: a small visible third-band gain

The same frozen5c candidate now demonstrates a visible3x gain over2x on Mars.
At frame5200, the completed3840x2160 CRT images differ by509 pixels in the far
left scenery, bounds(35,1066)-(127,1115). There are zero new near-black pixels
and the fixed car region is exact. The other12 sampled images are identical.
This is a small gain in one short sample, not elimination of pop-in or release
parity across Exotica's courses.

## Sample and matched comparison

A short scripted menu sweep establishes that selection follows absolute wheel
position: quarter-turn selects Korea, centering returns to Hong Kong. The next
half-turn scout selects Mars, confirmed by its displayed name at frame3000 in
the candidate capture. Held accelerator selects automatic transmission and
drives briefly without steering. The5200 picture shows elapsed0:09.19,71MPH,
third gear. This is synthetic input, not an attended or complete race.

Both2x and3x replays preserve all5500 recorded input/time rows. The sole semantic
environment change is the multiplier; paths are separately redirected. At4800
and5200, saved game RAM, WaveRAM, active ready/end resources and original control
quads match. Both completed original color/depth targets also match. Native
CPU images are blank with this Zeus path and are explicitly not a visual oracle.
There is no per-frame camera/ADC comparison in these new scouting runs.

Both candidates complete4064scenes and2580marked endpoint preparations with
zero rejection. Their owned shutdowns drain and join. No physical FFB or product
deployment occurred. Sparse snapshots do not qualify continuous appearance or
cost; no performance conclusion is drawn from these instrumented runs.

At4800 there are no third-band polygons. At5200 there are2286, from319future
instances. This passes the existing sample-selection gate before an additional
multiplier comparison. Against completed depth,680 internal pixels remain;
the actual matched display comparison above then confirms509 changed pixels.
These different counts describe different stages, not conflicting measurements.

## Reusable source-fragment diagnostic

`harness/exotica_fragment_sources.py` renders a saved insertion with an auxiliary
integer target identifying the last surviving quad. Color, depth, materials,
discard and command order remain intact. It first requires the entire saved
insertion's color/depth bytes to match exactly, then optionally screens a chosen
distance band against completed depth. Source identity includes both entry and
source address. It does not assume that the last fragment is the only contributor
to a blended pixel.

The canonical Mars5200 run reproduces the full insertion exactly, then the same
680-pixel conservative mask as the independent earlier screen. It identifies
19source objects;672pixels have nonblended last fragments and8have a blended last
fragment. The largest source contributes246pixels at sphere distance569678,
between the4096002x and6144003x limits. Do not flatten intrinsic blending to
implement an appearance fade. Two focused negative/ownership tests pass.

The scenario is retained as `fixtures/scenarios/exotica-mars-sightline.json`.
`synthesize_input.py --record-only` now avoids an automatic duplicate scout;
its report explicitly withholds identity/visual acceptance. Sparse `--gl-every`
uses global native frame alignment. Seven focused scenario tests pass.

## Retained unsuccessful attempts

- The first menu setup omitted the manifest argument and failed before launch.
- The scout's original image checker assumed cadence began at3060; native400
  cadence produced3200..5200. The six valid frames were retained without rerun.
- The first offline depth screen assumed the old2736-wide internal buffer;
  the current4K geometry uses2752. The saved-data correction retains the failure.
- Recursive object removal stopped at its64-render bound because removing
  occluders exposed other objects. It is not an ownership proof. The integer
  attachment avoids that ambiguity and needs two offline renders.
- A local projected-bounds draft mislabeled descriptor word17 as alpha. Its
  corrected draft removes that field; no RPM/opacity policy relies on it.

Next inspect the brief appearance interval around5200 and trace these sources
through visibility and handover. No new appearance policy is enabled. Retain
Amazon for its independent margins/collision/transparent-geometry coverage.

Local evidence is under `results/diagnostics/exotica-open-course-20260916`:
`menu-sweep-v2`, `open-course-probe`, `open-course-3x`, `open-course-2x`,
`open-course-band-selection.json`, `mars-multiplier-qualified.json`,
`third-band-completed-depth-v2`, and `mars-fragments-canonical`.
The equality-only completed-image subreport correctly saysfalse for5200;
the enclosing qualification reports the intended visual difference explicitly.

## Follow-up appearance samples

One matched pair samples5060..5340 every20frames, adding independent camera/ADC
traces and saved source/target snapshots at5100,5200,5300. Both preserve5500inputs,
all3700camera words and11100actual ADC reads/times over1800..5499. All30selected
original game/resource/quad/color/depth files match. Both again complete4064scenes,
2580marked preparations with zero rejection, and joined shutdown.

Of15completed4Kimages, four differ:5200by509pixels,5240by314,5260by146 and5280by16.
All four have zero new near-black pixels and identical fixed car regions. The
other11images are exact, including5220. This sampling does not establish smooth
continuous visibility; the equal5220sample must not be omitted from that account.

At5300,1961third-band polygons remain, but the checked full insertion and
completed-depth screen yield zero visible colored fragments, consistent with
the matching final images. The visible difference ending is therefore not proof
of a failed fade or missing3x geometry. A global opacity change is not justified
by these samples alone. The source decoder already enumerates the complete track
until its checked sentinel, with a128-section bound; it is not limited to just
the next few sections. Unsupported custom model handlers/classes remain a
separate coverage question.

Evidence: `mars-appearance-2x`, `mars-appearance-3x`,
`mars-appearance-qualified.json`, `mars-appearance-bands.json`, and
`mars5300-fragments`. The raw equality-only image report remainsfalse for the
four intended differences. No new game build or default-suite rerun was needed.
