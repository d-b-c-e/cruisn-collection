# Zeus upstream refresh, September15

There is one new Zeus renderer change since the previous review. Its small
solid-color register correction is now backported and separately qualified;
the saved Exotica data do not demonstrate a visual benefit from it. The larger
Grid mesh change is deferred. No deployment or public release was made.

- [Depth and blending #16094](https://github.com/mamedev/mame/pull/16094) merged
  September12 as `00c056a8edc37e5c2a2516de282f1f74d5b3a430`. Its head remains
  `54b7ec0720e1d3a3d26a2e881b06628f78732837`, the same revision already isolated
  in our optional render-policy experiment. Merging upstream does not change
  the results of that local evaluation or qualify it for the extra-scene path.
- [Mesh and solid fill #16122](https://github.com/mamedev/mame/pull/16122) merged
  September13 as `c34397f5b63d7fc1ca0f886242a277a93ab036b6`, head
  `8217480f785d3491130eb7af3ac9318bd4cce740`. It adds The Grid's mesh-command
  handling and takes solid fill color from render register6 instead of host
  register0. The author reports no visible Exotica change from that color fix.
- Current GitHub searches return no open PR matching `zeus` and none matching
  `midvunit`. These keyword searches are not a guarantee that unrelated titles
  cannot affect the engines. The current Zeus2 file history confirms the two
  merges above are its newest changes. The current driver path is
  `src/mame/williams/midzeus.cpp`; querying the old `midway` path misses new work.
  Its only change since September9 is the already-reviewed DIP-label correction.
  No changes appear in `williams/midvunit_v.cpp` during that interval.

## Relevance of the new solid-fill correction

The native renderer and independent model helper still take solid fill from
host register0. This differs from the new upstream interpretation. Before
backporting it, six saved original-model journals were inspected, including all
in-model render-register writes rather than just the initial context.

They contain1566 model records and25493 quad commands. The38 solid-fill commands
all select color0 from both the old and corrected register. No8-word mesh,
`0xa7` or `0xaf` command appears in these journals. Two journals cover the same
5000/5001 window; these counts describe the inspected data, not six independent
track regions. The checks include Amazon5072/5073,5978/5979,5990/5991,7187/7188
and the Hong Kong5000/5001 window.

This is not a full-drive proof and does not cover every future-scene model. It
does establish that changing the register cannot repair the sampled solid fills.
Do not attribute the known black margins or distance pop-in to this new upstream
fix without an actual differing operand. The register correction is a
compatibility fix, separate from the much larger Grid mesh implementation.

## Isolated register backport

The device's polygon producer now reads render R06. Its existing extra-data
structure supplies both CPU rasterization and GL submission. The canonical C++
and independent Python model decoders use the same register, including writes
inside a model. No wire format, shader, mesh decoder or depth/blend policy changes.

Focused tests distinguish the host status register from render color, check the
15-bit mask and a red-to-blue in-model change, and preserve the caller's context.
Two native tests and ten focused Python tests pass. Both decoders reproduce all
15,941 emitted polygons from the six saved journals byte-for-byte, including
the38 solid commands whose observed colors remain zero.

Frozen native `a87729610ae5195a34aa008911862bcde5d0c02d` has SHA256
`a255be67964d2fd461de41b310af0738752d5537b902b3b913966182d40df9e8`.
The232-patch export reconstructs tree
`239fd82e5d0f1049068bab8b5f22f7138e0e1aa8`.
One bounded5300-input Exotica replay passes against the retained same-settings
control. All283 saved binary/resource/model/motion files are exact, including
three completed S4 original/private color/depth pairs. All3429 future and active
scene rows,10287 material stages and74010 endpoint GPU rows match apart from
explicit timing fields. No additional full-game or unrelated-game suite was run.

The monitor is3440x1440. These are internal-target comparisons, not renewed4K
presentation, performance, distance-benefit or public-release acceptance.

Local evidence: `results/diagnostics/exotica-amazon-20260909/upstream-solidfill-saved-audit.json`
contains each source hash, frame span, command counts and color comparisons.
`solidfill-backport-qualified/`, `solidfill-regression-qualified.json` and
`solidfill-native-export.json` contain the subsequent tests, live comparison and
build identity. The personal87d installation and publicv0.5.0 remain unchanged.
