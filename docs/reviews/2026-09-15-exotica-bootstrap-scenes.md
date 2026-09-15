# Exotica scene activation from verified guest state

The candidate now offers `--exotica-bootstrap scenes`: captured lifetime tracking
starts at the verified pool rebuild, and the combined scene pipeline starts at
the next actual guest scene-begin transaction. The captured Amazon run reaches
both at native frame1,385. This replaces the configured startup cutoff in that
explicit mode; it does not yet remove the finite diagnostic end windows.

Activation checks the scene instruction and list-load signatures, full write
mask and value, pool readiness, completed lifetime initialization, and absence
of pending ownership/scene/fence/endpoint work. The64-byte scene proof preserves
the actual operands and serial. Boot callbacks are ignored until pool readiness;
no existing maps or queued work are cleared to manufacture a clean boundary.
The harness verifies the proof before resolving all dependent first-frame
metadata, including waiting, handover, admissions and early endpoints.

The first live candidate `eb830f7db57` stopped at1385: the private material codec
still required frame1800. That failed run remains in `bootstrap-scenes-4k`.
The correction adds an explicit `guest_ready` frame policy to HMT1, XWD1, XMD1
and retained-material encoding/decoding. Capture defaults preserve the previous
1800..16001 bounds. The new policy admits earlier nonzero frames only on this
verified startup path; the existing upper bound remains. Packet layout, palette,
WaveRAM generation, geometry, depth, size and ordering checks remain unchanged.

Four bootstrap Python tests and six relevant native tests pass (bootstrap,
new material-policy test, and four existing packet/retention tests). They cover
corrupt scene instructions/operands, out-of-order activation, capture rejection
of early packets, explicit early round trips, unchanged capture bytes, and
stale/duplicate/invalid material rejection.

The corrected 5,300-input replay passes every input/time and original-image
comparison and the independent scene/lifecycle/admission/handover checks:

- 411 additional early scenes submit no extra geometry.
- The later3,429 scenes match every field except named host timings.
- The complete51,534-event lifetime journal is byte exact to the earlier
  lifetime-start candidate.
- 175 saved geometry/resources/targets/operands/camera/ADC files are byte exact.
- 18 material or composite packets differ only in their two64-bit generation
  values, both advanced by1,233 (three material phases per additional scene).
- The two variable-length admission/cohort journals include the new scenes and
  are independently folded, not declared byte exact.
- All four completed3840x2160 CRT images5220/5224/5228/5232 are byte exact.

These are startup compatibility results, not increased distance or improved
performance. No additional game was run just for an analyzer correction.

Corrected native `067f0b0e095`, SHA256
`506fd16f7049b8e4891eff92533f7d91d7a596384892b28f09679ffd1ad1c00d`;
243patches reconstruct tree `80e1891ec40f69d3058629bf6b5ab54b4432bacb`.
Local evidence under `results/diagnostics/exotica-amazon-20260909`:
`bootstrap-scenes-retry-4k`, `bootstrap-scenes-qualified.json`,
`bootstrap-materials-native-export.json`. Both scene/material export scripts
already ran. Personal Stream Deck executable and publicv0.5.0 remain unchanged.

Next: separate normal runtime termination from finite capture completion and
remove the remaining end-window assumptions as one coordinated CPU/GPU policy.
Retain ownership/drain checks and keep machine reset distinct from the already
observed guest clears/rebuilds. Broader track and attended release gates remain.
