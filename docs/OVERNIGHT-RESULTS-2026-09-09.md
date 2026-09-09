# September 9 morning handoff

At this morning checkpoint the overnight queue was **PAUSED**. The maintainer
has since [explicitly resumed it](OVERNIGHT-2026-09-09.md); see the
[road-integration milestone](reviews/2026-09-09-host-road-integration.md) for newer work. Robust, comparable 3x draw distance across all
four games is **not complete**. The useful progress is a World 2.4 future-scenery
prototype, a targeted tunnel correction and substantially stronger road diagnostics.

| Game | What is established | What still blocks a replacement |
|---|---|---|
| World 2.4 | Host future sections add visible mountains/buildings at 3x over 2x in 16/31 Germany images. The original drive and 3x repeat stay exact. A coverage trial removes the newly exposed tunnel line in a targeted 4K comparison. | Roads are still excluded; distant ground gaps, remaining occlusion/handover and late unbound materials need work. Final shutdown candidate needs renewed 4K/default regression checks. |
| World 2.5 | Section/material layout and 2,686 ordinary allocation membership decisions have independent read-only checks. | No native future-section adapter yet; its active/pending behavior differs from 2.4. |
| USA | Existing global trials and bounded memory mappings are available. | Guest residency changes the original route; no useful extra 3x visibility is established. Needs a host scenery adapter. |
| Off Road | Existing coherent 2x/3x experiment has modest gains and repeatable candidate output. | No additional 3x pixels established; original timing/geometry differences remain. Needs its own residency/submission adapter. |
| Exotica | Frustum, admission and far-plane measurements identify separate limits; mapping controls preserve original GL images. | Earlier admission changes depth bias/order. No robust host scenery or extra-distance replacement yet. |

The latest [coverage/road review](reviews/2026-09-09-host-layers-and-roads.md) records
the accepted checks and retained failures. The [future-section review](reviews/2026-09-09-world-future-sections.md)
contains the full-drive 3x evidence. Road diagnostics now reproduce 23,589 projected
calls and 21,123 unclipped ordered draw calls across two gameplay intervals.
The native road implementation remains an uncompiled local draft.

The shutdown fix adds a bounded, output-free wait for queued diagnostic captures.
Small-window checks complete 51 captures and exercise a 32 ms final-frame wait.
The final 4K attempt was blocked by the unavailable 4K display; this was recorded
as a failure, not replaced with a different-resolution visual pass.

**Deployment:** Stream Deck remains on the accepted v0.5.0 native binary
(`87d04de4…`). The new candidate (`2099a187…`) is built separately. Personal
settings, original drives, v0.5.0/v0.4.0 packages and tags are preserved. No menus
were removed, no release was published and no physical force was generated.
Hosted workflows remain disabled; World force tuning remains deferred.

Next: finish the verified road codec and World 2.5 adapter, renew 4K capture and
cross-game acceptance, then carry the contracts to USA, Off Road and Zeus. Useful
attended recordings remain World New York (including the finish), a longer Off
Road route and an open Exotica course. Existing experiment options should only be
retired after their replacements show visible benefit and pass these checks.
