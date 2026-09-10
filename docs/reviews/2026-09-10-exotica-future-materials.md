# Exotica future models and fade handover

The current evidence supports continuing with a host renderer for future
scenery. It does not yet establish a safe 3× setting. These local studies use
the earlier Hong Kong recording, separately from the Amazon artifact fixes.

## Geometry is already present in the sampled WaveRAM

The independently decoded future sections at frame 3500 contain 2,719 potential
spheres inside an expanded 3× far limit. This is before horizontal culling,
occlusion or material-readiness checks. They select 970 distinct model bindings.

All 970 buffers parse as bounded Zeus model streams using the independently
reconstructed setup programs: 748 use 12-word polygons and 222 use 10-word
polygons. Together the unique buffers contain 13,638 polygon commands. This
checks their format; it does not independently identify each buffer's owner.

All 970 selected byte ranges remain unchanged in the later frame-4700 and
frame-5410 WaveRAM snapshots. Of the actual model submissions captured at those
later points, 187 and 214 respectively use these bindings and exactly match
their earlier frame-3500 bytes. That is evidence that some future geometry is
already loaded well before the game draws it. The remaining bindings lack that
later-use observation; successful parsing alone is not a residency guarantee.

Only 580 of the 2,719 potential instances reuse a model/palette pair already
submitted in the first snapshot. Restricting the renderer to that observed
catalog would leave 2,139 instances, involving 836 other bindings, unaddressed.
The implementation should verify resources generically rather than introduce
a fixed model allowlist.

Still required: exact native-frame/time alignment of source and device state,
ownership through track changes, completed uploads, texture ranges and animated
palette freshness. The earlier six-model scratch-buffer mismatches demonstrate
why a final WaveRAM snapshot cannot stand in for every use-time resource.

## The game's fade-in advances after admission

The original update routine advances the source alpha by the increment at
word 588, which is eight in these snapshots. It derives destination alpha from
the remaining fraction and ends the fade once source alpha reaches 247 or more.
This is an update over time after admission, rather than a simple depth-to-alpha
formula that automatically extends when the far plane changes.

Among 486 consecutive captured calls with the same object, model, position and
section identity, all 486 alpha/flag transitions match this reconstruction.
The initial complete-word comparison fails on three transitions: the low bits
also change list membership as the object finishes fading and is classified
again. That failure is retained. The narrower render-alpha/flags comparison
does not claim to reconstruct lifecycle links or physics state.

A bounded local write-tap probe now verifies489 actual updates:472 continuing
steps and17 completions. Every increment is eight, and every resulting packed
alpha and flag write matches. The6000-frame probe preserves original camera/ADC
timing and all21 sampled4K images. It observes the increment read and actual
result writes without changing guest memory; broader lifecycle behavior remains
outside this check. The reusable source promotion is still pending.

For host scenery, the handover needs explicit treatment. A host copy that has
already become visible should not suddenly disappear when the original game
admits a nearly transparent copy. A candidate policy is to retain the host
background copy through the original fade, then remove it once the original
copy is opaque. Geometry, depth, blending and frame-by-frame handover still need
validation before adopting that policy.

## Next bounded work

1. Promote the bounded fade-write probe and independent verifier, with the
   distinction between render fields and list membership preserved.
2. Capture source descriptors, private device state and live resource versions
   at one exact scene boundary. Validate future models and textures through
   later original submissions and track transitions.
3. Prototype extra scenery with isolated state and a depth representation that
   can distinguish surfaces beyond the original 24-bit range. Preserve original
   hardware submissions and verify occlusion and fade handover before increasing
   the user-facing distance setting.

Local evidence is under `results/diagnostics/exotica-amazon-20260909`:
`future-readiness-coverage`, `future-model-format`, `future-model-lifetime`, and
`fade-call-transitions` / `fade-render-transitions`. Raw game resources remain
local. No new native host drawing, deployment or release is claimed here.
