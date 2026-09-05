# Session Notes

- **Date:** 2026-09-05
- **Work:** independent assessment, then authorized diagnostic improvements
- **Baseline:** collection d099c2f / tag assessment-2026-09-05; MAME 58203bb1
  on fork/poc/quadlog; toolkit 4e99136 / same assessment tag. All pushed first.

## What Was Done
- Five assessment documents plus separate toolkit review; implementation results
  in docs/reviews/2026-09-05-implementation.md; commands in docs/DIAGNOSTIC-REPLAY.md.
- MAME changes 1c420f32 plus pin follow-up 1a2bb35f, pushed to fork; full series
  refreshed from mame0286. Three incremental builds succeeded; deployed mame untouched.
- Toolkit force fixes v0.10.0 / 47b06f08 passed CI; follow-up v0.10.1 / c9b76b7
  fixes native file loading on Linux, exposed by collection CI. Both consumers
  now pin v0.10.1; its final Windows/Linux CI passed. 105 managed tests and
  native semantic/conformance tests. Toolkit changes landed on master.
- Shared pre-gain force rise detector, centered impact fix, UDP address family,
  OCR consecutive-miss policy/file-only source initialization, typed SDL stop ABI.
- True MAME INP recording, archived executable/config, strict replay validation,
  synthetic USA gameplay, live GL capture metadata, offline native FFB analyzer.
- 21 collection tests pass; negative real GPU pixel test exits 1; capture-8000
  stays 100.0000%. Strict Zeus comparison fails as expected (93.6313% color).
- USA 6,000-frame driving case and 100 native images match across replay and
  candidate binary. Live GL record also matches native replay; 32 GL BMPs retained.

## Decisions Made
- Automated recording/replay disables FFB and external telemetry, including live
  user recording in this first version. Physical feel is still an attended test.
- Preserve dated assessment; no speculative renderer/distance patch or retuning.
- Native screenshot equality is distinct from async GL and subjective wheel quality.
- Toolkit math is canonical there; collection native/hud_speed_filter.h is canonical
  here. sync_toolkit.py checks both consumers; sync_native.py checks OCR helper.

## Open Items / Next Steps
- [ ] Record human-driven defect routes; verify World/Off Road/Exotica separately.
- [ ] Fix ordered texture/palette/clear replay and synchronization before geometry tuning.
- [ ] Add scene fences and deterministic live GL comparisons; current labels are approximate.
- [ ] Label collisions; explicit steering-axis effect and combined budget; physical wheel tests.
- [ ] Investigate selection pacing: USA live test averaged real time but p99 77.64 ms.
- [ ] Validate guest visibility/distance patch groups; native speed/Off Road OCR still open.
- [ ] Toolkit validity/provenance, VID/PID selection and backend lifecycle contracts.

## Context for Next Session
Full cases are gitignored under results/diagnostics. Use
scenario-20260905T231026Z-s1l7_egt/case for live-GL USA driving, or
scenario-20260905T224940Z-knuxy44n/case for native driving; both have passing
replays. Neutral archived seed: replay-smoke-20260905T224001Z-vop1s2s_/case.
Compact evidence is tracked in results/proof/2026-09-05-diagnostic-milestone.json.
The complete exported series (including final pin) applied to upstream files
and reproduced all 23 changed paths. Collection Windows/Linux harness and native
CI passed at 1131dc2 (run 33998673255); remaining edits are handoff documentation.
Use run_rig --record-case for an actual wheel drive; early prototype cases are
not supported references. No physical FFB quality or general rendering fix claimed.
