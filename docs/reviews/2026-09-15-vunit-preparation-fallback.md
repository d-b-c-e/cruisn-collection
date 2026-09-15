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

Before product use: qualify the other V-Unit paths, define Exotica's separate
failure boundaries, and provide continuous operation and visible player-facing
status. A fallback preserves a playable baseline; it does not repair the rejected
scene or fulfill extended-distance parity.
