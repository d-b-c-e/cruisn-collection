# World3x across race selection and a new race

Continuous quiet host scenery completes the recorded Germany drive and a
scripted continuation through race selection into a new coastal race. This
closes another finite-recording coverage gap; it does not establish all-course
quality, elimination of pop-in or a complete second race.

The control uses frozen native1a1b7e0ff6b and ordinary rendering. The original
9,269 input/time frames are preserved exactly and3,400 scripted frames appended.
The same native candidate then replays all12,669 with continuous3x scenery,
quiet journals and the old finite reference end unchanged. Physical FFB is0.

## Results

- All12,669 input/time frames and original native images match the new control.
  All10,869 camera samples and32,607 actual ADC reads/timestamps match through
 12668. The synthetic continuation is explicitly labeled, not attended driving.
- The renderer prepares5,497 scenes/13,049,354 quads; geometry aggregate is
  `daee844730b83e55`. Last preparation12667 and presentation12668 exceed the old
  reference end. The owned graphics worker drains8,767,675,336 ring bytes and
  joins without pending work, stream/GL errors or degraded preparation.
- Thirteen completed3824x2073 CRT client images on the3840x2160 primary display
  cover9000..12600 every300 frames. Ten are exact. Frame9600 shows race selection;
  later frames show active driving in a new coastal course.
- Changed frames11700/12000/12600 contain1,551/80,336/3,739 differing pixels.
  At12000, inspected beside the control, extra gray distant terrain is visible
  along the horizon behind the truck.11700 and12600 were also inspected; the
  foreground car, road and HUD appear intact. All differences are above y1250,
  preserving the full lower foreground region exactly.
- Newly dark pixels are0/164/18 respectively. The latter counts fall within the
  changed distant region and remain in the report. They are not dismissed as
  zero or automatically classified as missing textures.

The images are sparsely sampled. They cannot establish continuous appearance
quality, assert useful3x over2x visibility, or rule out a brief intervening
artifact. The candidate is compared with ordinary rendering here, not2x.
The known authored terrain gap and New York reproduction remain separate work.

Local evidence: `results/diagnostics/race-transitions-20260916/` contains
`world24-menu-tail-v1/case`, its prefix qualification, `world24-menu-tail-3x`,
and `world24-menu-tail-3x-qualified.json`. A local candidate-script syntax error
was corrected before emulator launch; no game was repeated to repair analysis.
No native code changed for this qualification. Personal installation and public
v0.5.0 remain unchanged. Next apply this transition scope to Off-Road.
