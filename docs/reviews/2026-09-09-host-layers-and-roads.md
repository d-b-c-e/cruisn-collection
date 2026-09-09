# World host coverage, road evidence and capture shutdown

This is an undeployed diagnostic checkpoint. The September 9 overnight queue is
paused after its morning cutoff. v0.5.0, the Stream Deck binary, personal settings
and the existing experiment menus are unchanged. Comparable 3x scenery across
all four games remains unfinished.

## Tunnel seam: coverage ownership is significant

The earlier future-section candidate introduced a thin green line across the
Germany tunnel road at frame 4408. Its original hardware geometry, textures,
palette and VRAM were unchanged. That integrity pass did not establish correct
foreground appearance.

The new explicit `--world-host-layer legacy|coverage|split|both` diagnostic separates
two possible causes: auxiliary pixels claiming foreground coverage, and auxiliary
vertices sharing the game's edge-alignment batch. The option is absent by default;
old recordings retain the previous behavior. No launcher option was added.

Coverage mode tags host pixels separately while preserving the dither material tag.
Foreground crack repair can then recognize a narrow gap even when distant terrain
has painted behind it. It preserves one-sided scenery silhouettes and transparent
texture holes. This still uses a screen-space repair heuristic; it is not a depth
buffer or a complete occlusion solution.

Three complete 4502-frame controls have 51 completed 3824x2073 images each:

- Legacy matches all 51 images from the preceding candidate exactly.
- Coverage changes 44/51 images. At frame 4408 the difference from the original
  pending-only control falls from 3,079 to 139 pixels, with no newly differing
  pixels outside the previous difference mask. The visible green line disappears.
- Combined coverage/batch separation matches coverage alone byte-for-byte in all
  51 images. Batch separation adds no demonstrated benefit in this interval.

All three retain original inputs, camera and actual ADC timestamps, ordered host
fingerprints, and identical captured original hardware stream/VRAM/texture/palette
files. This is a targeted improvement, not whole-track visual acceptance. The
139 residual pixels and wider occlusion/handover behavior remain open.

The first legacy launch failed with a render-consumer timeout during boot. Its
receipt is retained; a fresh run completed, but the precise timeout cause is not
established. Two split-only runs also retain their strict FAILs: they captured
41/51 and 50/51 images, missing the end of the requested interval at shutdown.

## Finish queued captures before destroying the machine

The GL thread now acknowledges a frame after its optional capture and presentation
complete. An explicit `MIDV_GL_DRAIN_FRAME` request, accepted only with physical
FFB disabled, waits at most ten seconds for that target before normal teardown.
Ordinary player exits retain their existing path. Replay requests the final aligned
capture frame; older binaries can ignore the request and still face the same strict
completed-image validation.

The final candidate is native `94368ee939ec305bd201fe061d2eed06384380f3`, built
separately with SHA256
`2099a1879ad59bebdb2918117dd166ae6bc4780d54386d4505d8fc77cc2b33b9`.
The preceding layer candidate `5214d945b28`, SHA256
`5fbf43960b3f9ae4ee8f4bbee19e1d07c2bb38a1578a85129e53a633d14fb491`,
owns the completed 4K comparisons above.

The 4K display was unavailable when testing the final shutdown change. That
requested run failed explicitly instead of silently substituting a display.
An explicitly small-window 4502-frame replay completed all 51 captures with a
250 ms diagnostic consumer stall. A separate 300-frame boundary check exercised
the wait: target 298, acknowledged 298, 32 ms wait, all three captures completed.
These are shutdown checks, not renewed 4K acceptance. The full seven-game/default
regression set was last qualified on the preceding `de1d6333cd9` candidate; it was
not rerun on the final candidate at this morning cutoff.

## Road rendering has an independent reference now

`lua/world_road_capture.lua` and `harness/verify_world_roads.py` promote the earlier
local probe into reusable bounded diagnostics. The road path keeps unpaired
vertices in the original ROM model but selects distant polygons/materials from
a small RAM template using metadata and the actual depth threshold. It cannot
be decoded as an ordinary packed ROM model.

The tunnel interval 4400–4500 and later road-gap interval 6400–6800 complete their
original 4502/6802-frame prefixes. Across both intervals:

- 23,589 centers, matrices, projected vertex buffers and template choices match.
- 17,821 calls use the distant template.
- 21,123 unclipped calls match their original ordered DMA words.
- 2,466 clipped calls remain outside the polygon reconstruction. Unowned draw
  events from other rendering paths are counted separately, not certified.

Final descriptor verification now optionally includes road render fields:
8,155 descriptors match, including 1,332 road-class allocations; 67 custom-class
allocations remain excluded. The first road-field check missed the class's bit-24
section tag and is retained as a FAIL. The corrected reference checks that bit
and the bit-25 section-direction contribution against the allocation code; this
recording does not establish broad direction-flag coverage.

No road renderer was integrated. An unfinished local C++ selection/decoding draft
is preserved under `results/diagnostics/world-host-layers-20260909/unfinished-road-draft`;
it is not compiled, exported, deployed or public proof. The canonical host decoder
still excludes roads. Next work is to integrate that codec with template/resource
guards, verify native/Python scene equality, then test whether it actually closes
the distant ground gaps without new foreground defects.

## Reproducibility and remaining acceptance

The 138-patch export reconstructs native tree
`3e7058bd9f494a871bae2ffd687e61edcc4366c2` exactly. The local Python/native/GPU
report passes 203 Python tests without skips, 15 native helpers and 32 GPU checks
across 42 commands. Source identity is
`388cb344a01bc0271310f46f9f42bb4238506da3643eeab6a99353591263dc77`.
Public proof lives
under `results/proof/2026-09-09-host-layers-and-roads`; it recomputes selected pixels,
input/timing/fingerprint equality and scalar road-selection/descriptor decisions.
Full raw geometry/material reconstruction and native build checks remain hashed
receipts. ROMs, raw models/textures and personal state remain local.

Before deployment: renew final-candidate 4K and seven-default checks; investigate
the retained boot timeout; complete road, material-lifetime and handover acceptance;
then implement separately guarded adapters for World 2.5, USA, Off Road and Zeus.
No cross-game 3x claim or removal of existing experiments is justified yet.
