# Exotica distant visibility and original fade handover

The future renderer is drawing many objects with their initial fade coefficient.
The offline completion experiment now preserves intrinsic blending and completes
only explicitly marked fades using the game's verified +8 update. This corrects
the experiment; it does not enable a live opacity override or solve handover.

## What the saved scenes establish

Three actual native scenes retain exact source/instance/ordered-quad joins:

| Native frame | Future instances / quads | Marked-fade instances / quads | Marked quads with source alpha 8 |
|---|---:|---:|---:|
| 5072 | 94 / 538 | 90 / 413 | 413 |
| 5644 | 672 / 6,123 | 665 / 6,037 | 4,262 |
| 7187 | 809 / 8,283 | 765 / 7,963 | 5,948 |

Every marked source in these samples starts with packed alpha eight. Model
commands can override the final quad state, so marked-source counts are not
counts of translucent pixels. Unmarked materials include other alpha values
and blending; these must remain intact. No unmarked `0x100`-only source appears
in these three scenes, which does not establish that such sources never occur.

The former offline `complete_fade` option blindly cleared `0x04000100`. It could
therefore remove intrinsic object blending and left the packed destination
coefficient stale for the lighting branch. The corrected endpoint requires the
`0x04000000` temporal-fade marker, computes the first completing +8 step, preserves
the low-word metadata and unrelated flags, and updates both packed coefficients.
Unmarked operands pass through unchanged. Marked alpha at or above 247 is rejected
as inconsistent with a continuing fade. This is an endpoint experiment, not an
instruction to change every game's transparency or a live fade policy.

## Completed pixels, not just an early insertion

A fresh control replay of the saved, ordered GPU interval ending at native5073
matches the previous composed color and depth exactly. It includes early future
geometry, retained waiting geometry at the actual completion boundary, filtered
active margins and all original commands/material updates.

Completing only marked future fades changes 16,066 completed RGB pixels, with no
new black pixels in this sample. Of those pixels, 8,502 brighten and 7,496 darken;
692 depth samples also change. Adding completion for the retained waiting cohort
changes 63,849 RGB pixels versus the same control, again with no new black pixels.
Vertices, instance order and unmarked future quads remain exact. The waiting
endpoint changes 184 of 849 quads without changing vertices or retained owners.

These results demonstrate a visible difference, not general visual acceptance.
Removing a fade changes depth/bias behavior as well as blending. The comparisons
cover one completed2736×1600 page in a2736×4096 internal target. They are neither a
new live4K check nor a temporal handover test.

## Why a blanket completion switch is insufficient

Actual proposal record watermarks were joined to later native pool generations
and original submissions, preserving source/realm/slot ownership. Of the future
instances at5072,79 have a first original draw that is still marked fading; the
corresponding counts are250 at5644 and223 at7187. Other instances finish fading
before first submission, and some never submit within the recorded window.

For example, a future source displayed at5072 allocates at5083, first draws at5219,
and completes its original fade at5249, approximately0.525 seconds after first
draw. Replacing a completed host copy with that original fading copy can produce
a visible drop at handover. An ownership-safe solution must carry visibility
through that transition and preserve intrinsic model blending. Keeping a second
translucent copy on top of the original is not established as equivalent.

The next step is to associate actual original model commands with the admitted
source lifetime, then test a private-target transition at its original command
position. Do not change guest physics, original command ordering or ordinary
foreground occlusion to conceal the transition.

## Validation and delivery

Three targeted native test programs and24 relevant Python tests pass. Six full
scene comparisons (three snapshots, original/completed endpoint) match independent
Python preparation across29,888 ordered quads. Default-fade outputs match prior
captures byte-for-byte; completed outputs match the locally GPU-tested geometry.
Boundary tests preserve unmarked blending and reject inconsistent completion
operands. The initial patch application failed atomically; no partial source edit
was retained.

Native source commit `21c1688ffee9defb9554e1c56c524dd8b75f6598` is pushed. The200-patch
export reconstructs tree `39bc51499f8e258b0ea1493d38bdec350fae7f79`. This source-only
change has not received a new MAME build: the available test executable remains
native0cc, whose live fade behavior is unchanged. No deployment, public release,
hosted CI or physical FFB was performed. Personal native87d/publicv0.5.0 remain
unchanged.

Local evidence under `results/diagnostics/exotica-amazon-20260909/`:
`future-opacity-audit`, `marked-fade-probe`, `marked-fade-completed5072`,
`marked-waiting-probe`, `marked-waiting-completed5072`, `opacity-handover-audit`,
`marked-fade-canonical` and `marked-fade-native-export.json`. Raw game resources
and rendered images remain local.
