# Session Notes
<!-- Written by wrapup; previous history is in git. -->

- **Date:** 2026-09-08
- **Branch:** master

## What Was Done
- Recorded explicit maintainer v0.4.0 release authorization in docs/releases/v0.4.0-approval.md.
- Added audited human-check waivers to release_gate; automated gates remain mandatory.
- Consolidated changelog/release notes, refreshed current roadmap and overnight checklist.

## Decisions Made
- Publish the current alpha to the existing private repository; no visibility change.
- Do not invent attended PASS results from blanket sign-off; record accepted coverage limits.
- Freeze game code at native97600e9597e; World FFB rollback and Exotica polarity correction retained.
- Postrelease order: Cheats, top-level Experiments, global distance across all four games.

## Open Items
- [ ] Complete current seven-case/five-fresh-boot/package gates and publish exact v0.4.0 ZIP.
- [ ] Preserve release receipts and schedule overnight work through 08:00 local September 8.
- [ ] Physical second-wheel/manual/soak checks remain unperformed, accepted as alpha limitations.

## Next Steps
1. Finish release gates/package/promotion; do not publish old rc2.
2. Implement docs/OVERNIGHT-2026-09-08.md in separate commits after publication.
3. Keep physical FFB disabled in automation; World tuning remains deferred.

## Context for Next Session
Native E:/Source/mame-src/vunit.exe SHA b5ba0021a51a1f9ec50e105dde9c8112cb3c7e4ce71009ce4294841296383ee2,
HEAD97600e9597e; Stream Deck uses this native binary and the source launcher.
Source/ZIP identities must be renewed after release-accounting code changes.
