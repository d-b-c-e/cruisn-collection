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

## External objects entering the pool

The later read-only3500-input control passes. At3454, the original free routine
returns object10B21, then five other externally constructed objects, into the
normal free list. None belongs to the rebuilt1201-node pool beginning1B5BD,
and none has an observed common-allocator allocation. Their actual paired
head/count writes are valid; treating every post-reset object as originating
inside that pool was incorrect.

The registry now permits an explicitly verified external adoption. The driver
still checks the original free instructions, slot/link, head/count and time;
after a rebuild it allows an unseen free only outside the known pool extent.
An unseen slot inside that free pool, a known double free, stale owner, invalid
address or exhausted history budget still rejects. The adoption is recorded as
an unknown free, with no fabricated allocation generation. Global clearing
removes the known extent until the next complete rebuild.

An independent raw head/count fold covers5800 transitions and all six external
adoptions through3490. The canonical compiled registry matches every operation
and result, and all5121 earlier native event identities/counts match its prefix.
The raw probe models rebuild at the observed head write; the existing native
tail/link guard supplies completed-rebuild proof. Eight lifetime Python tests
and the native lifetime test pass, including explicit adoption, repeated-free
rejection and history limits. The next candidate's full combined Hong Kong
trial is pending; this saved-data qualification does not clear it.

Native `c7e3e6b456fa071dc00110f60fd182a4629fa80c` is separately frozen, SHA256
`4a69ed65998705298bcb17495461403fa5e82e920be954747cbcc89b131d76b4`.
The221-patch export reconstructs `f62dd86d148e7b1e698e632c31198b4415de213d`.
Local evidence: `hong-kong-pool-transactions`, `external-pool-qualified`,
`external-pool-export.json` and `combined-hong-kong-external`.

Local evidence in `results/diagnostics/exotica-amazon-20260909`:
`combined-hong-kong`, `hong-kong-pool-clear`, `pool-clear-qualified`,
`pool-clear-export.json`, `combined-hong-kong-clear` and their plans/logs.
The new replay error handling reports native exit/fatal causes before secondary
incomplete-capture messages; it does not change acceptance thresholds.
