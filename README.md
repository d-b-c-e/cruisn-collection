# Cruis'n POC — V-Unit Cruis'n Collection

Native PC port of the Midway V-Unit racers (Cruis'n USA, Cruis'n World,
Off Road Challenge) as a **renderer-replacement over MAME** — the wanszai
architecture. Companion to the feasibility study at
`E:\Source\launchbox\Launchbox-Racing\docs\cruisn-usa-port-feasibility.md`.

**Status (2026-08-18): Phase 1 complete and rig-verified.** Cruis'n USA runs
in one window with an in-process GPU renderer — 16:9, 3–4× internal
resolution, per-scene 2D/3D presentation, artifact-free — with wheel input
via the racing build's ctrlr and force feedback staged for testing.

```
python harness/run_rig.py        # play it
```

## What was proven, in order (full log: results/RESULTS.md)

1. **Oracle** — attract mode is bit-identical across cleanroom runs: MAME's
   software rasterizer is a pixel-exact regression reference.
2. **Complete interception** — the DMA quad stream + texture/palette state
   re-renders MAME's framebuffer **100.0000% bit-exact** outside MAME.
3. **Widescreen is free** — the TMS32031 never clips to the viewport; 4:3 is
   a raster-time crop. Both 16:9 margins fill with real geometry.
4. **GPU pipeline** — a fragment shader reimplementing MAME's poly.h renders
   bit-exact at native and 289 fps at 4×/16:9.
5. **Live** — out-of-process viewer (136 fps sustained), then in-process GL
   inside `vunit.exe` via an owned-popup overlay: one process, one window,
   stock input/audio/FFB path.

## Layout

- `harness/` — run_rig (product launcher), oracle, capture, CPU rasterizer,
  widescreen analysis, record_diag (60fps flashing detector)
- `gpu/` — renderer.py (verified pipeline, **shader source of truth**),
  live_viewer.py (out-of-process debug path)
- `patch/` — full mame-src series vs base `6f55ed93` (branch `poc/quadlog`)
- `fixtures/` — calibrated NVRAM so boot reaches attract
- `results/` — RESULTS.md (engineering log) + proof images

## Environment

- Emulator half: `E:\Source\mame-src` branch `poc/quadlog` → `vunit.exe`
  (subtarget build; cannot clobber `mame.exe`). Toolchain: MSYS2 at
  **E:\msys64**, GCC 16.2.0 — build command and traps in `CLAUDE.md`.
- Assets come from the racing build (`Launchbox-Racing\Emulators\mame286`):
  roms, EmuEzRacing ctrlr, FFB Arcade Plugin files + Cruis'n tuning.
- Ships nothing copyrighted: user's own ROMs, patch + build script model,
  GPL-2.0+ obligations from MAME derivation. WB owns a live brand — see the
  feasibility doc's legal posture.

New session? Read `.claude/session-notes.md` → `CLAUDE.md` →
`results/RESULTS.md`, in that order.
