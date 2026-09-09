# Off Road future section descriptors — September 9, 2026

Off Road's ordinary future scenery can now be decoded independently of the
game's object allocator. The standalone native helper and independent Python
reference match all 46,133 loaded/future source records across twelve snapshots.
Of these, 2,424 loaded ordinary descriptors match actual objects, and 703 future
predictions match objects and material bindings created later in the recording.
This is a foundation for host rendering; it does not yet draw extra scenery.

## Why the pending list was insufficient

The preceding pending-object prototype found extra projected geometry at 2x but
none beyond that at 3x. The section loader only instantiates a limited range around
the current track section. The new source reads the remaining section definitions
without activating objects, changing guest memory, or advancing the guest CPU.

A local offline projection prototype combining pending and future sources finds
additional geometry at 3x. At snapshot 4000, projected screen-overlapping quads
increase from 205 at 2x to 762 at 3x; at 4500, from 465 to 482. Later sampled
views gain projected geometry without additional screen overlap. These are
bounding-box overlap counts, **not visible pixels or accepted graphics**. The
prototype's clipping, material readiness and render insertion are not qualified.

## Implementation and limits

- `native/offroad_future_sections.h` and `harness/offroad_sections.py` decode the
  four-word section table and eleven-word ordinary definitions. Absolute position,
  Euler rotation, stable tag, model and material references are reconstructed.
- Track order, first/last markers, section numbers, front/back pointers and lead
  counts are checked. Limits are 128 sections, 256 definitions per section and
  32,768 descriptors. Unmapped layouts fail explicitly.
- Loader-excluded definitions, dynamic model replacements, post-initialization
  custom handlers and alternate material bindings are excluded by behavior flags.
  No model allowlist is used. Alternate/local/billboard transforms remain outside
  the subsequent ordinary projection contract.
- Current material addresses are read again on every decode. They are not cached
  palette colors and are not evidence of upload readiness or material residency.
- `lua/offroad_section_capture.lua` bounds allocations, scene samples and optional
  snapshots. Main RAM is read through its share. Raw ROM/RAM and object operands
  remain local under `results/diagnostics/offroad-model-20260909`.

The allocator check originally failed for 29 of 1,409 objects: their model pointer
is deliberately replaced during initialization when flag `0x04000000` is set.
The failure is retained. Excluding that unqualified dynamic class gives 1,380
matching initial descriptors and 17,940 render-field comparisons. This initial
boundary precedes further custom hooks, so the host source has stricter exclusions
than the initial-field oracle.

## A real boundary failure, now covered

The first continuous probe recorded 1,978 scene boundaries. Strict completed-state
equality failed on seven: the current section had advanced while the front entry
and lead count had not yet settled. No allocation was live at those callbacks.
Five widely spaced snapshots had missed every one of these transitions.

The decoder now recognizes only the observed one-section mismatch and excludes
that entire uncertain section. Larger mismatches still fail. A second replay
captures all seven exact transitions plus the original five snapshots; native and
Python decoding, loaded-object membership, and later-allocation checks all pass.
The continuous probe covers 1,926 initialized scenes, seven partial boundaries and
52 pretrack scenes. The twelve snapshots include early attract and later gameplay
states; they are not twelve different tracks or complete-track coverage.

The final twelve-snapshot oracle checks 42,636 future definitions, including 32,432
ordinary sources, plus 3,497 loaded definitions. The original five-snapshot probe
separately checks 16,384 future/1,634 loaded definitions and 194 later allocations.
Those five snapshots overlap the broader twelve and should not be added as unique
coverage. All 703 later ordinary bindings in the broader set match, but only for
the captured lifetimes and tracks.

## Validation and next work

Two canonical 6,000-input headless replays preserve the original input/native
reference, 4,191 camera samples and all 16,764 actual ADC reads and timestamps.
They do not renew visible rendering acceptance. The preceding prepared-transform
and scene-snapshot runs retain their three completed 3824x2073 captures each.

Local checks pass 239 Python tests with no skips, 22 native test executables,
10,081 C31 vectors/137 yaw vectors and 32 GPU checks, 61 commands total. All 358
source files match identity
`c3c81d2a2e74c4ff8152b7bdb85f46bb2189772dd3d0043f6723f367d884680a`.
The [public proof archive](../../results/proof/2026-09-09-offroad-future-sections/README.md)
recomputes eight original input/motion traces, fifteen earlier completed 4K images
and scalar frontier checks. Raw geometry/material comparisons and native/GPU
executions remain hash-bound receipts.
An initial standalone analyzer invocation lacked the MinGW DLL path; its failed
receipt is retained separately from the successful geometry checks.

Next qualify live texture/palette ownership and uploads, original scene insertion
and sky/foreground ordering, then connect cached pending/future projection to
MAME. Require actual 1x/2x/3x gameplay benefit, repeatability, original route and
resources, clipping/occlusion/handover and smooth 4K presentation before promotion.
USA performance and visual acceptance, World 2.5 roads and Zeus remain open.

There is no MAME integration/build/export/default renewal for this standalone
milestone. Candidate cf58/SHA37c0a4ce retains its prior seven default passes;
personal Stream Deck remains v0.5.0/SHA87d04de4. No deployment, release, hosted
workflow, physical FFB, World force tuning or menu removal occurred. Work continues
directly; the one-minute heartbeat remains recovery only.
