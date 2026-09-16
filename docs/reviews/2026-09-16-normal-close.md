# Normal close during continuous scenery

One normal Windows close request during active gameplay qualifies on each
renderer family: Exotica and USA. Both use frozen native `f0b4db1f25d`, the new
`continuous-3x` replay preset, the primary 3840×2160 display and physical FFB0.
This is distinct from the earlier Lua end-of-recording stop checks.

The existing package checker identifies MAME windows by their exact executable
path. A local runner posts WM_CLOSE only to the selected frozen candidate after
observing frame4000 in the flushed input log. It does not touch the personal
executable. Neither trial required forced termination.

| Check | Exotica | USA |
| --- | --- | --- |
| Last input frame | 4012 | 4019 |
| Original input/time prefix | Exact | Exact |
| Native snapshots before close | 66 exact | 66 exact |
| Camera interval | 1800–3999, 2200 exact | 1800–3999, 2200 exact |
| Actual ADC reads in that interval | 6600 exact | 6600 exact |
| Prepared scenes | 2578 | 2275 |
| Graphics ring bytes, all drained | 3,461,300,680 | 5,228,793,624 |
| Native process exit | 0 | 0 |
| Owned graphics worker | Joined | Joined |

Exotica reports quiescent CPU/GPU ownership, no pending scenes, fences, models,
materials or endpoints, and no renderer/writer failure. All5018 marked endpoint
commands prepared and consumed, zero rejected, with no routine operand captures.
USA reports zero pending quads, dropped data, stream failures or GL errors; its
last prepared frame4017 and presented frame4018 exceed the old3600 reference end.
No candidate window remains after either trial.

The ordinary replay reports intentionally remain **FAIL** with
`record/replay frame count or input columns differ`: neither finished its full
source recording. Separate `*-normal-close-qualified.json` reports pass only
the declared shutdown and prefix scope. Camera/ADC comparison stops before the
close request so an interrupted final sampling interval cannot be misrepresented.
Native Exotica snapshots do not validate visible Zeus GL gameplay; no new visual,
performance, reset or complete-route acceptance is claimed.

The V-Unit replay checker previously collected independent bootstrap/runtime
receipts after full-input comparison, losing those results on an early exit.
Those checks now run before input comparison, as the Exotica checks already do.
Full replay failure and degraded-output failure remain strict. This ordering
change was syntax checked; actual retained USA shutdown receipts independently
pass the same canonical verifiers. The game was not rerun for reporting order.

Local evidence is under `results/diagnostics/race-transitions-20260916`:
`exotica-normal-close`, `usa-normal-close`, their control receipts, qualified
reports and separately derived motion prefixes. Local runners are
`check-normal-close-run.py` and `check-normal-close-evidence.py` under
`results/diagnostics/world25-roads-20260914`. The original failures remain.

One close point per engine is limited coverage, not every possible CPU/GPU
interruption boundary. Machine reset is separate, especially Exotica's currently
unsupported active-renderer reset. No deployment, release or physical FFB test.
