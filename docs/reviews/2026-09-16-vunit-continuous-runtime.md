# Continuous V-Unit scenery and owned graphics shutdown

An explicit `--vunit-runtime continuous` candidate policy now keeps host scenery
running after the old diagnostic end. It requires verified scene bootstrap,
future drawing, live GL and physical FFB disabled. The original finite bounds
remain recorded as comparison references; their values are not enlarged.
Absent selection retains capture behavior. Frame values must fit the existing
32-bit packet representation before host work proceeds.

The continuous path owns its graphics worker. On exit it flushes buffered CPU
uploads, requests shutdown, lets the consumer finish the already queued messages,
finishes a consumed partial batch without inventing a guest frame, waits for GPU
work, then joins the thread before emulator teardown. A worker that fails to
acknowledge within10 seconds fails explicitly. The existing detached-thread path
remains the default outside this candidate policy.

CPU and GPU completion receipts are separate. Verification requires the actual
prepared scene count/quad total to match the scene journal, successful bootstrap,
an owned-worker join, equal producer/consumer byte positions, no dropped or failed
stream, no pending quads and no observed GL errors. Completed/presented frames are
reported separately. This is `owned-worker-stop` completion, not completion of an
infinite capture; `capture_completed` remains false.

## Focused qualification

One native policy test covers legacy bounds, explicit-selection gates and
32-bit boundaries. Seven Python tests cover runtime, bootstrap and fallback,
including malformed/missing receipts, dropped/queued work and count mismatches.

Four recorded prefixes exercise continuation and shutdown:

| Game | Inputs | Reference end | Last prepared | Exact scene rows | Exact image after reference end |
| --- | ---: | ---: | ---: | ---: | ---: |
| USA | 4,002 | 3600 | 4001 | 2,267 | 3750 |
| World2.4 | 2,502 | 2250 | 2500 | 413 | 2400 |
| World2.5 | 2,502 | 2250 | 2500 | 648 | 2400 |
| Off-Road | 2,502 | 2250 | 2500 | 678 | 2400 |

All original input/timing/native-image comparisons pass. Every common scene's
semantic fields and ordered quad fingerprint match retained finite-startup runs,
excluding only named timing/cache-miss fields. First activation operands also
match. USA preserves2,201 camera samples and6,603 actual ADC reads; each other
run preserves701 camera samples and2,103 World or2,804 Off-Road ADC reads.
All four completed post-reference-end images are exact at3824×2073 on the4K
monitor with CRT. This specifically checks pixels after the shortened end,
unlike an earlier Exotica continuation test whose images preceded its end.

Every graphics thread joins with equal producer/consumer positions, zero dropped
messages, zero pending quads and zero observed GL errors. The final completed and
presented frames are4001 for USA and2501 for the other runs. Cumulative consumed
ring traffic is5,225,423,720 bytes for USA;4,718,642,024 for World2.4;
4,434,460,400 for World2.5; and2,354,362,560 for Off-Road. These are transfer totals,
not resident-memory measurements or files produced.

USA's first comparison incorrectly truncated the saved native scene interval at
4000 while the actual valid scene at4001 preceded replay stop4002. Its FAIL is
retained. A corrected analyzer compares every actual scene through the declared
verification end4001, rather than dropping the candidate's last scene. No game
was repeated for that correction.

A World2.5 negative trial injects preparation failure at1500, beyond the former
end1400. It stops extra scenery and retains original rendering through1552:
all1,552 native inputs and25 native images match, bootstrap qualifies147 scenes,
and the owned GPU joins after consuming all4,227,935,744 bytes with no pending
work or GL errors. Runtime verification correctly rejects this degraded run.
The initial harness report fails earlier because the saved case inherited a GL
capture interval beyond this short trial. That FAIL is retained. The separate
`world25-continuous-failure-qualified.json` checks saved native evidence and
receipts explicitly, without claiming absent GL images or repeating gameplay.

Nativee4860a3c76b freezes SHA256
bdd9b442dc572b574e4d6c119206d65ee6270ef5a8e858602d1aba2cd0885891.
251 patches reconstruct0e920025462cded1a48e2d485cb93a7b7a0daea5.
`export-vunit-continuous.py` has already run and must not be rerun.
Local evidence is under `results/diagnostics/world25-roads-20260914`, using
`*-continuous-live`, `*-continuous-qualified.json`, USA's corrected
`usa-continuous-qualified-v2.json`, and `vunit-continuous-native-export.json`.

## Still required

This is controlled continuous execution, not release acceptance for arbitrarily
long sessions, multiple races, every track or overall performance. Summary
journals and first operand snapshots are still enabled. Next separate routine
operation from persistent diagnostic capture while preserving a useful aggregate
geometry/completion receipt, then exercise track changes and final product gates.
Do not infer a new distance-quality improvement from this lifetime work.

The personal Stream Deck installation and publicv0.5.0 are unchanged. No release,
deployment, physical FFB or hosted CI ran.
