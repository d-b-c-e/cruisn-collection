# Exotica future-section foundation — September 9, 2026

Exotica's section allocator now has a standalone C++ reconstruction and an
independent Python reference. They build positions, rotations and initial render
fields without guest allocation or CPU execution. This follows the checked
[transform](2026-09-09-exotica-transforms.md) and
[Zeus model](2026-09-09-exotica-model-codec.md) decoders. It is not yet connected
to additional drawing in MAME.

## What is checked

The bounded allocation probe observes 1,135 allocations over eight sections and
six section headings. All 1,079 ordinary descriptors match the independent
reconstruction, including 2,158 initial texture/palette lookups and nine palette
overrides. High-byte custom model handlers and classes A/F account for the
56 excluded allocations. They require their own contracts; there is no model or
level allowlist. An initial reference incorrectly treated class F as an ordinary
type and reported 18 mismatches; that failure is retained locally.

Six snapshots reproduce the track's 54 sections and 7,147 source definitions,
including 6,323 ordinary descriptors per snapshot. Native and Python agree on
all 42,882 source records. Their 6,474 comparisons against actual ordinary
allocations include 2,507 allocations that happen after the snapshot used to
predict them. Those later comparisons also preserve the original initial material
bindings. The later sections outside these eight observed sections are checked
against the independent reference, not against actual future gameplay.

The loader's entry pointer, section number, position, heading and distance cursor
agree at every captured boundary. The probe tracks the whole section transaction
from B7E8 through the final position write at B840, including coroutine yields.
The first expanded prototype ended its activity marker at the earlier entry-pointer
write B817; inspection exposed that gap and the reusable probe extends it through
the position update. No live partial transaction occurs in the 4,191 sampled
boundaries. Partial exclusion and inconsistent-boundary rejection therefore have
synthetic coverage only.

Reverse sections, third-list direction handling and end markers are implemented
in the references. The current drive's eight loaded sections are all forward;
reverse placement has independent/synthetic coverage but no live allocation pass
in this recording. Material values are rebound when reconstructing a snapshot.
Lookup equality is not proof of WaveRAM upload readiness, texture lifetime or
palette-color stability.

Five 6,000-input runs—control, initial probe, expanded probe, reusable probe and
repeat—preserve 4,191 camera samples and 12,573 actual ADC addresses, values and
timestamps. Each matches all 21 original 3840×2160 images. The reusable probe and
repeat also match all 11 allocation/progress/completion/RAM/ROM capture files,
67,144,279 bytes including the exact recorded clock values.

Local checks pass 263 Python tests with no skips, 26 native test programs,
10,081 C31 and 137 yaw vectors, and 32 GPU checks across 72 commands. The
392-file source identity is
`ff1886dd6960bbe032f79038e1c747ee55d0622fa283c6d14cd62321a085337c`.
The [133-file public proof](../../results/proof/2026-09-09-exotica-future-sections/README.md)
recomputes the five input/motion traces, three selected 4K images per run and
loader transaction boundaries. Full descriptors, source/material comparisons,
remaining images and native/GPU executions are receipts; raw game operands remain
local. No full-track visual or material-lifetime acceptance is claimed.

## Reusable implementation

- `lua/exotica_section_capture.lua`: bounded allocation, whole-loader progress,
  six configurable RAM snapshots and read-only ROM-region capture. All raw game
  resources remain local. Completion, counts and code guards are explicit.
- `native/exotica_future_sections.h` and `harness/exotica_sections.py`: checked
  section traversal and render descriptors, with shared C31 arithmetic. No
  guest object allocation, linked-list mutation or simulated CPU execution.
- `harness/verify_exotica_future.py`: original source/placement/binding checks,
  later-allocation checks and optional full native comparison using
  `native/analyze_exotica_future.cpp`.

The caller must supply the selected ROM bank and trustworthy loader activity.
The decoder rejects inconsistent scalar boundaries and excludes the in-progress
section from future sources. A native scene adapter still needs to supply that
activity from a guarded transaction hook. The descriptors contain render metadata,
not the game's physics links.

## Next

Verify the Zeus state setup and material residency needed to render those future
descriptors. Reconstruct each object's private texture, alpha, depth and projection
context, then compare it against original model captures. Extra rendering must
leave the actual Zeus state, original output and simulation unchanged. Scene
insertion, foreground occlusion, distance fading, handover and full-speed 4K
presentation remain open.

Native remains the separately built eb17cf2/SHAee2bd4d0 candidate. The seven default
passes belong to the preceding model-codec milestone; standalone section work
does not renew that suite. Personal Stream Deck remains v0.5.0/SHA87d04de4. No
release, deployment, hosted workflow, physical FFB, World force tuning or menu
removal. Continue directly; the one-minute heartbeat is recovery only.
