# Exotica material write tracking — September 10, 2026

The private material path now has an explicit diagnostic choice:
`--exotica-host-material-pages scan|written|verify`. Absent settings preserve the
earlier full scan. Written mode checks only pages notified by actual WaveRAM
writes; verify mode compares the complete resulting packet with a full scan
before either can be queued. None of these modes draws extra scenery.

The tracker is independent of the original renderer's dirty span. It records
each expanded eight-byte WaveRAM write and retains marks until the entire
owned material packet has been queued and committed. Save-state restoration
marks every page because it bypasses ordinary device writes. This addresses
private image invalidation only; complete emulator save-state behavior is not
newly certified. The first material image still transfers all16MB.

The generic helper rejects invalid ranges without changing pending marks.
Tests compare1000 full/selected update packets, including restored images and
abandoned submissions, and demonstrate detection of an omitted notification.
The live verify mode is necessary to establish that the emulator actually
reports every relevant write; the standalone tests alone cannot prove that.

Native `ac10f2aae6e14650958f6a5ae249216b0cde1f31` is separately built and pushed.
Frozen `build/candidates/ac10f2aae6e/vunit.exe` SHA256:
`9daeb048e585bda8426fc9be83cd75eb3393a4d6e5d0193e1718436a4fce23cd`.
The164-patch export reconstructs tree`5a3703028fd9856a7e087a5e631e5dbcc8728ae1`.
Final317 Python tests/no skips,39 native programs and111 commands pass at
`f106f6e526f9333889bb410a3cee1af43d3e67a1bbb19203787f922eb01c0a6a`.
All nine paired trials pass: Amazon5072 verify/written/repeat, no-GL performance,
Hong Kong5000 verify/5990 written and full Amazon scan/written/verify. The scan
reference uses99442; eight trials useac10. They preserve440 paired4K images
(323 onac10), original motion/resources and sampled complete GPU material bytes.
Verify mode matches10,204 complete scan/selected packets. All seven default
regressions now pass onac10, including actual UDP/memory telemetry, four software
force checks, full Germany and21 Exotica images. Automated physical force stays0.

The earlier99442 full Amazon material run completed8860 frames, preserved7060
camera samples/21180 actual ADC reads and times, ten original resource files
and117 matching4K images. All5290 material updates matched the consumer;
complete GPU image/palette checks passed at6330,7187 and8760. The8760 scene has
no extra instances or palette rows. Independent geometry and scene-boundary
checks pass for all three snapshots. The attempted original-context7187 check
failed because its reference journal covers7199–7200; that failure is retained.
The three new full runs capture7187–7188 and pass that original-context check,
closing the missing comparison without discarding the earlier failure. Independent
source/scene oracles and full GPU bytes also pass at6330 and8760.

No-GL controls still include regular raw snapshots every60frames. They measured
88.63% emulation speed with bounds alone and82.54% with full-scan materials over
3501..5990. Mean CPU scene work was3.517ms versus4.965ms. The isolated no-GL
material upload maximum was0.603ms after initialization; the earlier88.357ms
capture-window spike was not reproduced there. This narrows its conditions,
not its root cause. The first full material image still requires initialization
or prewarming. Live written-page staging reduces steady mean work from1.412ms
to0.026ms (2456 scenes after initialization). With dense GL captures, measured
speed improves81.66% to87.82%, repeating at87.53%; the bounds-only control is87.05%.
Without GL captures, written mode reaches88.42%, versus82.54% for full scanning
and88.63% for bounds alone. These are instrumented intervals, not whole-game
smoothness acceptance. Initial producer/GPU work remains about49ms/25ms.

The public proof at `results/proof/2026-09-10-written-pages` recomputes the source
identity, measured staging means and receipt coverage for nine trials,10,204
comparisons,440 images and seven defaults. Raw GPU/resource/route bytes remain
local and are represented by receipts, not recomputed by that public verifier.

Personal Stream Deck stays v0.5.0/SHA87d04de4. No deployment, release, hosted
workflow, physical FFB, World tuning or experiment removal. Continue with
cached source descriptors and exact early depth rejection to reduce remaining
CPU cost, then initialization, guarded scene insertion/private depth, foreground
occlusion, handover and source eligibility. Local cache/depth prototypes are not
yet native runtime acceptance.
