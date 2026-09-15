# Combined candidate: seven default regressions pass

The existing seven-case local regression suite passes once on frozen native
`ebe10e87c333db14427b791a105b433a2641c0dc`. No failure or timing retry was needed.
The personal Stream Deck installation and public v0.5.0 package are unchanged.

| Case | Recorded inputs | Memory/packet telemetry samples | Result |
| --- | ---: | ---: | --- |
| USA original | 5,012 | 2,483 | Pass |
| USA widescreen | 5,012 | 2,483 | Pass |
| World 2.4 | 6,000 | 2,336 | Pass |
| World 2.4 Germany | 9,269 | 7,516 | Pass |
| World 2.5 | 6,000 | 2,538 | Pass |
| Off Road | 6,000 | 2,090 | Pass |
| Exotica | 6,000 | 2,684 | Pass |

All43,293 recorded inputs/times compare exactly. The V-Unit cases compare620
native snapshots exactly; Exotica's21 completed GL images also match exactly.
Its native CPU rasterizer is disabled, so its100 native snapshots are not an
additional meaningful image oracle. All22,130 active telemetry samples match the
independent memory probes, with each case clearing its active-count/speed gate.
The four applicable World/Exotica force-signal checks pass. Physical force was off.

Six predefined timing windows clear their95% gate. Ratios range from99.973% to
100.005%, including USA's selection and driving windows. These are existing
recorded-presentation default cases, **not** new 3× performance measurements,
final4K package acceptance, fresh-install checks, a soak or physical wheel tests.
No new local all-tests/package suite is claimed.

Native SHA256:
`6f65d28f6936c85f20d32a6cf2d251603f58ba38df7ad4c5d2c1bf8d9d3bafc2`.
The source identity remained unchanged across the run:
`34ace5674c134808e8932fd3cd3ab75380af5884dca16e320b07cc718651b710`.
Subsequent standalone diagnostic work is not covered by that source identity.

Local evidence: `results/diagnostics/parity-defaults-20260915-ebe/report.json`,
`qualified.json`, the seven case reports and the retained process log. Reuse this
result for unchanged native/default behavior; another whole-suite run needs a
new change, failure or unresolved concern that justifies it.
