# SETTINGS redesign proposal (G5) — draft for discussion, 2026-08-26

The current single-screen settings list has outgrown itself (9 rows, mixed
scopes), and the per-game model ("highlight a game card, then SETTINGS
tunes that game") works but is invisible. Confirmed with the user
2026-08-25: "works, though not intuitive at all."

## Proposed structure: three submenus + an explicit scope banner

```
SETTINGS
├── DISPLAY                (global)
│     CRT EFFECT            on/off
│     CRACK FILL            on/off
│     ASPECT                4:3 / TRIMMED / 16:9 FULL   ← per-game? see Q2
│     MARGIN FILL           on/off
├── WHEEL & FFB            (global)
│     WHEEL SETUP…          (wizard)
│     FFB STRENGTH          0–100%
│     SHIFTER TYPE          H-Pattern / Sequential / Buttons   ← NEW (G7/B7)
└── GAME TUNING: <GAME>    (per-game; big banner names the game)
      STEER SENSITIVITY     5–200 (default 25)
      STEER CURVE           50–200% (100 = linear)
      VOLUME                0–max  ← NEW (G9 CMOS poke, per game)
      FREE PLAY             on/off ← NEW (G9)
```

Notes:
- The GAME TUNING page opens scoped to the highlighted game card and shows
  a **large "TUNING: CRUIS'N WORLD"** header; LEFT/RIGHT on the header row
  cycles the game without leaving the page.
- SHIFTER TYPE writes the CONF port per game cfg (today it's inferred from
  wheelmap gear bindings; a visible setting beats inference — keep the
  inference as the default value).
- VOLUME/FREE PLAY use the now-mapped CMOS bytes (nvram_tool poke); no
  service-menu spelunking for players.
- Row count per page stays ≤6 — readable at 10 feet.

## User's direction (2026-08-29) — supersedes the draft above

Concrete design from the user:
1. **Global settings live at the bottom of the main menu** (as today's
   SETTINGS row) but contain ONLY the truly-global items: CRT, crack fill,
   margin/aspect handling, FFB strength, wheel setup.
2. **Selecting a game card no longer launches directly** - it opens a
   per-game submenu: **PLAY** (default highlighted; Enter-Enter still gets
   you into the game fast) plus the game-specific settings (steer
   sensitivity, curve, shifter type, volume, free play).
This kills the invisible "highlighted card scopes the settings" coupling
entirely. Implementation notes: the per-game page IS the scope banner; the
double-Enter fast path must stay muscle-memory compatible; wheel-hat
navigation everywhere.

## Open questions for the user (remaining)
1. Should ASPECT be global (one look for the whole collection) or stay
   per-game? (Today: global.)
2. Keep the game-card→settings flow at all, or move GAME TUNING behind a
   long-press/second button on each game card?
3. Volume: expose the raw 0–N CMOS value or a 0–100% remap?

## IMPLEMENTED 2026-08-29

The user's direction above shipped: per-game submenu (PLAY + sensitivity,
curve, volume, free play, World's revision toggle), global-only SETTINGS,
wheel+gas navigation. Answers to the open questions as built: ASPECT
stayed global (Q1); the card-opens-submenu flow replaced the old scope
coupling entirely (Q2); volume shows a 0-100% remap of each game's raw
scale (Q3). Shifter type stayed inferred from the wizard bindings
(H-pattern > paddles > none) rather than a visible row.
