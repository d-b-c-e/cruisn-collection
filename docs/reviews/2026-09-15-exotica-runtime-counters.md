# Quiet rendering no longer consumes cumulative capture budgets

The native candidate distinguishes cumulative diagnostic counts from live
storage bounds. Capture mode retains its existing limits. Quiet mode advances
the same counters with checked arithmetic, preserving monotonic IDs and rejecting
overflow before mutation or transport narrowing.

The changed cumulative limits cover lifetime records/bindings/emissions, original
endpoint IDs, admission sequence/journal bytes, waiting scene count, handover
journal bytes, early permissions and GPU endpoint-pair count. They no longer
stop quiet rendering merely because a diagnostic history would have become too
large. Quiet still tracks logical counts/bytes for completion summaries; those
values are not claims that omitted files were written.

The endpoint transport remains 32-bit. Its producer rejects a new model ID above
`UINT32_MAX` before incrementing or casting. Other changed cumulative counters
retain their 64-bit overflow checks. Limits on live slots, pending tickets,
admitted sources, packet sizes, snapshot files, resource identity and ordering
are unchanged. Snapshot/first-failure operands remain captured and bounded.

`native/diagnostic_count.h` supplies the checked addition used by the CPU and
GPU adapters. Its focused native test verifies capture rejection at 65,536,
quiet advancement past that point, exact 32/64-bit boundaries, byte-counter
overflow and rejection without changing the old value. It also runs 70,000
commands through the actual ticket and endpoint-pair encode/decode/order helpers
across two drained guest epochs. IDs remain monotonic; the final representable
32-bit ID works, while reuse of a low ID is rejected. This is a component test,
not a claim that 70,000 model commands were observed in the live drive.

One final combined 5,300-input quiet Amazon replay on native `d1576aad3ab` passes
at primary3840x2160 with CRT enabled:

- All four completed images at5220/5224/5228/5232 are byte-identical to capture
  mode on `d18bf17d820`.
- 192 saved camera/ADC/source/resource/geometry/original/private files match,
  including all39,408 bytes of endpoint snapshot operands restored by the prior
  file-retention fix.
- All deterministic native summary fields match. Scheduling-dependent batch
  partitioning and writer timing/occupancy remain separate from equality checks.
- Nineteen routine journals are absent, avoiding51,530,716 bytes in this segment.
- Existing per-event independent capture evidence remains in the control; the
  quiet report explicitly declines to claim that evidence for the quiet run.

No broad four-game suite or repeated timing benchmark was run. This change does
not increase drawing distance or establish speed gains. It removes one of the
obstacles to longer operation of the existing candidate renderer.

The frozen binary SHA256 is
`b29e54c4851bb7c9addd9a11087b4a78c813353cf3fe19b6abf0fcc35f2bbbf0`.
The239-patch series reconstructs tree
`1ad708d7477d12e96462228794eba9032189040a`. The Stream Deck/personal binary and
publicv0.5.0 remain unchanged. Local evidence under
`results/diagnostics/exotica-amazon-20260909` includes `quiet-counts-4k`,
`quiet-counts-qualified.json`, `quiet-counts-native-export.json` and
`diagnostic-count-test.exe`. The one-time export script has already run.

## Remaining startup and shutdown work

Quiet is still a bounded candidate trial, not continuous player mode. The
following dependencies must be handled together:

1. CPU lifetime startup currently waits for frame1799 or later; scene/endpoint
   windows start at1800. Lifetimes verify actual code signatures and current pool
   state. Replace the recording frame choice with verified guest readiness,
   without observing boot RAM initialization as gameplay allocations.
2. The actual scene marker atPC0x67f6, pending original submissions and ready
   fences determine which work owns a scene. Enable future work only after its
   ownership observation is ready; do not treat every native refresh as a scene.
3. The verified guest pool rebuild atPC0xbbc9 and global clear at0x85b4 already
   advance lifecycle epochs. A MAME machine reset is different: it currently
   fails after lifetime/fence activity. Supporting it requires explicit drain
   and reinitialization of CPU and GPU state, not merely clearing the maps.
4. CPU exit completion currently requires passing the configured final frame.
   Depth-mirror and retirement paths also validate finite frame windows. Ordinary
   user exit needs coordinated retirement/drain acknowledgments instead of
   declaring an unfinished diagnostic interval complete.
5. Only then use one useful multi-race recording, including return to menus and
   another race, to qualify bounded state and lifecycle transitions. Avoid more
   identical single-race replays solely to accumulate duration or submissions.

Open-view Exotica distance-transition evidence, broader track coverage, remaining
World terrain/New York findings, attended wheel acceptance and final package
gates remain separate release requirements.
