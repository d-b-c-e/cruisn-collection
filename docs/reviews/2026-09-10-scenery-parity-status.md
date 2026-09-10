# Extended scenery parity — September 10, 2026

There is tangible progress toward all four games, but no release-ready claim of
equivalent 3× distance or eliminated pop-in. All four now have native prototypes
that decode upcoming scenery without advancing guest simulation. Most recent
work has concentrated on Exotica, whose Zeus renderer needs a separate depth,
material and command-order implementation.

This assessment describes development candidates. The personal Stream Deck
binary and public package remain v0.5.0, native SHA256 beginning `87d04de4`.
The launcher's existing distance menus do not select these newer host renderers.

## Game-by-game evidence

| Game | Demonstrated improvement | Main remaining work |
| --- | --- | --- |
| World 2.4 | Future 3× adds mountains/buildings beyond 2× in 16 of 31 Germany captures. Host roads fill a measured distant uphill gap. | Broader terrain continuity, clipping, material lifetime, foreground occlusion and activation handover. New York remains a separate known problem. |
| World 2.5 | 3× changes 10 additional images beyond 2× in a 30-image sample; ordered scenery and images repeat. | Road/ground rendering is still restricted to 2.4. Disconnected terrain remains visible in the 2.5 sample. |
| USA | Earlier scenery at 1×/2×; 3× adds small changes in three of 16 sampled images. Independent geometry and original resources match. | Last measured 3× runs reached about 97.6%/97.0% emulation speed after caching; 2× reached 98.7%. Full-speed acceptance and broader visibility coverage remain open. |
| Off Road | 2× changes all 40 sampled images relative to 1×; 3× adds changes in six. Quiet runs measure approximately 100% speed and repeat exactly. | Existing scripted El Paso recording spends too long near one hillside. An attended complete-track drive is needed for terrain, tunnels, finish and handover coverage. |
| Exotica | Live future geometry/material insertion works through the private wide-depth renderer. Full Amazon drives preserve original route/resources; denser actual display sampling finds 33 of 233 frames differing at 3× versus 2×, and 3× repeats all 233 exactly. | The inspected changes are mostly small additions through foliage or at margins. Without heavy readbacks, 2× measures 94.69% game speed and 3× 90.79%. Useful visibility, opacity/handover, full speed and broader routes remain open. |

Detailed evidence: [World 2.4 roads](2026-09-09-host-road-integration.md),
[World 2.5](2026-09-09-world25-host-scenery.md),
[USA](2026-09-09-usa-future-rendering.md),
[Off Road](2026-09-09-offroad-host-rendering.md), and
[Exotica live future rendering](2026-09-10-zeus-live-future.md).
These captures sample particular routes; changed pixels alone are not visual
acceptance or a measure of how much earlier an object appears.

## What the recent Exotica work establishes

The full 3× Amazon run and repeat match all 14 completed internal color/depth
snapshots, five sampled immediate insertion packets/buffers and the ordered
scene/material records across 6,953 scenes. All five sampled insertions per run
also match an independent geometry preparation and pixel comparison.

Nevertheless, more submitted geometry has not yet produced more completed 3×
pixels than 2× in that sample. At one separately investigated bridge scene,
future drawing changes 131,707 pixels immediately, but the nearer original scene
subsequently covers every one. Disabling that correct occlusion would introduce
new visual errors. At another scene the eligible 2× and 3× geometry is identical.

The 2× versus 1× difference appears in four completed internal snapshots. One
larger difference is behind the race-results screen; it should not be counted as
proof of better distant scenery while driving. The next comparison presents the
extended target explicitly and records 233 completed 4K/CRT frames per drive,
using the game's actual display page. Sparse internal snapshots are insufficient
to settle the useful 3× question. The first [dense actual display comparison](2026-09-10-zeus-future-presentation.md)
now finds 33 of 233 frames differing between 2× and 3×. The largest changes occur
at the grid; inspected later changes are small regions through foliage or at the
left margin. The3× repeat matches all233 displayed frames exactly. This extends the sampling evidence
without turning changed-pixel counts into a useful-distance acceptance claim.

Separate Amazon candidates also address palette flicker, the stale rectangle
around the reported 1:12 and measured black ground wedges. The full active-margin
candidate passed its Amazon/repeat/Hong Kong and default checks, but measured
only about 93% speed without heavy captures. It is not deployed and is not yet
combined with the new future-target presentation.

## Next acceptance work

1. Build on the completed dense Exotica comparisons: improve driving visibility,
   opacity and the transition into original active objects. The original fade
   update is now a standalone helper with independent verification.
2. Reduce the [measured future-rendering cost](2026-09-10-exotica-fade-and-performance.md).
   The 3× preparation/upload path alone reaches only 90.77% game speed, while
   mirroring the original scene reaches 99.99%. Carry applicable improvements to USA.
3. Complete World 2.5 roads/ground and obtain an attended Off Road drive.
4. Validate original route/resources, materials, occlusion, handover and smooth
   4K output across more tracks. Renew the seven default regressions on the final
   combined binary before deployment or simplifying experiment options.

The last clean seven-default suite belongs to the native `50a` milestone. A
later USA widescreen run retained a 6.13-second menu-timing failure; a passing
retry does not erase it. Recent Exotica-specific checks are not a new full-suite
pass. Automated physical force remains zero, and World force tuning is deferred.
