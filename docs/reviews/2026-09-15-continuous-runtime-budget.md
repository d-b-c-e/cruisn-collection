# Continuous rendering needs a runtime mode

The current diagnostic adapters should not become a player feature merely by
extending their frame windows. The full Amazon evidence distinguishes finite
journals from the live ownership data needed to render correctly.

`harness/analyze_exotica_runtime_budget.py` reuses the independent admission
verifier, joining every packet and query to actual lifecycle watermarks and GPU
draw counts. Optional occupancy measurement preserves the existing verifier's
default output and checks. It needs no game, build or GPU work.

## Measured full-drive data

The accepted full Amazon capture has13906 admission packets,30308 original
endpoint queries and109804 early permissions. Through its complete86376-event
lifecycle journal:

- The admission ledger peaks at1866 entries, against its32768-entry live bound.
- Bound source identities peak at734, below the4096-slot registry bound.
- Both maps are empty at the final observed watermark after the game's reset.

These are logical entry counts, not heap measurements or proof of every track's
maximum. They do show that this drive's live ownership state is substantially
smaller than its accumulated diagnostic history.

| Diagnostic accumulation | Observed | Current cap | Used |
| --- | ---: | ---: | ---: |
| Lifetime rows | 86376 | 200000 | 43.2% |
| Original endpoint IDs | 30308 | 65536 | 46.2% |
| Admission packet journal | 13906 | 20000 | 69.5% |
| Admission journal bytes | 31184196 | 67108864 | 46.5% |
| Waiting scene journal | 6953 | 20000 | 34.8% |
| Handover cohort journal bytes | 49324904 | 67108864 | 73.5% |
| Early permission rows | 109804 | 200000 | 54.9% |

The diagnostic counters do not become available again when a guest pool resets.
They are deliberate evidence limits, not estimates of available game memory.
No time-to-failure extrapolation or repeated-race guarantee follows from one
drive. Increasing these numbers would postpone the issue without separating
runtime state from retained evidence.

The initial local analyzer omitted the recorded marked-only scope and therefore
used the smaller65536-row permission budget. That rejection is retained in
`runtime-budget-full-amazon.json`; the corrected metadata pass is
`runtime-budget-full-amazon-v2.json`. No game was rerun for this analyzer repair.
Five focused admission tests pass, including the optional occupancy result and
retirement/reuse behavior.

## Implementation order

1. Introduce separate runtime enablement and capture policy. Several callbacks
   currently use an open `FILE*` as their enabled flag. Closing journals alone
   would disable ownership processing. Explicitly separate those meanings.
2. Keep bounded capture mode unchanged for deterministic investigation. Runtime
   mode should retain a small summary and first-failure evidence, avoiding full
   per-frame/model/cohort journals and their lifetime row/byte caps.
3. Preserve live source, outstanding-ticket, packet-size, WaveRAM ownership,
   generation, ordering and scene-fence bounds. They protect different things
   from the journal caps and must not be globally relaxed.
4. Keep monotonic IDs and validate overflow before transport conversion. The
   native ownership registry uses64-bit IDs; endpoint pairs carry32-bit model
   IDs. The current65536 cap is not imposed by that codec, but removing it without
   checking conversion and consumer order would be incomplete.
5. Replace fixed observation windows with verified guest lifecycle activation
   and retirement. The current Exotica1799/1800 start and finite end were chosen
   for recordings, not for every player's first start, menu duration or restart.
6. Use saved lifecycle/command streams for long-count and reuse tests first.
   Then perform one justified multi-race recording, covering a return to menus
   and another course, to verify startup/reset behavior and bounded live state.
   Follow with the remaining package, attended wheel and final4K gates.

The V-Unit adapters are simpler: their rendering is not enabled through scene-log
file pointers, but per-scene logs still accumulate and operation remains bounded
by diagnostic frame controls. Give all games the same player-facing behavior
without imposing the same internal implementation on both engines.

The newly qualified failure paths provide a foundation for this work, not a
replacement for it. They remain explicit candidates, with degraded output kept
separate from rendering parity. The personal installation and public release
remain unchanged.
