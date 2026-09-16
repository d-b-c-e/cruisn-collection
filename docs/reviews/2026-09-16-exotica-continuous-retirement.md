# Exotica: recovery beyond the capture window

Continuous Exotica now qualifies the existing ordered future-assembly retirement
after the old diagnostic end. The continuous3x preset selects this narrow
original-renderer fallback, matching the intent of the V-Unit preset. Neither
policy turns degraded rendering into a parity pass.

Previously, the Exotica fault selector and verifier still required a failure
inside the old1800..5240 scene interval. The native selector now permits a
bounded diagnostic injection through16000 during explicit continuous operation,
and guest-based startup permits injection before the old first frame. The
Python verifier uses the actual trial extent, keeps the original reference
bounds and leaves two frames after an injected failure for retirement/presentation.
Finite-capture behavior remains bounded. The renderer's existing failure branch,
ownership checks and ordered retirement protocol are unchanged.

## One targeted comparison

Frozen native5c4da4891a9 runs one5400-input fault case and one ordinary-view
control on the primary3840×2160 display with CRT4x and physical FFB0.

- Failure is injected at5300, scene3887, beyond every old capture end.
- CPU retirement, GPU acknowledgment and first original presentation identify
  the same scene at5301.
- All5400 original input/time records and native snapshots match the source.
  All3600 camera records and10800 actual ADC reads match the control over
  1800..5399. Exotica native snapshots alone do not validate visible GL output.
- Both completed images5299/5300 differ from the ordinary view. All four images
  5301..5304 are pixel-exact to the ordinary view, starting at retirement.
  Paired5300 images and the retired5301 image were viewed: distant foliage
  changes while the car/HUD remain visibly intact in these samples.
- 3852 scenes complete their material/fence/ownership work; all9854 committed
  marked endpoints prepare and consume, zero rejected. No pending work remains.
  All5,576,392,768 queued bytes drain and the graphics worker joins.
- Native exits0. The replay deliberately reports degraded FAIL. The separate
  retirement qualification passes. This is not a new distance or performance
  acceptance result.

The initial analyzer wrongly required a nonempty MIDV_PATCH in both runs.
Neither Exotica run uses one. The original FAIL remains; corrected-v2 compares
the absence explicitly, then completes the same binary, settings, motion,
receipt and pixel checks from saved data. No game was rerun for that correction.

Three focused failure-policy Python tests, the native runtime test, three
preset tests and three prepared-recording tests pass. Prepared recordings now
reject inherited fault injection/consumer stalls and cannot qualify a retired
renderer merely because its input recording completed. The next Exotica live
plan was prepared with this candidate and policy; no attended game was launched.

## Limits and provenance

Only rejected future-geometry assembly is recoverable. Source identity, code,
resources, waiting/active work, endpoints and transport remain strict. Machine
reset is still unsupported after active Exotica lifetime tracking. Startup
failure recovery remains a separate next check, not covered by this late failure.
No menu, deployment, release or physical FFB change.

Native5c4da4891a9a147d62ffc17668f381e6000c76e9, SHA256
`e1064decae78d24ca4d397873e8f5b270dd02f30e79c8252727980fd712f8aa6`.
254 patches reconstruct `de584ffe34debd9a4dc406d05f64c2014e96879d`.
The native fork is pushed. Personal87d/publicv0.5.0 remain unchanged.

Local evidence under `results/diagnostics/exotica-amazon-20260909`:
`continuous-retirement-fault`, `continuous-retirement-control`, initial
`continuous-retirement-qualified.json` and accepted
`continuous-retirement-qualified-v2.json`. Export/check receipts are under
`world25-roads-20260914`. The new ready live plan is
`race-transitions-20260916/exotica-recording-plan-v3`; use a new output directory
when the user is ready to drive.
