# USA3x through Continue and a Golden Gate restart

The original USA case ends5,012 frames into the session with54 seconds remaining
on its race timer. A7,200-frame scripted tail waits for timeout, selects Continue
and restarts Golden Gate Park. This creates a12,212-input control, preserving
every original effective input and timestamp. The new reusable continuation
command performs the actual MAME recording, with explicit400-line height,4x,
CRT on, primary4K display and a copied/fingerprinted USA motion probe.

The same frozen nativef0b4db1f25d then replays the new case with continuous quiet3x
host scenery. The old finite scene reference3500..3600 remains unchanged:

- All12,212 input/time frames and native images compare successfully.
  All10,412 camera records and31,236 actual ADC reads/timestamps match through
 12211. This tail is scripted, not a second attended drive.
- All6,336 prepared scenes/14,903,983 quads complete without degradation. Ordered
  geometry aggregate is `a841407f7265d374`. Last preparation12209 and presentation
 12211 retain legitimate no-scene frames. The owned worker drains8,967,470,040
  ring bytes, joins, and reports no outstanding work or stream/GL error.
- The comparison first checks identical native height400, scale4, CRT1 and
  margin86. Thirteen completed3824x2073 client images cover8400..12000 every300.
  The two menu images8400/8700 are exact; the eleven gameplay images change.
  All changes remain above y1142, preserving the lower car/foreground exactly.
- Viewed8400 is the Continue screen;9000 explicitly labels Golden Gate Park at
  the race start;12000 reaches the bridge at in-game0:54.41. The latter pair shows
  additional distant bridge/roadside geometry. At9000 a small region between the
  start letters changes; both detailed crops are retained for inspection.
  Newly dark pixels are reported, ranging2..2,530 in changed frames, not silently
  treated as zero or automatically identified as missing-texture defects.

This adds restart/continuous-runtime coverage across all four game families,
including a longer second-race segment for USA. It is not a complete second race,
all-track or continuous temporal acceptance. Sparse pictures do not establish
elimination of pop-in or every overlay/painter-order case.

Local evidence under `results/diagnostics/race-transitions-20260916`:
`usa-menu-tail-v1`, `usa-menu-tail-3x`, `usa-menu-tail-3x-qualified.json` and the
start-detail crops. No new native code was needed for this qualification.
Personal Stream Deck copy/publicv0.5.0 remain unchanged; physical FFB and hosted
CI stayed off.
