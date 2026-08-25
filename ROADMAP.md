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
| **A2** | Game-code widescreen (parity with Ridge Racer) | ☑ | — | — | **REACHED 2026-08-24.** offroadc game-code clip patch shipped (rig-verified, auto-applies at 16:9 FULL); crusnusa 99%/99% + crusnwld 92%/99% native margin coverage (overdraw past 4:3 - no patch needed); Exotica native full 16:9 (Zeus chip). offroadc LEFT edge DONE 2026-08-24 (sign-test reject mirrored via a 12-word CALLLT routine in NOP padding - both edges now game-drawn; awaiting live drive). Nicety left: attract-showcase corners. |

## B. Features

| ID | Item | Status | Effort | Auto | Notes |
|----|------|--------|--------|------|-------|
| **B1** | Telemetry Phase B — speed (all games) | ◐ | M | ⚠️ | **REBOOTED 2026-08-23**: the attract-hunted words (USA 0x0F22D, World 0x0DDDC) track DRONES; player speed persists in NO memory (proven vs HUD-OCR ground truth across both RAM banks + C31 internal RAM). Replacement = **HUD-quad DMA tap** (digit identity is in the quad texcoords at queue time — correct by construction, all 3 V-Unit games). World calibrates headless (attract shows MPH box); USA needs one short drive. Speed emits 0 until it lands. |
| **B2** | Telemetry Phase B — RPM | ◐ | S | ⚠️ | **crusnusa CONFIRMED + wired 2026-08-23**: 0x0E632.lo16 (uint16, 0..~14.6k) — validated r=+0.91 against the on-screen tach gauge's fill pixels over a real drive. Earlier 0x0DC20 was a drone. World/Off Road RPM via the same HUD-gauge correlation once their captures exist (World headless-able). |
| **B3** | Auto-volume (full) — bake CMOS volume per game at boot | ◐ | M | 🙋 | **Measured 2026-08-23** (-wavwrite loudness pass): V-Unit trio mutually CONSISTENT (~-33 dBFS active) — no normalization needed; quiet in absolute terms = native mix. Exotica captured SILENT headless (attract sound likely off in CMOS; user hears it live when coined). Reclassified needs-the-wheel: Exotica volume needs a service-menu (F2) pass, then bake CMOS via nvram_tool. Blind pokes risk the NVRAM checksum. |
| **B4** | Steering settings growth — FFB strength + more knobs | ☑ | — | — | **DONE 2026-08-23.** FFB STRENGTH row (0–100%, default 100) scales the plugin's force ceiling via run_rig.apply_ffb_strength (patches FFBPlugin.ini [Settings], per-game keys untouched, no-op if plugin absent). Persists in collection.ini; also `run_rig --ffb`. SENSITIVITY + CURVE + ASPECT already shipped. |
| **B5** | Sky-streak polish — vertical-gradient sky fill in margins | ☐ | S | ⚠️ | First attempt (present-pass vertical gaussian blur) looked great on 3D sky but REGRESSED 2D screens (boot ROM self-test → vertical streaks): vertical blur smears any structured margin content. REVERTED 2026-08-23. Needs a sky-ONLY / 3D-scene-gated fill (the fill must not run on 2D/menu/test screens, or must detect sky vs structure). |
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
| **D1** | mame-src `cruisn-poc` string cleanup | ☑ | — | — | **DONE 2026-08-23.** Only stale ref was the midvunit_menu_assets.h header comment (generator already emits cruisn-collection); POC-NOTES.md was already clean. Fixed + patch refreshed. |
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
| **F1** | Tag v0.2.0 | ☑ | **DONE 2026-08-24.** Everything since v0.1.0 (CHANGELOG.md): fixes, wizard, telemetry, Exotica live GL, game-code widescreen both edges, per-game audio. `bgfx/` bundled by make_release.ps1; release body from `docs/release-notes/<tag>.md`. |

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
