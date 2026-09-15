# Exotica cross-track validation: pre-race pool clearing

The first combined Hong Kong trial stopped at native frame1986, before gameplay:
the lifetime adapter did not recognize a write from PC85B4. Amazon never
exercised this pre-race global-clear path during its observed interval.
The failed trial remains `combined-hong-kong`; it is not a coverage pass.

A bounded read-only probe on the unchanged f0 candidate identifies the original
loop. It zeros addresses0471 through11CB, including free-list head10A8 and
available counter10A9. AR0 advances after each store; RC reaches zero at the
last write, with repeat start/end85B3. The next common-pool rebuild sets the
counter to1200 and reconstructs its original1201-node chain. This is a global
invalidation followed by a separate rebuild, not an ordinary free/allocate pair.

The new adapter checks the exact instructions, range constants, store mask,
zero value/R0, AR0/RC/RS/RE, completed zeroed prefix, paired head/count and
bounded transaction time. Only the final clear write resets the registry and
admission epoch and retires source owners. A distinct `C` journal event lets
the independent lifetime, waiting, handover and admission folds invalidate the
same state. Guest memory, inputs and rendering policy are unchanged.

One focused native test checks valid and rejected clear contexts; the compiled
helper also accepts the actual captured head RAM and registers. Twenty-seven
focused Python tests pass, including rejection of stale owners/admissions after
clear. The original2300-input diagnostic has a retained empty-GL-index failure:
its inherited screenshots start after the shortened interval. Separate saved-data
checks verify all2300inputs,38native images,491camera and1473ADC rows without a
game rerun. These native images do not validate Zeus's displayed gameplay.

Native `101a323e223798bfbea6a8d0097d0fe3d6dbe42f` is built and frozen, SHA256
`b96cb11e28971d43de164565cfe6b38694222f36d9c03e89da2edaaf86b5a688`.
The220-patch export reconstructs `519af842d57cfb91218ed779a4369522e8c48e8b`.
Personal87d/publicv0.5.0 remain unchanged.

The combined retry handles three clears and three complete pool rebuilds,
reaching epoch7, but stops at frame3454/3455 on a separate registry transaction.
It has5120 recorded transitions and no bound scenery yet. It is still a failed
trial, not a full Hong Kong or release-parity pass. The next read-only probe
captures that later transaction before changing registry semantics.

Local evidence in `results/diagnostics/exotica-amazon-20260909`:
`combined-hong-kong`, `hong-kong-pool-clear`, `pool-clear-qualified`,
`pool-clear-export.json`, `combined-hong-kong-clear` and their plans/logs.
The new replay error handling reports native exit/fatal causes before secondary
incomplete-capture messages; it does not change acceptance thresholds.
