# USA activation from an actual scene

The candidate can now start USA's host scenery at the first successfully prepared
scene, instead of a fixed diagnostic frame. `--vunit-bootstrap scenes` requires
an explicit USA future-draw candidate, both rendering layers, live GL and physical
FFB disabled. World and Off-Road are rejected until separately qualified.

The native adapter bypasses only the lower capture bound. It retains the finite
end, every code/source/model guard, guest-cycle assertions and latched preparation
fallback. It writes checked little-endian RAM/fast-RAM operands after successful
preparation and before the first submission. The harness requires the activation
receipt, complete operands and matching first scene in the validated journal.
Inherited activation without explicit selection is rejected. A failed preparation
still disqualifies parity, including failures before the old capture start.

## Qualification

Four focused Python checks pass for selection, receipt/operand failures and the
existing preparation fallback. Native03ddf36820c builds and freezes separately;
248 patches reconstruct tree6fe1b58c1884911c59fadb4387c0751a68a6827e. Candidate SHA256
is b63803f0f149077550f4319df4b62c458018b64c69437c6edb20f121bad56333.

One5,012-input drive passes original inputs, emulated timing and native images.
Activation occurs at739 in this recording; that number is not in the policy.
Its saved RAM/fast RAM exactly match the earlier original-only scene observer.
The retained native analyzer, including complete code guards, and independent
Python reconstruction agree on the first scene's empty preparation.

The run prepares2,766 scenes through4999 without fallback. It adds2,016 scenes
before3500, totaling3,342,256 quads; first nonempty preparation is1606. These are
submission totals, not counts of newly visible objects. All750 later scene
records match the accepted horizontal-culling candidate, excluding only timings
and cache misses. All3,201 camera samples and9,603 actual ADC reads match exactly.

Six of seven completed images on the4K monitor are byte-identical. Frame3500
changes27,021 pixels in the distant strip around/beyond the bridge, with zero new
black pixels. The inspected foreground and HUD remain unchanged. This image
precedes the old candidate's first preparation at3501, so earlier scenery is an
expected difference. Both images were viewed. Actual captured client images are
3824×2073, not3840×2160 full-screen pixel buffers.

The initial analyzer incorrectly required all seven images to be equal and its
FAIL is retained. A separate qualification explicitly requires only3500 to change,
checks its black-pixel/foreground boundaries, and preserves exact comparison of
the later six. No game was repeated for this analyzer correction.

Local evidence under `results/diagnostics/world25-roads-20260914`:
`usa-bootstrap-live-4k`, `usa-bootstrap-qualified` (initial failure),
`usa-bootstrap-qualified-v2`, `usa-bootstrap-native-export.json`.
`export-usa-bootstrap.py` has already run and must not run again.

## Remaining work

This qualifies actual-boundary activation and retained later behavior, not every
early presentation, continuous runtime, multiple races or performance. The finite
end remains intentional for this stage. Next qualify World24/25 and Off-Road's
actual startup states, then carry guarded activation into normal session lifetime
with explicit completion/fallback semantics. The personal Stream Deck build and
publicv0.5.0 remain unchanged.
