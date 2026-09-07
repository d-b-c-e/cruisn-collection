# World 3x distance, earlier activation, and a release baseline

2026-09-07. User requested a controlled 3x distance experiment, independent
lookahead tests, and a maintainable checklist before another public release.

## Decision

**3x works technically, but has not demonstrated a useful further reduction in
Germany's mountain pop-in over 2x.** Earlier section activation has more effect
than raising this far limit. Keep 2x/lead 8 as the previously identified attended
candidate; retain 3x and lead 12 as explicit diagnostics, not launcher defaults.
No distance enhancement is applied to USA, Off Road, World 2.5 or Exotica.

The shared pending-list path is an upstream gate: an object must be available and
active before the far test and projection table can help. Other object/terrain
visibility tests, detail switching, allocation and occlusion can still matter.
This experiment does not identify one universal cause for every visible pop.
Continue toward a host static-transform oracle and drawing pending/future scenery
without activating guest gameplay objects; do not grow per-model patch lists or
assume ever-larger far constants solve the remaining problem.

## Implemented experiment

Native `b0540e36189cf799bd13d0b5796dc19a9d8e243a`, built executable SHA256
`aa92018876b8c07868057fdee7ccd1c7391dd1cad3d64f13134b3fbf977b8fec`.
`native/world_distance.h` remains canonical and synchronized to MAME.

- `--world-far 240000` adds 3x to the existing 80000/100000/160000 options.
- `--world-lead 0..12` allows a separate 12-section comparison.
- Expected-word checks still protect World 2.4's far/clamp instructions. The
  projection table stays in host memory; the 3x maximum index is 15000 and fits
  both the instruction immediate and the observed address range.
- No model/level allowlist, guest-RAM table extension or CPU overclock was added.
  Selective scenery cannot be combined with this experiment. All hooks remain
  disabled without the explicit native FAR setting and matching checked patch.
- The native helper, CLI composer, CSV validator and bounded Lua diagnostics
  understand the new limits. Unsupported games and out-of-range values fail.

## Full Germany matrix

All five runs used the same immutable attended source, 8783 input frames,
146 native images, 321 completed GL images, 7281 camera samples and 21843 actual
ADC reads. CPU clock stayed at 100%; physical force was disabled.
The original-distance control matches all native images. The new 2x/8 run also
matches the previous build's 2x/8 evidence exactly.

| Far / added lead | Emulation speed | Extended projection reads | Extra-range gate tests |
|---|---:|---:|---:|
| Original / 0 | 99.9004% | 0 | 0 |
| 2x / 8 | 100.0008% | 7,425,141 | 347,915 |
| 3x / 8 | 100.0006% | 7,926,248 | 352,802 |
| 2x / 12 | 99.9991% | 9,756,045 | 492,687 |
| 3x / 12 | 99.9183% | 9,993,440 | 502,463 |

Counters measure repeated operations, not unique objects or visible pixels.
Callback p99 was 26.5–27.9 ms; occasional long callbacks remain. These timings
do not establish smooth GPU presentation or eliminate the user's stutter report.

At lead 8, 2x and 3x camera words match throughout the trace, and actual ADC
frame/value/PC sequences match. ADC timestamps differ, so the strict motion
report still fails its timing comparison. Only 5/321 sampled GL images differ,
by 16–628 pixels at the small output size. Inspected differences include HUD
timing and effects; there is no demonstrated substantial scenery gain.

Lead 12 changes the old replay's route much more: camera first differs from
lead 8 at frame 1716; even 2x/12 versus 3x/12 first differs at 1992. Their later
full-run image differences cannot be treated as isolated scenery improvements.
Every candidate retains its original-route mismatch; none replaces the source drive.

## Controlled mountain section

Five separate runs preserve original history until frame 5900, intervene through
6140, and capture every second completed GL frame through 6300. Original prefix
6304 passes. The Lua interventions are bounded attribution probes, **not native
performance benchmarks**. Restoring projection does not undo earlier activation.

| First attributed model submission | Original | 2x/8 | 3x/8 | 2x/12 | 3x/12 |
|---|---:|---:|---:|---:|---:|
| Mountain CB1A8B | 6093 | 5981 | 5981 | 5925 | 5925 |
| Background CB2314 | 6119 | 6005 | 6005 | 5947 | 5947 |
| Forest CB2375 | 6119 | 6005 | 6005 | 5947 | 5947 |

At either lead, **all 201 completed GL images match between 2x and 3x**.
Lead 12 advances these submissions another 56–58 frames, but submission is not
the first unoccluded visible pixel. Terrain can hide early geometry. Model slots
also differ between runs; this is observed model presence, not proven stable
placement identity.

Between leads 8 and 12, camera words already diverge at 5924; 168/201 GL images
change, including later traffic and collision effects. All actual ADC values/PCs
match in this bounded comparison, but timestamps differ. Do not call this a
clean matched-scene visual win, or advertise a full second of visible improvement.
An attended drive would be needed before promoting lead 12.

The 3x/8 full native run repeats exactly against itself: 8783 inputs/times,
146 native images, all 321 completed GL images, camera words and actual ADC
values/timestamps. This proves repeatability of that candidate, not preservation
of the original attended route or physical handling acceptance.

Near-4K verification also finds no additional scenery: eight completed frames at
3824x2073, 6000..6140 every 20, match exactly between 2x/8 and a logged 3x/8 run.
The lossless frame 6040 is retained. Both use the same bounded intervention;
enabling diagnostic GL logging on the successful retry is explicitly recorded.
Cross-game verification is recorded separately in the release evidence directory.

One near-4K 3x-window run failed before any requested capture: the GL producer
reported a consumer timeout and switched to native presentation. The largest host
callback gap was 789 ms at frame 584, long before the intervention at 5900.
That locates a startup-period suspect, not a proven cause or precise failure frame.
No GL captures were delivered; the harness correctly failed the run. The existing
producer waits up to 500 one-millisecond sleeps when its queue is full. Do not
silently increase that limit or treat a successful retry as a fix. This failure
remains a release blocker pending diagnosis and repeated cold-start validation.

## Release work and actual defect found

The concise maintained roadmap is [RELEASE-CHECKLIST.md](../RELEASE-CHECKLIST.md).
It covers all four games, both supported shifter styles, free play, rebinding,
comparable force feel, default widescreen/CRT, menus, installation/upgrade, a
second wheel vendor, and a mixed-game soak. World 2.5 remains automatic-only.

Fresh-install seeds had free play **off** in USA, World 2.5, Off Road and Exotica.
The seven pinned setting bytes were changed to 1; World 2.4 was already on.
Existing user NVRAM and display/force settings were not changed.
New hardware-free tests exercise the actual configuration functions in temporary
rigs: seed defaults and preservation, CRT/full widescreen, World revision,
shifter/cabinet ports, binding replacement, high buttons and keyboard fallback.
They do not establish physical control behavior.

The real fresh-boot check then caught an important error in the old notes:
**Off Road does checksum its operator settings.** Its first edited seed replayed
exactly, but free play reverted to 0 at frame 761, with the attract screen showing
INSERT COINS. Read-only write taps traced two default-table writes through ED6E
(reported PC ED6F), called from ECBB/ECA5 after the factory-reset path.
DB9B..DBA0 compares the sum from ECD5 with stored word 0x35. The sum covers 47
big-endian values, encoded in the low bytes of four CMOS words each. The changed
seed summed to C2AD78 but still stored C2AD77.

`cmos_settings.py` now maintains that sum for the verified Off Road layout; the
launcher Free Play toggle and `nvram_tool.py` share it. One additional fixture
byte, 0x35C, changes 77->78. Unsupported layouts are rejected; unrelated bytes and
existing user settings are preserved. The corrected 1800-frame boot and replay
retain free play 1 and a valid checksum. Its attract capture visibly says FREE PLAY.
No boot-time reapplication or patch to game code masks the reset.

`check_fresh_boots.py` now boots/replays all five seeds and checks actual saved
settings after both runs. Release acceptance requires this separate report; the
original failed result is retained, rather than being replaced by the successful fix.

`release_gate.py` requires a complete regression suite, fresh-boot evidence and matching binary,
source and suite identities. Missing/skipped/stale evidence cannot clear release.
The separate attended ledger requires observations and hashed evidence for each
acceptance item; unobserved checks remain pending. The release workflow now runs
tests and ZIP content/dependency checks before publishing. It still rebuilds on
tag, so promotion of a previously tested artifact is a release-process prerequisite.
No public tag, release or new attended force-enabled session was created.

## Verified baseline before further release hardening

All seven default regression cases pass on the final source identity
`dea70cf8171b837936acd64eba90a4425c3fcebb6e4f3934f1bb96ae2fa8ebdb`:
USA original/widescreen, World 2.4 synthetic/Germany, World 2.5, Off Road and
Exotica, including its 21 completed GL reference images. The separate initial
seven-case pass is also retained. Both suites used the same native binary above.
All five fresh-seed boot/replay persistence checks pass; a separate Off Road
relaunch from its saved NVRAM also retains free play and the valid checksum.
Three V-Unit menu-handler checks pass. They exercise the real handler, not a
physical Esc press. All automated physical force was disabled.

92 Python tests pass. CI [34095982029](https://github.com/d-b-c-e/cruisn-collection/actions/runs/34095982029)
at `471ffd6` passes both Python platforms, native helpers and Mesa GPU quality.
The release gate passes its seven configuration tests, full replay suite and
fresh-boot evidence; **ready_for_release remains false**, with 39 attended/package
checks pending. No physical control or subjective force result was invented.

All 161 World proof ZIP entries were verified, five full motion/distance summaries
recomputed, and two near-4K PNGs checked against their original BMP pixels.
The release archive verifies another 124 runtime entries. The old executable,
SDL runtime and force profiles are copied to a local rollback directory before
any further renderer changes. The Stream Deck wrapper still launches this checkout
and `E:/Source/mame-src/vunit.exe`; global distance remains off in normal launches.

Proof: [results/proof/2026-09-07-world-3x](../../results/proof/2026-09-07-world-3x).
Release seed changes and readiness reports:
[results/proof/2026-09-07-release-baseline](../../results/proof/2026-09-07-release-baseline).
