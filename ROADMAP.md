# Cruis'n Collection — Roadmap

Stable IDs for easy reference. Detail lives in `results/RESULTS.md`
(chronology) and `.claude/session-notes.md` (handoff). Update status here
as items move.

**Status:** ☐ open · ◐ partial · ☑ done
**Effort:** S (hours) · M (a session) · L (a few sessions) · XL (arc)
**Auto:** ✅ good overnight/unattended · ⚠️ partial (needs a decision or a
capture) · 🙋 needs the user at the wheel

---

## A. Big arcs

| ID | Item | Status | Effort | Auto | Notes |
|----|------|--------|--------|------|-------|
| **A1a** | Zeus GL internal upscaling (Exotica sharpness) | ☑ | — | — | **DONE (session 5).** Exotica renders live through our GL renderer at 4× internal res with hardware-accurate bilinear textures - crisp. Proof: results/proof/zeus-live-vegas-4x.png. (Roadmap earlier mis-stated this as "native res".) |
| **A1b** | Exotica 16:9 widescreen | ☑ | — | — | **DONE (2026-08-23).** 3D scenes present 16:9 (wider canvas, margins cleared per frame, aspect hysteresis vs wobble); 2D screens stay 4:3. MIDZ_GL_MARGIN=0 forces 4:3. Perf recovered same session (skip double-rasterization: 94%→99.8%). |
| **A2** | FOV-constant DSP patch (proper Hor+) | ☑ | — | — | **RESOLVED 2026-08-23 (Exotica) — no game patch needed.** The game already renders full 16:9; black margins were our overlay's page-blind margin clear wiping the displayed page every frame. One scissor fix in zeus2.cpp → true Hor+ (proof: results/proof/zeus-true-169-*.png). V-Unit games keep the shipped margin-extend approach (their transform does clip to 4:3). Toolkit built along the way (MIDZ_PATCH / MIDZ_PCLOG / MIDZ_RINGTAP + full crusnexo disassembly) now serves C2. |

## B. Features

| ID | Item | Status | Effort | Auto | Notes |
|----|------|--------|--------|------|-------|
| **B1** | Telemetry Phase B — wire Off Road + World speed | ◐ | S | ⚠️ | USA done/live-verified (0x0F22D). **World done 2026-08-23** (0x0DDDC, hunted via speed+odometer signature, live-verified 0→277 over UDP) — NEEDS ONE WHEEL CHECK that this field == the on-screen speedo vs a sibling. **Off Road still open**: attract demo shows no clean accelerate-from-0 curve (candidates spike-and-drop / signed velocity); needs an on-screen-MPH correlation pass at the wheel. |
| **B2** | Telemetry Phase B — RPM | ☐ | M | ⚠️ | No clean candidate on first pass (may be normalized 0..1 / gear-reset). Revisit with on-screen correlation. |
| **B3** | Auto-volume (full) — bake CMOS volume per game at boot | ☐ | M | ⚠️ | `=`/`-` manual volume shipped. Full = RAM/NVRAM-hunt the volume byte, poke at boot so nobody adjusts. Tooling (nvram_tool.py + RAM-hunt) ready. |
| **B4** | Steering settings growth — FFB strength + more knobs | ☐ | S | ✅ | SENSITIVITY + CURVE shipped. Add FFB strength (and aspect is already the WIDESCREEN row). Self-contained shell + cfg work. |
| **B5** | Sky-streak polish — vertical-gradient sky fill in margins | ☐ | S | ✅ | Faint horizontal streaking where sky is clamp-extended in top margins (all 3 V-Unit games). Refine margin-extend to gradient-fill sky. Cosmetic. |
| **B6** | Wizard >32-button capture already solved via rawjoy | ☑ | — | — | Raw Input HID (rawjoy.py) sees all 128 Moza buttons. (Kept for reference.) |
| **B7** | GEAR UP / GEAR DOWN sequential-shift bindings | ☐ | M | ✅ | User request (2026-08-23): wizard offers Gear Up/Down for sequential/paddle shifters; a stateful translator (virtual current gear) asserts the right game gear button across all four games. Needs driver-side state (ctrlr mappings are stateless) - env-gated input hook. |

## C. Game-code patches (unblocked by MIDV_PATCH)

| ID | Item | Status | Effort | Auto | Notes |
|----|------|--------|--------|------|-------|
| **C1** | Off Road coinage → 1 coin / 1 credit (or free play) | ☐ | S | 🙋 | One service-menu (F2) change to bake into the fixture, OR locate the CMOS coinage byte and patch. Needs a service-menu pass or a hunt. |
| **C2** | Render distance / texture pop-in | ☐ | L | ⚠️ | Game-code (TMS32031) culling/LOD patch. Research-grade, no promise. Uses the FOV-trace groundwork + patcher. |

## D. Housekeeping

| ID | Item | Status | Effort | Auto | Notes |
|----|------|--------|--------|------|-------|
| **D1** | mame-src `cruisn-poc` string cleanup | ☐ | S | ✅ | POC-NOTES.md + generated-header comments still say cruisn-poc. Piggyback on the next mame-src commit (forces a patch-series refresh). |
| **D2** | Gamepad axis-order table validation | ☐ | S | 🙋 | Positional/approximate; validate on a pad-only run (support bundle shows truth). |
| **D3** | Mid-game EIP=0 crash singleton | ☐ | M | ⚠️ | One-time (2026-08-19), unexplained. WER minidumps in rig/crashdumps/. Investigate if it recurs. |
| **D4** | Upstream the winhybrid DIJoystick2 fix to MAME | ☐ | M | ✅ | Nice-to-have; the 128-button fix benefits mainline. |
| **D5** | Upstream MAME watch (standing task) | ☐ | S | ✅ | Check mamedev PRs (zeus2/midvunit/dcs) each catch-up + before every release tag. Already in project memory. |

## E. Ideas (researched)

| ID | Item | Status | Notes |
|----|------|--------|-------|
| **E1** | Achievements | ✋ dead-end | RetroAchievements needs approved clients; arcade RA = FinalBurn Neo (no V-Unit/Zeus); standalone MAME never integrated rcheevos. Blocked by policy. `docs/ACHIEVEMENTS.md`. Only alive as a bespoke non-RA layer fed by the speed/RPM telemetry (B1/B2). |

## F. Release

| ID | Item | Status | Notes |
|----|------|--------|-------|
| **F1** | Tag v0.3.0 | ☐ | Once the pending rig test passes. Everything since v0.1.0 (v0.2.0 never tagged): all fixes, wizard, telemetry, Exotica live GL, widescreen + backdrop fix, per-game audio. Bundle mame-src `bgfx/` (Exotica CRT) in the release. |

---

## Plan of attack — overnight sessions

Batched by what runs well autonomously. Each session is self-contained and
commits as it goes.

### Overnight 1 — "Telemetry + settings complete" (all ✅/⚠️, low risk)
- **B1** wire World speed (turnkey hunt) + Off Road speed (best-effort slot, flag for verify).
- **B4** FFB-strength setting (shell + cfg).
- **B5** sky-streak vertical-gradient polish.
- **D1** cruisn-poc string cleanup (rides the mame-src commit B-work triggers).
- Deliverable: telemetry real for USA+World+(OffRoad), nicer settings, cleaner margins.

### Overnight 2 — "CMOS baking" (⚠️, needs the hunt but unattended-capable)
- **B3** auto-volume: RAM-hunt volume byte per game, poke at boot.
- **B2** RPM hunt (with the speed anchor for correlation).
- **C1** Off Road coinage: locate CMOS coinage byte, bake into fixture (avoids the service-menu pass).
- Deliverable: games boot at correct volume + coinage, RPM telemetry.

### Overnight 3 — "Zeus upscaling arc, phase 1" (XL, start the big one)
- **A1** Zeus GL: capture Exotica quads → build the CPU oracle (mirror the V-Unit zeus_rasterize approach at internal res) → first upscaled render.
- Deliverable: proof-of-concept Exotica at 3-4× internal res (may span multiple overnights).

### Optional / R&D — "FOV novelty" (A2)
- Only if you want the proper-Hor+ experiment for its own sake. Uncertain, IDA-grade. Not needed for any shipped feature.

### Needs you (not overnight)
- **C1** service-menu pass (if not baked via hunt), **D2** pad validation, and all **testing**.
