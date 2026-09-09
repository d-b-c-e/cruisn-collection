# Off Road Challenge — widescreen left edge: fresh-eyes handoff

> Historical research/design note. Its assumptions and proposed settings may be
> superseded. Use the [current documentation index](README.md) and
> [roadmap](../ROADMAP.md) for supported behavior and next work.

Written 2026-08-24 after a long session with many model hand-offs. The
right edge is solved and shipping; the **left edge is not**, and this
document is a clean, self-contained brief so a fresh session can solve the
left with the same quality as the right. Treat the "what we concluded"
sections as *evidence to re-examine*, not settled fact — some reads during
this session may have been skewed by context loss.

---

## The goal (one sentence)

Off Road Challenge (`offroadc`, Midway V-Unit, TMS320C31 game code + our
in-process GL renderer over MAME) should show clean 16:9 on **both** sides
during driving — the right already does, the left still shows the far
sky/horizon backdrop through gaps in the ground (blue wedges). There should
be a symmetric fix.

Screens the user provided: driving frames where the **bottom-left** margin
shows blue (sky/water) where ground should be; the **right** margin in the
same frames is clean. The asymmetry is the central clue.

---

## What DID work on the right (the proven, shipping fix)

**Mechanism: widen the game's own screen clip/cull bound via an in-memory
code patch (ROM files never touched).**

- The V-Unit games copy their TMS320C31 program from ROM into work RAM at
  machine_reset (`midvunit.cpp: memcpy(m_ram_base, memregion("maindata")
  ->base(), 0x20000*4)`), then `midv_apply_patches(m_ram_base)` overlays
  word patches from the file named by env var `MIDV_PATCH`. Format per
  line: `WORDADDR OLD NEW` in hex, OLD verified before applying (or `*`).
  Applies only for `addr < 0x20000`. Logs "N applied, M skipped" to
  `midv_gl.log` when `MIDV_GL_LOG=1`.
- offroadc's poly clip/cull reads its screen bounds from a small DATA table
  in the program image (word addresses):
  - `$11233 = 0x200 = 512`, `$11234 = 0x190 = 400` (screen dims)
  - **`$11235 = 0x1FF = 511` = x-MAX clip bound (RIGHT edge)**
  - `$11236 = 0x18F = 399` = y-MAX clip bound (bottom)
  - `$11230 = 256.0` (C3x float) = projection X center
  - No runtime writers of these (grep the disasm for `STI ...,($1235)` = 0).
- The clip/cull routine is at ~`0x2096` (and ~9 sibling call sites). Per
  edge it does: `AND3` the 4 vertices' outcodes → branch-reject if all
  share the edge, then `SUBI3 bound,vertex` + combine for the straddle
  clip. Widening the bound widens BOTH the whole-poly cull and the clip.

**The patch (shipping):** `patch/game/offroadc-widescreen.txt` contains
`11235 1FF 255` — widen the right x-max bound from 511 to 597
(= 511 + 86, our per-side 16:9 margin in the 512-wide game space).

**Why it's provably correct (not a zoom/FOV distortion):**
- CENTER-region quad count is BIT-IDENTICAL with and without the patch
  (430674 both) — projection did not move a single pixel; it only stops
  discarding margin geometry.
- Right-margin quads increase ~19% (16730 → 19904 in one measure; +12472
  in another run). An opponent vehicle + more canyon that were culled
  off-screen now appear. Visual proof was captured (see git history around
  commit 9a22dec "A2 PROVEN").
- 120s attract stable; user drove it live and approved ("looked great").

**Wiring:** `harness/run_rig.py` auto-applies
`patch/game/<rom>-widescreen.txt` via `MIDV_PATCH` whenever the aspect is
full 16:9 (`margin` None or ≥80) and the file exists; 4:3 / TRIMMED skip
it; an explicit `MIDV_PATCH` in the environment wins. So the right fix is
live from the launcher at 16:9 FULL.

---

## The left edge — what we know, and the open question

### The code is genuinely asymmetric (verified)
In the same clip routine (`0x2096`):
- RIGHT (max) edge: `SUBI3 R1,vertex` where `R1 = $11235 = 511`, a table
  constant → widened by one word.
- LEFT (min) edge: `AND3 *AR4,*AR3,R0` / `AND *AR5` / `AND *AR6` →
  `BLTD` (branch if negative). This tests the **sign bit** of the vertex X
  directly — "off the left" means "X went negative." There is **no
  constant** for the left; the bound is implicitly zero (the sign).

So a one-word table patch cannot widen the left the way it did the right.
A left bound change would mean editing instructions to bias X before the
sign test (e.g. test `X + 86 < 0` instead of `X < 0`), which is invasive.

### But the left may not be a culling problem at all (RE-EXAMINE THIS)
Measured: quads reaching past x<0 are **identical** with and without the
right patch (26758 vs 26758). Interpretation offered during the session:
the game already submits all its left-side geometry (straddling quads are
kept; only quads with all-4-verts off-left are rejected, and there are ~0
of those). If that holds, widening a left cull recovers nothing — the blue
is the far backdrop showing through genuine gaps in the near terrain, not
missing culled geometry.

**Caveat for fresh eyes:** the "0 culled on the left" measurement counted
quads with `max_x < 0`. That may be the wrong test — the interesting case
could be quads that STRADDLE and get their left portion CLIPPED (cut at
x=0) rather than rejected. If the game clips straddling terrain at x=0, the
terrain would stop at the 4:3 edge and the backdrop (drawn behind, clipped
differently or full-width) would show in the margin. That is exactly the
observed artifact and would be fixable game-side by widening the left CLIP
(not the reject). Worth confirming whether offroadc does per-poly
clip-to-bound or relies on a 512-wide framebuffer/scissor. See the clip
helper around `0x2309`/`0x20B0`+ and the emit path.

### The user's strong intuition (take seriously)
"Whatever worked on the right should be symmetrical on the left." The right
fix widened a clip bound and real geometry appeared. If the left terrain is
being clipped at x=0 (rather than already fully present), the symmetric fix
is to widen the left clip too — the challenge is only that the left bound
is encoded as a sign test, so it needs an instruction-level change or a
different constant to be found.

### The renderer-side alternative (tried, reverted — for reference)
There is a renderer "backdrop cover": the scene shader tags the sky/horizon
backdrop band (per-game texbase low byte; offroadc = 0x7f, meta bit 1) and
can discard/cover it inside the margins, then a margin-extend fills the
hole from the 4:3 boundary column. This DOES remove the blue (28% → 0% on
the artifact frame) BUT:
- It was gated to the same switch as the smear-prone margin clamp-extend,
  which the user runs OFF (it streaks sky/clouds and 2D screens).
- An attempt to split them shipped a regression: cover-without-fill left
  BLACK holes; that was reverted (commits ce34f8e / 381216fd reverted).
- A cleaner renderer approach was sketched (tag covered-backdrop as
  mask==2 and fill only those pixels from nearest real terrain, always-on,
  independent of the general extend) but NOT finished.

The user's preference is a **game-code (symmetric) fix** like the right,
not a renderer cover — pursue that first.

---

## Reproducible tooling (all verified working this session)

- **Disassemble a game's program** (needed to find its clip code/bounds):
  run vunit.exe with `-debug -debugscript <file>`; the script contains
  `dasm "<abspath.asm>",0,0x20000,1,":maincpu"` then `go`. The program is
  already in RAM at reset (memcpy above), so dasm at reset works. Output is
  ~3.4MB. offroadc's is regenerable to `results/offroadc-prog.asm`
  (gitignored). USA/World disasms also captured this session (same method).
- **Capture quads + a frame** for offline rendering: `harness/run_capture.py
  <vunit.exe> <frame> offroadc` (set `MIDV_PATCH` in env to capture patched).
  Produces `results/capture-offroadc-<frame>/` with quads.bin + videoram/
  texture/palette dumps.
- **Render wide, offline** (the shader source of truth):
  `python gpu/renderer.py <capdir> --wide --scale 2` (add `--crackfill` to
  enable the backdrop cover + margin extend). Writes gpu-wide[-fill]-s2.png.
- **Quad-stream measurement**: parse `quads.bin` (38-byte records: 4B
  frame, 2B page, then 16×u16 dma_data; verts x at u16 indices 2,4,6,8 as
  int16). Count quads reaching x<0 (left margin) / x>512 (right margin) /
  center. This is how "bit-identical center + right gained" was shown.
- **Artifact metric that DOESN'T get fooled**: the naive "fraction of lit
  pixels" counts blue-through-ground as "covered" (this misled the session
  into claiming the left was 100%). Instead measure sky-blue pixels in the
  region where ground belongs: `b > r + 25 and b > 120` in the bottom half
  of the left margin. On the artifact frame this read 28%.
- **Exact-mode invariant** (must never break): `python gpu/renderer.py
  results/capture-8000` and `results/capture` must both say
  `100.0000% bit-exact`. The margin/cover/fill paths are gated off in exact
  mode, so they don't affect it — but always re-check after shader edits.
  After any `gpu/renderer.py` shader change: `python harness/gen_shaders.py`
  then rebuild (see CLAUDE.md build line).
- **Live check caveat**: headless `MIDV_GL_SNAP` writes 1x1 BMPs (no real
  backbuffer), so live visual verification needs the user at the rig. The
  offline renderer uses the same GLSL and is the trustworthy proxy — BUT it
  keeps stale canvas content between frames where the live overlay clears
  per-frame, so it can mask/telegraph fill behavior differently. Confirm
  final look live.

---

## Suggested first moves for the fresh session

1. Re-open `results/offroadc-prog.asm` (regenerate if absent) and read the
   FULL clip routine from `0x2096` through the emit/clip helper it calls.
   Decide definitively: does offroadc CLIP straddling polys to [0,511]
   (per-poly Sutherland-Hodgman), or only REJECT fully-off polys and rely
   on a 512-wide framebuffer? Find where x=0 (left) enters the clip math.
2. If a left clip-to-bound exists: widen it symmetrically to -86 (mirror of
   the right's 511→597). Verify with the quad-stream measurement (left
   margin gains real terrain quads) and the not-fooled artifact metric
   (bottom-left sky-blue → ~0%), then a live drive.
3. If the left is genuinely not clipped (geometry already present): the blue
   is backdrop-through-terrain, and the fix is renderer-side. Finish the
   mask==2 approach (cover backdrop in margins, fill ONLY those pixels from
   nearest real terrain, always-on and independent of the smear-prone
   general extend). Keep exact mode at 100.0000%.
4. Whatever the fix, ship it behind the existing 16:9 FULL path and confirm
   live that BOTH margins are clean during driving with no smear and no
   black holes.

## Ground truth to preserve
- Right fix works and is live — do not regress `patch/game/
  offroadc-widescreen.txt` or the run_rig auto-apply.
- Exotica (Zeus) and crusnusa/crusnwld already present ~full 16:9 natively;
  offroadc is the only game needing the game-code treatment.
- Full session narrative is in `results/RESULTS.md`; widescreen research +
  the wanszai-topology explanation is in `docs/widescreen-research.md`.

---

# RESOLVED — 2026-08-24 (late session, fresh eyes)

Both edges now ship from `patch/game/offroadc-widescreen.txt` (auto-applied
at 16:9 FULL). Proof: `results/proof/offroadc-left-edge-FIXED.png` (top =
right-only build, bottom = both edges; attract frame 3398, deterministic).

## Why the right worked and the left didn't (the actual asymmetry)

Every one of the nine poly-emit loops does the same four **trivial-reject**
tests before DMA-ing the raw screen coordinates to the hardware (there is
no per-poly clip to the screen at all — the rasterizer clips):

| edge | test | bound |
|---|---|---|
| left  | `AND3 *AR4,*AR3,R0; AND *AR5,R0; AND *AR6,R0; BLTD exit` — sign bit survives the AND ⇔ **all four x < 0** | implicit 0 (the sign bit) |
| right | `SUBI3 R1,*ARn,Rk` ×4, AND, `BLTD exit` ⇔ all four `R1 − x < 0` ⇔ all four x > R1 | `R1 = ($1235)` = 511 → patched 597 |
| top / bottom | same two shapes on y | sign / `($1236)` = 399 |

The right test has a **data constant**, so one word widened it. The left
test has **no constant** — it is a sign test — so there was nothing to
patch. Widening the right kept quads whose bbox lies in `(511, 597]`;
nothing equivalent existed for `[-86, 0)`, and every ground/wall quad
whose right edge fell short of x = 0 was still discarded. The backdrop
(one huge quad, always straddling) survives, so it showed through.

## The flaw in the previous session's "the left isn't culled" conclusion

It counted quads with `max_x < 0` in the DMA stream and found ~0, reading
that as "nothing is lost on the left". But quads rejected by the game never
reach the stream — a working all-off-left reject *produces* that zero. The
measurement was a tautology, not evidence. The right fix measured the same
way beforehand would also have shown "0 quads with min_x > 511".

Both hypotheses in the handoff were therefore wrong in a useful way: the
game does not per-poly clip at x = 0 (the "clip" hypothesis), and the
geometry was not already present (the "gaps" hypothesis). It was
trivially rejected, exactly as on the right.

## The fix: mirror the right edge — reject only when all four x < −86

Replacing the nine `BLTD` words with `NOP` (reject never) was tried first
as a diagnostic: left-margin blue on the artifact frame 5.5 % → 0.0 %,
centre + right streams unchanged. But over the 3,397-frame run it added
70,628 records, of which **34,569 were entirely off-canvas (x < −86)** and
**42 had wrapped through the 16-bit DMA port** (a regular strip at
x ≈ 10,051…32,122 = game-space −55,000…−33,000 & 0xFFFF). Off-canvas polys
are waste; wrapped ones are on-screen garbage waiting to happen. So the
shipping fix is the exact mirror of the right edge.

There is no room at the sites for four biased adds, so each site's
`BLTD <exit>` becomes **`CALLLT $2224`** (PC-relative conditional call,
op `0x7207xxxx`; the site's three delay-slot `SUBI3`s simply run after the
return instead) into a shared 12-word routine placed in unreachable
alignment padding (28 `NOP`s after `BU $2240`, no branch or data
references):

```
2224  LDI   $0056,R3        ; 86
2225  LDI   $8000,R5        ; -32768
2226  LSH   $10,R5          ; R5 = 0x80000000 (INT_MIN)
2227  ADDI3 R3,*AR3,R4      ; v0.x + 86
2228  ADDI3 R3,*AR4,R6      ; v1.x + 86
2229  AND   R6,R4
222A  ADDI3 R3,*AR5,R6
222B  AND   R6,R4
222C  ADDI3 R3,*AR6,R6
222D  AND   R6,R4           ; N set  <=>  all four x < -86
222E  LDILT R5,R1           ; reject: x-max bound := INT_MIN
222F  RETSU
```

The trick that makes one routine serve nine sites with different exits and
return points: it never branches to the exit itself. On reject it loads
**R1** — the x-max bound the site is about to test — with `INT_MIN`, so the
site's own right-edge test (`R1 − x` negative for every x ≥ INT_MIN+1)
discards the poly through its existing `BLTD exit`. Otherwise R1 keeps
597 and the site continues untouched. R3–R6 are dead at the call (the
right test rewrites them on return); R1 is reloaded from `($1235)` at the
top of every iteration. Core semantics checked in MAME's C3x: `LT` = N
flag; `LSH` count sign-extended from 7 bits (`$10` = left 16);
`callc_imm` pushes `pc+1` and adds the signed 16-bit displacement.

Sites (all `BLTD` → `CALLLT $2224`): `203D 209B 20F6 245F 24C9 2606 26C0
2871 294F` (the tenth `($1235)` load at `2008` is a jump-in preamble that
lands on `20F6`). `294F` is inside the big-poly subdivider (`291E`), so
sub-pieces of near ground quads get the same treatment — those are exactly
the bottom-left wedges.

## Verification (attract oracle, frame 3398, `run_capture.py`)

| | records (frames < 3397) | removed vs baseline | added |
|---|---|---|---|
| right-only (shipping before) | 567,185 | — | — |
| + left reject NOP'd | 637,813 | 0 | 70,628 (36,003 in `[-86,0)`, 34,569 off-canvas, 42 wrapped, 14 at x=0) |
| **+ left mirror (shipping now)** | 603,196 | **0** | **36,011** (36,003 in `[-86,0)`, 8 with a vertex at x = 0 the game over-rejected) |

- Mirror additions are a strict subset of the NOP stream (0 outside it).
- Frame-3398 wide render: bottom-half blue left 5.5 % → **0.0 %**, right
  0.0 % → 0.0 %, centre identical; mirror render pixel-identical to the
  NOP render (100.0000 %).
- Exact mode still 100.0000 % on `capture` and `capture-8000` (no
  renderer change was needed — the renderer's margin/cover/extend paths
  stay OFF; the game now draws its own margins on both sides).
- Loader: "22 applied, 0 skipped"; run to frame 12000 stable (see RESULTS).

## What's left

- **Live drive** at the rig (attract can't exercise the player's car,
  heavy subdivision under the camera, or the stack at race load). The
  patch path is identical to the right-edge one the user already approved.
- Top/bottom edges use the same two shapes if a vertical widen is ever
  wanted (not needed for 16:9).
- crusnusa / crusnwld already cover ~99 % natively; if their last percent
  is ever wanted, expect the same sign-test shape on their min edges.
