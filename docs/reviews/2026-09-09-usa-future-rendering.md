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
