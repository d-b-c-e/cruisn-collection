# Exotica: choosing useful distance samples

The latest investigation does not justify another rendering change. The saved
Amazon samples either contain no third-band geometry or place it behind nearer
depth. Keep the accepted early-visibility and margin repairs; do not advertise
these findings as useful3x distance parity or elimination of pop-in.

## Active-object handover check

The current active-list path deliberately repairs horizontal margins within the
original distance limit. Waiting objects leave the retained path after their
first original submission. That suggests a possible gap for an already-drawn
object that later moves beyond the original far boundary during a camera turn.

Nine sealed snapshots across seven distinct Amazon frames were checked from
three retained runs. Only one object is beyond the original sphere boundary but
within3x in these samples. It appears at5072/5080, slot137047, generation36074.
Its first original submission is5132; its exact lifetime owner is still present
in the waiting cohort with16 polygons. The other sampled views contain no such
candidate. This does not prove all active objects are covered over a full drive,
but it provides no evidence for adding an extended active-object path now.

## Completed depth and multiplier comparison

At5644, all26,535 pixels affected by the earlier outer-tenth removal experiment
have nearer depth before the waiting pass starts. The same relationship remains
through waiting, active margins and completed5645. This locates the later depth
writes; it does not prove opaque ownership or exclude blended contributions.

One same-frozen-candidate2x replay completes5300 inputs. Camera, actual ADC,
lifetimes, original model records, saved original targets and resources match
the retained3x run. All three completed2736x4096 private color/depth pairs at
5073,5081,5220 are byte-identical. No physical force was enabled.

**The sample selection was weak:** the future and waiting packets at all three
sampled scenes contain zero third-band polygons. Earlier admissions could still
affect later original replacements, but these snapshots do not meaningfully
exercise the outer boundary. Do not repeat this comparison as a3x quality gate.
The first attempted4K invocation stopped before launching because that monitor
was no longer connected; its failure is retained. The successful comparison
uses internal targets and makes no external-image or final4K claim.

A further offline screen tests the two saved scenes with substantial third-band
geometry:5644 has3746 polygons,7187 has3139. Each immediate insertion first
reproduces its own recorded color/depth bytes exactly. Drawing only that band
against its later completed depth produces zero colored fragments in both cases.
This is a conservative sample-selection exercise, not a reconstruction of all
completed commands or a claim about transparency. The7187 resources are from the
older combined-composition run and are not relabeled as the latest fade policy.

## Preventing another low-value replay

`harness/exotica_distance_samples.py` reports actual serialized distance-band
counts in saved future and waiting packets. It validates unique source identities,
ordered quad spans and matching quad-file sizes. `--require-third-band` fails
sample selection when none of the chosen samples contains third-band polygons.
Presence still does not establish visibility; absence does not exclude an
earlier admission's effect on later original replacements.

Two focused tests pass, including malformed/truncated/overlapping records and
zero-polygon instances. The actual5072/5644 fixture selects5644's3746 third-band
polygons and correctly reports zero at5072. No native build or default-suite
rerun is needed for this diagnostic helper.

The next useful Exotica distance sample needs an open sightline, not another
repeat of the occluded Amazon windows. A contrasting attended course would help.
The existing Amazon recording remains valuable for margin, transparency,
handover and collision coverage and does not need replacing.

Local evidence under `results/diagnostics/exotica-amazon-20260909/`:
`active-far-gap-audit.json`, `far-appearance-stage-localization5644.json`,
`temporal-multiplier2` (display preflight failure),
`temporal-multiplier2-internal`, `temporal-multiplier-qualified`,
`third-band-completed-depth`, and `distance-sample-selection.json`.
Personal87d/publicv0.5.0 and the latest combined native0ce candidate are unchanged.
