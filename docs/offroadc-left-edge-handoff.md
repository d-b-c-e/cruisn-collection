# Off Road Challenge — widescreen left edge: fresh-eyes handoff

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
