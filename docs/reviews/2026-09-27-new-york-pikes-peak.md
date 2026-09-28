# New York and Pike's Peak recorded drives — September 27

The maintainer recorded a World 2.4 New York drive and an Off-Road Pike's Peak
drive on the physical 2560×1440 primary monitor. Both used the frozen native
`03123d5b272` candidate, continuous 3× scenery, CRT4×, an external recording
clock and literal `MIDV_FFB=0`. The recordings and all large captures are local
under `results/diagnostics/world-new-york-20260927-live-1` and
`results/diagnostics/offroad-pikes-peak-20260927-live-1`; they are not product
assets. The installed personal UX707 and public v0.5.0 are unchanged.

## World 2.4 New York

The attended recording passes 9,695 inputs with 3,931 prepared host scenes,
19,767,760 submitted quads and owned shutdown. It reaches the New York finish
(the captured game result shows 2:07.76); it **does not reproduce** the earlier
reported finish-line crash. This does not establish whether the prior crash was
intermittent or specific to the old 3×/+12 guest settings. The maintainer
reported missing textures on both far margins during this drive.

A bounded 9,302-input replay of the same recording preserves original
input/time and native images, stable display topology, and owned shutdown. It
captures 25 completed 2544×1353 frames every 300 frames from 2100 through
9300. The images show black outer wedges at several locations, including a
large right wedge at completed frame 3600 and wedges on both sides at 6000.
The latter replay is a visual survey, not a defect-area measurement; simple
dark-color counts also include authored dark scenery and the CRT mask.

At completed frame 3600, a separate exact source capture joins visible page 0
to preparation frame 3596 and 2,452 host packets. The completed BMP is
byte-identical to the earlier survey. Full original DMA and four indexed
planes are captured from the same input and emulator. A four-connected
24,769-pixel region inside indexed right-margin ROI `(2402,634)..(2735,763)`
has **index zero and ownership tag zero in both extended and original planes**.
At sampled fine `(2600,700)` and `(2700,700)`, neither an original command nor
a host packet projects over the tight `(2598,698)..(2602,702)` probe; nearby
original sky ends above it and ground begins below it in native coordinates.
The exact zero ownership and conservative projected bounds make this sampled
black wedge a draw-coverage gap, not a failed texture read. They do not prove
that every New York artifact shares that cause, or that a generic skirt/fill
is safe. The older Hawaii skirt trial produced a worse visible wall, so a
source-qualified ground candidate is the next plausible experiment.

The more representative completed frame 6000 has visible black wedges on
**both** margins. Its source-joined replay passes the same original comparisons
and produces a completed BMP byte-identical to the survey (SHA-256
`5e2d604b…99c2826`). Visible page 0 joins to preparation 5997 and 10,555
host packets. An exact zero-index/zero-tag four-connected screen, clipped to
the sampled margin regions, finds 8,117 pixels on the left (fine bounds
`(0,470)..(169,538)`) and 11,651 on the right (`(2563,470)..(2735,574)`).
These pixels are unowned in both extended and original indexed planes.
At tight left `(18,498)..(22,502)` and right `(2698,538)..(2702,542)`
probes, **neither** the original DMA commands nor the 10,555 host packets have
projected bounds over the sample. At the left sample the nearest original
projected bands end around native y272 and restart at y281; the point maps to
y274–275. At the right sample, adjacent authored bands stop at y259 and
restart around y267; the point maps to y264–265. These bounds are conservative;
the exact ownership values establish the missing pixels. The two-sided result
supports a draw-coverage mechanism in this part of New York, but says nothing
about distant object pop-in or defects elsewhere.

Evidence: `gl-survey-run/report.json`, `margin-3600-dma-run/report.json`,
`margin-3600-geometry-v3.json`, and `margin-3600-point-geometry.json` in the
World local directory. Frame 6000 is in `margin-6000-dma-run-v2/report.json`,
`margin-6000-{left,right}-geometry.json` and
`margin-6000-{left,right}-point.json`. The first 6000 run is preserved as
`margin-6000-dma-run/report.json`: it **failed** before comparison because
the requested source frame 5996 was not on the completed visible page.
The source journal identified 5997; only v2 is qualified. The initial 3600
margin analyzer invocation failed because
the World mirror omitted an optional `metadata_game` field; the analyzer now
uses its documented World default, and the same saved capture passes. The
new component count is ROI-clipped and source-hashed, not a whole-screen gap
area. The sky-colored V-Unit gap screener returned zero here because these
pixels are unowned index zero rather than authored sky colors.

## Off-Road Pike's Peak

The attended Pike's Peak recording passes 9,657 inputs with 4,072 prepared
host scenes, 7,011,715 quads and owned shutdown. The saved course-select and
track-start images confirm the route. A matched control/resident-margin pair
replays the same 9,002-input prefix on the stable physical 1440p display. Both
pass original input/time and native-image comparisons and owned shutdown, and
each provides ten completed 2544×1353 images at frames 3600 through 9000 in
600-frame steps. The resident candidate submits **268,381 additional quads**
over 3,745 scenes, yet all ten completed images are byte-identical to control.
Thus this sparse course sample shows no new center damage and no demonstrated
margin benefit; extra submission cannot be counted as visible improvement.
The frames cover a paved approach, dirt, a tunnel, and snow. They are not a
frame-by-frame or 4K safety proof and do not repeat the El Paso sharp-turn
positive result on Pike's Peak.

The reusable `harness/compare_offroad_resident_course.py` validates both
replays, binary/case identity, actuator-off settings, capture receipts,
schedule/page identity and exact center pixels before reporting margin deltas.
It reproduces the earlier El Paso late-pair result (20 changed right-margin
pixels at 4000, exact 6000/8000) and passes the Pike's Peak pair. Local reports
are `paired-control-run/report.json`, `paired-resident-run/report.json`, and
`paired-safety-v2.json` under the Pike's Peak directory. Near-black counts in
the comparator are only review hints, not texture-defect proof.

Neither recording qualifies 4K, physical wheel/FFB, every course, or a public
renderer deployment. The next efficient World step is to test a
source-qualified geometry policy against the saved two-sided indexed and
completed frames without repeating an attended drive. For Off-Road, target a known Pike's Peak margin
defect or a denser short interval before inferring that the resident candidate
improves this route; avoid another full-drive replay merely for more sparse
identical samples.
