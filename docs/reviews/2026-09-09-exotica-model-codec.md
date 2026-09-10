# Exotica Zeus model codec — September 9, 2026

Exotica now has a standalone model decoder that reproduces original Zeus geometry
and render state in both C++ and independent Python. This follows the checked
[game-side transforms](2026-09-09-exotica-transforms.md). It is a foundation for
host-owned scenery; the new decoder does not yet draw additional objects.

## Exact original geometry and state

Three captured scene windows at frames 3500, 4700 and 5410 contain 939 model
submissions and 13,876 input polygons. Both decoders reproduce all 8,126 emitted
polygons in their original order. Comparison covers the entire 260-byte record:
all 17 state fields and all eight padded vertex slots. This includes texture
selection, UVs, transparency, depth bias, depth-write flags and clipping bounds.

The cases exercise 10-, 12- and 14-word polygon formats, 131 near-plane rejects,
5,619 backfaces and 50 partially clipped polygons. The decoder applies 1,732
model-local register writes to private context copies. It never writes those
changes back to the emulated Zeus device. That distinction matters because an
earlier guest-admission experiment changed original depth bias from 2047 to zero.

A repeated frame-4700 capture reproduces all 316 models and 2,570 polygons. Its
539,152-byte model journal is byte-identical, including the exact emulated clock.
The three windows establish original model decoding, not all game commands or
future material lifetime. Palette-load commands inside models remain explicitly
unsupported until their ownership and upload behavior are checked.

## Capture and verification

The separately built native candidate adds an opt-in, bounded journal at the
existing Zeus capture boundary. It records the model before execution, its
private starting context, and the actual original polygon span produced by that
call. Capture requires Exotica and physical force disabled. It is limited to
4,096 models and 64 MB, validates WaveRAM bounds and records completion. Ordinary
launches do not enable it.

Use `harness/replay.py --zeus-capture-frame FRAME --zeus-capture-models` with an
existing Exotica recording. `harness/verify_zeus_models.py` checks the completed
journal in Python and can run `native/analyze_zeus_models.cpp` for a second full
comparison. Truncation, ownership, unsupported commands, private state, signed
depth bias, alpha and near clipping have focused tests.

Five 6,000-input replays preserve 4,191 camera samples and 12,573 actual ADC
addresses, values and timestamps over frames 1800–5990. All match the 21 original
3840×2160 gameplay images. At frame 4700, the control, captured run and repeat
also preserve all eight original Zeus resource files, matching the earlier
candidate. Those include original records, WaveRAM and palette/register state.
The other two model windows have full independent geometry checks but no separate
old-candidate resource pair at those times.

The initial local prototype assumed ten words per polygon and encountered 1,271
unknown-command issues. It is retained locally. The completed journal records the
actual polygon size and starting state for each call; no model allowlist is used.

## Build and acceptance

Native commit `eb17cf2dd0483e9e08907eb994643570977b289b` is built separately as
`build/candidates/eb17cf2dd04/vunit.exe`, SHA256
`ee2bd4d0070f3b2126c9971b30074e1160bc3f4bece76839f30559a9cff0017f`.
The 147-patch export reconstructs tree
`87a5bf7c64ed8aec6c17f05120be0ef9775f139a`.

Local checks pass 257 Python tests with no skips, 25 native test programs,
10,081 C31 and 137 yaw vectors, and 32 GPU checks across 69 commands. The
384-file source identity is
`1f74e3a1f37d9c5ea06dc36595ffe640489ae2c48b6b98258c0b14d51055441c`.
All seven default regression cases pass on this exact candidate and source
identity, including the full Germany replay, actual UDP/memory telemetry, four
software force-policy/polarity checks and Exotica's 21 original 4K images.

The [182-file public proof](../../results/proof/2026-09-09-exotica-model-codec/README.md)
recomputes five input/motion traces, three selected 4K images per run and the
seven telemetry/four software-force verdicts. Full model geometry and state,
raw resource equality, remaining images and native/GPU executions are hash-bound
receipts. Raw ROM, model, WaveRAM and geometry operands stay local.

## Next

Reconstruct Exotica's section allocator and future render descriptors, then check
model/material residency and the correct scene insertion boundary. Only after
those contracts are checked should the standalone transforms and model decoder
feed additional host-owned draws. Original resources, foreground occlusion,
handover, repeatability and full-speed 4K presentation remain acceptance gates.

The personal Stream Deck binary stays at v0.5.0/SHA87d04de4. No deployment,
release, hosted workflow, physical force, World force tuning or menu removal.
Continue working directly; the one-minute heartbeat is recovery only.
