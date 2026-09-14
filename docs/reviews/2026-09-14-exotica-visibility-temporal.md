# Continuous presentation through original fade completion

Two same-candidate Amazon replays now cover the earlier visibility transition
with55 consecutive completed presentation frames. Both5,300-input runs pass.
The candidate remains native1d3216d7a83; no new build or deployment was needed.
One control retains original appearance; the other enables earlier visibility
and qualified private original replacements during5218–5288.

All original camera/ADC/lifetime traces, model operands, original draw rows,
admission queries and packet-source journals are byte identical between runs.
The early run consumes8,638 private replacement quads across1,117 models. Its
17,330 original queries include9,135 prior admissions;738 sealed active permissions
independently match their exact source generation and draw history.

## What the sequence shows

Completed3440×1440/CRT presentation captures cover5216–5270 without drops. The first
four are identical. The first visible difference is presentation5220; an earlier
private render-buffer change is not necessarily the page already being displayed.
Thereafter79,223–102,784 pixels differ per frame. No frame introduces a newly black
pixel. A fixed foreground region, x1300–2099/y900–1339 in these captures, is byte
identical throughout. This region is a limited foreground check, not an oracle
for every foreground object.

Paired images at5219,5244 and5252 were inspected. The later frames show additional
distant forest, with vehicle, water, elephants and HUD intact in these views.
The forest remains present around the tracked original fade-completion boundary.
This is meaningful temporal evidence for this short Amazon segment; it does not
validate every tree individually or every track/turn.

Three tracked source owners first draw at5219/5220 with packed alpha8 and reach
unmarked alpha248 at5249/5250. Every observed marked draw is admitted and receives
the private replacement. The original path remains intact. The initial local
analyzer wrongly required a draw at every intermediate alpha. Some updates have
no corresponding submission: two owners omit200/216 and the third omits192/208.
The failed report is retained. The revised check retains those gaps and verifies
strictly advancing eight-unit states, the actual completion, and admission of
each observed draw. Neither replay was repeated for this analyzer correction.

## Limits and next step

Capture pacing deliberately waits for screenshot storage; these runs do not
measure uninstrumented performance. The debug activation itself is abrupt.
A gradual appearance policy at the farther visibility boundary remains open.
No final4K, full-drive appearance, or four-game release parity is claimed.

Next extend the experiment across a complete drive. The current all-command
endpoint observer is capped at120 frames to bound logging; most commands are
unmarked and cannot change. Add an explicit marked-only observation scope with
bounded journals, retaining exact FIFO ownership, original controls and admission
checks. Then use the existing full Amazon recording to find remaining unsupported
handover/appearance cases. Optimize measured costs after correctness.

Local evidence under `results/diagnostics/exotica-amazon-20260909`:
`visibility-temporal-control`, `visibility-temporal-early`,
`visibility-temporal-qualified` (failed cadence assumption), and
`visibility-temporal-qualified-v2` (accepted traces, per-frame metrics and pairs).
Personal87d/publicv0.5.0 and FFB remain unchanged.
