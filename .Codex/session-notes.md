# Session Notes

## Latest: launcher graphics controls and Exotica polarity review (2026-09-06)

- Branch codex/launcher-graphics-options from 0183bf3; separate implementation and
  review commits. Authorized push and fast-forward master after exact-head CI.
- Added Settings -> Display -> Graphics Experiments, per-game seam alignment,
  USA v4.5 detail distance and draw limit; all OFF by default. Other games/clones
  cannot receive USA instruction addresses through these settings.
- harness/graphics_options.py is the shared config-to-environment/patch resolver.
  Explicit MIDV_PATCH wins; full-wide + selected patches combine with guards.
  Launch logs include seam, margin and legacy fill flags. CLI/direct launches read
  the same saved graphics configuration. Margin Fill is removed from the normal
  shell, legacy INI ignored/reset on save; explicit developer env/API remains.
- 51 local Python tests pass (8 new). Offscreen Display/USA/OffRoad/Exotica pages
  visually checked; proof in results/proof/2026-09-06-launcher-graphics. No native
  code/shader change, emulator rebuild or new physical FFB test in this batch.
- IMPORTANT: docs/reviews/2026-09-06-exotica-polarity.md identifies Endprodukt's
  FFBPluginRacerMAME and custom MameRacer289.2. His open PR16057 says Wheel Invert
  is force/shifter polarity, not steering direction. His plugin negates Exotica
  force after enabling it. Old local log used motor sign alone to infer mirrored
  driving. Our MIDZ_WHEEL_INVERT input workaround is UNREVALIDATED, unchanged.
- Actual launcher functions tested with six temporary configs: no complete shift
  bindings -> Stand Up, complete bindings -> Sit Down. Wheel Invert On by default
  independently. Imported Kit survives. Local rig already Sit Down/On/Dedicated.
  Evidence results/proof/2026-09-06-fanatec-review/launcher-dips.json.
- Next FFB step: no-force 8-case Cabinet x polarity DIP x input-mirror matrix with
  actual race left/right behavior, raw motor and menu/shifter logs. Then separate
  game motor polarity from device polarity; do not flip global direction blindly.
- Also inspect Exotica raw -128 stop BEFORE gain: current driver may clamp it to
  -127 before motor_level can reject it. Endprodukt normalizes before gain. No
  occurrence established in tester trace. Current 800% Exotica gain vs plugin's
  400% is not a portable feel baseline; assess clipping before strength shaping.
- Tab likely hidden beneath custom overlay; no native-menu visibility integration.
  Exotica MIDZ_GL=0 provides native display for an attended service session. Direct
  vunit.exe lacks launch env, so silent FFB is expected without MIDV_FFB=1.
- Stream Deck still calls Launch-Cruisn.bat -> this source collection.py ->
  E:/Source/mame-src/vunit.exe. Python UI changes take effect on launcher restart.
  MAME remains 377ddc06db1, SHA256 4b37437b6096d47cb1ba3105eb902d36cc1466540db768698d90467959427b6a.
  Toolkit b726d56/v0.11.1 unchanged. No new public release/tag created.

## Previous rendering batch: retained context

- Date: 2026-09-06. User authorized autonomous improvements, separate commits,
  push and fast-forward master after CI. Collection branch for this batch:
  codex/seam-diagnostics-and-distance. Start a880a85; earlier assessment tags intact.
- Primary handoff: docs/reviews/2026-09-06-seams-distance.md; previous batch review:
  docs/reviews/2026-09-06-follow-through.md. RESULTS.md is append-only chronology.
- MAME E:/Source/mame-src branch poc/quadlog HEAD377ddc06db1; push ONLY remote fork.
  Full105-commit export reconstructs tree f3af6c85edc8c9df8b03e085662b6d472826f4c6.
  Never touch the racing deployment's mame.exe. vunit.exe is the local candidate.
- Toolkit E:/Source/dbce-wheel-mod-toolkit master b726d56/v0.11.1, unchanged this
  batch. Prior CI109 managed tests/native vectors passed; both consumers synced.

## Implemented this batch

- Canonical gpu/renderer.py quality shader now keeps fine samples in spans that
  round empty at native resolution. Generated MAME header updated, not hand-edited.
  Native captures results/capture and capture-8000 remain100.0000% exact; GPU12
  fixtures pass. Off Road/World gameplay has1,141/181 changed owner samples.
- Added topology/material/UV-constrained T-junction alignment (gpu/tjunctions.py,
  native/tjunctions.h), C++/Python12-case conformance, harness/inspect_pixel.py.
  Opt-in MIDV_GL_TJUNCTIONS=1 / replay --align-tjunctions. Never scale1; defaultOFF.
  Off Road5518 q125–127 share a vertex displaced0.678435px; correction closes
  tested blue seam (634→0 restricted samples), also changes adjacent interpolation.
- Zeus completed visible-frame fences and captures.csv; replay --compare-gl.
  New fixtures/scenarios/exotica-input-sweep.json supplies6000 driving frames,
  correct port ordering/analog mapping and first-refresh attosecond rounding.
  Local case next-exotica-fenced-gameplay/case captures21 real race images5400–5420.
- CRITICAL: previous Zeus GL native race screenshots were BLACK because CPU
  polygons are skipped. Old matching black images were not a visible oracle;
  headless/live differences did not establish emulation nondeterminism.
- --zeus-native diagnostic double-rasterization produces real CPU race images
  while all21 GL images match. --zeus-stop-frame5500 verifies native rendering
  resumes when GL stops; clean6000-frame exit, replay correctly fails on fallback.
- Removed bogus RPM from packed speed text E632 (MAME921bd); status0/unavailable,
  Forza RPMfields0. Actual loopback5012packets/statuses and human replay pass.
- Added harness/run_regressions.py, fixtures/regressions/collection.json. Runs
  six local cases serially with explicit visual coverage/timing gates and missing/
  uniform-reference rejection.43 Python tests pass. CI also runs GPU/native tests.

## Evidence and distance findings

- Tracked proof: results/proof/2026-09-06-seams-distance/. Full runs are gitignored
  results/diagnostics/next-*. Keep originals and failed controls immutable.
- next-six-regression passes original/wide USA5012inputs/83native images each,
  World2.4/2.5 and Off Road6000/100 each; Exotica6000inputs/21 GL images. Callback
  ratios ~100%, USA selection included. Not proof of all tracks or physical FFB.
- next-exotica-fenced-gameplay/replay first automatic run stopped abruptly at4125
  (0x6E76003B), no useful stack/fault event found. Later visible repeats and dual
  control pass. Retain unexplained exit as OPEN, not quietly a pass.
- Distance trace next-full-distance-trace:293609samples/500objects,15 admissions
  among9objects just past80k, max81035. Earlier120193-sample window had none.
  Matched late far patch4340 adds97quads at4346, preserves2121originals/order/
  texture/palette/nativeVRAM, but final4ximage hasZERO extra owner pixels/changes.
- next-lod-full-drive: late2800 LOD12k/22.5k adds5.2528%DMA work over remainder;
  99.9975% emulation speed2800–4980, inputs equal,37expected native image changes.
  Both LOD and new farplane patch files are diagnostic-only, no launcher defaults.
- New analyze_distance.py keeps far-gate admissions separate from model changes;
  it does not enumerate unloaded objects or prove section-streamer causality.
- USA wide-vs-stock history still differs: original ADC/digital20001reads and
  timestep1921writes agree. First velocity9680/position90AB shifts3063→3064.
  New next-vector/matrix/producers/origin/rotation probes trace this into player
  orientation10AFB..03 (copy9645/9646) and multiplication96D8; velocity inputvector
  differs later. Prior state dependency remains open. No physics compensation.

## Prior behavior to preserve

- USA guarded numeric displayed MPH from E632/formatterA7C2/HUDrenderer7A91,
  visible-page glyph checks, expiry3frames, OCR fallback; NOT physics/RPM.
- V-Unit ordered persistent render stream; lossless backpressure/failure rejection.
  Broad MIDV_GL_MARGINFILL defaultOFF restores real World/Off Road sky. Local
  crack-fill default/radius unchanged; do not expand it to conceal missing geometry.
- Toolkit optional steering impact mixer detects RAW force before driver gain/
  slew/clamp; structural force retains adaptation; common final strength. Optional
  ffb_impact=1, physical acceptance OPEN. Actual contact labels still needed.
- Default recordings/replays are forceOFF. --record-with-ffb only for an explicitly
  attended real recording; no physical force in timeout-capable diagnostics.
- Original my-drive and usa-widescreen-candidate-case remain distinct. Guest code
  changes need matched prehistory; renderer changes compare the same game patch.

## Next priorities

1. More real routes and matched owner/texture evidence for residual World tree
   seams and Off Road margins; expand opt-in join coverage before default use.
2. Find object-list/section residency producer and test LOD across other routes;
   follow player-orientation producer dependency before claiming physics equivalence.
3. Label wall/car impacts, then attended wheel testing; numeric producers for
   World/Off Road/Exotica, validated RPM if a real producer exists.
4. Investigate any recurring Exotica abrupt exit and broaden actual GL gameplay
   windows. Do not return to native-black screenshots as a passing visual oracle.

MSYS2 E:/msys64, OS=Windows_NT exported INSIDE MINGW64 shell; build with both
midvunit.cpp and midzeus.cpp sources. Avoid concurrent live games and timing runs.
Archived-exe headless probes can run alongside builds; candidate replays lock the
root vunit.exe. Append mingw PATH for helper DLLs; prepending selects MSYS Python
without numpy. Full command documentation: docs/DIAGNOSTIC-REPLAY.md.

The final executable, including the diagnostic stop control, also passes
`next-final-exotica`: 6,000 inputs, all 21 completed GL frames and the timing gate.
