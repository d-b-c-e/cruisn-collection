# Exotica adaptive scenery admission — 2026-09-08

Exotica has an earlier, global admission limit that is separate from its 204800
far plane. Raising this earlier limit changes some distant pixels, but the
candidate also changes original draw state/order, and later images differ widely.
It remains a **bounded diagnostic**, with no new native adapter or launcher
control promoted tonight.

This follows the [far-plane null result](2026-09-08-exotica-far-distance.md).
Tools are committed as `4c47b67`. Native `12e9ea6a374` and its deployed SHA256
`9936c7160ddb708949d9e776c9197d833e868ffc921fd679153a72ab99735275`
remain unchanged. Physical force is disabled; the release and personal settings
are preserved.

## The earlier control

The game initializes word `589` to 90000 in `B710..B712`. It then adjusts that
limit using its emulated timer: routine `840C` reads Timer0 at `808024`, which
the MAME driver implements from elapsed emulated time. Routine `82C2` selects
an increase of 150 or a decrease of 500 and normally clamps to 60000…130000.
Another path subtracts twice the negative adjustment. A separate conditional
track/section path can force 47500; it was not observed in this recording.
These are game values, not host wall-clock timings.

The pending-object path compares projected depth against `589` at `B772`, before
objects reach the final sphere culler. The second comparison at `B775` provides
an independently observed check that the first branch passed. The loader also
compares a cursor against an upper section value plus 12 at `B7B9..B7BC`.
The track's observed lead is 45, and loading advances in batches; increasing the
loader constant alone is not equivalent to admitting already loaded objects.

`lua/exotica_streaming.lua` first ran read-only from 2500 through 5990. Actual
observations begin at 3485, with gameplay loading. All 6000 original inputs and all
**21 original completed GL captures** match. The probe observes 132624 admission
tests: 36608 pass and 96016 fail. The original limit varies from 90000…130000, and rejected
depths range from 90111…168375. Thus substantial rejection happens well inside the far
plane. These are repeated visits, not 96016 unique objects or visible features.

## Bounded intervention

Four full 6000-frame runs hold coherent CPU reciprocals and wide bounds fixed
during 4500…5990. They replace only the two guarded admission-limit reads with
160000 or 190000, leaving the stored adaptive limit, far plane, loader threshold,
ROM and guest RAM unchanged. The taps are removed at the end of the interval;
objects already admitted remain part of the subsequent game history.

| Trial | Pending passes / rejects | Original stored limit | Final sphere admissions | Instrumented emulation speed |
|---|---:|---:|---:|---:|
| Coherent control | 24345 / 9890 | 125300…130000 | 387144 | 97.7756% |
| Fixed 160000 | 24361 / 0 | 124000…130000 | 396867 | 97.1698% |
| Fixed 190000 | 24361 / 0 | 124000…130000 | 396867 | 97.3505% |
| Fixed 160000 repeat | 24361 / 0 | 124000…130000 | 396867 | 96.5754% |

The 160000 candidate repeats both complete diagnostic traces and all 15 completed
1920×1080 images exactly. The 190000 run has identical final sphere traces and
images to 160000; there is no demonstrated additional benefit from 190000 here.
The new coherent control also has the exact raw sphere trace from the preceding
far-plane study, showing that the additional observation did not alter that
control's emulated decisions.

Twelve of 15 sampled images differ from the coherent control. Early differences
are small: 52 changed pixels at 4700 and two at 5100. Large differences from 5300
must not be counted as added scenery; camera/route identity has not been
established for this candidate.
The existing synthetic drive is slow and goes off the road. This is neither a
new attended drive nor proof that pop-in is solved. The Lua timing includes
instrumentation overhead and does not predict a future native adapter's speed.

## Matched 4K scene and retained failures

Two independent prefix runs capture actual Zeus resources/submissions around 4700
and completed 3840×2160 frames 4699/4700. Differences are confined near distant
scenery: 367 and 374 pixels respectively. Texture wave RAM and the initial palette
are identical between the runs.

Both strict frame and explicit scene comparisons report **FAIL**. The candidate
contains 2972 records versus 2831, including 2753 quads versus 2612. Geometry-only
association finds 2560 identical quads as a multiset, but only 2409 in original
order. 52 original quads lack an identical geometry match. Original render state
also changes: 1786 source-alpha values, 1810 destination-alpha values and 814 depth
bias values differ at equal geometry. Only one matched quad with changed alpha
has blending enabled; most alpha changes are inactive for those opaque draws.
The 814 changed depth-bias records have the depth-min flag enabled. These narrower
findings help prioritize investigation but do not override the strict failures.

A follow-up isolates that bias change further: **all 814 switch from 2047 to
zero**, and each has unique geometry in both captures. Neither depth-clear flag
overrides the bias branch. The two ambiguous geometry associations elsewhere in
the stream are explicitly excluded from this conclusion. This still does not
establish that those state changes cause the visible differences.

The native renderer copies the signed 24-bit value of render register `0x15`
into each quad, and both CPU and GL paths add it to depth. The next diagnostic
should trace `zeus2_pointer_write(0x15, ...)` with FIFO/model command provenance,
then compare the transition preceding the affected original submissions. Do not
globally force a bias or assume that extra geometry merely needs a longer far
plane. The [state-bias receipt](../../results/proof/2026-09-08-exotica-admission/README.md)
recomputes this narrower finding from the retained local captures.

The experiment therefore identifies a useful earlier control without establishing
a safe product setting. The next step is to isolate the active depth-bias/order
effects, or render future static scenery on the host while preserving the game's
original submission state. Do not simply advertise a higher multiplier or remove
strict checks to turn these results into a PASS.

## Verification and next coverage

`analyze_exotica_streaming.py` checks contiguous observations, actual branch
progression, original/effective limits, loader operands and incomplete intervals.
`run_exotica_admission_trials.py` freezes both probes into each run and keeps
completed pixels, original inputs, repeatability and timing separate.

All 168 Python tests and all four CI jobs pass
([run 34225451570](https://github.com/d-b-c-e/cruisn-collection/actions/runs/34225451570)).
All 268 source hashes agree locally and on Windows/Linux; identity
`8c20a78779c02b150e4aa3f6a18181a6199a862d736fe9fd24211530e51d9c13`.
The deployed native build's previous seven-case regression remains its product
baseline; these analysis tools do not alter that binary.

Evidence is in `results/diagnostics/exotica-streaming-20260908`, with an 83-entry
derived archive under `results/proof/2026-09-08-exotica-admission`. Its verifier
uses the companion far-distance archive to reuse the identical coherent trace.
It recomputes admission, sphere, input and timing results and preserves both
strict failures. Images, raw Zeus resources and state-delta analyses remain
hash-bound receipts requiring their local inputs for GPU reproduction.

A fresh attended Exotica drive on an open level would improve visual coverage.
World New York and a longer Off Road drive remain valuable separate recordings.
Independently, continue studying admission state/order and the host static-scenery
path. Do not change force feedback or release defaults to support these trials.
