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

`replay.py --zeus-capture-frame N` now captures and strictly validates Zeus
submission/resource evidence. `--capture-state` explicitly rejects Zeus instead
of pretending V-Unit dumps cover it. `zeus_rasterize.py` shares the strict parser,
which rejects truncated/unknown records and invalid vertices. The new comparator
includes effective palette state, preserves duplicates/order, and pairs with
completed GL rather than interpreting unchanged live CPU buffers as success.

## Current native validation and next work

The native stock control completes all 6000 frames and matches all 21 original
3840×2160 completed GL images. Stock, margins and projection full-boot runs pass
input comparisons and native log coverage at approximately 100% emulation speed;
the remaining candidate repeatability/default regression results will be added
at the checkpoint. Current local harness: 156 Python tests pass.

Keep these controls experimental. Full candidate repeatability, cross-game
disabled controls and a new attended Exotica drive remain separate requirements.
The present evidence supports wider edge visibility, not a claim that Exotica
pop-in is solved. World/USA/Off Road admission/residency mechanisms remain distinct.
