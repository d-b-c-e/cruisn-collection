# Session Notes
<!-- Written during the assessment baseline; subsequent implementation updates follow. -->

- **Date:** 2026-09-05
- **Branch:** master (assessment baseline)

## What Was Done
- Wrote five independent assessment/proposal documents in `docs/reviews/`.
- Reviewed collection, modified MAME and `dbce-wheel-mod-toolkit` sources.
- Rechecked six archived V-Unit captures: 100.0000% native pixel equality.
- Checked generated shaders and vendored force headers without changing them.
- Updated README/AGENTS to distinguish archived proof from gameplay quality.

## Decisions Made
- Preserve this assessment in a committed/pushed baseline before implementation.
- User explicitly authorized subsequent improvements and fixes while away.
- Prioritize reliable test failures, immutable diagnostics and recorded gameplay.
- Attract-mode proof does not clear moving-gameplay rendering reports.
- Automated graphics/algorithm tests must not actuate a wheel.
- Keep the current renderer approach; investigate cause-specific visibility,
  resource ordering, precision and streaming improvements using repeatable cases.

## Open Items
- [ ] Implement reliable renderer/oracle pass/fail and failure-injection tests.
- [ ] Build isolated real-driving input recording/replay with run manifests.
- [ ] Repair typed emergency FFB cleanup and output acknowledgment.
- [ ] Address live resource ordering and patch-group validation.
- [ ] Repair collision detector integration and telemetry absence handling.
- [ ] Investigate car-selection slowdown with a dedicated recorded case.

## Context for Next Session
The other session finished at collection `8035c12` / MAME `58203bb1`.
It incidentally committed two draft review documents; this session completes
the assessment without undoing that commit. World OCR's three-digit range was
verified there; Off Road OCR is explicitly still broken. Full review evidence
and acceptance criteria are in `docs/reviews/2026-09-05-assessment.md`.
