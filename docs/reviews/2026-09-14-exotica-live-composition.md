# Live extended scenery and ground-margin repair

An explicit development mode now combines Exotica's early future scenery,
retained waiting scenery, and active ground-margin repair. Short and full Amazon
replays pass. The sampled black left wedges around game elapsed35 and45 seconds
are repaired while the existing extended scenery remains intact. This is still
a private candidate: no personal deployment, public release or physical FFB test.

## Runtime change

`--exotica-host-compose margins` requires an explicit candidate, active/future/
waiting drawing, lifetime observation, an actual command fence, tracked private
materials, and the private wide-depth renderer. Existing incompatible options
remain rejected when this gate is absent. Physical FFB remains disabled.

The producer preserves the completed waiting geometry and ownership cohort until
the active pass. Confirmed duplicates are removed using the previously verified
geometry/material helper. Retained owners must match identities observed when
the active scene was sealed, and remain live/unsubmitted at device completion.

The consumer enforces three ordered material phases per scene: early future,
zero-page waiting continuation, then ready-time active changes. The waiting phase
does not clear pending guest dirty pages. The active phase commits those pages
after queuing its owned image; the next future stage advances from that image.
Original game texture and palette updates remain independent.

The active pass shares the private wide color buffer and draws only the margins,
using a copy of its D32 depth buffer. It preserves the original target and the
existing private depth. Snapshot checks enforce unchanged original color/depth,
unchanged center/other-page color, and unchanged private depth. The existing
standalone active path retains its original D24 behavior.

## Validation

The accepted short replay covers5200 inputs,3400 camera rows and10200 actual ADC
samples. All match the original recording. All3332 scenes deliver their three
material stages. At5072 and5080, independent filtering matches the native bytes,
removing59/52 duplicate instances and490/139 duplicate quads respectively.

| Native proposal | Remaining active quads | Black pixels repaired at insertion | New black pixels |
| --- | ---: | ---: | ---: |
| 5072 | 32 | 6,459 | 0 |
| 5080 | 21 | 4,231 | 0 |
| 5644 | 248 | 1,919 | 0 |
| 6330 | 71 | 0 | 0 |
| 7187 | 0 | 0 | 0 |
| 8760 | 0 | 0 | 0 |

The short run's completed5073 displayed color/depth page matches the independent
offline composed render exactly. Its original GPU color/depth and entire private
depth match the prior accepted live candidate. Six completed3440×1440/CRT images
were captured; the inspected sharp-turn image shows the filled ground.

The full run covers8860 inputs,7060 camera rows and21180 actual ADC samples,
all unchanged. All6953 future scene rows match the prior accepted run after
excluding only host timing columns. Lifetime events, handover scene rows and
the complete cohort journal are byte-identical. Three original GPU color/depth
pairs and15 original proposal resource/geometry files match the prior candidate.
Four new composition snapshots independently verify filtering/material ownership.
All20859 material stages and22 requested completed presentation captures finish.

Completed5645 changes15947 RGB pixels, repairs1919 black pixels and adds no new
black pixels versus the prior future/waiting image. Its center and entire private
depth are unchanged. Completed6331 and7188 are color-identical on the displayed
page and depth-identical to the prior live candidate. The zero changes at these
two samples are preserved as results, not counted as visual improvements.

An apparent right-edge black wedge in the intermediate5644 insertion image is
filled by later original commands before completed5645. It is not evidence of a
remaining displayed defect at that sample; completed frames remain the relevant
acceptance point. Broader temporal/artifact coverage is still required.

The changed harness paths pass46 focused Python tests. The standalone native
composition helper retains its earlier strict C++11 and actual-snapshot checks;
native helper synchronization passes. No broad all-game matrix was repeated.

## Failures retained and corrected

The first native candidate stopped at2219 because a blanket equality check on
lifetime record counts rejected two unrelated frees during an empty cohort.
The second candidate captures and verifies the specific retained owners at
sealing/completion instead. The original failed run remains available.

The first offline/live acceptance script wrongly required equality of the entire
private depth buffer. Its inactive page had different prior waiting-draw history,
with77196 different depth pixels. The displayed page matches the offline oracle,
and the **entire** depth buffer matches the prior live run. The original failed
assertion/script is retained; corrected comparisons use those explicit scopes.
No replay was needed for this verifier correction.

## Performance and remaining work

The full instrumented run reports91.22% emulation speed. Its monitor and capture
schedule differ from prior4K runs, so this is not a speed-improvement comparison
or full-speed acceptance. The next measurement removes heavy readbacks before
choosing a performance change.

Recorded CPU work totals include18.03s for future/waiting scene assembly and4.46s
for its geometry hashing, versus1.42s for active assembly and1.51s for active
sealing. Active material work is0.15s. Queue and GPU-submission timings overlap
other work and must not be summed as exclusive CPU costs or GPU execution time.
These figures suggest investigating the main scene assembly/delivery path before
optimizing the small active duplicate filter.

Next: reduce measured runtime cost, retain useful visibility through original
handover, renew final4K acceptance, and carry equivalent acceptance through the
other games. Diagnostic/private-renderer gates and physical FFB acceptance still
need to be resolved before product exposure. This does not certify release-ready
3× parity or eliminated pop-in across all four games.

Native first gate: `b6e0b8e8c79`, SHA256
`726af9ca4b04d8217594194401d079c0b6163e35bf076b362a4f058d07b7b463`.
Accepted owner-aware candidate: `e4cfcb864be`, SHA256
`c6a955fa3f509aecf7d6d8661bbf173485f8f4cd82f0f38a9865d9bce2a151c5`.
Both are separately frozen with the same force profile and pushed to the native
fork.193 exported patches reconstruct tree
`e6ceb0690e11af69f9387791c75577616af5644c`.

Local evidence under `results/diagnostics/exotica-amazon-20260909/`:
`composition-live-short` (failed), `composition-live-retry`,
`composition-live-acceptance-final`, `composition-live-full`,
`composition-full-acceptance`, and the corresponding plans/acceptance scripts.
Personal native87d04de4 and publicv0.5.0 remain unchanged.
