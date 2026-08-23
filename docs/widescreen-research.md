# Widescreen techniques for fixed-4:3 3D games — research (2026-08-22)

Due-diligence survey of how the emulation/modding community adds 16:9 to
games authored for 4:3, and what applies to the V-Unit / Zeus games.

## Two distinct mechanisms (do not confuse them)

**A — game-code/data patch.** Overwrite a hardcoded constant in the game's
own compiled code/RAM so the *game's* projection math computes a wider
frustum. Emulator does nothing special.
- PCSX2 `.pnach`, GameCube/Wii Gecko/AR codes, **Sega Naomi SH4 ROM hex
  patches** (closest real precedent to us), DuckStation/PS1 community
  patches. All are word-level instruction/constant overwrites — the same
  class as our `MIDV_PATCH` DSP-RAM patcher.
- Canonical IEEE-754 pair `0x3FAAAAAB` (4/3) → `0x3FE38E39` (16/9) recurs
  across MIPS/PPC/SH4. **Does NOT apply to TMS320C31 (non-IEEE float).**
- Real lesson (Silent's GT2 PS1 patch): the constant lives in MULTIPLE
  code paths (main view, mirror, menus) — 7-line patch grew to 70.

**B — emulator-side intercept.** The emulator rewrites the projection
matrix / geometry-engine output in its own reimplemented renderer; game
code untouched. Dolphin's Widescreen Hack (post-multiplies GX proj matrix
horizontal terms), DuckStation GTE squash, **Sega Model 2/3 emulators**,
N64 HLE plugins. Our GL overlay is architecturally a mechanism-B renderer.

## Hor+ vs Vert- vs stretch

- **Hor+**: vertical FOV fixed, horizontal expands → genuinely MORE world
  visible at the sides (skybox/backdrop/terrain that existed but was
  off-screen). The FOV-constant patch is Hor+ by definition.
- **Vert-**: horizontal fixed, vertical shrinks → reads as zoom-in, no new
  content.
- **Anamorphic stretch**: no new content, just un-squish/letterbox.

## THE KEY FINDING: FOV patch does NOT avoid "revealed backdrop"

Every research thread converged: patching the real game-side FOV/projection
constant does **not** avoid the revealed-backdrop artifact, and can reveal
**equally much or more** of the same content — plus adds new risk (culling/
LOD/fog tuned for 4:3). Evidence:
- **FlexFOV-SM64** (real, proper FOV patch) had to separately re-engineer
  sky (two-pass), fog (camera-distance), lighting, billboards; particles
  still broken.
- **Michelin Rally Masters FOV fix**: documented "car interiors visible at
  wider FOV" — exactly our artifact class.
- **DuckStation GTE-squash docs**: "skybox geometry doesn't receive the
  squash... void at screen edges"; "world-space classifiers test 4:3 bounds
  the GTE never sees, scenery pops."
- **Sega Model 2/3**: needed SEPARATE controls for 2D backdrop layers
  (`Model2_SetStretch*` ×4; Supermodel `-wide-bg` distinct from
  `-wide-screen`). Model 3 docs admit "objects will be culled by games,
  which are not aware of the extended field of view."
- gametechwiki universal note: "objects outside 4:3 might suddenly appear/
  disappear... fade effects only affect the 4:3 area."

Mechanically: fixed-function/DSP pipelines compute full-frustum vertex
positions and clip-to-display LAST. Off Road's water plane is *already
computed*; our margin-unclip just stops discarding it. A DSP FOV patch
would ask for MORE width of that same backdrop content — likely worse, not
better, for this specific bug.

## Arcade/MAME precedent

- **Sega Naomi (SH4)** = closest real precedent: literal ROM hex patch,
  discovered via debugger watchpoint on FP registers during projection
  setup → brute-force candidate testing → screenshot diff (DEmul/Cheat
  Engine). Informally organized (Discord "Esppirals").
- **Model 2/3** = mechanism B in from-scratch renderers (like us).
- **Namco System 22, Midway V-Unit/Zeus**: ZERO prior art found anywhere.
  **We would be first.**

## TMS320C31 playbook (CRITICAL: non-IEEE float format)

TMS320C3x float: `[EXP 8b two's-complement unbiased][S][FRAC 23b]` (exp at
TOP, sign in the middle) — NOT IEEE-754. IEEE hex constants will silently
fail to match. Computed C3x hex words for the values to grep:

| value | TMS320C3x hex word |
|---|---|
| 4/3 (1.33333, aspect) | `0x002AAAAB` |
| 3/4 (0.75) | `0xFF400000` |
| 1.0 | `0x00000000` ⚠ collides with zero-fill |
| -1.0 | `0xFF800000` |
| 320.0 | `0x08200000` |
| cot(30°) 60° FOV | `0x005DB3D7` |
| cot(37.5°) 75° FOV | `0x0026D017` |
| cot(20°) 40° FOV | `0x012FD6AC` |
| cot(22.5°) 45° FOV | `0x011A827A` |

Caveats: prioritize non-round values (round ones drown in zeroed RAM);
work word-per-record from our dumps (no endianness); treat low 1-2 mantissa
bits as wildcard (toolchain rounding).

Search method: (1) no in-game FOV toggle exists, so no snapshot-diff; use
static + dynamic. (2) MAME's own debugger watchpoint on the DSP regs
feeding our (already-RE'd) viewport/page_control regs = the Naomi technique
via our own emulator. (3) grep dumps for the C3x candidate words. (4)
confirm a hit's LDF feeds a MULF scaling ONLY the X path (asymmetric =
aspect term; symmetric = generic zoom). (5) verify: FOV widens cleanly
L/R, HUD doesn't shift, expect some backdrop seam. (6) expect multiple
call sites. IDA has a C3x module; MAME's `tms32031.cpp` = ground-truth
semantics.

## Recommendation

**For the Off Road water artifact: do NOT use the DSP FOV patch** — it
won't avoid the artifact and adds risk. Instead, the field-standard fix
(how Model 2/3 handle it): **content-specific masking at our render layer**
— identify the water/backdrop draw call(s) via our quad introspection and
scissor/cull just that geometry within the margin regions. Second choice:
accept + document as a known cosmetic caveat (what GT2, OoT/GLideN64,
Model 3 all shipped).

**The FOV-constant patch is worth a SEPARATE, explicitly-scoped R&D effort**
— it's the "proper" Hor+ (game's own culling/AI agree with the wider view),
we have unusual advantages (word-level DSP patcher, RE'd viewport regs,
MAME tms32031 ground truth + debugger), and it's genuinely novel (first on
V-Unit). Go in knowing: zero prior art, non-IEEE hex table above, budget
for multiple sites, and it will likely still show edge backdrop — so it is
NOT "the fix" for the current bug.
