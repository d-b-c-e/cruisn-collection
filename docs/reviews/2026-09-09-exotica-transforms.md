# Exotica transform foundation — September 9, 2026

Exotica2.4 now has a standalone native transform helper, independent Python
reference and bounded Lua probes. The helper reproduces the game's camera
transform, object rotation, matrix-cache decision, scaled Zeus command words
and near/far model choice without executing guest CPU code. It is not linked
into MAME and does not yet draw extra scenery.

## Evidence

The final probe covers3500..3525,4650..4750 and5400..5420:148 frames,
40093 calls,487 objects and384 ordinary selected models. Native and Python agree
on all captured centers/depths and emitted transform packets. These include
13693 matrix updates and26400 translation-only commands. Independently checking
the preexisting cache value reproduces every update/reuse decision. All39541
ordinary model emissions match the actual command-ring writes;3051 use the
farther model. The threshold is a signed depth strictly greater than25000.

World-coordinate mode0 covers40067 calls. Already-transformed mode3 covers26;
its position and rotation bypass the camera transform. Modes1/2 remain rejected
by the standalone helper because these captures do not exercise them. Rotation
preparation preserves the C31's extended intermediates and explicit scratch
store/reloads; ordinary floating-point matrix multiplication is insufficient.

The remaining552 calls use the special flag0x80 path. Their centers, rotations
and transform commands pass, but their model geometry/emissions are excluded.
There is no model or level allowlist.

Four6000-input runs—control, initial probe, expanded probe and final reusable
probe—preserve4191 camera samples and12573 actual ADC addresses/values/timestamps
over1800..5990. All four match the21 original3840x2160 images and identical
captured Zeus records, WaveRAM, palettes, register snapshot and CPU-buffer files
at4699..4700. Unchanged CPU buffers under liveGL are not a visual oracle.

## Failures retained and corrected

The first reference finds102 transform-packet mismatches in28661 calls. Its
normal object+5 rotation source was wrong for flag0x80, which uses object+0x8b.
The read of B47D at PC6964 is in a delayed branch's final slot: special draws
read that constant but branch away from the ordinary model command. The final
probe also watches the actual command-ring completion at PC6970. All39541
ordinary calls have exactly one matching completion; special calls have none.

The expanded frame range includes a mode3 path absent from the first range.
An initial strict Lua-frame/native-frame offset assertion also fails.28451 calls
have an offset of1 and11642 have0; two emissions cross a native frame boundary
between preparation and completion. The verifier records both native frames and
exact emulated times, and permits that adjacent-frame transition explicitly.
Both initial clock failures are retained. An initial standalone analyzer launch
also lacked MinGW runtime DLLs on PATH; the corrected environment passes.

## Reusable tools and boundaries

- `lua/exotica_model_capture.lua`: ordered, bounded windows totaling at most240
  frames and65536 calls; code/layout guards; direct main-RAM reads; no guest
  writes, allocation or input synthesis. Raw object operands remain local.
- `lua/exotica_motion_trace.lua`: bounded camera and actual analog-read trace.
  The shared motion comparer now checks Exotica's analog-port address as well
  as frame, PC, value and exact time.
- `native/exotica_transform.h` and `harness/exotica_transform.py`: standalone
  arithmetic, cache policy and LOD selection. Callers still own revision,
  material, scene and special-model guards.
- `harness/verify_exotica_transforms.py`: checks completeness, identities,
  expected commands and actual emissions; optionally checks the independent
  `native/analyze_exotica_transform.cpp` executable against every call.

Local checks pass253 Python tests/no skips,24 native test programs,10081 C31/137
yaw vectors and32 GPU checks,66 commands. The376-file source identity is
`79f84eb16e15b9a7d9fb9863e4f9f34bef614b04f85b2f049c0f5474378b88a2`.
The [public proof](../../results/proof/2026-09-09-exotica-transforms/README.md)
recomputes four input/motion traces and three selected4K images per run. Full
transform/raw-resource/native/GPU execution and remaining images are receipts.
The123-file archive contains no raw ROM/model/WaveRAM/object dumps.

## Next work

Decode Exotica's Zeus WaveRAM model packets independently, then compare original
projected quads and material/depth state. Keep the extra renderer's state isolated:
earlier guest-admission experiments changed original depth bias2047 to0. Resolve
pending/future-section descriptors, material upload readiness and the scene
insertion boundary before adding host drawing. Preserve original resources,
occlusion and handover; additional submissions alone do not establish a benefit.

Native remains4a507c5f372/SHA c88ae4f2, separately built for Off Road. Its seven
default passes belong to the preceding Off Road milestone; this standalone work
does not renew that suite. Personal Stream Deck stays v0.5.0/SHA87d04de4. No new
native build, release, deployment, hosted workflow, physical FFB, World force
tuning or menu removal occurred. Continue directly; the one-minute heartbeat
is recovery only, with no cutoff.
