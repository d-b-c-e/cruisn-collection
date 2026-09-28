# USA Golden Gate: 3× bridge appearance and original sky panel

The saved Golden Gate continuation exposes two different rendering issues at
completed frame 10500. In matched 3824×2073 CRT images from the same frozen
binary, ordinary and continuous 3× both display a dark rectangular panel in
the right sky. The 3× image additionally shows a distant red bridge structure
at the far left. It looks skeletal in this view; the later frame 12000 has the
full nearby bridge in both modes. Earlier visibility counts were therefore a
real distance gain, but not sufficient evidence of better appearance throughout
the approach.

The 4K control and 3× run both passed 12,212 recorded input/time frames, native
images, camera/ADC traces and owned shutdown in the September 16 qualification.
At frame 10500, a fixed right-panel ROI `(2995,525)..(3245,1045)` has **zero**
changed completed RGB pixels. A separate left-bridge ROI
`(150,700)..(550,1120)` has **29,470** changed pixels (65,207 across the whole
image). These are ROI counts, not exact object masks.

To check ownership, a bounded frozen `f762e01d63b` replay captured the same
source frame at physical 1440p with literal `MIDV_FFB=0`, an original-only
indexed mirror and the original DMA. MAME returned zero, recorded 10,502
frames, captured one completed image and stopped its worker. The original raw
replay report is **FAIL**: the USA host analyzer incorrectly rejected two
strictly timed page scenes within frame 8015. Its frame check has been fixed to
allow equal frame numbers while still requiring unique scene keys and strictly
increasing emulated times. The focused ten-test USA suite passes. A separate
posthoc report passes 5,481 ordered host scenes, input/time and native image
comparison (zero mismatches), display watch, original mirror and owned stop.
The raw failure remains intact; posthoc qualification does not turn it into a
successful full replay report.

The right panel maps to **original DMA ordinal 2233**, an untextured,
dithered rectangle at native `(460,100)..(500,200)`, palette pen 8. An
independent GPU reconstruction identifies 33,000 final indexed pixels of this
quad at fine `(2184,796)..(2347,1199)`. Every one matches both the combined
and original-only captured indices and tags; none has auxiliary ownership.
This is an original game quad, already in the ordinary 4K image. Its purpose
and the correct user-facing treatment remain open; suppressing it based on
this one frame could erase an intentional HUD effect. By contrast, three
sampled red bridge pixels in the 1440p candidate carry auxiliary tag 5 over
original sky/tag 1. The 3× experiment is drawing that distant structure
earlier, while its completeness and transition quality need a targeted gate.

Local source-hashed evidence:
`results/diagnostics/race-transitions-20260916/usa-golden-gate-panel-run/report.json`
(raw FAIL), `posthoc-qualification-v1.json`, `panel-source-screen-v1.json`,
and the frozen 4K control/3× `mvgl_007.bmp` images in `usa-menu-tail-v1/case/record`
and `usa-menu-tail-3x/run`. The source replay uses a newer frozen diagnostic
binary and a physical 1440p display; its ownership check is one scene, while
the matched 4K images establish the panel's unchanged appearance. Neither
resolves whether the panel is intentional, nor proves smooth bridge fade or
release-ready 3× quality. No renderer, personal installation or release was
changed.

Next bounded gate: inspect the saved Golden Gate interval where the bridge
first becomes visible and identify which original/auxiliary fragments appear
before a product rule is considered. Do not treat the left ROI's changed count
as a quality pass. The panel is a separate, source-owned visual issue.
