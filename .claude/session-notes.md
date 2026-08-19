# Session Notes
<!-- Handoff notes. Read these first, then CLAUDE.md, then results/RESULTS.md. -->

- **Date:** 2026-08-18
- **Branch:** master (mame-src side: `poc/quadlog`)

## What Was Done (single marathon session, 08-17 → 08-18)

The entire POC-to-playable arc:
1. **Oracle**: attract mode proven bit-identical across cleanroom runs.
2. **Capture + CPU re-render**: 1.25M quads captured; Python rasterizer
   reproduces MAME's framebuffer 100.0000% bit-exact.
3. **Widescreen**: TMS32031 never clips — true Hor+ 16:9 is a raster-window
   change; both margins fill 100% with real geometry.
4. **GPU prototype**: moderngl pipeline 100.0000% bit-exact both scenes;
   4×/16:9 at 3.5 ms/scene (~289 fps).
5. **Live, out-of-process**: shared-memory ring + viewer at 136 fps sustained.
6. **Live, in-process**: GL thread inside vunit.exe, owned-popup overlay,
   one window. **Rig-verified artifact-free** after four fixes driven by the
   user's live observations (owned popup vs DC-cache punch-through; per-scene
   margin scissor-clear; axis-aligned 2D classifier; 2px overscan inset).
7. **FFB staged**: plugin files beside vunit.exe, `output windows` set,
   racing-build Cruis'n tuning (GameId=22).
8. Product reframed as **V-Unit Cruis'n Collection** (USA + World + Off Road
   Challenge); Exotica = Zeus hardware, stretch goal gated on a scoping capture.

## Decisions Made

- Renderer-replacement over MAME (wanszai architecture), not recompilation —
  TMS32031 has no tooling ecosystem; MAME already emulates it.
- Index-space rendering (R16UI palette indices) so verification is
  word-for-word vs videoram; palette pass after.
- Overlay = owned top-level popup, never a child window (MAME caches its
  window DC; child clipping is unfixable).
- Shaders generated into mame-src from `gpu/renderer.py` — one source of truth.
- Exact mode exists for verification; quality mode (float u/v, continuous
  coverage) is the shipping configuration.

## Open Items

- [x] **Wheel test PASSED** (2026-08-18 night): coin/Start/Esc/steering/FFB
      all confirmed through the Stream Deck button, fullscreen. Along the
      way run_rig.py gained: `output windows` (was documented but missing —
      FFB was silent without it), borderless-fullscreen + focus enforcement
      (button launches had dead keyboard), ctrlr sanitizer (BUTTON33+ tokens
      invalidated whole seqs, killing keyboard Start), and hang auto-retry.
      Details in RESULTS.md's 2026-08-18-night sections.
- [ ] `JOYCODE_1_BUTTON33+` dropped by token parser — wheel coin/start on
      high buttons still don't bind (sanitized ctrlr works around it;
      keyboard 5/1 fine). Root-cause MAME's joycode token validation vs our
      128-button DIJOYSTATE2 patch.
- [ ] Verify crusnwld + offroadc through the renderer (same driver; oracle
      harness works unchanged — needs their NVRAM fixtures).
- [ ] 16:9 margin pop-in sweep across long gameplay (2 scenes verified clean).
- [ ] 2D-vs-3D classifier: watch for misclassified scenes during real play.
- [ ] Multi-hour soak (texture churn, leaks, ring health).
- [ ] Collection shell (Phase 5): game-select menu, config file, CRT pass —
      wishlist in the racing repo's feasibility doc.
- [ ] Zeus scoping capture for Exotica (stretch): find midzeus's render choke
      point, assess like we did process_dma_queue.

## Next Steps

1. ~~Ingest the user's wheel-test results; fix what they surface.~~ DONE —
   Phase 1 closed end-to-end (rig-verified playable via Stream Deck).
2. JOYCODE high-button tokens root cause (wheel coin/start).
3. crusnwld/offroadc verification passes.
4. Begin the collection shell / config layer.

## Context for Next Session

Everything is committed: cruisn-poc (master), mame-src (`poc/quadlog`, series
exported to `patch/`), racing repo (feasibility doc + ROADMAP current).
`RESULTS.md` is the full engineering log — trust it over memory. The user has
FFB staged and untested; their live screen observations have been the most
effective debugging instrument in the project — solicit them.
