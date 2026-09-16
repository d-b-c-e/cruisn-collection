# Invalidate V-Unit scenery caches at machine reset

USA, World and Off-Road previously cleared host scenery caches when their later
track callbacks observed an empty, changed or rewound track cursor. Machine
reset itself replaces guest RAM and did not invalidate these caches. Native
1800458b8e3 clears the four host caches at that actual boundary, before RAM
reload. Runtime totals and an existing failure retirement remain unchanged.
This removes a dependency on observing an intermediate track state; it is not
a claim that a stale model was reproduced in ordinary gameplay.

A World2.4 control records6600inputs with reset4620, preserving all4619 prior
inputs/times from the existing Germany recording. The matched continuous3x run
passes the normal replay: every input/time/native snapshot agrees,1859scenes
submit6,167,404quads, and9,609,422,120ring bytes drain with owned worker shutdown.
The same scheduled reset completes in both runs.

Seven completed CRT images are captured on the primary4K monitor; the actual
window client is3824x2073. Four are exact, one pre-reset image changes five
pixels, and the new London bridge attract views6000/6400 change32,199/289,740pixels.
Both pairs were viewed: extended scenery supplies the farther bridge span and
far-left buildings. All seven lower foreground regions from y1200 are exact.
The three sampled reboot images4800/5200/5600 are entirely exact. Attract views
show operation after reboot, not full London gameplay or temporal pop-in quality.

No new USA/Off-Road reset replay, camera/ADC trace, physical-wheel test or broad
default suite was run for these seven source lines. Their initial empty-cache
state is unchanged; per-game reset acceptance remains explicitly scoped.
The first candidate command redundantly supplied a preset-owned height option
and was rejected before launch. Removing that duplicate option retained the
same400-line profile; only one candidate game ran.

Local evidence: race-transitions-20260916/world-reset/record-check.json,
host3x/report.json and qualified.json. Build/export receipt:
world25-roads-20260914/vunit-reset-native-export.json.257patches reconstruct tree
5fa2e306091e16a62728d771d3ada36bf7d1c2b5; frozen candidate SHA256
6e9c16800f9ed1577ce8f76128cf5bbb1c9e702bd6dbb80874438165ac64bc9e.
Personal Stream Deck binary and publicv0.5.0 remain unchanged.
