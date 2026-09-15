# World terrain boundary: original mesh edges remain visible at 3×

The detached terrain in the saved Hawaii scene is still unresolved. A newly
identified lower edge belongs to the original authored model, whose complete
vertex depth range is already inside the 3× plane. Increasing the distance or
clipping that particular model cannot extend its bottom edge.

## Source and image checks

The saved World 2.5 dispatcher at `0x58ec` reads a table through RAM `0x58eb`;
the captured table resides at ROM `0xc10c41`. It selects the first matching
metadata entry and returns without a handler if none matches. The duplicated
`0xa08` entry therefore uses its first handler. Disassembly uses the unchanged
MAME C31 disassembler against the captured RAM, without executing the game.

Among the 244 excluded future definitions, 66 have unmatched metadata:
34 `0xa32`, 31 `0xa05`, and one `0xa16`. The no-match path preserves the parent
descriptor. An offline prototype allows only this group, leaving all existing
ordered quads exact. It adds 24 quads but changes **zero** completed pixels.
Matching handlers inspected for the other definitions schedule animation/effect
work, including later model replacement. No blanket static-object interpretation
is justified, and no custom-object support is promoted from this test.

A second prototype keeps only complete in-range polygons from otherwise
depth-crossing models. It adds 113 quads; also allowing a near-intersecting sphere
adds eight more. Both preserve all previously accepted ordered quads and change
the same 682 completed pixels. The terrain gap remains. Crossing polygons still
are not clipped; these are diagnostic variants, not runtime fixes.

Disabling the separate scenery LOD selection makes all 8,403 ordered quads and
the completed image exactly unchanged. Full-detail road selection was already
active. The suspected terrain uses its original model; this sample provides no
evidence of a hidden lower-detail scenery model causing the gap.

## A concrete authored edge

Original host quad 880 covers the detached lower boundary. It belongs to object
`2147484204`, source `15967477`, original model `15960292`, section `16043070`.
An independent C31 reconstruction matches all 26 emitted quads from its 54
vertices and 38 source polygons. Its depth range is 204,219.297–221,957.781,
wholly within the configured 240,000 far plane. Its flags are `0x2000`.

The lower edge between vertex indices 32/33 runs from projected
`(333.912, 214.057)` to `(324.235, 215.723)` in native coordinates, and occurs only
once in this model's index topology. Adjacent sampled pixels below it have no
host coverage and show the original ocean tile, drawn before host insertion.
This is not a later background overwrite. Index topology can include duplicated
positions, so open-edge counts alone are not a complete manifold assessment.

This narrows the next question to adjacent authored coverage and the relationship
between terrain boundaries and the game's ocean backdrop. It does not prove all
World gaps have this cause. Generic clipping may still improve other crossings,
but cannot create missing mesh below this already in-range edge. Automatic
skirts, texture stretching or foreground occlusion bypasses are not implemented.

All comparisons use one offline 2736×1600 quality render with original command
ordering/resources. The existing baseline image is rechecked byte-for-byte
before each comparison. No new game replay, MAME build or deployment was needed.
Local evidence: `results/diagnostics/world25-roads-20260914/` directories
`custom-dispatch`, `custom-noop`, `partial-far`, `partial-both`, `full-scenery`,
and `terrain-boundary.json`. Raw instructions, game meshes and screenshots stay
local. Personal native87d/public v0.5.0 remain unchanged.
