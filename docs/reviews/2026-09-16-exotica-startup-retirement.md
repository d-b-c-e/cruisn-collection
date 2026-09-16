# Exotica: first-scene recovery without endpoint coverage

The existing continuous fallback also returns to the original view when the
first eligible future assembly fails during startup. This check exercises the
empty-workload edge separately from the preceding mid-race failure. Native
5c4da4891a9 is unchanged; no additional build was required.

One2000-input fault case and one ordinary-view control run on the primary4K
display with CRT4x and physical FFB0. Injection is requested from frame1;
verified guest startup reaches the actual failure at1385, scene2. CPU/GPU
retirement agree at1385 and first original presentation is1386. The game
continues through track selection and exits0.

All2000 input/time records and33 native images match control. The200 camera
records and600 actual ADC reads over1800..1999 are exact. All three completed
3840×2160 frames1945..1947 exactly match the ordinary view;1945 was viewed and
shows normal track selection. This is startup/menu coverage, not another driven
course or observation of the first visible retirement frame itself.

One scene completes its three material stages and fence. There are zero endpoint
commits and zero endpoint GPU pairs; the admission ledger contains two empty
packet headers. The CPU/GPU report no pending work, all125,867,456 ring bytes
drain, and the graphics worker joins.

The normal quiet-renderer check deliberately remains **FAIL**. Its native
endpoint `complete` flag includes positive workload coverage, so three endpoint
summary flags are0 here. Zero work cannot certify endpoint rendering. We did not
rewrite those flags or relax the full-workload verifier.

The replay reporting path now saves the independent retirement receipt before
workload validation. A quiet-journal failure is retained as `verification_error`
while independent input and completed-image checks continue; the final report
still fails. The original run predates that final reporting adjustment, so its
raw report stops at the journal error. A saved-data checker completes the
remaining input/motion/pixel checks without another game execution and explicitly
keeps `renderer_workload_passed=false`. The prepared recorder likewise refuses
to call this a qualified host-renderer recording.

Validation: the unchanged strict journal verifier still rejects the saved empty
workload, the recorder reports retired original-only output, syntax checks pass,
and the separate saved recovery qualification passes. No broad suite or repeated
game run was used to improve the outcome. No claim of journal-file completeness
is added beyond the existing native receipts.

Local evidence under `results/diagnostics/exotica-amazon-20260909`:
`startup-retirement-fault/report.json` (retained FAIL),
`startup-retirement-control`, and `startup-retirement-qualified.json` (narrow
recovery PASS, full workload FAIL). The local runner/checker are under
`world25-roads-20260914`.

Machine reset, physical FFB, broader course coverage and useful outer-distance
visibility remain open. Personal87d/publicv0.5.0 are unchanged; no deployment or
attended recording. Next inspect existing scripted Exotica course-selection work
before deciding whether an open-sightline sample can be obtained autonomously.
