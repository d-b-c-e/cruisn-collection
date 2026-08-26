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
| **B1** | Telemetry Phase B — speed (all games) | ◐ | M | ⚠️ | **2026-08-26 overnight: HUD OCR extended to World + (provisionally) Off Road.** crusnwld box (14,76,342,368) calibrated offline from the user's drive captures - USA's digit templates read World's digits unchanged (shared font confirmed; validated trace 0->97 with clean accel/decel). offroadc's MPH box sits at the TOP of the screen (outside the old dump window): provisional box (228,270,22,52) from the user's screenshot geometry, runtime OCR rejects unreadable frames (emits 0, never garbage); the RAMDUMP hud window is now per-game (offroadc rows 0-99) so the next drive validates it offline. Exotica speed still unhunted (Zeus). |
| **B2** | Telemetry Phase B — RPM | ◐ | S | ⚠️ | crusnusa CONFIRMED + wired (0x0E632.lo16, r=+0.91 vs tach). World: TWO hunt rounds 2026-08-26 (210 OCR-aligned race frames, refined variance-based tach metric, all 3 RAM banks, lo16/hi16): best r=0.47 - like player speed, World's RPM does not live in dumped memory with a shape the gauge metric can catch. Next attempt needs a dedicated capture (2-3 standing-start full-throttle runs, gears held, no menus) AND a hand-verified tach-segment pixel list for the metric. Off Road follows the same protocol once its HUD box is validated. |
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
| **C3** | Cruis'n World full-margin coverage | ◐ | M | 🤖 | **CODE COMPLETE 2026-08-26, pending live drive.** Sky half (5-tile panorama) AND terrain half (big-poly subdivision path: 4 right-bound immediates 511->597, 2 sign-test branches -> CALLLT x+86 routines in padding) both in crusnwld-widescreen.txt. 12000-frame attract: 0 records removed, +134 all-margin. World's ordinary polys were never screen-culled (hence the high native coverage) - the holes were dropped sub-quads of large near polys, i.e. crash cams / close walls, so the live drive is the real test. crusnusa: same check whenever gaps are ever observed (~99% native). |

## G. Rig-session triage — 2026-08-25 (user's minor list)

| ID | Item | Status | Effort | Auto | Notes |
|----|------|--------|--------|------|-------|
| **G1** | Launch "ding" — STILL present, all four games | ☑ | M | ⚠️ | **SOLVED 2026-08-25 (config, one line): the tuned FFBPlugin.ini shipped `BeepWhenHook=1`** - the plugin chimes MessageBeep(MB_ICONASTERISK) on hook install by design, default 0. Flipped to 0 on the rig, guarded in run_rig.apply_ffb_strength (re-forced every launch), forced in make_release.ps1's shipped ini. Verdict = silent launches on the user's next session. |
| **G2** | Launcher hangs on quick game exit (stuck LAUNCHING, alt-tab/alt-f4 dead) | ☑ | S | ✅ | **FIXED 2026-08-25**: enforce_foreground aborts as soon as the target window dies or stops answering WM_NULL. Quick-exit probe: WM_CLOSE handled in 0.7s, no post-exit foreground fighting (0/8 samples), launcher recovers. |
| **G3** | Exotica car-select stats text illegible | ☐ | M | ⚠️ | RECLASSIFIED 2026-08-25: text equally illegible via MAME's own d3d output (user captured both) → upstream zeus2 emulation bug. **Upstream checked 2026-08-26: no text-rendering fix exists post-0.286** (only #15719 road fix - backported - and open #15723 - backported); fixing this = novel zeus2 RE (texture/alpha path at small glyph sizes), a candidate for our next upstream-grade contribution. Fresh-session-sized. |
| **G4** | Off Road track-select: thin black vertical seams | ☑ | S | ⚠️ | **FIXED 2026-08-26**: 2D screens now get a tight 1-px crack-fill pass (3D keeps the full radius; the fine-dither checkerboard guard already protects translucency). Hairline bitmap-tile seams like the Off Road track select's vertical lines fill; anything wider on a 2D screen is left alone as potentially intentional. |
| **G5** | Settings UX: per-game labels unclear + screen cluttered | ☐ | M | 🙋 | CONFIRMED with user 2026-08-25 (works, not intuitive). **Design proposal drafted: docs/settings-redesign.md** (three submenus - DISPLAY / WHEEL & FFB / GAME TUNING with an explicit game banner; new rows for SHIFTER TYPE, per-game VOLUME and FREE PLAY now that CMOS is mapped). Three open questions for the user in the doc. |
| **G6** | Settings screen invisible to screenshots | ☐ | S | ⚠️ | 2026-08-26 investigation: keyboard exonerated (settings mode ignores unknown keys - PrintScreen can't exit it), and the captured image genuinely RENDERS menu mode, so something flips `mode` around the capture. Next: a one-line mode-transition log in the shell + a repro with the user. |
| **G7** | Manual mode: H-pattern gear engagement mis-detected | ☑ | M | ⚠️ | **IMPLEMENTED 2026-08-25, pending live drive**: run_rig.apply_shifter_config writes CONF=H-Pattern (V-Unit trio) + sitdown-cabinet DIP (crusnwld DSW 0x20, crusnexo DIPS 0x400) into rig/cfg when [wheelmap] has gear1-4 bound; closed-loop verified (MAME's rewritten cfg keeps :CONF value=0 after a real launch). User to confirm: USA gears engage on ENTRY now, World offers MANUAL, Exotica shows transmission select. "Sequential" (5) remains the B7 answer for paddles. |

| **G8** | FFB forces not released when a game closes | ☑ | S | ⚠️ | **INTERIM SHIPPED 2026-08-25**: run_rig.release_ffb() (SDL2 HapticStopAll/Close on every device, borrowed from the plugin's own SDL2.dll - its source confirms DLL_PROCESS_DETACH did exactly this) runs after every game exit in both the blocking launcher and the shell path. Real fix (patched plugin) folded into G1's follow-up if ever needed. |
| **G9** | B3 volume bytes: first data points | ☑ | M | ⚠️ | **RESOLVED 2026-08-26: no checksums anywhere.** Single-byte persistence experiments on all four games: every poked byte survived a full boot (crusnwld nvram 0x93C, offroadc 0x7BC/0x92C, crusnexo m48t35 0x27, crusnusa 0x200-mirror-set - the game even accepts a lone mirror change). Byte map + `nvram_tool poke` shipped. Remaining polish: label master-vs-minimum for offroadc's two fields from the F2 menu next time someone is at the wheel, then bake shipping defaults (B3). |

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
