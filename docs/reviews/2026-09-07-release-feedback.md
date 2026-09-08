# Release feedback investigation — 2026-09-07

Later attended feedback rejected the World force gate. It has been
[rolled back with World strength unchanged](2026-09-07-world-ffb-rollback.md).
The rc2 ZIP and gate evidence below remain the historical baseline.

Status: implemented, built and automatically validated; attended acceptance
remains pending. No new public release.

## Preserved incident evidence

`results/diagnostics/release-feedback-20260907/manifest.json` hashes the saved
configuration, launch history and available force/render logs before new tests.
The World 2.4 launch starting 20:40:21 UTC used far240000 / lead12 and ended with
`Unimplemented op @ 3EF9C170: 15A3ED45`. The following far160000 / lead8 launch
exited normally. Both reported 100.00% average emulation speed. This confirms
the crash, not its cause. No contemporary Windows crash dump was found: the
emulator reported a guest CPU fatal error rather than a Windows access violation.

The user believes race-end wheel oscillation occurred in the 3x/+12 race and
suspects it is independent of distance. The original force trace had already
been overwritten. Launch history now retains bounded force-log/CSV tails as well
as render logs. The last brief Exotica startup cannot represent the earlier drive.

## Telemetry findings

- World 2.4: tach palette code9ADA reads player pointerEE0E, rev+52 and gear+51.
  World 2.5 has separately verified code9ACF and pointerEE08. Both use the same
  rev-to-22-segment multiplier as USA. The complete Germany candidate preserves
  9269 inputs/154 native images. All7516 active samples match an independent Lua
  memory probe; all9269 actual Forza packets and JSON agree. Normal loaded
  upshifts lower RPM. An assertion that *every* gear increase must lower RPM
  fails: countdown/rapid intermediate changes and a rev-limited sequence retain
  revs. Do not replace these real game values with invented drops to pass that test.
- Exotica: HUD codeC2C0 reads pointer10BE, gear+62, rev+63; 32 tach segments use
  multiplier0.6669921875. Speed producer3C1B..3C1D writes integer MPH1074. The HUD
  has a separate metric conversion. Previously no Forza frames were emitted at
  all because Zeus does not execute V-Unit's telemetry frame routine. A driver
  wrapper now emits independently of CPU versus GL rasterization. The first
  candidate preserves6000 inputs and all21 completed GL reference images;
  all2684 active samples match the independent probe, all6000 Forza packets agree.
  This case covers first gear, not all-gear acceptance.
- Off Road: the old OCR font/region reader fails. HUD submission provenance
  leads to AD91's formatter, which reads the smoothed speed at19D11 multiplied
  by19D77. AD9B reads actual gear at player+B. ACA7 reads rev at player+36 and
  divides it by8000 for the tach. The player is selected by19D25 + BC*1C86C.
  Its C code uses DP=1 for globals; copying USA/World's DP=0 assumption would
  read the wrong memory. The candidate preserves6000 inputs/100 native images,
  matches2090 active independent samples and emits6000 agreeing Forza packets.
  The recorded speed reaches40MPH; this case covers neutral/first gear only.
  An initial6001-packet failure exposed duplicate emission during partial screen
  updates. Emission now occurs only at the final visible clip, once per frame.

The presentation remains the explicit arcade RPM scale approved for USA.
Code checks, bounds and game/HUD lifetime gates reject unrelated menu memory.
Original ROM/code dumps stay local; only bounded probes and derived evidence are
appropriate to commit. Failed stack probes are retained and are not passing evidence.

## Force, steering and release work

Exotica's automatic ADC mirror was coupled to the force/shifter DIP on an
unproven steering assumption. The launcher now leaves ADC mirroring off by
default; an explicit diagnostic override remains available. Its output strength
is trimmed20% after driver byte conditioning, including peaks that were already
clipped. Global saved preferences are unchanged. Physical direction and comfort
need an attended drive.

World's independent complete-drive probe observes active driving state4 and
flags bit4, which clear at race end. The native force gate now follows this
verified state, with separate checked addresses for2.4 and2.5. Exotica requires
both its HUD-active and driving-control flags. Inactive transitions clear the
held constant force, impact state and rumble; the worker stops its condition
effects until driving resumes. Raw game motor telemetry remains available.

Germany's dedicated force test preserves9269 inputs/154 native images. It records
8803 motor writes:6839 active,1964 inactive, with1468 nonzero raw commands suppressed.
At native frame8853, the race ends while the game still requests20, then15,12 and
so on; all requested host levels are zero. Exotica preserves6000 inputs/21 completed
GL images and suppresses2072 nonzero pre-drive commands. Independent Lua state
matches every comparable decision in both tests. These are software-command
checks with physical output disabled, not measurements of wheel torque or comfort.

CRT-on is already the fresh launcher default. Packaging now runs the actual
frozen launcher's settings reader with no personal rig and rejects CRT-off,
non-widescreen, wrong-scale or enabled per-game experimental defaults. This check
passes on the new ZIP; the old overnight ZIP remains a separate rollback baseline.

## Repeatable regression coverage

The regular seven-case suite now captures actual Forza/JSON UDP on private
loopback ports for every game, compares it with independent game-memory probes,
requires at least500 active samples and10MPH, and checks force gating for World
and Exotica. Inputs, native/completed-GL images and existing timing gates remain
required. A failed telemetry capture no longer prevents the normal image/input
comparison from running. No packets are sent to the user's SimHub ports and
automated runs never enable physical force.

The final executable is native f2e5b63dd72:
`80688f753070bffe5e55654fed1fd7ffdbd1158acd978e44c9a2a660b40fba57`.
The121-patch export applies to mame0286 and reconstructs exactly tree
`26264b1217f62b08aaab544658cda7a8e9128746`.
113 Python tests, native C++ drivetrain fixtures and canonical-header sync pass.
All seven full final-build replays pass, with matching original inputs/images,
live UDP and independent memory samples. Exotica includes21 completed GL images.
Configured timing intervals range99.9735..100.0070% emulation; this is callback
timing, not a claim of perfect presentation pacing.

| Case | Frames / Forza packets | Independent active samples | Maximum speed | Gears covered |
|---|---:|---:|---:|---|
| USA original | 5012 | 2483 | 134MPH | 0–4 |
| USA widescreen | 5012 | 2483 | 134MPH | 0–4 |
| World2.4 synthetic | 6000 | 2336 | 142MPH | 1–4 |
| World2.4 Germany | 9269 | 7516 | 148MPH | 1–4 |
| World2.5 compatibility | 6000 | 2538 | 145MPH | 1–4 |
| Off Road synthetic | 6000 | 2090 | 40MPH | 0–1 |
| Exotica synthetic | 6000 | 2684 | 39MPH | 0–1 |

CI34164817060 atba6cee5 passes all four jobs. Windows, Linux and local checkouts
agree on every217 source-input hash, identity
`9eeaefe1defee4ac06ea198a1ea192499ab6785abe0c684774a9b504f642d7cd`.
All five fresh seeds also pass1800-frame boot/replay and free-play persistence
checks, including Off Road's checksum. The individual discovery and candidate
results above retain their original build IDs; they are not relabeled as
final-build results.

## Candidate and preserved proof

Clean packaged commit bb62a22 produces
`build/CruisnCollection-v0.4.0-rc2-20260907-170505.zip`, SHA256
`e8847b70fc9436a23aa38ffdb2f2756009c040c6acbaf7bff577a42a947224f8`.
All1632 packaged file hashes and fresh defaults pass. The extracted frozen ZIP
passes four game boots with12 completed GL captures, eight launcher pages, setup
health and support diagnostics, with development paths and physical force disabled.
Later documentation/evidence changes preserve the same product source identity.

[The proof directory](../../results/proof/2026-09-07-release-feedback/README.md)
contains160 archived derived files, exact hashes, reports and a ROM-free verifier.
All seven telemetry and four force-gate verdicts recompute exactly from that archive.
The release gate passes configuration, the complete suite and fresh-save checks;
all43 human/shared requirements remain pending. Current Windows/neutral boots do
not replace a clean-profile install, an attended upgrade or a full physical drive.
Saved user INI SHA256 remains
`b5c521b42433078a22e87b80753e8a44944ce8056949bee3c45c568b58780752`.
Stream Deck continues to launch this checkout and the tested mame-src/vunit.exe.

## Release versus later work

Before publication: attended Exotica steering/startup, World race-end force release,
four-game RPM/gears, SimHub/Buttkicker and comparable force feel; complete the
release checklist against this exact candidate package. Keep distance experiments
off for the baseline. Treat the New York3x/+12 crash as an unresolved experiment
defect; do not infer that2x is safe from a single successful run.

After release, as requested: record a complete New York drive with the external
clock, diagnose black flashing and the finish-line failure with paired default,
2x and3x trials, add cheats for all games, extend distance experiments only with
game-specific validation, and make experiment controls consistent without
duplicating settings or applying another game's addresses.
