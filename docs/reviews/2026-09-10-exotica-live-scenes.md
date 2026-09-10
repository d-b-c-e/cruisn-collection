# Exotica live scene observation

The standalone assembler now has an opt-in MAME observation path. It builds
private future geometry at an original Zeus model submission, checks that no
emulated CPU cycles change, and can capture a bounded scene for independent
Python reconstruction. It does not submit extra geometry to the GPU.

`--exotica-host-scene observe` requires an explicit candidate, an Exotica frame
interval and physical force zero. The multiplier is independently selectable
at 1x, 2x or 3x. Absent controls install no observer. Original recording settings
remain unchanged. Captured RAM, ROM, WaveRAM and geometry stay local.

## Initial result and retained failure

Native `a56142283b9` passes the initial Hong Kong4970–5010 observation:
41 scenes and392,173 generated quads, with no guest-cycle changes. The5000
snapshot matches independent Python instance/quad bytes and the actual original
device context. All21 completed4K captures, ten original resource files and
4,191 camera/12,573 ADC samples match the control.

The broader Amazon run fails at its first observed native frame3500 with
`Exotica host live camera changed`. This is an observer-only diagnostic failure,
not acceptance of the attempted run and not a crash in the personal build.
The failure is retained under `observer5072-initial`.

A separate, read-only CPU journal explains why selecting the first eligible
model of a **native refresh** is incorrect. The actual game scene starts at
61.258712299 seconds in native frame3499; some of its model preparation extends
into frame3500. The game's camera then advances. A late model cannot supply an
arbitrary new scene with whichever camera happens to be live at device time.
The timing probe completes3600 original inputs and five4K captures; these facts
alone are not a complete route/resource comparison.

## Corrected observation boundary

Native `f49e8acc7d3b2da5beb0c7815804fa0a79117ab0` uses the game's scene-start
and scenery-list boundaries. It selects the first supported original model
inside those lists, latches the scene identity and camera, and preserves the
camera, view, bank, clock and zero-cycle guards at device consumption. A native
refresh can contain no new game scene. The observer does not manufacture one.

`lua/exotica_scene_capture.lua` independently journals scene start, sky/special
models, scenery-list entry, ordinary models and list completion. The live
snapshot verifier can require that journal and the original device-model
journal. It rejects a later eligible model, incomplete scene boundaries or a
different camera. This establishes a checked observation point; it does not
yet establish a safe GPU insertion point or prove ownership of material bytes.

The candidate is separately built at `build/candidates/f49e8acc7d3/vunit.exe`,
SHA256 `9c7dcd272ea609e1b28fa86c9cdd07f2dfca0b089edcbf198e3dfee8caa1d606`.
All161 exported patches reconstruct native tree
`958fde28bb648cc97910856e992e38b95dbafdb0`.
The local suite passes301 Python tests without skips,35 native helpers and99
commands at source identity
`64fe329411b7e8207c763258889829a9072a7aff268b6465743c6f8f05a4a1d3`.
The broad Amazon run completes2,457 observations/20,343,986 generated quads.
Original motion,17 completed4K images and ten original resource files match.
Its initial snapshot verification fails because the original-model journal ends
before the selected native5072 scene. That failure is retained separately.
Moving the original journal window one frame later and repeating **both** the
control and observer produces a complete independent pass:1,611 instances,
16,335 quads/401 viewport quads, exact original device context, and the first
supported model of the independently journaled game scene. No guard was removed.
All2,457 ordered scene, clock and geometry fingerprints also repeat exactly
between the initial and correctly aligned capture runs.
Hong Kong5990 also passes its paired run, exact original context and scene
boundary:818 instances/5,478 quads/452 viewport quads. The5000 comparison initially
requests17 images against a21-image reference; the strict completeness check
correctly rejects that test configuration. A new control/observer pair uses the
full original21-image interval and passes:1,515 instances/9,595 quads/4,740
viewport quads. Across the six control/observer replays, all55 sampled4K images
per side and all three original resource pairs match. Hong Kong
2,457scene/30,411,603quad/clock fingerprints repeat across its two observation
windows. Seven-default renewal is running separately; it is not implied by
these observations.

## Cost and conservative offscreen bounds

The first broad Amazon observation averages6.21ms for source assembly, geometry
and full hashing; p99 is11.61ms and the maximum14.72ms. The one requested raw
snapshot separately costs336.5ms. These are diagnostic timings, not extra-GPU
rendering performance. Production drawing must avoid that synchronous snapshot
work and unnecessary geometry processing.

A local Python prototype derives an axis-aligned bound from actual model
vertices. Outward-rounded float intervals propagate the original transform and
projection; bounds crossing the near plane remain eligible. It does not rely on
the game's sphere radius. Comparison against all independently verified native
quads in the three earlier standalone snapshots rejects no viewport polygon:

| Scene | Objects rejected before polygon projection | Offscreen quads avoided | Viewport quads retained |
| --- | ---: | ---: | ---: |
| Hong Kong5000 |725/1,515|4,741/9,596|4,740|
| Amazon5072 |1,535/1,622|15,881/16,408|382|
| Hong Kong5990 |740/818|4,598/5,478|457|

The standalone local native draft agrees with Python for all3,955 objects and
rejects the same3,000 offscreen objects. It is not linked into MAME. It still
needs reusable source integration, independent boundary/rounding tests and
broader live comparison before enabling it. These three snapshots do not
establish general correctness or a frame-time improvement. The earlier
prototype report counted only its stored visible
polygons; the follow-up `scene-model-bounds-native-quads.json` explicitly joins
the complete native instance/quad files to count avoided offscreen work.

## Remaining work

Renew default regressions on the exact candidate, then connect owned material data,
separate host depth, sky/foreground ordering and source handover. Earlier
unsubmitted sources still need eligibility checks to address the Amazon black
ground patch without reviving removed or moving objects. Extra admitted
geometry and unchanged original resources are insufficient visual acceptance.

The upstream review covers master17d291 and all291 open PRs. A September10
09:17UTC refresh found no additional Zeus work. See the separate
[upstream review](2026-09-09-zeus-upstream.md) for the isolated depth/blending
trials and the still-missing dot-clock/framebuffer-latching change.

The [public proof](../../results/proof/2026-09-10-exotica-live-scenes/README.md)
checks33 hash-bound receipts and their declared consistency. It does not
recompute the unarchived geometry, resources, motion or pixels.

Personal Stream Deck remains v0.5.0/SHA87d04de4. The last seven-default acceptance
belongs to b3d82b/SHAe7780a7a. No release, deployment, hosted workflow, menu removal,
World force tuning or physical-force test occurred.
