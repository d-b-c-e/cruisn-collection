# Off-Road El Paso: sharp-turn left margin opening

The existing attended El Paso recording has a sustained large steering input
at frames 3051–3195. At completed frame 3120 (race time about 0:12.90), both
the saved ordinary 4K render and the saved 3× render show a blue opening below
the far-left terrain. The 3× render adds distant hillside but does not close
that opening. This is a concrete reproduction of the left-margin coverage
class the owner reported; the two saved images alone do not establish whether
all reported black patches have the same source.

I replayed only the first 3,200 inputs of that recording with the current
frozen diagnostic native `0068ac85867`, explicit capture-mode continuous 3×,
CRT 4×, physical FFB disabled, and one completed frame at 3120 on the stable
2560×1440 primary display. Input/time and native-image comparisons pass with
zero mismatches; the display watch saw no topology change. The completed
2544×1353 image again shows the opening. The indexed mirror at frame 3120
passes its receipt checks and identifies visible page 1. Its extended/ordinary
mask difference marks 32,066 host pixels, all at internal x=0..297 and
bottom-up y=971..1205; the remaining opening still shows the background.
Those bounds identify where this host contribution lands, **not** an exact
pixel attribution for every part of the displayed wedge.

The first attempt selected the continuous 3× preset and an original indexed
mirror together. That preset forces quiet journals, which the native mirror
explicitly forbids. It failed immediately with `Invalid V-Unit journal policy`
before gameplay; raw report `left-gap-3120-run/report.json` is retained. The
launcher now rejects this combination during preparation with a precise error.
The passing run uses explicit capture-mode controls. Fifteen focused original
mirror/runtime tests pass. The preflight rejection is retained at
`left-gap-3120-quiet-rejected/report.json`; the passing evidence is at
`left-gap-3120-capture-run/report.json`, all under
`results/diagnostics/offroad-full-20260910`.

No source-level terrain fix is accepted yet. The next bounded investigation
should join the displayed scene to original and host quad/source ownership at
the missing edge, then test a local coverage hypothesis against adjacent
frames. Extending the far limit alone has already failed to close this sample.
The older 4K captures preserve the visual comparison; this new 1440p run is a
separate diagnostic and does not replace final 4K acceptance. No installed
binary or public release changed.
