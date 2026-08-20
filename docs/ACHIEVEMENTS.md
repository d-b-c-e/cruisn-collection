# Achievements for the Cruis'n Collection — feasibility research

*Status: parked idea, researched 2026-08-20. No implementation planned.*

## Why there is no existing path

- **RetroAchievements (RA)** integrates via their `rcheevos` C library, and
  only approved emulator clients can submit (hardcore) unlocks.
- **Arcade on RA flows through FinalBurn Neo**, which has no V-Unit or
  Zeus drivers — Cruis'n titles cannot get RA sets that way.
- **Standalone MAME has never integrated rcheevos.** The structural reason:
  MAME's memory maps shift between versions, breaking RA's requirement of
  stable, hashable addresses. Additionally RA's emulator-approval policy
  means a custom fork (us) would never be blessed for hardcore; that wall
  is policy, not technology.

## Why this project is unusually well positioned to do it anyway

| RA blocker | Our situation |
|---|---|
| Memory maps drift across MAME versions | We ship a **frozen 0.286** build — addresses never move |
| No per-frame memory hook | MAME Lua reads game RAM per frame (proven: `lua/input_dump.lua`); C++ hooks also available in our patch |
| No way to render unlock toasts | The Esc-menu overlay already draws over the game; one generated font atlas (same pattern as `gen_menu_assets.py`) enables arbitrary text |
| Nowhere to persist/browse | The shell has config persistence + a Settings screen; an achievements gallery is a natural page |
| RAM addresses unknown | Shared work with **telemetry Phase B** (speed/RPM hunting) — one differential memory-search effort feeds both features; attract demo races change speed/position, so hunting works unattended |

## Design ladder

1. **Local achievements (very doable)** — JSON-defined conditions over RAM
   values ("win a race", "hit 200 MPH", "beat US 101 under X"), evaluated
   per frame by a Lua plugin (or C++ in the patch), toasted by the GL
   overlay, tracked per-game in `rig/` (e.g. `achievements.json`), browsed
   in the shell. No external dependencies, works offline, survives forever.
2. **RA-compatible authoring (cheap insurance)** — express conditions in
   rcheevos condition syntax (or embed rcheevos itself, evaluating locally
   without their server). If RA ever supports this hardware, definitions
   port; authoring tools like RATools become usable.
3. **Official RA (not worth chasing)** — requires their emulator client
   approval + community set approval; custom forks are excluded by policy.

## Implementation sketch (when/if resumed)

1. **RAM hunt** (unattended-capable): run attract, snapshot maincpu RAM per
   frame via Lua (`manager.machine.devices[":maincpu"].spaces["program"]`),
   differential search for values matching on-screen speed/position/timer.
   Attract demo races provide changing ground truth without a driver.
   Deliverable: per-game address table (also unblocks telemetry Phase B).
2. **Engine**: Lua `-autoboot_script` (or plugin) loading
   `achievements/<rom>.json`, evaluating conditions per frame, writing
   unlock events to a file/UDP that the overlay + shell consume.
3. **Toasts**: extend the overlay with a generated ASCII font atlas
   (gen_menu_assets pattern) → "ACHIEVEMENT UNLOCKED: <name>" slide-in.
4. **Shell gallery**: achievements page under Settings; read unlock state.
5. **Definitions**: start with ~10 per game; playtesting tunes thresholds.

## Effort estimate

- RAM hunt harness + first address table: one session (shared with
  telemetry Phase B).
- Engine + toasts + gallery: one to two sessions.
- Definition authoring: ongoing/fun, requires play.

## References

- rcheevos: https://github.com/RetroAchievements/rcheevos (condition
  evaluation library, MIT-ish licensing — embeddable)
- RA emulator/approval docs: https://docs.retroachievements.org/
- Prior art in this repo: `lua/input_dump.lua` (per-frame Lua machine
  access), `gen_menu_assets.py` + Esc overlay (in-game rendering),
  `MIDV_TELEM_UDP` (event transport out of the emulator).
