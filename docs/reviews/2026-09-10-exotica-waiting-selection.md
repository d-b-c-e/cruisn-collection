# Exotica allocated scenery before first submission

The reusable waiting-selection helper now derives eligible objects from the
native allocation registry and reproduces five independently checked scene
snapshots. It is **standalone**, not yet linked into the live renderer. This
closes the selection gap before trying live continuation; it does not establish
fade/handover or eliminate pop-in.

## Why this matters

The existing future-only pass excludes a source as soon as it becomes allocated,
although the original game can wait several seconds before first submitting it.
The [drawing-admission investigation](2026-09-10-exotica-drawing-admission.md)
measured that gap. This helper retains an ordinary source only while its actual
allocation is still live, bound to that source and never submitted by the game.

`native/exotica_waiting.h` takes ordered reconstructed sources, the matching
bank/track realm, `scenery_lifetimes::Registry` and coherent current RAM reads.
It returns full slot/epoch/generation/source handles separately from geometry.
Historical sources remain `future=false`; eligibility no longer requires
rewriting that field to disguise allocation state.

The helper preserves source order, rejects duplicate identities and checks
immutable position/rotation/model/material/progress operands against the source.
It copies current mutable render fields, normalizes the previously mapped game
mode flag and never reads the adjacent object's padding word. Reset/reuse and
previous original submissions invalidate waiting eligibility. Source, slot,
command-ring, realm and count bounds remain explicit; failure does not partially
replace the caller's output.

## Actual event and geometry comparisons

The local native analyzer folds validated prefixes of the accepted 795fc native
lifetime trace up to each snapshot's exact recorded device time. It derives the
selection itself; the older independent Lua/Python lists are comparison oracles,
not inputs to the selection helper. The native registry and current operands
then feed the canonical geometry assembler.

| Native snapshot frame | Selected waiting allocations | Geometry variants checked |
|---|---:|---:|
| 3900 | 252 | 1×/2×/3×, current/completed object fade |
| 5072 | 155 | 1×/2×/3×, current/completed object fade |
| 5644 | 298 | 1×/2×/3×, current/completed object fade |
| 6330 | 52 | 1×/2×/3×, current/completed object fade |
| 7187 | 1 | 1×/2×/3×, current/completed object fade |

All **30 comparisons pass**: allocation handles and source order match the
independent original-event join; ordered instances and quad bytes match the
independent Python geometry. The initial local-header run and the separately
compiled canonical-header run both pass. These five boundaries precede the
post-race reset; reset/reuse behavior additionally has synthetic coverage.
Completed fade is a comparison variant, not a promoted opacity policy.

The native unit test covers first submission, reuse, reset, a different realm,
all immutable operands, current mutable fields, source order, padding isolation,
command-ring exclusion and boundary/budget failures. Full local checks pass:
**358 Python tests with no skips, 50 native tests, 142 commands including GPU**.
The 518-file source identity is
`e7af2918899c599e4519f1f25613d3d6ce23f4a45e67a27c6beb04e0a621567e`.

Local evidence is under
`results/diagnostics/exotica-amazon-20260909/waiting-registry-canonical` and
`waiting-selector-local-checks`. The [public proof](../../results/proof/2026-09-10-exotica-waiting-selection/README.md)
checks hashes and receipt consistency. It does not redistribute game resources
or rerun raw scene/native/GPU execution.

## Next live step

First add explicit observation that computes these candidates at the existing
device boundary while leaving the current future packet unchanged. Require
lifetime coverage through that boundary and complete allocator transactions.
Compare actual ownership, proposed geometry, original route/resources and
completed 4K frames before adding drawing.

Drawing must merge future and waiting candidates in source order, using current
owned materials and the existing private wider-depth target. First-fade/opaque
handover remains a separate problem: first submission is not necessarily first
visible pixels, and object fade fields are not every quad's final alpha. Preserve
intrinsic transparency and correct foreground occlusion.

Native795fc, personal87d and public v0.5.0 are unchanged here. The earlier
seven-default suite still retains one World renderer timeout despite its passing
retry; this standalone checkpoint does not renew or replace that suite.
