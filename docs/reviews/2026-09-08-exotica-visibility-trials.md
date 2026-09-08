# Exotica global CPU visibility trials — 2026-09-08

The CPU's horizontal sphere tests can omit real geometry in the widescreen
margin. A matched early gameplay scene restores one textured edge polygon while
preserving every original submission and its effective palette. Removing the
CPU projection clamp is a separate experiment: additional admissions alone have
not established a useful increase in visible distant scenery.

Native `6a2b7ae93fa` implements explicit `MIDZ_VISIBILITY=stock|projection|margins|both|off`.
Unset/off installs no hooks. It preserves the 204800 far plane, Zeus projection,
guest RAM/ROM, force behavior and default settings. Native SHA256:
`cec6d98afc732b7e1a268deb763a7afeab112c66e32a4a5ed643817f1f3fdc5a`.
The 127-patch export reconstructs tree `6d2e8a22e8641bbf6709eb2f1d5a5092c6bd0dcc`.

## Bounded Lua experiment

`results/diagnostics/exotica-visibility-20260908/trials` contains five complete
6000-frame runs. Only frames 2500–4300 enable the read substitutions; the probe
drains and removes its hooks afterwards. No guest memory is written.

| Trial | CPU sphere admissions | Changed completed GL images vs stock | Emulation speed in instrumented window |
|---|---:|---:|---:|
| Stock | 215946 | 0/19 | 97.9180% |
| Projection | 220008 | 3/19 | 97.7830% |
| Margins | 238066 | 9/19 | 96.3770% |
| Both | 246902 | 9/19 | 96.3103% |
| Both repeat | 246902 | 9/19 | 96.5570% |

Both trials have byte-identical full sphere traces and identical 19 completed
1920×1080 GL captures. Stock reproduces all 339018 poses/decisions from the prior
read-only audit. Original input/native comparisons pass, but Exotica's live CPU
framebuffers are not a gameplay visual oracle.

Strict pose comparisons fail later in the drive. For projection, sequence 86920
lands one frame earlier (3698 vs 3699); later traffic poses differ as well. The
larger image change at frame 3700 includes the race-start timer. Do not describe
all changed pixels as newly visible scenery or the old route as preserved.

## Resource and submission evidence

Three independent prefix runs capture actual Zeus submissions/resources around
frame 3500 and completed GL frames 3499/3500. `scene-stock`, `scene-margins` and
`scene-both` all complete and validate their resource sizes and frame windows.

The margin-only scene retains all **3691 original records**, including **3532
quads**, bit for bit and in order. The only additions are one palette load and
one quad. Comparing each original quad's effective palette also passes. Texture
wave RAM and the initial palette are byte-identical. The added quad lies at
native x=541.79…737.66, outside the original right edge; completed images show
the restored upper-right detail. This is geometry, not a filler or stretched sky.

The combined scene preserves texture memory but changes 42 existing submission
records and adds more geometry. The strict ordered-original check is **FAIL**,
retained as `scene-both-geometry.json`. Repeatability does not erase this failure.

## Native adapter and harness

The canonical helper is `native/exotica_visibility.h`. Exact Exotica 2.4 opcodes,
table constants, CPU consumer PC/registers, object pointer, depth/radius and
range checks guard substitutions. Only the original final reciprocal entry at
the CPU sphere consumer can use a virtual factor for indices 5000…12800. Other
table consumers retain their original values. Horizontal bounds change only at
their two verified consumers. No object/model/level allowlist is used.

Backing RAM reads avoid recursive address-space taps. No current-object cache
survives a save/load; diagnostic counters reset on reset/load. Buffered native
`exotica-visibility.csv` includes guard coverage, far rejects, extended reads and
accepted spheres. The unit helper passes against both synthetic guards and the
actual captured program. The Python analyzer rejects partial or inconsistent
native logs; passing it is not a visual acceptance claim.

`replay.py`, `derive_case.py` and attended `record_drive.py` accept
`--exotica-visibility`. Candidate derivation now supports `--keep-patch`, including
an originally absent patch, and rebinds frozen patch/cheat dependencies before
copying them. Effective options remain in the new recording manifest.

Settings → Experiments → Cruis'n Exotica now exposes **Widescreen Scenery**.
It selects only `margins`, defaults off, and applies to enhanced widescreen
scale >1. Native-renderer fallback suppresses the saved experiment. An explicit
developer environment or recording CLI control still wins. Projection/both stay
developer controls; their visible distance benefit is not established. The
top-level Experiments placement and per-game filtering are preserved.

`replay.py --zeus-capture-frame N` now captures and strictly validates Zeus
submission/resource evidence. `--capture-state` explicitly rejects Zeus instead
of pretending V-Unit dumps cover it. `zeus_rasterize.py` shares the strict parser,
which rejects truncated/unknown records and invalid vertices. The new comparator
includes effective palette state, preserves duplicates/order, and pairs with
completed GL rather than interpreting unchanged live CPU buffers as success.

## Current native validation and next work

The native stock control completes all 6000 frames and matches all 21 original
3840×2160 completed GL images. All five full-boot native trials complete. Both
repeats all 6000 per-frame native counter rows and all 19 completed GL images
exactly. Each native intervention also matches all 19 images from its corresponding
bounded Lua trial. Native stock/margins/projection measure approximately 100%
emulation speed. The default regression suite also passes all seven cases. Current local harness: 157 Python tests pass; offscreen Exotica
and root menu screenshots were inspected for layout and filtering.

New `margins-case` and `both-case` recordings each repeat all 6000 input/native
frames, all 6000 native counter rows and **35 completed 1920×1080 GL images**
from frames 2500 through 5900. Derivation is synthetic replay of the existing
input recording, not a new human drive. Local/Linux/Windows agree on all 255
source hashes, identity `fa5809b1880d4373652c68e2e034afa992c97d15a29b8f4698ba4cf3a0a121a3`.
All four CI jobs pass at both `dc1f5af` (34213164187) and `0e758f3` (34213524599).

Comparing margins against both over that longer window changes 19/35 images.
Large later differences begin at sample 5300; both versions of this synthetic
drive run off the road. These differences cannot certify earlier scenery at an
identical camera pose. The full comparison remains a difference/FAIL receipt,
separate from each candidate's successful repeatability result.

The native stock log also establishes that **3669 actual far rejections** occur
in frames 4686…5986. None occurred before frame 4301. Thus the initial sphere
audit correctly found no far rejects in its window, but did not cover the part
of the drive where the 204800 limit matters. A future global far-plane trial
should target those later frames and pair an extended reciprocal range with
actual Zeus submissions/resources and completed images. Simply observing more
admissions still does not prove successful distant rendering or residency.

All seven disabled-feature regressions pass, including actual telemetry/independent
memory checks, unchanged World force passthrough expectations and Exotica’s 21
completed original 4K images. Configured timing windows are 99.9714%…100.0055%
emulation speed; this is not a measurement of presentation latency.

The [173-entry evidence archive](../../results/proof/2026-09-08-exotica-visibility/README.md)
passes its standard-library verifier. The source used by Stream Deck is updated;
saved settings and the v0.4.0 tag/ZIP remain unchanged.

Keep these controls experimental. A fresh attended Exotica drive remains necessary
for handling/route acceptance.
The present evidence supports wider edge visibility, not a claim that Exotica
pop-in is solved. World/USA/Off Road admission/residency mechanisms remain distinct.
