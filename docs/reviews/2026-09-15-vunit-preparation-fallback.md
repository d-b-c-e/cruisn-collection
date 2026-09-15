# V-Unit scenery preparation fallback

The candidate now has an explicit, latched fallback for failures while preparing
extra scenery, before any polygons from that scene have been submitted. This is
a diagnostic release-engineering step, not a newly enabled product setting.
The personal installation and public v0.5.0 remain unchanged.

## Behavior and limits

`--vunit-host-failure original` requires an explicit candidate, V-Unit host draw,
live GL, a bounded scene interval and physical FFB0. A rejected future-source
collection, active-road list or host scene build stops further extra submissions
for the remainder of that launch. The ordinary game continues. Partially built
host caches are not used again. No guest state, device transport or original
renderer data is rewritten to accomplish the fallback.

Absent controls retain strict behavior. `--vunit-host-failure strict` selects it
explicitly for diagnostic testing. Revision/code-signature and read-span guards,
guest-cycle changes, packing/depth contracts and device/transport failures remain
fatal. World active-road code checks are factored separately from list topology
so a code mismatch cannot be mistaken for an unsupported scene.

`--vunit-host-inject-failure-frame N` exercises the failure at the first qualified
scene at or after N. It changes no guest memory. The acknowledgment identifies
the policy and requested frame; a single failure receipt gives the actual frame,
stage and fallback decision. The harness rejects missing, duplicated, unexpected
and inconsistent receipts. Saved fault settings require explicit selection.

A completed degraded run **fails parity**. Its independent input/image comparison
is retained, and a separate qualification can establish whether fallback itself
worked. Neither injection nor a real unsupported scene can silently become a
passing rendering result.

This contract covers read-only CPU preparation in USA, both World revisions and
Off Road. Exotica's queued private rendering, resource ownership and handover need
a separate design; this switch does not apply to Zeus. Actual completed-buffer
fallback qualification below covers World 2.4 only.

## World Germany evidence

First, the existing bounded host interval was stopped after7300 using the prior
candidate. At completed7340, both main color/coverage pages equalled the original
mirror. This established that ordinary rendering repopulates the targets; it was
not yet a fault test.

The successor then injected a preparation failure at7300, actually reached at
scene7301, while leaving the requested interval open through7340:

- All7342 recorded inputs complete; native input/image comparison passes.
- All5542 camera and16626 ADC rows equal the scope-stop control.
- All2750 pre-failure scene rows equal control after excluding the eight named
  host timing fields. Last extra scene is7299; no retry or later submission.
- Both physical pages' indexed color and coverage exactly equal their same-run
  original mirrors and the scope-stop control: all eight plane files agree in
  the corresponding comparisons.
- Completed7340 CRT presentation is byte-identical to the scope-stop control.
- Native exits normally; replay reports an explicit degraded FAIL as intended.

The display was3440x1440, with a3424x1353 completed V-Unit image and2736x1600
internal pages. This adds no final4K or performance acceptance. The separate early
strict injection fires at1800 and exits with code3 and the expected fatal reason;
its receipt explicitly says fallback0. No full-drive repetition was needed.

Focused option/receipt tests cover all four supported ROM identifiers, orphaned
injection, candidate/FFB/draw/bounds gates and both normal and degraded receipts.
The native active-road test checks both revisions, distinguishing valid code with
bad list topology from code mismatch. No unrelated suite was rerun.

## Candidate and remaining work

Native `f520034d48ef033f87306d4d50a97082151c515a`, binary SHA256
`71731f982e5b332d5fad9b2199c7c90414bb62219d6be5728592f6249ee44109`.
233 exported patches reconstruct tree
`05998434c28235064026f71cdcf9046d254fafa2`.

Local evidence under `results/diagnostics/world25-roads-20260914/`:
`world-scope-stop-qualified.json`, `world-injected-fallback-qualified.json`,
the corresponding immutable run/plan directories and
`host-failure-native-export.json`. Raw game resources remain local.

Before product use: finish the separate qualifications below, define Exotica's
failure boundaries, and provide continuous operation and visible player-facing
status. A fallback preserves a playable baseline; it does not repair the rejected
scene or fulfill extended-distance parity.

## USA and Off Road qualification

The next isolated change extends the existing original-only mirror to USA and
Off Road. The replay harness configures their host options before validating
mirror ownership. Both native and harness checks require split/tagged host
submissions. World fade metadata remains World-only. Seven focused mirror tests
pass; this changes no ordinary shader, source admission or rendering policy.

One retained route prefix per adapter then exercises the same failure latch:

| Game | Inputs completed | Failure / last extra scene | Camera / ADC rows exact | Completed mirror |
| --- | --- | --- | --- | --- |
| USA | 4042 | 4001 / 3999 | 2242 / 6726 | 4040, both2736x1600 pages |
| Off Road, El Paso | 5102 | 5060 / 5058 | 3302 /13208 | 5100, both2736x1604 pages |

All pre-failure deterministic scene rows match retained controls:250 USA rows
and1579 Off Road rows. Each run had substantial extra geometry before failure.
Both physical pages' main color and coverage exactly equal their same-invocation
original-only mirrors after fallback. Each native process exits normally; both
replays deliberately report degraded FAIL while retaining passing original
input/native-image comparisons. One completed CRT image is captured per case at
3424x1353; these exact frames have no prior completed control screenshot, so no
cross-run presentation equality is claimed for them.

Native successor `e1f9ce0f17f9b97bb610c424427b495d2d4ae984`, binary SHA256
`2c2d462fa1b8bbc60f3a5fc4b91c5cdcf491f8963c0825ed0b90171c37f48647`;
234 patches reconstruct tree `47ccb660151557b52067d6b3b7075b9c22c62903`.
Local evidence: `usa-injected-fallback-qualified.json`,
`offroad-injected-fallback-qualified.json`, their retained run/plan directories,
and `vunit-mirror-native-export.json` in the same evidence root.

All three V-Unit adapters now have an actual injected-failure qualification.
World2.5 uses the shared World path and its code guards are unit-tested, but no
additional2.5 fault replay was performed solely to repeat that shared latch.
Exotica and continuous product operation remain separate open work.
