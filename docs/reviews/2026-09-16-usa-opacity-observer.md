# USA: measure a fade after actual foreground occlusion

A new candidate-only USA observer transports every emitted host polygon's
camera depths to the GPU and records hypothetical distance opacity after the
ordinary draw stream. It leaves the displayed palette/CRT path unchanged.
This supplies a completed-frame measurement before deciding whether a fade is
useful; it does not enable a USA fade or invent road classifications.

The native work is split into metadata transport (5832c43917c) and observation
without presentation changes (0d24929d1c7). The latter is frozen with a verified
build attestation, SHA256
65376963ee84a46fa3441b174e8ff177301207d5925eb1dbebfe4476b6495fe2.
The259-patch export reconstructs tree
f0566454c7eb70addd9994c20f3900f707c28164.

Use --usa-host-fade-metadata with an explicit candidate, USA3x future drawing,
far coverage, both ownership layers, physical FFB0 and a bounded original-mirror
snapshot. Adding --usa-host-opacity-observer measures the existing World-style
240,000-unit plane and20,000-unit transition. It only writes the auxiliary
opacity attachment. Original commands and CPU writes keep their existing
ordered image behavior. The World fade cannot be enabled against USA.

## Measured result

One3522-input control/observer pair passes. The control uses5832 and the observer
uses its0d249 successor; this is not a same-binary pair or a performance test.

- Original input/time/native images,1721 camera and5163 actual ADC records match.
- Original DMA, framebuffer, texture and palette captures at3520 match.
- All eight completed indexed/mask planes at3501 match exactly.
- All five completed3824x2073 CRT images at3500..3504 match on the4K primary.
- All11 scene rows match except six explicitly named host duration columns.
- All38,225 depth packets reach the consumer. The3264 captured polygons include
  100 far-crossing polygons; their complete ordered DMA/depth words independently
  match reconstruction from the saved3501 RAM/ROM scene.

The completed visible page has only41 partially opaque fine pixels; the other
page has20. There are no zero-opacity pixels. Every affected pixel retains the
host ownership tag. The visible-page bounds are x1089..1361, y764..791 in the
2736x1600 internal image. Indices or masks differ from the original-only view at
those41 pixels, but palette/filtering could make the eventual RGB effect smaller.
This is a narrow horizon effect, not evidence that most observed USA pop-in is
caused by the final3x plane. Do not spend another replay on this same interval
merely to obtain a larger result.

The first local qualification incorrectly compared current geometry with a
pre-horizontal-cull file and failed. Updating the canonical Python reference to
the already verified all-vertex cull reproduces all3264 packets exactly; decoded
model counts and earlier material validation remain. A second checker failure
used the vertex metadata bit8 as the framebuffer ownership bit. The shader maps
that to mask bit4. Both failed reports are retained; corrected v3 passes. Neither
failure caused a game replay. Nine mirror/metadata tests and nine USA host tests
pass.

## Cross-game implications

USA can reuse World's depth representation and outer plane. Off-Road cannot
copy its admission or wire bounds: its3x sphere threshold is141,888 while vertex
projection extends to191,040. Its optional depth reconstruction is already
qualified. Next carry that distinct profile through an observation-only path,
preserving its existing admission and avoiding a new far-coverage discard.
A fade still needs surface eligibility, a useful visible boundary and temporal
handover acceptance before product promotion.

Local evidence: results/diagnostics/world25-roads-20260914/
usa-metadata-live-off, usa-opacity-live-on, usa-opacity-qualified-v3.json.
The initial usa-opacity-qualified.json and v2 remain failed.
Personal Stream Deck87d/publicv0.5.0 are unchanged. No deployment, hosted CI,
physical-force testing or release occurred.
