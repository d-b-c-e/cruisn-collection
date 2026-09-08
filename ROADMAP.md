# Cruis'n Collection — Roadmap

Stable IDs for easy reference. Detail lives in `results/RESULTS.md`
(chronology) and `.Codex/session-notes.md` (handoff). Update status here
as items move.

**Status:** ☐ open · ◐ partial · ☑ done
**Effort:** S (hours) · M (a session) · L (a few sessions) · XL (arc)
**Auto:** ✅ good overnight/unattended · ⚠️ partial (needs a decision or a
capture) · 🙋 needs the user at the wheel

---

## Current priorities (2026-09-08, after v0.4.0)

v0.4.0 is published, with its exact ZIP verified after download and release evidence
archived in results/proof/2026-09-08-v0.4.0-release. The ordered, actionable queue
is [the overnight checklist](docs/OVERNIGHT-2026-09-08.md):

1. **Cheats submenu: initial implementation complete.** Continuous imported
   toggles/choices, default-off selections and replay state work across the four
   games. Five timer probes/replays and a frozen activation pass. Live one-shots,
   code-restoring actions and individual rank/nitro validation remain follow-up.
2. **Experiments beside Display: complete.** Contexts, preferences and exclusions
   are preserved; Back returns to Settings. See [overnight evidence](docs/reviews/2026-09-08-cheats-and-experiments.md).
3. **NEXT: Global draw-distance experiments for all four games**, prioritizing earlier
   visible mountains/trees and diagnosing activation, residency and draw limits.
   World New York black flashing and the 3x/+12 crash need further investigation.
4. Broaden attended drives, shifter and second-wheel coverage. World oscillation
   and cross-game force normalization remain known issues, with tuning deferred.

Current automated suite has seven cases, including completed Exotica GL frames.
All games now have guarded gear/rev telemetry with estimated RPM; World speed
still uses OCR. Fresh free-play seeds are corrected, including Off Road's checksum.
Historical tables below preserve earlier milestones and are superseded by this
queue and the dated engineering reviews where their status differs.

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
| **B2** | Validated engine RPM | ☐ | M | ⚠️ | **2026-09-06 correction:** USA E632 is packed decimal speed text, not RPM. The old correlation-based mapping is removed. RPM is unavailable until a guarded producer is found; Forza RPM fields remain zero and JSON reports rpm_status=0. World/Off Road/Exotica also need validated producers. |
| **B3** | Auto-volume (full) — bake CMOS volume per game at boot | ◐ | M | 🙋 | **Measured 2026-08-23** (-wavwrite loudness pass): V-Unit trio mutually CONSISTENT (~-33 dBFS active) — no normalization needed; quiet in absolute terms = native mix. Exotica captured SILENT headless (attract sound likely off in CMOS; user hears it live when coined). Reclassified needs-the-wheel: Exotica volume needs a service-menu (F2) pass, then bake CMOS via nvram_tool. Blind pokes risk the NVRAM checksum. |
| **B4** | Steering settings growth — FFB strength + more knobs | ☑ | — | — | **DONE 2026-08-23.** FFB STRENGTH row (0–100%, default 100) scales the plugin's force ceiling via run_rig.apply_ffb_strength (patches FFBPlugin.ini [Settings], per-game keys untouched, no-op if plugin absent). Persists in collection.ini; also `run_rig --ffb`. SENSITIVITY + CURVE + ASPECT already shipped. |
| **B5** | Sky-streak polish — vertical-gradient sky fill in margins | ☐ | S | ⚠️ | First attempt (present-pass vertical gaussian blur) looked great on 3D sky but REGRESSED 2D screens (boot ROM self-test → vertical streaks): vertical blur smears any structured margin content. REVERTED 2026-08-23. Needs a sky-ONLY / 3D-scene-gated fill (the fill must not run on 2D/menu/test screens, or must detect sky vs structure). |
| **B6** | Wizard >32-button capture already solved via rawjoy | ☑ | — | — | Raw Input HID (rawjoy.py) sees all 128 Moza buttons. (Kept for reference.) |
| **B7** | GEAR UP / GEAR DOWN sequential-shift bindings | ☑ | M | ✅ | **IMPLEMENTED 2026-08-29 natively** - no translator needed for V-Unit: MAME's CONF "Sequential" (5) mode already keeps a virtual gear (shift_button handler, Shift Down=P1_BUTTON5 / Up=P1_BUTTON6). Wizard gained SHIFT UP/DOWN steps (skippable); apply_wheelmap arbitrates H-pattern vs paddles (they share BUTTON5/6 - full H-pattern wins); apply_shifter_config writes CONF=0 (H) or 5 (Seq). Exotica has NO native sequential mode (gears BUTTON2-5, no CONF) - paddles-only rigs keep its auto-select; the old stateful-translator idea remains as an Exotica-only future polish. |

## C. Game-code patches (unblocked by MIDV_PATCH)

| ID | Item | Status | Effort | Auto | Notes |
|----|------|--------|--------|------|-------|
| **C1** | Off Road coinage → 1 coin / 1 credit (or free play) | ☐ | S | 🙋 | One service-menu (F2) change to bake into the fixture, OR locate the CMOS coinage byte and patch. Needs a service-menu pass or a hunt. |
| **C2** | Render distance / texture pop-in | ◐ | L | ⚠️ | **GATE FOUND 2026-08-30 round 2** (RESULTS.md): crusnusa word 0x55 = renderer draw-distance (80000), LOD switches at words 0xBF/0xC3 (8000/15000). All prior nulls explained: the game re-copies ROM over words <0x10040 at startup - fixed with the self-healing MIDV_PATCH (mame-src 784bdfc6, benefits C1 too). Control verified live (20000 collapses the world). Extension limited by the SECTION STREAMER's spawn window (p75 ~72k) - round 3 target. Try-me: patch/game/crusnusa-renderdist-experiment.txt; needs user's eyes at the wheel before productizing (SETTINGS row). |
| **C3** | Cruis'n World full-margin coverage | ◐ | M | 🤖 | Sky + terrain-cull halves SHIPPED and live-verified except a RESIDUAL minor class: rare black edge slivers (user's NY report) = geometry never submitted at margin positions - buffer-cap theory tested and FALSIFIED 2026-08-29 (relocated+4x buffer -> zero stream delta). Remaining suspect: upstream object-level visibility cull, a future hunt; quantified tiny (4.2% of one margin band on 1 of ~30 attract driving frames). Known-minor for now. |

## G. Rig-session triage — 2026-08-25 (user's minor list)

| ID | Item | Status | Effort | Auto | Notes |
|----|------|--------|--------|------|-------|
| **G1** | Launch "ding" — STILL present, all four games | ☑ | M | ⚠️ | **SOLVED 2026-08-25 (config, one line): the tuned FFBPlugin.ini shipped `BeepWhenHook=1`** - the plugin chimes MessageBeep(MB_ICONASTERISK) on hook install by design, default 0. Flipped to 0 on the rig, guarded in run_rig.apply_ffb_strength (re-forced every launch), forced in make_release.ps1's shipped ini. Verdict = silent launches on the user's next session. |
| **G2** | Launcher hangs on quick game exit (stuck LAUNCHING, alt-tab/alt-f4 dead) | ☑ | S | ✅ | **FIXED 2026-08-25**: enforce_foreground aborts as soon as the target window dies or stops answering WM_NULL. Quick-exit probe: WM_CLOSE handled in 0.7s, no post-exit foreground fighting (0/8 samples), launcher recovers. |
| **G3** | Exotica car-select stats text illegible | ☐ | M | ⚠️ | RECLASSIFIED 2026-08-25: text equally illegible via MAME's own d3d output (user captured both) → upstream zeus2 emulation bug. **Upstream checked 2026-08-26: no text-rendering fix exists post-0.286** (only #15719 road fix - backported - and open #15723 - backported); fixing this = novel zeus2 RE (texture/alpha path at small glyph sizes), a candidate for our next upstream-grade contribution. Fresh-session-sized. |
| **G4** | Off Road track-select: thin black vertical seams | ☑ | S | ⚠️ | **FIXED 2026-08-26**: 2D screens now get a tight 1-px crack-fill pass (3D keeps the full radius; the fine-dither checkerboard guard already protects translucency). Hairline bitmap-tile seams like the Off Road track select's vertical lines fill; anything wider on a 2D screen is left alone as potentially intentional. |
| **G5** | Settings UX: per-game labels unclear + screen cluttered | ☐ | M | 🙋 | **USER DESIGN LANDED 2026-08-29** (docs/settings-redesign.md): global-only settings stay on the main menu bottom row; selecting a game opens a per-game submenu (PLAY + that game's settings - sensitivity, curve, shifter, volume, free play). **IMPLEMENTED 2026-08-29**: game cards open a per-game submenu (PLAY default + sensitivity, curve, VOLUME, FREE PLAY, and for World a GAME REVISION 2.4/2.5 toggle); the SETTINGS row is global-only (CRT, crack fill, aspect, margin fill, FFB, controls). Steering wheel + gas also navigate every menu. Pending user drive-test. |
| **G6** | Settings screen invisible to screenshots | ☐ | S | ⚠️ | 2026-08-26 investigation: keyboard exonerated (settings mode ignores unknown keys - PrintScreen can't exit it), and the captured image genuinely RENDERS menu mode, so something flips `mode` around the capture. Next: a one-line mode-transition log in the shell + a repro with the user. |
| **G7** | Manual mode: H-pattern gear engagement mis-detected | ☑ | M | ⚠️ | **IMPLEMENTED 2026-08-25, pending live drive**: run_rig.apply_shifter_config writes CONF=H-Pattern (V-Unit trio) + sitdown-cabinet DIP (crusnwld DSW 0x20, crusnexo DIPS 0x400) into rig/cfg when [wheelmap] has gear1-4 bound; closed-loop verified (MAME's rewritten cfg keeps :CONF value=0 after a real launch). User to confirm: USA gears engage on ENTRY now, Exotica shows transmission select. **2026-08-29: World could NEVER offer MANUAL on rev 2.5 - the "automatic" revision deleted the feature; the World card now boots crusnwld24 (rev 2.4, widescreen patch ported 54/54) - confirm shifter select at the wheel.** "Sequential" (5) remains the B7 answer for paddles. |

| **G8** | FFB forces not released when a game closes | ☑ | S | ⚠️ | **INTERIM SHIPPED 2026-08-25**: run_rig.release_ffb() (SDL2 HapticStopAll/Close on every device, borrowed from the plugin's own SDL2.dll - its source confirms DLL_PROCESS_DETACH did exactly this) runs after every game exit in both the blocking launcher and the shell path. Real fix (patched plugin) folded into G1's follow-up if ever needed. |
| **G9** | B3 volume bytes: first data points | ☑ | M | ⚠️ | **RESOLVED 2026-08-26: no checksums anywhere.** Single-byte persistence experiments on all four games: every poked byte survived a full boot (crusnwld nvram 0x93C, offroadc 0x7BC/0x92C, crusnexo m48t35 0x27, crusnusa 0x200-mirror-set - the game even accepts a lone mirror change). Byte map + `nvram_tool poke` shipped. **2026-08-29: masters pinned from the user's menu-max diffs** - offroadc nvram 0x2FC (0-255; the 0x7BC/0x92C pair was play stats), crusnexo m48t35 0x27 (scale 0-30), crusnwld 0x9C (0-255, same byte in rev 2.4). crusnusa master still unpinned (in-game = / - keys meanwhile). The shell's per-game VOLUME / FREE PLAY rows now edit these bytes directly. Left: pin USA's master, then bake shipping defaults (B3). |

| **G10** | Perf regression: USA/World stutter (couple fps on rig) | ☑ | S | 🤖 | **FIXED 2026-08-29**: MIDV_DMA_PCLOG's std::getenv ran per DMA word (patch series 61) - USA 60%/World 35% unthrottled headless. Static-cached: 372%/416% restored (was 300-470% historically). Patch series 62. User to confirm on the rig. |

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

## Exotica force feedback (2026-09-03: found and wired; native since the evening)

Done the same night: MIDZ_IOLOG + wheel sweep located the motor byte at
crusnexo_leds_w offset 0 (a held centering spring); exposed as output
"wheel". Since the evening the emulator drives the wheel itself (mvffb,
SDL2 haptics), so the "crusnusa" name spoof and any plugin PR are gone.
Remaining: a MAME PR for the driver output (drop the "unknown purpose").

## Open after the 2026-09-03 rig session

1. **Exotica GL overlay glitches (Amazon track)**: investigated overnight
   2026-09-03 (RESULTS): three race captures bit-exact offline, live
   overlay matches MAME's own renderer frame for frame including the
   near-camera foliage close-ups (magnified texels + rectangular
   transparency holes = hardware). Not reproduced as an overlay fault.
   A latent ring-overflow bug (stale texture memory) was fixed on the
   way. Re-open only with a screenshot of a specific frame.
2. **USA draw-distance experiment**: rig look said "identical". Measure
   instead: scripted race with and without gamepatch_crusnusa, MIDV_QUADLOG
   per-frame quad counts and A/B snapshots at the same frames; if the
   counts match, the section streamer really is the wall (C2 round 3).
3. ~~**Exotica manual transmission**~~ **SOLVED 2026-09-04**: not an
   upstream gap - the TRANS SELECT screen is gated on the DS1 "Wheel
   Invert" DIP (Endprodukt's find, confirmed headless here). Launcher sets
   it and cancels the driving-side mirror; the virtual sequential shifter
   is live. Remaining: a rig drive to confirm the shifter in a race.
4. Distant road specks in USA (cosmetic; screenshot 2026-09-03).
5. World NY "black textures": the persistent dark rectangle at the right
   is the game's translucent HUD widget (checkerboard on hardware,
   smoked glass at 4x) - faithful. Margin slivers (C3) not seen in three
   NY captures. Nothing to fix unless a screenshot shows otherwise.

## Open after v0.3.6 (2026-09-04: built-in FFB shipped)

- Fanatec verdict on the native path (direction, strength 50 + smooth 50).
- Launcher: LEFT pressed right after opening can act as ENTER (input arming).
- Distant red/blue road specks in the V-Unit games (cosmetic).
- `ffb_damper` / `ffb_friction` untried on the rig; decide whether either
  earns a SETTINGS row.

## ~~Speedometer telemetry~~ SOLVED 2026-09-05

The reader's window clipped the hundreds digit: `crusnusa` x0 was 30, and the
leftmost lit column sat exactly on 30 in 2758 samples with only 112 reads ever
segmenting three cells. Speed could never exceed 99, so every three-digit
moment failed and decayed toward zero - median 13 mph on a real drive.

Fixed by sweeping x0 with the new `MIDV_HUD_X0` / `MIDV_HUD_THR` knobs:
30 -> max 88, **18 -> max 141** with 15x the three-digit reads and no extra
failures, 12 pulls in the road behind the HUD and breaks every read. Now
median 74 while moving, 6% zeros.

Two things that made this take four attempts, worth remembering:
- Speed was never written to the trace (gated on a RAM path disabled for
  every game), so support bundles could not answer "what did the reader
  see?". It is traced now, with the cell count and leftmost lit column.
- A videoram dump taken at a two-digit moment "proved" there was room, and
  sent the search in the wrong direction twice. Instrument the reader, not
  the picture.

**Still open**: `crusnwld` and `offroadc` boxes were calibrated the same way
and validated only below 100 mph (World's note literally says "0->97"). They
are very likely clipped too - sweep them the same way.
