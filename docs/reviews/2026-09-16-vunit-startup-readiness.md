# World and Off-Road startup readiness

Short original-only replay prefixes now identify both the first scene hook and
the first initialized frontier for World2.4, World2.5 and Off-Road. All six
prefixes pass input, timing and original native-image comparison. No host
renderer was enabled and no physical FFB was used.

| Game | First scene | First initialized frontier | Matched scene-prefix rows |
| --- | ---: | ---: | ---: |
| World2.4, Germany recording | 623 | 1675 | 530 |
| World2.5, Hawaii recording | 623 | 1206 | 295 |
| Off-Road recording | 1045 | 2170 | 512 |

These are observations of the recordings, not activation constants. The initial
2,101-input prefixes saved scenes1/2/16. Additional bounded prefixes saved the
missing first frontier:1,212 inputs for World2.5,1,682 for World2.4, and3,502 for
Off-Road. The latter's earlier prefix remained entirely pretrack. The updated
observer can select the first nonzero frontier at the actual scene hook, removing
the need to guess its snapshot sequence. This optional snapshot shares the
eight-snapshot budget and must be captured before the observer reports success.
Default observer output remains unchanged.

The overlapping original scene records and first RAM/fast-RAM operands match
between each pair, excluding requested snapshot flags and the added optional
frontier marker. Every first initialized frontier passes the full existing
native stock-code, scene, future-source and applicable road guards.

World's early empty state exposes an important difference:2.5 already recognizes
the cleared track state, whereas2.4's scene guard rejects its zero pending limit.
The stock-code, future-code and road-code checks still pass for both. A future
2.4 startup policy must explicitly recognize and skip this qualified empty state;
it must not relax the instruction checks or attempt to render menu lists.

Independent Python descriptor/model projection agrees with the native helper
for both initialized World snapshots, including roads at1×/2×/3×. No new later
allocation ownership evidence was captured in these runs. Off-Road's first scene
is a valid empty pretrack preparation. Its initialized snapshot prepares569
objects and1,560 quads at3×; the entire ordered output and counters match Python,
and native cold/warm cache output is identical.

Native candidate03ddf36820c is unchanged. These observations establish startup
readiness for the captured states, not early live rendering, transitions through
multiple races, performance or release parity. Next extend the gated USA
activation path with each game's verified readiness rules, then verify actual
execution before changing session-end policy.

Local evidence: `results/diagnostics/world25-roads-20260914`, under
`world24-startup-*`, `world25-startup-*`, `offroad-startup-*`, and
`vunit-startup-qualified/report.json`. Raw game operands remain local.
