# Zeus upstream refresh: solid-fill source requires a separate trial

The upstream depth/blending work we evaluated as a gated policy has now merged:
[PR16094](https://github.com/mamedev/mame/pull/16094), September12,
merge `00c056a8edc37e5c2a2516de282f1f74d5b3a430`. Its head is the previously
examined `54b7ec0720e1d3a3d26a2e881b06628f78732837`. This is a status update,
not a newly discovered depth fix.

[PR16122](https://github.com/mamedev/mame/pull/16122) merged September13 as
`c34397f5b63d7fc1ca0f886242a277a93ab036b6`. It adds eight-word mesh commands,
including interpolation and triangle assembly used by The Grid, and changes
solid-fill color from the host/status register00 to render register06. The
latter change is absent from our native renderer, `native/zeus_model.h`, and
independent Python model decoder. A shader-only change would not correct the
color source or keep those paths consistent.

## Evidence from Exotica

The saved, complete GPU command journals contain 18 solid quads out of3,349
at native5072/completion5073, and zero out of3,459 at7187/completion7188.
All18 currently carry black. Their projected bounds are small and wholly
inside the original horizontal viewport: x36.59–151.17, y100.89–208.53.
This is actual use of the affected color path, but does not explain the large
black margin patches. The journals do not include render06 at each submission,
so they cannot tell us whether the corrected color would differ.

Sixteen saved future, waiting, handover and active quad arrays at5072/5644
contain no solid quads. That is a bounded sample, not a full-drive claim.
No new Exotica renderer change or replay is justified from these counts alone.

Next recover current render06 from corresponding owned model contexts or add
a bounded read-only solid-command observer. Compare the actual old/new colors,
then trial the narrow color fix separately from mesh support and transformation
refactoring. Preserve original recordings and qualify both original and private
render paths if it changes visible output.

## Scope and retained evidence

Fresh GitHub API PR and merge responses are retained locally under
`results/diagnostics/zeus-upstream-20260915`, along with `solid-usage.json` and
`solid-locations.json`. The initial local reader used the legacy CPU-record
parser on a GPU journal and rejected it; the corrected pass uses the canonical
strict GPU journal parser. No failed result was accepted.

This refresh examined the two named PRs and recent Zeus source history. It does
not replace the September10 complete open-PR inventory or claim that every
currently open PR has been reviewed again. Native, personal and public Exotica
rendering remain unchanged by this investigation.

## Owned-context follow-up

A neighboring original capture at5071 supplies the missing device contexts:
240 models reconstruct3,255 ordered original quads byte-exactly, with no model
exclusions. Re-decoding them with render06 as the solid-color source changes
none of the19 solid quads; both sources are black. The modified decoder preserves
all geometry and all other state fields. This is a separate adjacent capture,
not an assertion that its19 quads are the18 at5072.

This removes the immediate justification for another Exotica replay or broad
mesh backport to address these particular artifacts. Retain the upstream fix as
a separately qualified maintenance item. Local `solid-owned-contexts.json` and
`solid-owned-original-qualified.json` retain the comparison and original-byte
qualification. No live observer or renderer change was made.
