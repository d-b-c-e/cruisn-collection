# Carrying private draw admission into original objects

The standalone `native/exotica_admissions.h` now carries actual private draw
history into later source allocations. It separates pending future descriptors
from generation-qualified objects. Binding, removal, slot reuse and registry
reset are explicit; a missed lifecycle event rejects instead of silently adopting
the current slot occupant. Duplicate/empty draw claims and invalid order reject
before updating the ledger. Command tickets must retain their qualification by
value so later object removal does not alter an already committed command.

This helper is not yet linked to MAME. The caller must submit only nonempty
instances from successfully queued private packets, observe all source lifecycle
events, and establish the packet's actual placement. The ledger establishes
submission history, not that any particular pixel was visible or an opacity policy.

One recorded Amazon packet at5072 supplies a real test: its GPU receipt confirms
draw mode, scene and538 quads. All packet geometry matches the instance slices.
Only63 of94 instances have quads and enter the ledger; zero-quad instances do not
gain admission. The exact later lifetime journal and1,150 observed original
commands produce40,147 compiled operations. All output matches an independent
Python fold.61 original commands qualify from this particular earlier packet.

Among the11 saved endpoint examples, eight qualify and three remain excluded.
The initial expectation of exactly seven was wrong: the earlier reconstruction
excluded model2 because its preceding model lacked an ordinary CPU context.
The new current-context observer independently proves its original and endpoint
bytes, while the old source/generation audit already proves its earlier admission.
The failed seven-only assertion remains; this is a documented coverage increase.

One new completed GPU replay replaces those eight models'74 quads at their
original command indices. Its full color and depth hashes equal the earlier
seven-model result: the additional model has no net visible contribution in this
completed interval. Relative to the original,3,830 RGB pixels and2,331 depth
samples differ; no new black pixels, other-page changes or invalid depths appear.
This is one offline2736×1600 page, not live temporal or4K acceptance.

Next connect admission to actual future/waiting queue success and bind its proof
to original command tickets. Private-target replacement must preserve the normal
target and original material/command order. Do not turn endpoint preparation into
an unconditional opacity override. No further broad replay was needed for this
standalone step; the latest native binary remains e0afe6360fd.

Local evidence: `results/diagnostics/exotica-amazon-20260909/admissions-actual`
(initial expectation failure), `admissions-qualified`, `admitted-endpoints-render`
and the native admission unit test. Personal/public builds, FFB and launcher
settings are unchanged.
