# Live Exotica waiting-scenery observation

The allocation-owned waiting selector now runs at the actual native scene
boundary. It reproduces independently checked geometry through the full Amazon
recording without changing the existing future packets or original displayed
frames. It still **does not draw waiting scenery**.

A new handover check finds a concrete reason not to enable the proposal blindly:
at snapshot 5072, **10 of 155 waiting candidates receive their first original
draw later in that same game-scene interval**. Adding them immediately could
draw translucent scenery twice. Allocation identity alone does not resolve
the original renderer's admission order.

## Candidate and boundaries

Native `9ad781f7f3981930b2cd269d3d253ca114121e94` is separately built and frozen at
`build/candidates/9ad781f7f39/vunit.exe`, SHA256
`20004be372ba31e9f0d781d2503be10846db853900b5528f65468ac5e5f11daa`.
The 186-patch export reconstructs tree `ba88fcb40a9caa496c970163cb5aab70782fd792`.
The native commit is pushed to the project fork. Personal executable87d and
published v0.5.0 remain unchanged.

Explicit `--exotica-host-waiting observe` requires a candidate, Exotica, an
existing private-wide future pass and lifetime coverage starting at native1799
through at least hostlast+1. It checks completed allocator/binding transactions
at each proposal boundary. The existing zero-guest-cycle check includes this
observation. No original/future geometry or materials are rewritten.

Each log row records scene/frame/device time, registry epoch/sequence and the
**exact lifetime-journal record count**. The last field is necessary because
several allocator, binding or submission events can have the same timestamp.
The verifier folds that exact prefix rather than guessing order from time alone.
Captured owner handles must remain live, bound, unique and never submitted;
ordered instance ranges and geometry fingerprints must match the files.
The ordinary future DTO state remains intact (`future=false` for waiting sources).

## Recorded comparisons

The first 6,000-input trial passes, preserving 4,200 camera rows, 12,600 actual
ADC timestamps and 21 completed 3840×2160/CRT images. Three snapshots match the
independent original Lua owners and Python geometry.

Full Amazon and its repeat each preserve **8,860 inputs, 7,060 camera rows,
21,180 actual ADC timestamps and 21 completed 4K/CRT images**. Both produce:

- 6,953 waiting proposals, comprising 1,021,808 candidate visits and 5,552,865
  proposed quads; these are repeated scene visits, not unique objects.
- The same 6,953 ordinary future scene fingerprints and 19,945,019 future quads
  as the prior reference. Captured RAM, WaveRAM, contexts and future geometry
  also remain exact at all five boundaries.
- The prior 86,376-record native lifetime journal unchanged.
- Five waiting snapshots with **252 / 155 / 298 / 52 / 1** allocation handles,
  all matching independent original Lua identity/order and Python geometry.

All 17 waiting/lifetime trace and snapshot files repeat byte-for-byte. These
trials display the **original target**, and compare it to the accepted original
control. They do not renew the older 233-frame extended-presentation acceptance
or demonstrate new live waiting pixels.

A full disabled-waiting control on the same candidate also passes the original
motion, 21 displayed images and future-geometry checks. It produces no waiting
log or snapshots. Existing lifetime observation remains enabled in that control.

The new CLI/receipt tests cover configuration gates, captured ownership,
same-timestamp event prefixes, malformed counts/clock/geometry, stale or already
submitted allocations, incomplete completion and disabled-artifact rejection.
Full local checks pass **375 Python tests, no skips; 50 native tests; 142 commands
including GPU**, source identity
`4ee7aac74d5981871af3e72d1f733c957419506202ccd7f4833fdd6259dc7c4f`.
This is not a renewed seven-gameplay-default suite; the prior World timeout and
separate successful retry remain recorded at their earlier checkpoint.

## Handover finding and next implementation

The five captured owner sets were joined to later original first-draw events
until the next selected scene's start. All five following scene identifiers
are consecutive, so the sampled interval has no missing scene identifiers.
Only snapshot5072 has first admissions in that interval: ten, beginning about
4.6 microseconds after the proposal. Some fall on the next native screen frame
while still belonging to the same game-scene interval.

This check is five-snapshot coverage, not proof of every scene's final admission.
The next step is an explicit scene/command-boundary handover ledger. Filter or
otherwise reconcile original submissions before accepting combined early drawing;
retain intrinsic transparency, original command order, material ownership and
foreground depth. First compare the filtered5072 geometry/pixels offline, then
validate a bounded native handover observation before changing live drawing.
Do not simply make waiting scenery opaque or allow both copies to blend.

LOCAL commands/evidence under `results/diagnostics/exotica-amazon-20260909`:
`waiting-observer-trial.py`, `check-live-waiting.py`, `waiting-handover-window.py`,
`waiting-observer-short`, `waiting-observer-full`, `waiting-observer-repeat`,
`waiting-observer-repeat-exact.json` and `waiting-observer-local-checks`.
Raw geometry, resources, traces and images stay local.

The [public receipts](../../results/proof/2026-09-10-exotica-waiting-observation/README.md)
verify source/hash and receipt consistency only. Native/raw geometry, game
execution, pixels and local test execution remain separately recorded evidence.
