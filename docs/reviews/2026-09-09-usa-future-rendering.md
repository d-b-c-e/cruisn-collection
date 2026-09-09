# USA future rendering — September 9, 2026

USA's independently checked future-section source is now connected to a separate
MAME candidate. It produces earlier scenery without guest allocation, guest writes
or extra emulated CPU cycles. **Performance and full visual acceptance remain
open.** The candidate is not deployed; Stream Deck remains on v0.5.0.

## Implementation

`--usa-host-source pending|future` explicitly freezes the source in recordings.
Absent options preserve old drives. Future geometry is cached by track/section;
current partially allocated sections are excluded. Every scene refreshes palette
bindings, reference counts and reverse owners. Palette colors remain live.

The bounded upload-queue reader defers references to banks with queued uploads;
a pending texture upload defers all future objects. Malformed queue nodes and
unknown destinations fail the diagnostic guard. The sampled live scenes contain
no outstanding uploads or partial sections, so these transitions have synthetic
coverage only. No model/track allowlist was added.

Future descriptors use stable host identities and the existing USA codec and
host transport. Original pending objects keep their own identities and ordering.
Main RAM is read directly; bounded ROM/internal reads disable side effects. Each
callback asserts that the guest cycle count stayed unchanged.

## Measured results

Candidate `eee9fc5dd29ff4aa17b235393136a5a6b0c929ec`, SHA256
`5f77af81814d65675d69dc91afeddef97d0b2c180be9a3ac3c9be597f5cd5930`, is frozen in
`build/candidates/eee9fc5dd29/vunit.exe`. The 143-patch export reconstructs tree
`2a51babfffe699ccc790508a3f8a07cabf943c8b`.

Six 5012-input runs cover stock, pending3x, future1x/2x/3x and repeated future3x.
All preserve 3211 camera samples and 9633 actual ADC values/timestamps over
1800..5010. All 16 requested gameplay GL captures complete at 3824x2073.

| Comparison | Different captured frames |
|---|---:|
| Stock to future1x | 10/16 |
| Future1x to future2x | 13/16 |
| Future2x to future3x | 3/16 |
| Future3x to repeat3x | 0/16 |

The additional 3x differences are small on this route: 1005, 68 and 46 pixels at
frames 3600, 4700 and 4800. The future source visibly fills trees/buildings around
the horizon, including the previously sparse view at frame 3700. This is not a
claim that pop-in is eliminated or that every new silhouette has correct occlusion.
The 3x run repeats 6,445,085 ordered host quads over 750 scenes exactly.

A detailed 5012 replay with four native-clock snapshots preserves the same route,
16 GL images and all ordered fingerprints. Independent Python and native readers
match future admission, placement, material choices and ordered projection at
all three planes for four live snapshots and five earlier snapshots. The actual
3x runtime quads match the independent reference at all four exact scene clocks.
The prior pending-scene oracle also passes with the new depth rejection ordering.

Two 4502 runs preserve all 153,833,626 bytes of original hardware DMA history,
video RAM, texture RAM, palette RAM and metadata, plus 2701 camera/8103 ADC samples.
This preserves original resources; it does not certify the inserted layer's
occlusion or host-to-guest handover.

The first old/new pending comparison failed because the old capture includes
five more scenes through 5009, while the new bound ends at 5000. All 16 images and
the complete route already matched. The explicit common host interval 3501..4999
matches all 750 scene decisions/fingerprints; the initial failure is retained.

## Performance finding and next work

Summary-only future3x callbacks have p99/max 14.98/16.58 ms, with approximately
95.2% emulation speed over frames 3500..5000; repeat is 95.4%. Future2x is 97.6%.
This fails the desired smooth full-speed experience. Detailed logging is a separate,
heavier diagnostic path and is not used for those performance numbers.

Next reduce repeated immutable model decoding and measure again without changing
quads, palettes or captured pixels. Then renew seven default regressions on the
final candidate. Shared C31 arithmetic and material ordering must remain exact.
Further clipping, sky/occlusion, upload transitions and handover coverage remain
required; World2.5 roads, Off Road and Zeus adapters continue afterward.

Local checks pass 227 Python tests with no skips, 19 native helpers, 10081 C31/
137 yaw vectors and 32 GPU checks across 53 commands. All 341 files match identity
`9e3786b2139a0240fdcef7e5d8a8455da76107fbde76a4e4bc2e197825136210`.
Seven-default acceptance still belongs to candidate4e565; this checkpoint does
not renew it. Raw resources stay local in
`results/diagnostics/usa-future-render-20260909`. No release, deployment, physical
FFB, World force tuning or hosted workflow occurred.

## Separate model-cache trial

Native `439c5f1ab0a`, SHA `17dc5cc93e6317f8873f861fb211857be12924cd62a89c922ba910d59fe6198e`,
caches immutable ROM models with bounds of 1024 entries/1,048,576 operand words.
Track changes clear the cache; live palette bindings and projected vertices are
excluded. The future-definition limit is now explicitly enforced at 65,536.

Two new 3x runs and one 2x run preserve all inputs, camera/ADC timing, all 16 GL
images per comparison and complete ordered scene fingerprints. 3x callback p99
falls from 14.98 to 12.95 ms (repeat 13.66 ms), but throughput is still only
96.1%/95.5%; 2x is 98.3%. The full-speed acceptance failure remains open.
227 Python/19 native/32 GPU checks pass. Further local microbenchmarks found no
consistent gain from a different leading-zero instruction or cached local float
coordinates; those prototypes were not promoted. A cached extended reciprocal
table shows a small repeatable saving and is the next isolated trial.

## Separate reciprocal-table trial

Native `cf58c40632c`, SHA `37c0a4cef63b2bc56ef8d8daaccd4b75e457621633e3c93f228570cda6d0dc93`,
adds a bounded 40 KB host table for USA's extended reciprocal entries. Original
guest entries remain live. Exhaustive boundary comparisons cover all supported
planes and reject invalid ranges. World has the reusable helper available but
its rendering call sites are unchanged.

Two 3x runs and one 2x run again preserve the original route and all 16 GL images
and ordered fingerprints compared with the uncached implementation. 3x p99/max
is 11.94/12.55 ms (repeat 12.49/12.93 ms), approximately 97.6%/97.0% emulation
speed; 2x is 98.7%. This is progress, **not a full-speed pass**. The remaining
cost includes projection and submitting substantial scenery that is often
hidden. A future visibility optimization needs its own conservative geometry
and occlusion proof; do not drop objects merely to improve the timing numbers.

Final resource preservation and all seven-default gates pass on this candidate:
the original153,833,626 bytes remain identical, actual UDP/memory checks and four
software force-policy checks pass, and Exotica's21 GL images match. All227 Python,
19 native,10081 C31/137 yaw and32 GPU checks pass at341-file source identity
`b04de1be0667dfc3c17d6bcdc51c2a447fd95b67c35c09e2e24d751f436176f0`.
The145-patch export reconstructs tree`9befa7f28da953a1f32d9a4142bf9bae431e9b10`.
These default checks do not certify the new USA extended scene's performance.

Off Road's separate model/projection probe has completed its first control and
two capture runs after these gates. It uses DP=1 data addresses, five-word LOD
descriptors, float vertices and six-word polygons rather than USA's model layout.
The first oracle rejected an assumed two-word vertex stride. Correcting the
capture to its actual three-word stride gives463 prepared projections/3309
ordered DMA quads matching Python/native references. The ordinary path consumes
XY; the third word contains prior data and is not asserted. Original1201 camera/
4804 ADC values and times remain equal in these3001 runs. The failure is retained.
This is a local decoder prototype, not an extended Off Road renderer. Broader
windows, LOD/material/transform dispatch and4K captures are next.

Publishable USA evidence is archived in
`results/proof/2026-09-09-usa-future-rendering`:282 files/49,509,678 bytes. The
standalone verifier recomputes17 routes, four selected4K windows, repeated host
fingerprints/costs and seven telemetry/four software force verdicts. Full raw
model/resource oracles, other GL images and native/GPU builds remain receipts.
