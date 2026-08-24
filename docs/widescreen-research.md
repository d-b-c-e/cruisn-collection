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

---

## FOV R&D progress (overnight session 7, offroadc) — constant map found

Applied the C3x-float method to Off Road Challenge's program (disassembled
via MAME debugger `dasm` -> results/offroadc-prog.asm, 131072 words):

**Data constant table located at ~0x11180-0x11260** (program-RAM word
addrs), decoded with the corrected C3x float format:
- `0x11185..0x11192` = reciprocal table 1/2, 1/3, 1/4 ... 1/15.
- `0x11230=256.0  0x11231=512.0  0x11232=400.0` = screen dims (V-Unit is
  512x400; 256 = horizontal center/half-width).
- `0x11233..0x11236` decode as INTEGERS 512/400/511/399 = clip bounds.
- `0x1121F=960  0x11220=640  0x1121D=184  0x1121E=1472` = viewport-ish.
- `256.0` (0x08000000) recurs in code at 0x0A205, 0x0A2C7, 0x0A300,
  0x0A39C, 0x0A417, 0x0A49C (LDF sites) — the projection X-scale/center
  candidates.

**Perspective divide (1/z) found at 0x010AF8** — a Newton-Raphson
reciprocal `y' = y*(2 - x*y)` (MPYF3/SUBRF 2.0/MPYF/RND, twice). This is
the projection core; the horizontal FOV scale MULF is in its callers
(screen_x = x*(1/z)*SCALE_X + 256).

**Next focused step** (a disasm-reading session): trace the callers of
0x010AF8, find the MULF applying SCALE_X to the X path only (not Y),
confirm SCALE_X (likely one of the 256.0 LDF sites), test-patch it via
MIDV_PATCH and observe FOV widen. Per the research this yields true Hor+
(game culling agrees) but will NOT fix the water artifact and may reveal
more backdrop — it is a "proper widescreen" R&D goal, not the artifact fix.
Encoder + search: reproducible via the c3x_encode() snippet in this arc's
session log.

## 2026-08-24 addendum: wanszai's method, finally explained (from MAME source)

Question: how do wanszai's ports (Ridge Racer Collection/System 22, Sega
Rally/Model 2, Virtua Racing + Virtua Fighter/Model 1, Ace Driver/System
22) achieve clean true 16:9 when V-Unit can't?

His repos are ALL binary-only (no source, no technical docs; checked every
repo 2026-08-24). But MAME's own source answers the mechanism:

**On System 22, the geometry pipeline IS emulator code.** namcos22.cpp:
"In MAME, this main task is done in simulate_slavedsp instead" - the slave
DSP (transform/projection/clip) is HIGH-LEVEL SIMULATED in C++.
namcos22_v.cpp holds m_camera_zoom, m_camera_vx/vy and the view window
vu/vd/vl/vr as plain driver variables, applies projection as
`p->x = v[i].x * m_camera_zoom`, and performs the culling ("fully behind
camera") itself. The game's 68020 submits an OBJECT LIST + camera block;
everything after that - projection, view volume, visibility - runs in
code the porter controls. Widescreen = widen the C++ camera. No game
patch, no revealed-cull artifacts, because the game never culls to the
screen in the first place: that was always the (now emulator-side) DSP's
job. Model 1/2 are the same story (TGP/geometry HLE) - wanszai's entire
catalog sits on platforms with an open-source camera.

**V-Unit is the opposite topology.** The TMS32031 running GAME CODE does
transform+clip+cull internally and hands the emulator only final
screen-space quads. The camera is compiled, proprietary, per-game code.
There is no emulator-side knob; the choice is (a) present what the game
submits (our approach - the games overdraw generously, so fill-off 16:9
is ~95% covered natively) or (b) patch the game's DSP code (the A2-class
FOV/clip-constant R&D).

**Zeus2 validates the theory perfectly**: Exotica's projection runs on
the Zeus chip = emulator side, and we achieved TRUE clean 16:9 there with
an emulator-side fix - exactly the System 22 situation. V-Unit is simply
the unlucky architecture where the fence runs on the other side of the
camera.

Bottom line: nobody has "solved" game-side culling; the famous clean
ports never had to face it. For V-Unit, Ridge-Racer-grade 100% width
needs the game-code patch path (we own the toolkit: MIDV_PATCH, full
disassembly, constant maps) - a scoped future R&D, not a missed trick.

## 2026-08-24 BREAKTHROUGH: game-code widescreen WORKS on V-Unit (offroadc)

The A2 goal is no longer theoretical. Following the wanszai topology
finding (V-Unit's clip/cull runs in game DSP code, not the emulator), we
located and widened that code's screen bound - and it works.

**What was found** (offroadc, results/offroadc-prog.asm):
- The TMS32031 poly clip/cull reads its screen bounds from a small data
  table: $11233=512, $11234=400 (dims), **$11235=511 (x-max)**,
  $11236=399 (y-max), $11230=256.0 (projection center). No runtime writers.
- The clip/cull lives at 10 sites (0x2008..0x294B), each: load xmax/ymax,
  AND3 the 4 vertex outcodes (reject if all past an edge = CULL), then
  SUBI3 bound-coord for the straddle CLIP. Widening the bound widens BOTH
  the cull and the clip on that edge.

**The experiment** (MIDV_PATCH $11235: 511 -> 597, memory-only, ROMs
untouched):
- CENTER region quads BIT-IDENTICAL (430674 -> 430674) - projection did
  not move a pixel. This is the decisive self-check: it is NOT a zoom/FOV
  change, it is purely un-culling margin geometry.
- Right-margin quads +19% (16730 -> 19904); 120s attract stable.
- VISUAL (results/proof/offroadc-gamecode-widescreen.png): the right
  canyon wall extends past the old x=511 cut AND an opponent truck that
  was culled off-screen now appears. Exactly the Ridge-Racer-style result.

This is - as far as the prior research found - the FIRST game-code
widescreen on Midway V-Unit hardware. Mechanism confirmed; it is the same
class of fix wanszai gets for free on HLE'd platforms, done here by
patching the game's own compiled bound.

**Remaining for full symmetric parity:**
- LEFT/TOP edges are MIN-edge rejects tested by the SIGN of the vertex
  coord (0x2098 AND3 + BLTD), not a table constant - so left needs a small
  CODE patch (bias x by +86 before the sign test), not a one-word change.
  (Baseline already submits 47k quads left of x=0, so the left side is
  much less culled than the right; right-only is already a big visible win.)
- Per-game: crusnusa / crusnwld need their own disasm + bound-table hunt
  (same method; the constants will be at different addresses).
- Product wiring: gate behind the WIDESCREEN setting; verify live at the
  wheel (game AI/LOD tied to visibility could misbehave - watch for it).
- Ultrawide bonus: once the bound is a patched parameter, 21:9 (3440x1440)
  is just a larger bound + canvas - potentially BEYOND Ridge Racer's 16:9.
