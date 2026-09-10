# Amazon margin artifacts and extended-depth capacity

The marked Amazon drive has several different failure modes. The palette fix
already restores the reproduced black sky and incorrect distant colors near
game 0:09 and 0:19. The later black ground and the checkpoint rectangle need
separate fixes. This review follows the [upstream audit](2026-09-09-zeus-upstream.md)
and [palette-lifetime validation](2026-09-09-zeus-palette-lifetime.md).

## Marked gameplay windows

Five captures enable actual native CPU rasterization alongside the enhanced GL
renderer. Every capture matches all 1,048,576 native RGB24 and depth entries in
the independent CPU oracle. Camera and actual ADC reads/times preserve the
original recording's corresponding prefix. Their overall replay reports retain
the expected FAIL against the original recording's skipped CPU images; those
reports are not relabeled as passes.

| Game elapsed | Capture | Finding |
|---|---|---|
| 0:35 | 5072, GL5060–5084 | Left ground wedges also appear in independently extended CPU coverage. Of 519 black margin pixels in the measured lower area, 482 have no submitted triangle coverage. |
| 0:45 | 5644, GL5632–5656 | This center sample has a right ground wedge. Of 2,006 black margin pixels, 2,004 have no submitted geometry. |
| 0:57 | 6330, GL6318–6342 | No black ground in the measured lower margins at the exact center. The approximate user timestamp still needs broader coverage. |
| 1:12 | 7215 and 7216, GL7198–7228 | A checkpoint post persists in the right margin on alternating frames after the post is absent from submitted models. Every-frame captures are essential; even-frame captures miss it. |

The local wide CPU coverage prototype preserves the full native center exactly.
It starts unknown margins without prior geometry and separately rasterizes the
extra columns. Its margin output is an absence/coverage diagnostic, not a GL
pixel oracle. Counts above cover the lower 250 rows of the two 88-column margins
on the active page. Unknown contents on the inactive page are excluded.

## Checkpoint rectangle hypothesis and isolated candidate

At frame7200, the checkpoint post is real geometry, including in the original
4:3 CPU framebuffer. Its captured vertices have positive depths; clipping that
model away would hide legitimate content. Later captures no longer submit that
model, but completed GL frame7215 retains a flat vertical remnant.

The corresponding guest clear covers only rows216–399 of page0, or616–799 of
page400: 184 rows. The enhanced renderer clears the same rows in its widened
margins. Old color and depth can therefore survive in their upper216 rows.
New, more distant geometry fails against that old near depth. This explains the
alternating page behavior and is under direct native A/B validation.

Native `c527bbf4792533b587d8d48692d69ca112b0fc1e` adds an isolated
`--zeus-margin-clear legacy|page` diagnostic. Page mode expands an aligned clear
contained within one known400-row page to that page's full margins. It preserves
the guest's512-column center and the other framebuffer page. Unknown, unaligned
or spanning layouts keep their original clearing behavior. Absent settings keep
old recordings unchanged. Explicit trials require Exotica, live GL, a candidate
and physical force zero; startup and completion receipts verify the selected mode.

Four synthetic GPU cases reproduce stale upper-margin depth on both pages and
verify its removal, with exact center/other-page colors and depth. Native tests
cover every aligned subrange of both pages plus unaligned, spanning and wrapped
addresses. The first GPU fixture failed because it used a nonexistent capture
field; that failure is retained, followed by the corrected four passing cases.
These are fixture results, not yet gameplay acceptance.

Full local checks pass278 Python tests without skips,31 native helpers,
10,081 C31/137 yaw vectors,32 existing GPU cases,25 upstream policy cases,
three palette cases and four page-clear cases across87 commands. Source identity:
`7cb966d14bcf2f06986024ff7e7d68bb58c8fa7add94a9cbe6a6f3dbefecfde2`.
The serial native legacy/page/repeat Amazon trial is active; its dense window
captures every completed frame7198–7228 and actual CPU resources at7216.

Separate candidate: `build/candidates/c527bbf4792/vunit.exe`, SHA256
`238a879814d43fae349329d88a21e77a1d3dbdc5325c27be42274f8b89d7baef`.
The152 exported patches reconstruct tree
`dd624bb767ab5f044dfa42c57ff7d42cb395fd9d`.
All-seven-default acceptance currently belongs to parent5a80/SHA66b0132e.
The personal Stream Deck executable remains v0.5.0/SHA87d04de4.

## A further obstacle to genuine 3x distance

The host must support larger depth values before drawing distant future scenery.
The current Zeus fragment shader clamps to the original24-bit depth maximum.
Independent future-section descriptors and actual camera/C31 transforms already
produce larger centers when the original far-sphere criterion is expanded.

| Snapshot | 1x potential spheres / over24-bit centers | 2x | 3x |
|---|---:|---:|---:|
| 3500 | 1,286 / 0 | 1,798 / 504 | 2,719 / 1,425 |
| 4500 | 1,738 / 0 | 2,565 / 745 | 2,565 / 745 |
| 5500 | 624 / 0 | 624 / 0 | 624 / 0 |

These counts omit horizontal culling, occlusion and material readiness; they are
capacity evidence, not a count of new visible objects. Vertex extents can exceed
their centers. Simply feeding all these quads into the existing depth path would
collapse distinct distant surfaces at its maximum. A separate background depth
layer or an explicitly wider host depth mapping must preserve original hardware
depth comparisons, translucent overlap and handover. The existing private-state,
WaveRAM upload and palette-binding work remains necessary as well.

Raw local evidence: `results/diagnostics/exotica-amazon-20260909`.
Game models, ROM/RAM, palettes and WaveRAM stay local. There is no extra Exotica
host drawing, release, deployment, World tuning or experiment removal at this
checkpoint. Page clearing cannot supply ground geometry the game never submitted.
