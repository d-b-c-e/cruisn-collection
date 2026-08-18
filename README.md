# Cruis'n USA — Renderer-Replacement POC

Proof-of-concept work for the feasibility study at
`E:\Source\launchbox\Launchbox-Racing\docs\cruisn-usa-port-feasibility.md`.

Goal: prove the two load-bearing claims of the study —

1. **MAME's software rasterizer is a usable pixel-exact oracle** — attract
   mode replayed twice produces bit-identical frames (`harness/run_oracle.py`).
2. **`process_dma_queue()` is the whole interception surface** — a tiny patch
   can capture the complete quad stream, and the stream is sufficient to
   re-render the frame externally (`patch/`, `harness/`).

## Layout
- `harness/run_oracle.py` — determinism oracle (two cleanroom runs, pixel diff)
- `lua/snap.lua` — frame-scheduled snapshots, driven by SNAP_FRAMES env
- `fixtures/nvram-crusnusa/` — calibrated NVRAM so boot reaches attract mode
- `patch/` — quad-capture patch against mame-src (0.286 + local DIJOYSTATE2 patch)
- `results/` — reference frames + capture analysis

## Environment
- Oracle runs against the deployed racing-build binary
  (`Launchbox-Racing\Emulators\mame286\mame.exe`) — never modified here.
- POC builds happen in `E:\Source\mame-src` as subtarget builds (`vunit.exe`),
  which cannot clobber the deployed `mame.exe`.
- Toolchain: MSYS2 at **E:\msys64** (reinstalled 2026-08-17 after the C: wipe;
  the old `C:\msys64` note in the racing CLAUDE.md is stale). GCC 16.2.0.
