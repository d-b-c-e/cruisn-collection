# POC Results — 2026-08-18 (overnight session)

Both load-bearing claims of the feasibility study are now **proven**, not argued.

## 1. The oracle is real

`run_oracle.py`: two cleanroom runs of Cruis'n USA attract mode (deployed
mame286 binary, seeded calibrated NVRAM, fresh cfg, unthrottled, headless)
produce **bit-identical pixels at all 8 sampled frames** — from CPU-board test
through the animated title screen. ~11 s per run.

## 2. The interception point is complete — bit-exact re-render

The `vunit.exe` subtarget build (113 MB vs 666 MB full MAME; **one incremental
build cycle** on the 20-core box) with a ~60-line env-gated patch captured:

- **1,249,062 quads** over frames 738–2399 (38 bytes each, 47.5 MB)
- videoram + textureram + paletteram dumps at frame 2398

`rasterize.py` — a Python port of MAME's exact pipeline (float32 everywhere,
`round_coordinate`'s midpoint-toward-−∞, the `+0.001f` inclusive nudges, the
forward/backward edge walk, C float→int32 truncation with the cvttss2si
INT_MIN case) — replayed the final 8 frames:

```
coverage : 204800/204800 = 100.00%   (whole page redrawn every cycle)
raw u16  : 204800/204800 = 100.00%   BIT-EXACT vs MAME's framebuffer
```

`rerendered.png` is the Golden Gate title screen — bridge, logo shading,
opponent cars, INSERT COINS text — reproduced outside MAME **to the bit**.

## Stream statistics (renderer sizing data)

| metric | value |
|---|---|
| quads/frame | mean 769, median 241, **max 2,654** |
| mode: tex | 84.1% |
| mode: textrans | 10.5% |
| mode: flat | 3.4% |
| mode: textransmask | 2.0% |
| dithered quads | 0.4% |
| texture RAM | 8 MB total, 256-px row stride, 8-bit texels |
| palette | 32,768 pens, xRRRRRGGGGGBBBBB |

Max 2,654 quads/frame is nothing for any GPU of the last 25 years. Four
shader variants cover the entire hardware.

## Traps documented for the real implementation

- **Page semantics**: dest page = `page_control & 4`, visible = `& 1`, and the
  flip lands mid-frame — a dump/present can catch the pointer one step stale.
  The freshly completed frame is the dest page of the last full frame.
- **Frame numbering off-by-one**: a snapshot at Lua frame N runs screen_update
  with `frame_number() == N-1`.
- **First boot** parks on CALIBRATE CONTROLS; seed NVRAM (fixture included).
- **Degenerate quads exist in the real stream** (zero-width extents with huge
  dpdx). C's float→int32 conversion semantics (INT_MIN) must be honored.
- **The game redraws the entire back page every cycle** — no incremental
  damage tracking needed in a replacement renderer.
- 3D begins at frame ~738; everything before is direct-CPU videoram writes
  (boot screens), which a quad-only renderer correctly ignores.

## Feasibility study updates

- "Does texture RAM get rewritten often enough for cache invalidation to be a
  perf issue?" — textures were fully stable across the captured window; a
  write-invalidated cache will be nearly idle in attract. (Gameplay unmeasured.)
- "Can per-quad perspective be recovered from u/v gradients?" — the capture
  contains everything needed to prototype this offline against real data,
  without touching MAME again.

## Environment notes

- MSYS2 reinstalled to **E:\msys64** (C:\msys64 died with the C: wipe).
  GCC 16.2.0 builds MAME 0.286 fine with `NOWERROR=1`.
- MAME's makefile needs `OS=Windows_NT` exported *inside* the MSYS2 login
  shell — the profile clears the inherited value.
- Build: `make SUBTARGET=vunit SOURCES=src/mame/midway/midvunit.cpp
  REGENIE=1 NOWERROR=1 TOOLS=0 -j18`

---

# Widescreen spike — 2026-08-18 (follow-up session)

**The gating unknown is RESOLVED: true Hor+ 16:9 needs NO game-code changes.**

The decisive fact was already in the captured stream: **the TMS32031 does not
clip projected geometry to the viewport.** Vertex x runs −8427..12935 against
a 0..511 screen with no pile-up at boundary values (no DSP clamping), ~7% of
vertices land outside 4:3 horizontally, and **65,698 quads lie entirely
outside the 4:3 window** — submitted by the game, discarded by MAME's
rasterizer at its cliprect. The 4:3 picture is a raster-time crop, not a
game-side frustum.

`widescreen.py` re-rendered two captured scenes into a 684×400 window
(16:9 at the original pixel aspect, 86 px margins each side):

| scene | margin pixels rendered | centre vs MAME dump |
|---|---|---|
| title screen (frame 2398) | **100.00%** both sides | 99.99% (DDA drift, see below) |
| canyon demo race (frame 7998) | **100.00%** both sides | **100.00%** |

Proof images: `results/proof/widescreen-title.png`, `widescreen-canyon.png`.
Canyon walls, road edges and lane markings continue seamlessly into the
margins in both scenes.

Additional findings:

- **Scene/page structure**: consecutive frames sharing a `page_control` form
  one scene (~27-quad setup chunk + ~1,200-quad body in attract; ~105 + ~1,230
  in gameplay). The last complete scene is the second-to-last run — a
  quad-count threshold is not a robust way to find it.
- **DDA drift**: quads MAME clips at x=0/511 get u/v starts adjusted
  analytically at the clip edge; the wide render reaches the same pixels by
  int32 DDA stepping from further left. Same math, different rounding —
  ~0.01% of centre pixels. Irrelevant to a real GPU renderer (which
  interpolates analytically per-pixel anyway); visible only against the
  software oracle.
- Capture backstop must scale with the dump frame (`-str` at 120 s ends
  before frame ~6,900).

**Honest caveats**: two scenes tested; objects the game distance-culls could
still pop in at margins during long play — sweep more frames during real
development. HUD/text stays 4:3-centred (authentic). Vertical overhang exists
too (y −4956..1481), so 21:9 is likely equally free.

---

# GPU renderer prototype — 2026-08-18 (follow-up session)

**The pipeline the real port needs, running on the real GPU (RTX 5080,
OpenGL 4.3 via moderngl), verified bit-for-bit against MAME.**

## Architecture (`gpu/renderer.py`)

- **One scene → one draw call.** Each quad = 2 triangles covering its
  bounding box; all quad data rides as flat varyings. GL's primitive-order
  guarantee provides the painter's algorithm within the draw call.
- **The fragment shader is poly.h, analytically**: the forward/backward edge
  walk, per-scanline extents with `round_coordinate`'s midpoint rule, param
  interpolation with left-clip adjustment, the four fill modes, the dither
  mask, and C's float→int32 truncation. GPU rasterization rules never leak
  in: fragments outside MAME's coverage are discarded.
- **Index-space rendering**: R16UI framebuffer holding palette indices —
  the hardware's own framebuffer format — with a palette pass to RGB after.
  Readback of the index buffer enables word-for-word verification.
- **Exact mode** (`--scale 1`): u/v follow MAME's integer-DDA semantics.
  **Quality mode** (`--scale N --wide`): continuous coverage and float u/v
  at sub-pixel precision — the shipping configuration.

## Verification

| scene | GPU vs MAME videoram | speed (native) |
|---|---|---|
| title (frame 2398) | **100.0000% — 0 of 204,800 differ** | 0.135 ms/scene |
| canyon (frame 7998) | **100.0000% — 0 of 204,800 differ** | 0.189 ms/scene |

Quality mode at 4× + 16:9 (2736×1600): **3.5 ms/scene ≈ 289 fps** — 5×
headroom over the 57 Hz target, in a Python-orchestrated prototype.

Proof images: `results/proof/gpu-canyon-4x-wide.png`, `gpu-title-4x-wide.png`.

## Bugs found on the way (all now encoded in the shader)

1. **Missing scanline-range check** (97.24% → 99.9985%): poly.h renders rows
   `[round(miny), round(maxy))`; bounding-box fragments outside that range
   extrapolated plausible x-extents and let later quads steal shared-edge
   rows from earlier neighbours. 5,646 of 5,647 bad pixels were ownership
   flips from this.
2. **Page history** (99.9985% → 100%): the game leaves sub-pixel cracks
   between adjacent quads (3 px on the canyon scene) where the hardware
   shows the page's previous frame. A real renderer reproduces this for
   free by never clearing pages; isolated-scene replays must prepend the
   prior same-page scene.
3. `shared` is a GLSL reserved word.
4. GLSL float division is only spec'd to 2.5 ULP; NVIDIA's is IEEE-correct
   in practice, and an fp64-reciprocal "fix" made nothing better (double
   rounding). Verified irrelevant here; worth re-checking on other vendors.

## What this retires

The renderer-replacement concept is now demonstrated end to end: capture →
GPU pipeline → bit-exact against the oracle → 4×/16:9 output with 5×
performance headroom. Remaining work is *integration*, not proof: feeding
quads from the live emulator instead of a capture file, presenting the GPU
image instead of MAME's software frame, texture/palette upload on write,
and input/FFB — engineering with no open research questions.

---

# Phase 1 step 1 — LIVE out-of-process rendering (2026-08-18)

**The GPU renderer now runs the game live.** MAME (vunit.exe, `MIDV_LIVE=1`)
streams into a 128 MB shared-memory ring; `gpu/live_viewer.py` renders and
presents in its own window in real time.

- Stream contents, in strict emulation order: quads, page flips, coalesced
  CPU videoram spans, texture/palette snapshots on dirty.
- **Sustained 136 fps at 3× 16:9 (2052×1200), zero ring drops, over full
  attract cycles** — presentation outruns the 57 Hz emulator more than 2:1.
- Both content regimes handled: 3D scenes present full 16:9 (margins are
  real geometry); **2D quad screens (high scores, logos) auto-crop to 4:3**
  via a quad-count heuristic (<300 quads/scene), since their 16:9 margins
  hold texture garbage the game never meant to show. CPU-drawn screens
  (boot/test) arrive via the vram-span path and letterbox natively.
- Perf work that mattered: `build_vertices_fast` (vectorized, bit-identical
  to the scalar builder, ~2 ms vs ~65 ms per scene — the difference between
  12 fps and 136 fps) and skip-to-latest scene scheduling under backlog
  (lossless: every scene fully repaints its page).
- Traps: moderngl's `clear()` respects the current viewport (reset before
  clearing); pygame has no Python 3.14 wheels yet (glfw used instead).

Proof: `results/proof/live-park-16x9.png`, `live-hiscore-letterboxed.png`.

**Phase 1 step 2 (next): in-process GL inside the vunit build** — one
window, no IPC. The out-of-process viewer stays as the reference/fallback.

---

# Phase 1 step 2 — IN-PROCESS GL renderer (2026-08-18)

**One process, one window.** `MIDV_GL=1 vunit.exe` spawns a render thread that
consumes the ring in-process and presents through a disabled, no-activate
overlay child over MAME's own window — input/audio/dinput8-proxying stay
stock MAME, which is exactly what the FFB Arcade Plugin needs. Shaders are
GENERATED from the verified Python reference (`midvunit_gl_shaders.h`).
Verified via backbuffer BMP self-capture: boot (CPU screens), 2D quad
screens, and 3D attract all render through the whole cycle.

Bugs this stage surfaced (all fixed, all documented in the patch):
- **WS_CLIPCHILDREN** missing on MAME's window → MAME's present alternated
  with the overlay (the "every other frame is a different resolution" report
  from the rig — that live observation was the diagnosis). `-video gdi`
  underneath makes the clip airtight.
- **Boot was black**: palette/texture sync only fired from the quad path,
  and boot screens draw before any quad exists → sync moved to screen_update.
- **Presentation flapping**: real 3D scenes can be as small as ~260 quads;
  the 2D-crop threshold at 300 made aspect mode flip per scene. Now 120.
- ++presents in a condition plus an else-increment = the snapshot cadence
  check only ever saw odd values. Rookie hour.

`run_rig.py` now launches the single-process configuration (external viewer
remains available via MIDV_LIVE=1). Remaining for the rig: FFB Arcade Plugin
drop-in next to vunit.exe, wheel/audio verification, 2D-crop threshold
sanity-check across a full attract rotation.

---

# OPEN ISSUE at session end (2026-08-18): residual flashing

record_diag caught it objectively during a run_rig boot: intermittent
X.X.X.X frame-diff bursts (~frames 283+, 305+ of an 8s 60fps desktop
capture). The alternating frames LOOK identical at 960px scale - the change
is subtle/localized. Saved pairs in results/flash-evidence/.

Next session, first move: numpy-diff flash_283 vs flash_284 and print the
bounding box of changed pixels - that localizes whether it's MAME's window
region (present-fight surviving gdi+CLIPCHILDREN), the overlay's own
letterbox bars, taskbar/toast noise, or cursor blink. The user reports one
earlier run looked flash-free (window config differed: 1368x800 + scale 3 +
sound none measured clean, mean diff 0.06).

Also fixed at session end: run_rig now passes -keepaspect 0 - without it
MAME's -maximize keeps the GAME's 4:3 aspect, so the window itself stays
4:3 and the 16:9 overlay letterboxes inside it (user report). UNVERIFIED
at the rig since.

Rig checklist standing: FFB Arcade Plugin drop-in beside vunit.exe;
JOYCODE_1_BUTTON33+ tokens from EmuEzRacing get dropped by the token parser
(coin/start on high buttons may not bind - keyboard works meanwhile).

---

# RESOLVED at the rig (2026-08-18, late): the flashing/artifact family

User-confirmed clean after four root-caused fixes, each diagnosed from
live rig observation:
1. **Alternating renders** -> the overlay is now an owned top-level popup
   (MAME's gdi caches its window DC, so child-clipping can never work).
2. **Stale margins** (scenery strips beside 4:3 screens, borders at crop
   edges) -> per-scene scissor-clear of the margin strips; the 512-wide
   hardware region stays persistent.
3. **2D screens presenting wide** -> axis-aligned-rectangle dominance
   classifier (>=70%), replacing fragile quad-count thresholds.
4. **Thin bright border** -> 2px overscan inset, CRT-style.

Phase 1 fully verified at the rig. Next session: FFB Arcade Plugin
drop-in beside vunit.exe, JOYCODE button-33+ token drops, sound-on play.

---

# STAGED for wheel test (2026-08-18 evening)

FFB Arcade Plugin is dropped in beside vunit.exe (dinput8.dll +
FFBPlugin.ini with the racing build's Cruis'n tuning + SDL2.dll) and
run_rig.py sets `output windows`. To test at the wheel:

    cd E:\Source\cruisn-poc && python harness/run_rig.py

- Coin = 5, Start = 1 (keyboard; wheel high-button tokens still dropped)
- Expect steering + road-feel/bump FFB once driving
- Known plugin quirk: ~50% first-launch hang during device enumeration -
  kill and relaunch, second try lands
- NEVER hard-kill mid-game with FFB active (stranded-torque trap);
  Esc out normally, Stop FFB Stream Deck key clears a stuck wheel
- If wheel steers but stays mute: flip `output windows` -> `output network`
  in run_rig.py's ini writer (one word) - first thing to try

---

# Stream Deck button chain: three launch bugs fixed + verified (2026-08-18, night)

User's first button-press test (Elgato "Games" profile, key stored as [7,2],
System-Open -> Launchbox-Racing\scripts\Launch-Cruisn.bat) surfaced three
issues. All root-caused; the fix lives entirely in run_rig.py + the bat.

**0. FFB staging gap found first**: the docs claimed run_rig.py set
`output windows` but the ini writer never emitted it - the FFB Arcade Plugin
reads MAME's Windows outputs, so the wheel would have steered silently. One
line added; user then confirmed FFB alive at the wheel.

**1. "Can't fullscreen"** - MAME ran `-window -maximize`, and the overlay
tracks MAME's client rect, so the game lived inside a titled maximized
window. run_rig.py now strips the frame post-boot (GWL_STYLE) and spans the
window across its monitor; the overlay follows on its own. `--windowed`
opts out. Verified: window rect == monitor rect (3840x2160), no
caption/thickframe bits.

**2. "No keyboard at all"** - the button's console held the foreground;
MAME's window never got focus, which kills both keyboard and the wheel's
foreground-mode DirectInput. run_rig.py now runs enforce_foreground():
ALT-tap (releases the foreground lock) + SetForegroundWindow in a loop that
verifies BOTH GetForegroundWindow AND GetGUIThreadInfo.hwndFocus equal
MAME's window, for up to 45 s until stable. Pitfall discovered on the way:
activation can land on the OVERLAY instead (Windows redirects activation to
an owner's last-active owned popup; SwitchToThisWindow reliably triggers
this) and the overlay's DefWindowProc eats every key - never use
SwitchToThisWindow here, and treat fg==overlay as failure. Verified stable
fg=focus=MAME t=5s..40s after a cold bat launch.

**3. "Coin works, Start doesn't"** (user's second test - the report that
cracked it) - EmuEzRacing.cfg binds START1 as
`KEYCODE_1 OR JOYCODE_1_BUTTON35`. vunit's parser drops BUTTON33+ tokens
and MAME invalidates the whole sequence, killing the keyboard alternative
too; COIN1 (`... OR JOYCODE_1_BUTTON22`) parses fine, hence the split.
run_rig.py now writes a sanitized rig-local copy (rig/ctrlr/) with invalid
alternatives stripped (START1 -> KEYCODE_1; 264 all-invalid ports across
the file removed so MAME defaults apply); axes/pedals/shifter untouched;
the racing build's file is never modified. Root cause of the token drop
(validation vs the 128-button DIJOYSTATE2 patch) stays an open item.

Also landed: the bat now `start /min`s python; run_rig auto-detects the FFB
plugin's ~50% first-launch enumeration hang (no responsive MAME window in
20 s -> kill + one relaunch; safe, pre-FFB) so the button is one-press.

Probe lessons (for future automation): GDI screen capture (BitBlt /
PIL ImageGrab) shows the GL overlay as pure black - use MIDV_GL_SNAP for
ground truth (full 3840x2160 16:9 attract confirmed pixel-perfect, proof:
results/proof/2026-08-18-fullscreen-button-launch.png). Synthesized keys
(keybd_event) never reach MAME's rawinput provider - keyboard claims need
physical keys. WM_CLOSE on MAME's window is a clean remote quit (used 5x,
zero stranded-torque incidents).

Standing at section close: physical Start=1 / Esc / wheel+FFB pass by the
user pending on the sanitized-ctrlr build (game left running at the rig).

---

# WHEEL TEST PASSED (2026-08-18, night)

User confirmed at the rig on the sanitized-ctrlr build: "it worked!" —
coin, Start, Esc, steering, and FFB all live through the one-press Stream
Deck button, fullscreen. Phase 1 (playable rig) is closed end-to-end.

---

# OVERNIGHT BUILD (2026-08-19, unattended): CRT pass + collection shell + 3-game boot

User prioritized launcher + CRT (Phase 4/5 items pulled forward) and left
for the night. All work below is machine-verified; the rig pass is the
morning checklist at the end.

## CRT pass — live in the product

- `gpu/renderer.py` PAL_FS grew a `uCrt`-gated block: gentle barrel warp
  (black outside the glass), per-source-line gaussian scanlines with
  brightness-dependent beam width, 3-tap horizontal beam softness,
  two-phase magenta/green shadow mask (rainbow-free at any output size —
  the first cut used RGB triads and produced ugly moiré), rounded corners
  + vignette + 1.42 gain. The uCrt=0 path is untouched, and the exact-mode
  invariant compares the index buffer upstream of the palette pass anyway:
  re-verified **100.0000% / 0 differing pixels** twice.
- `--crt` flag renders offline previews; header regenerated per the
  documented workflow; `midvunit_v.cpp` reads `MIDV_GL_CRT=1` at boot and
  **F9 toggles live** (GetAsyncKeyState edge-poll in the present loop).
- **Lesson (cost ~40 min of ghost-chasing):** downscaled screenshots
  AVERAGE AWAY scanlines and mask — three "the CRT isn't working" probe
  runs were actually fine (uniform readback said uCrt=1 all along); a 1:1
  crop of the 4K backbuffer showed the effect immediately. Never judge a
  subpixel effect on a resized preview.

## Collection shell — the deck button is now the product

- `harness/collection.py`: fullscreen borderless game-select menu on the
  glfw+moderngl stack. Cards = LaunchBox title screenshots + clear logos
  (racing repo's Images/Arcade tree), gold pulse on selection, footer
  hints. Keyboard: arrows/A-D select, Enter/Space launch, **C toggles CRT
  for the next launch**, Esc quits. Best-effort joystick nav (hat +
  buttons). Config persists in `rig/collection.ini` (crt/scale/last rom).
  `--shot out.png` renders one offscreen frame (automation/preview).
- Launches via `run_rig.launch_game()` — run_rig.py refactored into an
  importable module (same CLI, plus `--crt`). Shell hides during play,
  returns + re-takes foreground after Esc.
- `Launch-Cruisn.bat` (the Stream Deck button) now opens the shell.
- **E2E machine-verified:** bat → shell fullscreen+focused → Enter →
  crusnusa fullscreen+focused → WM_CLOSE → shell returns focused → Esc
  exits. Proof: `results/proof/2026-08-19-collection-shell.png`.

## Startup screens + first boots of the other two games

- crusnwld stopped dead at MAME's bad-dump warning (`c31boot.bin` is a
  known BAD_DUMP): `skip_warnings` is REFUSED whenever
  `rom_load().warnings() != 0` (frontend ui.cpp:781, by design), and
  injected keys cannot dismiss it — rawinput ignores keybd_event, and the
  win32 keyboard provider didn't register them either (tried, reverted).
- Fix: **`MIDV_SKIP_STARTUP_SCREENS`** env gate in
  `display_startup_screens` — the first patch outside the driver files
  (frontend `ui.cpp`, 7 lines, inert unset). run_rig sets it. This is
  also the wishlist "boot-straight-to-attract" behavior.
- **offroadc: FULL 3D ATTRACT through the renderer on first ever run** —
  16:9 margins filled with real geometry, letterboxed correctly on the
  3440x1440 ultrawide. Zero renderer changes needed. Proof:
  `results/proof/2026-08-19-offroadc-first-attract.png`.
- crusnwld boots to **CALIBRATE CONTROLS** (no NVRAM fixture — crusnusa
  needed its fixture for the same reason). Renders correctly (underlay
  path). One-time calibration at the rig persists in `rig/nvram`.

## Morning checklist (user)

1. Deck button → shell appears → pick each game, drive.
2. **F9 in-game**: A/B the CRT look at the rig. Tuning knobs are all in
   `gpu/renderer.py` PAL_FS (mask strength 0.62, gain 1.42, beam widths
   0.35/0.65, warp 0.041/0.052) — regen header + rebuild after edits.
3. crusnwld: run its one-time CALIBRATE CONTROLS (service/TEST = F2).
4. Off Road Challenge gameplay + FFB feel — FFBPlugin GameId=22 is the
   Cruis'n tuning; offroadc may deserve its own profile later.
5. C key in the shell chooses CRT-on/off per launch; it persists.

---

# Evening debugging session (2026-08-19): FFB root cause, perf, crash forensics, crusnwld VERIFIED

User's morning-after reports, all root-caused with the user live at the rig:

## 1. "FFB centers but no game forces" + MAME64.dll error → FIXED
The FFB Arcade Plugin's MAME mode needs **MAME64.dll** (the MAME output
client: init_mame() + callbacks deliver the rom name via mame_copydata and
per-frame force values via mame_output). The original 3-file copy beside
vunit.exe missed it. With it copied: FFBlog.txt shows `RomName = crusnusa`,
`RunningFFB = RacingFullValueActive2` — same active mode as the racing
build. Game forces live.

## 2. Audio crackle / "performance issues" → FIXED (priority 1)
Average speed had sunk to 94-97% (audio crackle = MAME underrun). A/B
proved the FFB client innocent (97.2% with, 94.2% without). Ambient load
(Defender, Pit House, Spotify all active) + default priority was the
cause: `priority 1` in the rig mame.ini → 99.7-99.9% across three runs.
User independently reported the next run "seemed improved".

## 3. Intermittent crash → GL thread exonerated, plugin teardown implicated
Event Log chain: msvcrt!memcpy AVs at ~every second EXIT (post-stats,
teardown phase), plus one mid-game EIP=0 crash (8:46pm, unexplained
singleton — watch). Evidence: racing build (same plugin, mame.exe) has
ZERO faults in 60 days; a HEADLESS capture run (our GL thread never
started) still exited 0xC0000005 → not our thread. Hardened anyway:
`mvgl_exit()` machine-exit notifier flags the GL thread down and waits
for acknowledgement before teardown ("machine exit" now in the GL log at
every close; 3/3 clean cycles). Remaining teardown AV is post-exit
cosmetic, almost certainly the plugin's exit path (it TerminateProcess-
hooks exit and leaves scanner threads running). WER LocalDumps now armed
→ rig/crashdumps/ collects minidumps for real attribution when it recurs.

## 4. "Cruis'n World emulation is really very bad" → IT ISN'T. VERIFIED 100.0000%
MAME flags crusnwld fully-working (no imperfect-graphics/sound flags), and
the oracle now proves OUR renderer is faithful on it too:
- fixtures/nvram-crusnwld snapshotted from the user's rig calibration.
  Caveat learned: headless runs re-demand CALIBRATE CONTROLS (no input
  devices → analog sanity check fails), so crusnwld captures must run in
  the rig config with the wheel attached. run_capture.py generalized to
  take a rom argument.
- Capture at frame 3400 of 3D attract (61.7 MB quads) with Lua-exit
  alignment (first attempt compared a scene ~800 frames past the dump —
  0.001% "mismatch" that was pure harness misalignment, not renderer).
- **GPU vs MAME videoram: 100.0000% bit-exact (0 differing pixels).**
What the user actually experienced was the perf underrun (#2) + first-boot
calibration + (possibly) CRT mask taste — NOT emulation quality. The
"throw Fable at the emulation" question dissolves: there is nothing to fix
in the core for crusnwld.

Standing after this session: user to re-feel FFB in USA + re-judge World
at speed; stretch goals queued (launcher music/SFX, wanszai-style Esc
settings overlay in-game); analyze first minidump when the teardown AV
recurs.

---

# Overnight session 2 (2026-08-19 night): all three games verified, wheel wizard, shell polish

User's evening feedback (5 items) all root-caused or shipped; the wanszai
teardown reshaped the input roadmap.

## ALL THREE GAMES NOW 100.0000% BIT-EXACT

offroadc's first verification pass showed 401 differing pixels - exactly
one column (x=511): offroadc runs a 512x401 mode with visarea right edge
at x=510, and gpu/renderer.py hardcoded the cliprect at 511. rasterize.py
always honored meta's visarea; renderer.py now does too (wide mode still
deliberately unclips into the margins). After the fix:

| game | exact-mode result |
|---|---|
| crusnusa | 100.0000% (0 of 204,800) |
| crusnwld | 100.0000% (0 of 204,800) |
| offroadc | 100.0000% (0 of 205,312 - 512x401 mode) |

Note for the C++ renderer: HEIGHT=400 is a constant; offroadc's 401st line
is currently not presented by the overlay (cosmetic, one line - open item).

## Wheel high-buttons: REAL root cause found and fixed

The DIJOYSTATE2 base patch only touched the pure dinput module - but the
default Windows joystick provider is **winhybrid**, which still passed
c_dfDIJoystick (32-button legacy, no fallback). New verbose diagnostic
showed "128 buttons reported, DIJoystick (32-button legacy) format
accepted" for the Moza. This means the high buttons NEVER worked in the
racing build either. Fixed winhybrid to request DIJoystick2 with legacy
fallback (mame-src 3cac3d67): Moza now exposes 140 items.

Second half: MAME's items for buttons 33-48 use standard tokens
ADDSW1..ADDSW16 (ITEM_ID_ADD_SWITCH; 49+ collapse into OTHER_SWITCH and
are unaddressable). EmuEZ's BUTTONnn dialect never parses - the launcher's
ctrlr translator now maps BUTTON33-48 -> ADDSW1-16. Verified live via a
Lua input-dump harness (scratchpad dump_input.lua pattern -
manager.machine.ioport fields + input:seq_to_tokens): START1 resolves to
"KEYCODE_1 OR JOYCODE_1_ADDSW3" (wheel button 35), gears land on wheel
buttons 33/34. Physical presses = user's morning test.

## Wheel-setup wizard (wanszai teardown -> feature)

Inspected the installed Ridge Racer Collection: RRC.exe is a full wrapper
owning DirectInput (settings.ini with crt/curve/ffb/maps; wheel_di.ini
written by an in-game press-to-bind wizard; menumusic.mp3 + bgra menu
assets; multi-device aux binding incl. the user's DS-8X shifter + Stalk).
Our v1 equivalent shipped in the shell: **S = WHEEL SETUP** - press-to-bind
COIN/START/VIEW1-3/RADIO/GEAR1-4 across all connected joysticks (glfw),
saved to collection.ini [wheelmap], applied at every launch by the ctrlr
generator (device name -> mapdevice JOYCODE index, auto-added for new
devices; button n -> BUTTONn+1 or ADDSW; game-specific EmuEz sections are
stripped of wizard-claimed ports so the wizard always wins). E2E-verified
via simulated wheelmap + Lua dump: gear1 on the DS-8X resolves as
JOYCODE_2_BUTTON1.

## Shell polish

- Menu music (extracted from the LaunchBox Cruis'n USA video snap via
  ffmpeg -> rig/assets/menumusic.wav, mci loop) + synth nav/select blips
  (winsound, coexists with mci). Music pauses during play.
- Instant return: the shell now watches the game WINDOW and reappears when
  it dies (0.6 s measured), reaping vunit's slow teardown (FFB plugin exit
  races + WER dump writes = the old "several seconds") in the background.
  run_rig gained launch_game_async(); blocking launch_game kept for CLI.

## Fullscreen + cursor fixes (user reports)

- crusnwld snapped back to 4:3: MAME resizes its own window on video-mode
  changes. run_rig now runs an enforce_fullscreen watcher for the window's
  lifetime (skips while minimized).
- Cursor floating + error-beep clicks: the overlay was DISABLED+
  TRANSPARENT - EX_TRANSPARENT passes no hit-tests without EX_LAYERED, so
  clicks hit a disabled window = beep. Overlay now has a real wndproc:
  cursor hidden over the game, clicks SetForegroundWindow(owner)
  (mame-src cc0aff8c).

## Rendering-artifact research (user request)

- The dark dithered rectangles (user's Cruis'n World screenshot; also in
  our frame-3400 capture next to the CHECK gantry) sit INSIDE the 4:3
  area where we are bit-exact -> they are MAME's own output (authentic or
  an unreported core inaccuracy; no matching MAMETesters report).
- Known open: MT 01798 (crusnwld green artifacts in manual-mode neutral,
  minor, open since 2008). offroadc texture colors (MT 05356) fixed in
  MAME 0.152.
- Sky black-bars at 16:9 edges: World's sky IS 3D geometry extending past
  4:3 (tiles span x -61..705 in the captured scene) - margins fill in most
  scenes; where the geometry runs out, margins go black (scene-dependent).
  A floating hillside box at the left margin edge = off-screen parked
  geometry the game never meant to show - the known margin-pop-in class.

Standing: physical wheel test of wizard bindings + FFB forces; Esc in-game
settings overlay (designed, not built: GL-thread menu polled via
GetAsyncKeyState, WM_CLOSE exit path, MAME Tab menu meanwhile).

---

# Overnight session 3 (2026-08-20): Exotica lands, nav overhaul, install story

## Cruis'n Exotica — "simpler than we think" confirmed

The user asked to go hard at Exotica support. Decisive prior fact: the rig's
FFB log shows RomName=crusnexo 20,000+ times — the user already plays it via
MAME 0.286, so "supported at parity" only needs packaging.

- **One exe, four games**: midzeus.cpp added to the vunit subtarget
  (SOURCES=midvunit.cpp,midzeus.cpp + REGENIE). Blocker on the way: genie's
  source scanner cannot tokenize the raw-string shader header
  ("unterminated character literal") — generator rewritten to emit escaped
  C strings (harness/gen_shaders.py, now the documented regen path).
- Shell shows 4 cards ("CRUIS'N COLLECTION" now — Exotica is not V-Unit);
  run_rig gives Zeus games `video d3d` (no GL overlay to punch through —
  MIDV_GL hooks are inert for zeus) and everything else applies unchanged:
  fullscreen surgery, focus enforcement, FFB plugin (racing log proves
  crusnexo FFB works), startup-screen skip (crusnexo is NOT_WORKING-flagged
  → warning screen; env-gated skip handles it), NVRAM fixture seeded from
  the racing build (fixtures/nvram-crusnexo).
- **E2E verified**: TRANS SELECT attract at 100.00%, fullscreen 3840x2160,
  focused, clean close.

## Zeus renderer-replacement scoping (the gated stretch item) — VIABLE

`zeus2_renderer::zeus2_draw_quad` (devices/video/zeus2.cpp:1550) is the
choke point, and it is as clean as V-Unit's process_dma_queue: every quad
arrives as structured data (4 verts, u/v, texdata) with the model-view
matrix in device state. Env-gated counter POC (MIDZ_STATS=1) profiled
attract: **24–2,067 quads/frame typical, 6,325 peak** — far inside the GPU
budget (V-Unit: 2,654 peak, rendered at 289 fps at 4x).

Three-level assessment recorded:
1. Parity packaging — DONE tonight.
2. GL replacement over zeus2_draw_quad — same arc as the V-Unit POC
   (capture → reference → GL → in-process), architecturally EASIER
   (perspective-correct + Z-buffer are native GPU concepts); oracle
   compares vs MAME's own imperfect output.
3. True arcade accuracy — Zeus2 has unemulated features upstream
   (NOT_WORKING flag); a level-2 renderer could approximate/fix visuals
   ABOVE the emulation, wanszai-style, without core work.

## Launcher: proper navigation + wizard input fixed

- User report "wizard ignored my wheel buttons": pyGLFW returns
  (LP_c_ubyte pointer, count) tuples from get_joystick_buttons/hats — the
  code iterated the 2-tuple, so no press ever registered and hat nav
  silently TypeError'd. Proper unpacking now; jid scan 0-15 (Moza=3,
  Stalk=4 — the old range(4) missed the stalk entirely).
- Menu restructure per user: game cards row + SETTINGS row (up/down),
  Settings screen = CRT toggle / WHEEL SETUP / BACK. Wizard returns to
  Settings. Wheel: hat navigates, any button = OK.
- Menu music: harness/make_music.py pipeline (yt-dlp → trim → loudnorm →
  rig/assets/menumusic.wav); user's requested track installed (866 s,
  first 17 s trimmed). Blips self-regenerate on first run.

## Install/distribution story (user request)

- docs/INSTALL.md: player path (release folder + setup.ps1 + own ROMs +
  FFB plugin download) and developer path (MSYS2 build from the patch
  series). Legal posture restated: no ROMs, no assets, no binaries.
- setup.ps1: checks Python/deps (auto-installs), locates vunit.exe + ROMs,
  verifies the four FFB plugin files, writes CruisnCollection.bat with the
  CRUISN_* env overrides.
- Portability pass: CRUISN_VUNIT/ROMS/MAME_DIR/CTRLR/ART env overrides;
  missing art → generated cards; missing EmuEZ ctrlr → wizard-only ctrlr;
  missing audio → silence.

## UDP telemetry (user stretch idea) — design sketch, not built

- Force: the FFB value already flows through MAME outputs (the plugin
  consumes it) — a UDP mirror is trivial: env-gated sender in our patch or
  a second output client. Phase A.
- Speed/RPM: live in game RAM (HUD renders them) — needs per-game address
  hunting (Lua memory search while driving at known speed), then the same
  env-gated UDP sender reads them per frame. Phase B. Target consumer:
  SimHub custom-UDP profile driving a Buttkicker.

Standing after session 3: user to re-test wizard + nav + music; Exotica
from the shell; then the Esc overlay and telemetry Phase A are next.

---

# Rig test round 1 + crack fill — 2026-08-20/21 (overnight session 4)

## Rig findings (user at the wheel) and their fixes

1. **Shell booted straight into the last game** (offroadc): a phantom
   wheel-button press during device enumeration (Moza wake reports zeros
   before real state; the 0→1 settle read as a press) hit the "any wheel
   button = OK" menu rule with the remembered selection. Fixed in
   collection.py: 1 s per-device silence after a joystick appears, input
   arming windows after boot/return, per-button 0.6 s debounce (a button
   down <0.6 s ago is a re-enumeration glitch, not a press), and joystick
   input held dead while the previous vunit is still tearing down + 2 s
   (teardown's DirectInput release re-enumerates the wheel SECONDS after
   the shell is back — this was the "auto-relaunched a few seconds later"
   report).
2. **Seconds of desktop + weird focus after quitting**: MAME's window
   outlives its message pump through the teardown drag (FFB exit race +
   WER dump), so the IsWindow watch waited it out. The shell now also
   treats two consecutive 1 s WM_NULL timeouts as "exiting"
   (run_rig.window_responding). And the shell now NEVER hides: it stays
   fullscreen behind the game for the whole session (wanszai-style) with
   a LAUNCHING screen while MAME boots — no desktop flash either way.
3. **Wizard bound the wheel's return-spring to GAS**: baseline was
   snapshotted while the wheel was still returning. Now: Press-Enter-to-
   begin gate, ~1 s swallow-everything cooldown after every bind/skip,
   and axis baselines arm only after ALL axes sit still (0.35 s samples,
   <0.06 delta).
4. **Exotica**: stretched (`-nokeepaspect` is wrong for the d3d path →
   now `-keepaspect`), fuzzy (`-prescale 4`), lamp/7seg panel ate the
   bottom fifth (`-view "Screen 0"`), Esc dead / unquittable (UI_CANCEL→
   F12 remap is now V-Unit-only), throttle "flutter" + dead shifter:
   crusnexo wires gears=BUTTON2-5, radio=6, views=7-10 (midzeus.cpp) —
   the wizard's V-Unit-convention default section had the latched shifter
   holding a wrong button. New translated `<system name="crusnexo">`
   ctrlr section. Black opponent cars / sprite garbage = upstream zeus2
   emulation (unchanged from the racing build); only the Zeus GL arc
   could address it.
5. Cursor: hidden in the shell (glfw), parked in the bottom-right corner
   in-game (SetCursorPos 32767,32767 — the arrow glyph renders
   off-screen; MAME never hides it for a borderless -window window).

## Crack fill (MIDV_GL_CRACKFILL, default ON, shell SETTINGS toggle)

The hardware leaves sub-pixel cracks between quads where the persisted
page's previous frame shows through (authentic, but it shimmers). Fix
shipped through the full stack:

- Scene pass gains a second render target: R8UI "written this scene"
  mask (renderer.py FS `outMask`; C++ overlay attachment 1 +
  glDrawBuffers, mask-only glClearBufferuiv per scene so the page itself
  still persists).
- Palette pass: an unwritten pixel is redirected to its nearest written
  neighbour ONLY when written pixels exist on both sides along some axis
  (true between-poly cracks). One-sided pixels — geometry silhouettes
  against the cleared 16:9 margins — stay untouched. Radius 4×scale fine
  px. 3D scenes only (2D screens / CPU-shadow path keep persistence).
- Exact mode untouched by construction (single-draw path, fill radius 0)
  — re-verified **100.0000%** vs MAME videoram on `results/capture` and
  `results/capture-8000` after the shader changes.
- Live-verified on the rig build: crusnusa (99.97% avg speed) and
  offroadc (100.00%, 512×401 mode) attract runs, MIDV_GL_SNAP snaps
  artifact-free, GL err=0, FBOs complete.

**Honest finding**: quality mode's continuous coverage already closes
nearly all static cracks that exact/integer mode shows (canyon 4× wide:
166 of 4.4M pixels filled; offroadc rig capture: 11). So the "momentary
see-through ground" seen in offroadc GAMEPLAY is probably NOT the static
crack class — candidates: the game's own transient LOD/pop seams
(authentic), or a live-path scene-timing case. Needs an at-the-wheel
capture session (record_diag or MIDV_GL_SNAP while driving) to classify.
The fill stands regardless: it is a strict no-op wherever the scene
covers the frame.

Standing after session 4: user re-tests round 2 (launch flow, wizard
gate, Exotica fixes, crack fill A/B on Off Road); v0.2.0 tag once the
rig test passes.

---

# ZEUS GL ARC, phase 1: capture + CPU oracle — 2026-08-22 (session 5)

**The Zeus2 renderer-replacement arc is underway and the oracle stage is
done in one session.** Same methodology as V-Unit: instrument → capture →
CPU reference bit-exact vs the hardware framebuffer.

## Capture instrumentation (zeus2.cpp/.h, env-gated, zero cost unset)

`MIDZ_CAPTURE=<dir>` + `MIDZ_CAPTURE_FRAME=<floor>` +
`MIDZ_CAPTURE_MINQUADS=<n>`: records everything that mutates the frame
buffer, in submission order (poly->wait precedes the direct paths, so
submission order == mutation order): quads (post-transform, post-near-clip
verts + complete raster state), pal_table loads (emitted on change), fast
clears, frame_write register snapshots. Bracketed by full pre/post
color+depth dumps (4 MB each) + waveram (16 MB) + regs. The min-quads
trigger arms on the first >=n-quad frame past the floor and records until
n quads landed — frame numbers drift between boots and Exotica's 3D
renders every other frame, so frame-number triggers alone are useless.

## CPU oracle (harness/zeus_rasterize.py)

Replays a capture from pre-state and compares against post-state.
Replicates bit-for-bit: poly.h render_triangle (y-sort, round_coordinate,
float32 plane-equation params, extents at pixel centres), zeus2
render_poly_8bit (integer-stepped z, per-pixel perspective divide in
float32, swizzled texel fetchers, transcolor reject-if-any-of-4,
`rgbaint_t::bilinear_filter`'s SSE row-lerp-halving
(((r1>>1)*v + (r0>>1)*(256-v))>>15), rgb_t::scale8 truncation, saturating
adds, the texture_alpha integer alpha lerp), fast clears and frame_write.

## Verification — three captures, all 100.0000%

| capture | quads | content | color | depth |
|---|---|---|---|---|
| register screen | 38 (+460 frame_writes elsewhere) | 2D UI | **100.0000%** | **100.0000%** |
| title showcase | 1,723 | 3D car + alpha logo glow | **100.0000%** | **100.0000%** |
| transition/heavy | 6,489 (incl. 3,489 blended, 23 solid, 84 depth-clear) | multi-frame 3D | **100.0000%** | **100.0000%** |

Zero differing pixels in any capture, color AND depth, across the full
4 MB buffers — not just the display window. Coverage still to exercise:
texel modes 0 (4-bit) and 2 (rgb555 / texture-alpha, the water-skier
sprites) — need a gameplay capture; implementations ported from source.

Notes for the GL phase: Zeus2 blending is order-dependent per pixel
(read-modify-write vs evolving framebuffer), so the GL renderer targets
bit-exact for non-blended pixels and visually-exact for blended ones
(GL float blending rounds; zeus scale8 truncates) — the CPU oracle stays
the bit-exact reference, exactly as rasterize.py does for V-Unit.
Blend states (blend_enable, srcAlpha, dstAlpha) group into consecutive
runs for batched draws; depth = gl_FragDepth from the shader-computed
24-bit value; per-quad palettes bake into a 2D array texture.

## ZEUS GL ARC, phase 2: GPU renderer prototype — same session

**gpu/zeus_renderer.py renders the capture stream on the GPU.** One
universal blend config (shader premultiplies by srcAlpha / per-pixel
texture alpha, outputs dstAlpha as fragment alpha, ONE/SRC_ALPHA);
gl_FragDepth carries zeus2's 24-bit depth (clear/min variants in-shader);
batches split only on (blend, depth test, effective depth write, page row
base, cliprect); per-batch scissor applies the hardware cliprect in
quad-local y — without it, back-page quads with slightly out-of-range
local y spill into the DISPLAYED page (found as a corner blob of wrong
pixels; the bug class to remember for the live overlay). Swizzled texel
fetchers, SSE bilinear, palettes as a 256-wide array texture (one row per
pal_table load), full 512x2048 FB space as the render target, direct-op
records applied via CPU mirror sync at segment boundaries.

Verification vs the bit-exact CPU oracle (display window, scale 1):

| capture | exact | within ±1 | within ±4 | max delta |
|---|---|---|---|---|
| register screen | **100.0000%** | 100.0000% | 100.0000% | 0 |
| title showcase | 93.63% | 99.9360% | 99.9927% | 206 (≈15 px, silhouette edges) |
| transition/heavy | 33.26% | 99.9595% | **100.0000%** | 3 |

The ±1 mass is GL float blending rounding vs scale8 truncation (documented
stance: CPU oracle = bit-exact reference; GL = product path). The
transition capture is ~all blended pixels, hence low "exact" but max
delta 3. Quality mode at 4x (2048x1600): glass-smooth geometry, crisp
HUD/plate text — proof image `results/proof/zeus-gl-showcase-4x.png`.

**Remaining for the arc** (next session): in-process live integration -
hook zeus2_draw_quad + present like the midvunit overlay (window
machinery reusable), env gates, Esc menu/CRT for Exotica, then the shell
flips crusnexo off the d3d path. Perf note: 6.5k quads/frame in dozens of
batches is trivial GPU load at 4x.

## ZEUS GL ARC, phase 3: LIVE in-process integration — same session

**Cruis'n Exotica now runs through our own GL renderer, live, in one
process, at 4x internal resolution.** The mzgl overlay lives inside
zeus2.cpp (no build-system changes): an owned NOACTIVATE popup sized to
the MONITOR (not MAME's window - see perf), fed by an in-process 64 MB
ring carrying the same records MIDZ_CAPTURE writes plus waveram dirty
spans and display flips, consumed by a GL thread running the
oracle-verified zeus_renderer.py pipeline (shaders generated into
zeus2_gl_shaders.h). Esc menu (pause included), F9 CRT (new RGB present
shader with the V-Unit CRT pass), MIDZ_GL_SNAP, crt statefile - full
parity with the V-Unit overlay. run_rig defaults Zeus games to MIDZ_GL=1
(gdi underneath, small un-maximized MAME window holding focus);
MIDZ_GL=0 restores the d3d/bgfx fallback.

Bugs found on first light, both fixed:
1. **Screens accumulated** (high-score table over copyright text over
   menus): the fast-clear CALL SITE was still gated on capture only -
   clears never reached the live ring. One-line gate fix.
2. **Flashing during the demo race**: the display-base flip was emitted
   once per frame at screen_update, so the overlay kept presenting a page
   the game had already begun clearing. Flips now emit AT the zb38
   register write, in stream order with quads and clears.

Perf attribution (60 s attract runs): d3d no-overlay 100.00%, gdi
no-overlay 99.48%, gdi+overlay 97.3-97.7% during the hunt -
scale-independent (1..4), not vsync, not FB size, not the emit path
(pal-table memcmp per quad eliminated anyway; FB space halved to 1024
rows = the hardware's actual address space... which crusnexo uses 0..800
of). Final configuration measured **99.76%** with crusnusa regression at
99.93%. Residual ~0.3-2% (run variance) parked for an ETW session.

Verified live: title showcase, registration/high-score screens
(frame_write path), Vegas demo race - all clean at 4x, snaps in
results/verify-mzgl. Standing: user play test (wheel input, Esc menu
pause, CRT taste, gameplay texture modes via zeus_capture_play.py).

---

# Game-code patch system + ground-culling investigation — 2026-08-22 (session 6)

## In-memory code patcher (MIDV_PATCH) — SHIPPED

The V-Unit games `memcpy` their whole TMS320C31 program from the maindata
ROM into program RAM at every reset (midvunit.cpp machine_reset). The new
`midv_apply_patches` overlays word patches on that RAM copy - **ROM files
on disk are never touched** (GPL/legal bright line intact). `MIDV_PATCH=
<file>`, lines `WORDADDR OLD NEW` (hex; OLD verified or `*` to skip, so a
patch is safe to ship for one version and inert on a mismatch). Verified
end-to-end (identity patch: "2 applied, 0 skipped"). Docs + disassembly
recipe in `patch/game/README.md`. This is the foundation for all future
game-code fixes (coinage, FOV, culling, ...). Full offroadc disassembly
via MAME's own debugger `dasm` command (no unidasm build needed):
`results/offroadc-prog.asm`.

## Ground-culling / "sky through ground at far L/R" — INVESTIGATED, not a cull

The bottom-corner blue wedges in offroadc widescreen are NOT a culling
limit and NOT a renderer hole:
- Native 4:3 render of the same scene has **zero** blue in the bottom
  corners - so it is a widescreen-margin-only phenomenon.
- The ground-plane quads already carry vertices at **x=-366 .. x=+1000**
  (hardware screen is 0..511) - the geometry is submitted FAR wider than
  4:3, not clipped at the screen edge. There is no clip constant to widen.
- At the wedge pixels, hardware x=0 IS written - with water blue
  (24,115,165), by a legitimately-drawn backdrop/water plane that is
  off-screen in 4:3. So crack-fill / margin-extend correctly leave it
  alone (the pixel isn't a hole), and a game-code culling patch would do
  nothing (the game already draws there).

Conclusion: the corner blue is *revealed backdrop*, an inherent
consequence of showing more of the world than the 4:3 frustum. The clean
lever is margin width, not a game patch.

## Runtime 16:9 margin (MIDV_GL_MARGIN) — SHIPPED

MARGIN is now runtime in the overlay (0..86 per side; default 86 = full
widescreen). run_rig sets a per-game default: **offroadc = 64** (trims the
outer margin where the canyon water plane showed as corner wedges);
crusnusa/crusnwld stay at 86. Verified: offroadc bottom-corner blue 0.00
after the trim, terrain intact, thin clean pillarbox. Also the earlier
margin-EXTEND fix (probe walks inward past the +0.5-offset dead column)
ships this build - true black holes now fill from the boundary column.

Also this session: NVRAM reset to a clean fixture-seeded baseline for all
four games with snapshots (rig/nvram-snapshots, 20260822) as the reference
for the settings-baking workflow (harness/nvram_tool.py). ROMs verified
OK by MAME's own checker.

---

# Overnight session 7 (2026-08-22/23) — audio, water artifact, FOV R&D

## Task 2: Off Road water-margin artifact — reproduced, characterized, mitigation shipped

Reproduced the "sky/water through the ground at far L/R" in a 150 s
fill-off attract sweep: 11 of 60 bright-scene snaps show a light-blue LAKE
plane in the bottom-corner margins (proof:
results/proof/offroadc-water-margin-artifact.png, the CHECK POINT scene).
Confirmed exactly the research-predicted revealed-backdrop class: the lake
is legitimate world geometry off-screen in 4:3, exposed by the 16:9
margins; the pixels are WRITTEN by the water quad (not a hole), so
crack-fill/margin-extend correctly leave them.

**Surgical fix (content-specific backdrop masking) NOT done autonomously -
by design.** It is an aesthetic, per-content judgment: culling the water
quad in the margins risks smearing/harming legitimately-wide scenes (the
canyon race margins show correct rock/terrain). Doing it safely needs
visual iteration with the user across multiple scenes, not a blind
heuristic. Tooling gap noted: V-Unit statedump is frame-only; a scene-match
/ min-quads trigger (like the Zeus MIDZ_CAPTURE_MINQUADS) would make
capturing a specific 3D scene reliable - worth adding before that session.
**Shipped mitigation stands: the ASPECT / WIDESCREEN toggle (4:3 CLASSIC /
16:9 TRIMMED / 16:9 FULL).** Added a MIDV_DBG_QUADID render mode to
renderer.py (outIndex = gl_PrimitiveID/2) for per-pixel quad attribution
when that session happens.

## Task 1: per-game menu audio — DONE (see commit)
Real attract audio per game from LaunchBox video snaps; cross-fade on card
highlight, 1.2 s fade-out on launch.

## Task 4: Telemetry Phase B (speed) — crusnusa CONFIRMED + wired; hunt turnkey

RAM-hunt method built and proven. Added a periodic DSP-RAM dump hook
(MIDV_RAMDUMP_DIR + MIDV_RAMDUMP_EVERY) and a differential analysis:
capture RAM across a demo-race acceleration, find the C3x-float word that
ramps 0->top monotonically and resets per lap.

- **crusnusa speed = DSP word 0x0F22D (C3x float, MPH), CONFIRMED**:
  trajectory 0->78->176->252->294 cruise, reset 0 per demo lap. Wired into
  telemetry (`telem_notify("speed", mph)`), verified LIVE: 4066 UDP
  datagrams, 0..301 mph, correct accel curve. Unblocks SimHub/Buttkicker
  speed feed and the parked achievements idea. Speed also mirrored at
  0x0DCD5 (work copy).
- **offroadc**: a per-car speed ARRAY at ~0x1C1xx-0x1C6xx (player + 3
  opponents); strong candidates 0x1C40E, 0x1C1D7 (0->73->188->221 vary
  with terrain). Needs on-screen-MPH correlation to pick the player slot -
  left as "hunt pending" rather than wire a possibly-wrong address.
- **crusnwld**: not yet hunted (same turnkey method).

Adding a game: `MIDV_RAMDUMP_DIR=<dir> MIDV_RAMDUMP_EVERY=20 run_rig ...`,
then the differential analysis (see this session log), then add the addr
to s_speed_addr[] in midvunit_v.cpp. RPM: no clean candidate found on the
first pass (may be normalized 0..1 or gear-reset); revisit with the
on-screen correlation.

## Task 2 SOLVED (session 8): backdrop-margin suppress fixes the water artifact

The FOV-trace pivot paid off differently than planned. Using MIDV_DBG_QUADID
to attribute the blue "lake" pixels in capture-offroadc-rig's left margin,
they resolved to quads 0-3 - the sky/horizon BACKDROP band (texbase low
byte 0x7f, full-width, drawn first), NOT a separate water plane. It shows
through the 16:9 margins wherever the terrain trapezoid doesn't reach.

**Fix = the research's first-choice content-specific masking, done safely:**
flag backdrop quads (texbase & 0xff == 0x7f AND width > 200px) into a meta
bit and discard them inside the 16:9 margins. The pixels go unwritten, so
the existing margin-extend fills from the 4:3 boundary column - SKY in the
upper margin, TERRAIN in the lower - which covers the reveal automatically.
Terrain/rock quads (texbase 0x25xx-0x30xx) are untouched. Width gate
excludes a stray 16px 0x7f quad in crusnwld (verified: 0 false positives on
crusnusa canyon/title, crusnwld).

Verified: exact mode still 100.0000% (suppress is off in exact mode);
capture-offroadc-rig left-margin water 0.643 -> 0.000, right-margin canyon
rock preserved; LIVE full-16:9 attract sweep bottom-margin water 0.40 ->
0.02 across the whole cycle, terrain/cacti extend naturally into the
margins, 100% speed. Proof: results/proof/offroadc-water-FIXED-16x9.png.
Ships default-on with crack/margin fill (MIDV_GL_CRACKFILL=0 or
MIDV_GL_MARGINFILL=0 disables). Minor residual: faint horizontal streaking
where sky is clamp-extended in the upper margins (a vertical-gradient sky
fill could refine it later).

This is the artifact the user chased across sessions 5-8; full 16:9 Off
Road is now clean. GAME_MARGIN can stay empty (full width) as the default.

## 2026-08-23 — Exotica TRUE full 16:9: the game was never culling — WE were clearing it (session 9)

The "Zeus FOV patch" arc ended in the best possible way: **no game-code
patch is needed at all.** Cruis'n Exotica already renders a full 16:9
field of view; the black margins were self-inflicted.

The hunt (in order, each step narrowing the truth):
1. **MIDZ_PCLOG** (new env-gated diag in zeus2.cpp): histogram of game-CPU
   PCs submitting FIFO commands. Result: ALL 603k model draws come from PC
   0x0B686 — an IRQ handler draining an 8K-word circular command ring
   (read ptr $046D, write ptr $046E) to the Zeus FIFO.
2. **MIDZ_RINGTAP** (new env-gated diag in midzeus.cpp machine_start):
   RAM write tap cataloguing PCs that write 0x24xxxxxx draw-model headers.
   Found the ring-fill library (0x067F2-0x06D03), the HUD sprite list
   builder (0x0E400/0x0E426, screen-center 256/200 convention), and that
   all queue routines are dispatched via function pointers (zero static
   callers — why static xref hunting kept failing).
3. **The decisive measurement** (should have been step 1): column-occupancy
   of the capture-zeus-race quads across a 688-wide canvas. Left margin
   ~40 quads/column, right margin ~90-136 (center ~200). A painter's-order
   flatten showed coherent terrain/horizon/scenery continuing seamlessly
   through both margins. **The game submits a wide world; there is no 4:3
   cull to widen.** (The C3x disassembly's CMPF-0.5 sites were RNG rolls;
   the CMPF-200.0 "clip" candidates were audio-pan distance tests.)
4. Live-path repro: MIDZ_GL_SNAP sweep showed margins 0.0% lit on every
   present while offline said they should be full → the drop was OURS.

**Root cause:** the mzgl canvas holds BOTH page-flip buffers (1024 rows;
present selects the visible band via uBaseRow), but the 16:9 margin clear
that rides the game's frame-sized fast-clear used a full-height scissor.
Every frame start, clearing the DRAW page's margins also wiped the
DISPLAYED page's margins — so margins were black except for the sub-ms
between flip and the next clear. The center survived because the game's
own clear (add_span) is page-scoped.

**Fix (zeus2.cpp):** scope the margin clear to the cleared page's rows
(row0 = addr/CW, nrows = count/CW), mirroring add_span. One scissor change.

**Verified:** attract sweep after fix: margins 75-100% lit in every 3D
scene (were 0.0%), 2D screens still 4:3, hysteresis intact. Tunnel race:
road + lane markings + tunnel lights span edge-to-edge; showcase close-up
fills full width. Proof: results/proof/zeus-true-169-tunnel.png,
zeus-true-169-showcase.png.

Kept for future work: MIDZ_PCLOG, MIDZ_RINGTAP, MIDZ_PATCH (in-memory
code patcher, built + tested inert — ROM files untouched), and the full
TMS32032 disassembly at results/crusnexo-prog.asm (8.7MB, regenerable via
MAME debugger dasm). These are the toolkit for C2 (render distance) and
any future game-code experiments.

## 2026-08-23 — Telemetry B1: World speed hunted + wired (session 9, cont.)

Reusable speed-hunt method (now proven across two games):
1. `MIDV_RAMDUMP_DIR` + `MIDV_RAMDUMP_EVERY=30` over a ~240s attract demo
   dumps the 0x20000-word DSP RAM. Attract drives the player car through
   several full races (5 accel segments), so speed shows as a repeated
   0→top→0 curve.
2. Offline (results/ramhunt-<rom>): decode each word as C3x float across
   time, keep words that (a) sit at ~0 between races, (b) rise smoothly to
   80-500 with |Δ|<45/dump, (c) do this in ≥2 races.
3. Disambiguate speed from same-shaped junk by the **odometer partner**:
   a neighbouring word (±0x40) whose per-dump DELTA correlates (windowed,
   >0.96) with the candidate's value — distance = ∫speed. This signature
   self-validated on crusnusa 0x0F22D (partners +6/-56, corr 0.997) and
   rejected all drone/HUD lookalikes.

crusnwld: the hunt returned a clean 10-field cluster (stride 0xB0, all
0→~285 with odometer partners at fixed offsets) — one car's physics state,
not 10 cars (identical segments/on-screen-fraction across all 10). Wired
the mid-cluster field 0x0DDDC. End-to-end verified: MIDV_TELEM_UDP emits
0→277 per demo race (53% nonzero). **Open:** one wheel check to confirm
0x0DDDC is the speedometer field and not a wheel-speed / velocity-component
sibling (they diverge only under wheelspin/slide; steady-state identical).

offroadc: same pipeline found NO clean speed curve in its attract demo —
candidates either spike-to-max-and-drop (per-scene latches) or read as
signed velocity components (go negative). Needs the on-screen-MPH
correlation pass at the wheel to pick the player slot. Left at 0
(telemetry-off) rather than wire a guess.

Also tightened s_speed_addr to hunted PARENT romsets only (removed the
dead, typo'd crusnu40/crusnu21 clone entries; clone builds can relocate
DSP RAM, so unlisted games get telemetry-off instead of an unverified
address).

## 2026-08-23 — B2 RPM hunt: leading candidate, needs on-screen tach (session 9)

Re-ran the crusnusa attract with a FINE dump interval (MIDV_RAMDUMP_EVERY=3,
~1738 dumps over 90s) because RPM's sawtooth is faster than the 30-frame
speed-hunt cadence could resolve (a gear shift is well under 0.5s; the
coarse dumps aliased right past it).

Leading RPM candidate: **0x0F0C0 (mirror at 0x0DB67)** — bounded 1.1-1.54,
present through the race, and it DOES step-drop at shift points
(1.32 -> 1.12 exactly where the gear changes), which speed does not. Both
copies are bit-identical (engine writes two mirrors).

Not wired, deliberately. Two unresolved concerns make it unsafe to emit:
1. It sits FLAT at ~1.20 while speed climbs 4->176 (first gear); true RPM
   tracks speed linearly within a gear, so this is not cleanly proportional.
   It may be a gear-normalized or redline-clamped quantity, not raw RPM.
2. No independent cross-check exists for RPM the way the odometer partner
   nailed speed, and the 90s fine capture caught only one full race.

Verdict: same class as offroadc speed — needs a one-glance on-screen
TACHOMETER correlation at the wheel to confirm 0x0F0C0 is the tach (and to
recover its scale). Until then B2 stays unwired rather than stream a
possibly-wrong value. Tooling (MIDV_RAMDUMP_DIR + the sawtooth/within-gear
detector) is turnkey for the confirming pass.

## 2026-08-23 — B5 sky-margin streak polish (session 9)

The 16:9 margin-extend (clamp-stretch of the 4:3 boundary column) smeared
the sky's per-row cloud/dither detail into horizontal streaks across the
synthetic margins (all 3 V-Unit games). Fixed in the present pass
(gpu/renderer.py fetch_smooth): margin-region UNWRITTEN pixels get a wide
vertical gaussian blur (radius ~height/24) instead of the single clamped
tap. A stretched sky should be a smooth gradient, so this is faithful; the
horizon (sky->terrain) blends over that span as soft atmospheric haze
rather than a hard streak line. Real geometry is one tap as before.

Safe by construction: the whole thing is gated on uMargin>0, which is 0 in
exact / 4:3, and the present pass never feeds the exact comparison (that
reads the index buffer). Re-verified exact mode 100.0000% on capture and
capture-8000 anyway. Header regenerated (gen_shaders.py), rebuilt, live
overlay runs err=0. Before/after: results/proof/vunit-sky-margin-smoothing.png.

## 2026-08-23 — B3 volume: measurement pass (session 9)

Captured 45s of each game's attract audio headless (-wavwrite, results/
audio-levels) and measured RMS/peak/active loudness to make any volume fix
data-driven rather than a blind CMOS poke.

Findings:
- **V-Unit trio (USA / World / Off Road) are mutually CONSISTENT**: active
  loudness ~-33 dBFS on all three (attract is ~95% near-silence; the sound
  effects that do play sit at the same level). No cross-game normalization
  needed among them. They are quiet in ABSOLUTE terms (peaks ~-23 dBFS),
  matching the user's "volume low" note - but that's the native attract mix;
  raising it means the game's internal/CMOS volume (or the amp), not a
  renderer knob.
- **Exotica captured as DIGITAL SILENCE** (0 non-zero samples of 4.3M,
  stereo 48k) even though the user clearly hears it at the wheel. So the
  headless attract can't measure it. Most likely ATTRACT SOUND is off in
  its CMOS (a standard operator setting - the user hears audio because
  they're coined up and driving, not watching attract), or a DCS-headless
  quirk. Either way the "Exotica quieter" question can't be answered
  offline.

Conclusion: no safe autonomous action. The V-Unit trio needs nothing.
Exotica's volume (and whether attract sound is simply disabled) needs a
one-time service-menu (F2) pass at the wheel - then bake the CMOS into the
fixture (nvram_tool.py flow ready). Blind CMOS pokes risk the games'
NVRAM checksum. B3 reclassified as needs-the-wheel for Exotica.

## 2026-08-23 — B2 RPM CONFIRMED + wired (crusnusa), via a real drive (session 9)

The user drove crusnusa ~180s (capture_drive.py, RAM dumped every 6 frames,
1771 dumps). That real gameplay data settled B2:
- **Debunked the attract candidate 0x0F0C0**: near-zero during real driving
  (it was an attract-mode-only value, like 0x0F17A). Good that it wasn't
  wired.
- **Confirmed 0x0DC20 = engine RPM / tach.** Speed-anchored hunt on the
  drive (rpm must track speed within a gear and DROP at shifts while speed
  continues): 0x0DC20 tracks speed*~2.85 through acceleration, then shows a
  sharp V-dip exactly at the Lo->Hi gear shift while speed stays pinned -
  the tach signature speed can't have. Confirmed on the plotted full drive
  (results/rpm-plot-DC20*.png: the first run's shift-dip is unmistakable).
  Observed 0..912 (redline ~900; attract spiked to ~1371).

Wired as "rpm" over MIDV_TELEM_UDP alongside speed; verified end-to-end in
attract (6514 datagrams, tracks speed, dips together at slowdowns). Emitted
in raw game tach units (like speed's raw units) - downstream (SimHub/
Buttkicker) scales.

Method note for World/Off Road RPM: same one-command drive
(harness/capture_drive.py <rom>) + the speed-anchored shift-dip hunt. Their
RAM layouts differ so each needs its own capture; crusnusa proved the method
end-to-end.

## 2026-08-23 — Telemetry Phase C: SimHub-native Forza packets (session 9)

The JSON stream was never SimHub-consumable without custom work - SimHub's
Forza profiles listen for Forza's binary "Data Out" packet. So the emulator
now speaks it natively: MIDV_TELEM_FORZA=host:port emits the FH4/5 324-byte
packet per frame (IsRaceOn, timestamp, EngineMax/Idle/CurrentRpm - game
tach units x8, clamped at redline 7500 - forward velocity + Speed in m/s,
gear byte). SimHub / dash apps / bass-shaker profiles read the game as
Forza Horizon with stock profiles.

Config: collection.ini [telemetry] forza=host:port (or "on" = 127.0.0.1:5300);
rig set to 127.0.0.1:8000 (the user's SimHub FH6 page listens there). If
the FH6 parser rejects the legacy 324-byte layout, pick Forza Horizon 5/4
in SimHub instead (that IS our packet) and match its port in collection.ini.

Verified headless: 3476/5794-packet runs, all 324 bytes, RPM sweeps
0->7500 (clamped), speed to 301 mph across attract demos. JSON stream now
only emits when MIDV_TELEM_UDP is set (Forza-only mode works alone).
Currently real data = crusnusa speed+rpm, crusnwld speed; other fields
zeroed until hunted.

## 2026-08-23/24 — The telemetry ground-truth saga (session 9, late night)

The SimHub dash misbehaved through every fix attempt; each user test
falsified another hypothesis until the real story emerged. Chronicle:

1. **Emit format**: SimHub reads Forza's binary "Data Out" packet, not our
   JSON. Built the FH4/5 324-byte emitter (Phase C, above). Dash moved but
   read wrong.
2. **Diagnostics built**: forza_probe.py (live decode of our packets +
   CSV timeline; proved the emit side repeatedly), forza_synth.py
   (synthetic drive straight to SimHub; proved SimHub + the profile +
   packet layout end-to-end - dash tracked all four signals perfectly).
3. **Menu garbage**: outside races the drone words held junk (speed ~990
   -> pegged the dash speedo at dial max; the reported "stuck at 210").
   Added plausibility + freshness gating. Helped, still wrong in-race.
4. **The drone revelation**: the user's probe CSV showed emitted speed
   frozen bit-exact at 246.8 for 45s while rpm lived, and the tach
   sweeping through shifts while their HUD gear sat in 4th. Conclusion:
   **the attract-hunted addresses (crusnusa 0x0F22D speed, 0x0DC20 rpm,
   and by method crusnwld 0x0DDDC) track DRONE cars.** Attract demos are
   drone-driven - shape-hunting them can never find the player.
5. **The stop fingerprint**: user drove 4-5 accelerate-to-full-stop
   cycles. NOTHING in external RAM matched (c3x/int/16-bit/bytes, values,
   magnitudes, vector pairs, derivatives; detector validated on synthetic
   data). Exposed + dumped the second RAM bank (0x400000, never captured
   before): nothing. Dumped the C31's on-chip internal RAM (0x809800, 2K
   words): nothing. **The player's displayed speed persists in NO memory**
   - computed transiently each frame.
6. **HUD ground truth**: added hud_*.bin dumps (visible-page rows 300-399)
   and OCR'd the on-screen MPH digits (glyph clustering + 7-seg-adjacent
   labeling; the narrow "1" needs min-cell-width 2, and 3-digit reads drop
   their leading 1 intermittently - readings >99 must be
   continuity-verified). 827/1205 frames decoded of the user's final drive.
7. **RPM FOUND AND CONFIRMED**: rank-correlation of the OCR speed against
   every word surfaced 0x0E632.lo16 (rho .83); its profile is a tach
   (pegged at cruise, sawtooth up the gears, idle at stops); and the
   clincher - the HUD RPM GAUGE's fill-pixel count correlates **r=+0.91**
   with it. **crusnusa player RPM = 0x0E632 low 16 bits, raw 0..~14650.**
   Wired (RpmAddr now carries format + per-game Forza scale). Speed
   entries all zeroed until the proper fix lands.
8. **The proper speed fix (in progress): the HUD-quad DMA tap.** The MPH
   digits are textured quads through process_dma_queue; the digit identity
   is in the texcoord bytes (dma_data[10..13]) at queue time. Read the
   digits at the source - correct by construction, works for all three
   V-Unit games. Calibration = align MIDV_QUADLOG quads in the MPH box
   with OCR'd HUD dumps (crusnwld attract shows the MPH box, so World
   calibrates headless; USA needs one short user drive or the shared font
   mapping).

Also this session: ForzaKeeper in the shell (zeroed packets whenever no
game runs - SimHub freezes on last values otherwise; keeper packets MUST
carry sane EngineMaxRpm/Idle, an all-zero packet wedges SimHub),
multi-target MIDV_TELEM_FORZA (SimHub + probe simultaneously), rig
telemetry on port 8000.

**Margin-fill regression CONFIRMED AND FIXED**: the user's phone photo
from the first widescreen nights proved the original clean look - the
V-Unit games draw nearly the full 16:9 natively and margins showed real
geometry, no fill. The clamp-stretch margin-extend (added later, default
on) caused the reported edge smearing. MARGIN FILL is now a SETTINGS row
and defaults OFF everywhere. (Their photo also proves the dithered
billboard rectangles are original game pop-in - C2, not a regression.)

## 2026-08-24 — HUD OCR speed SHIPPED (autonomous block)

Postscript to the saga: the DMA-tap plan died on arrival - the entire
1.6M-quad World rig capture contains ZERO digit-sized quads; the V-Unit
HUD is CPU-blitted into videoram, not queued. (Attract in USA AND World
hides the MPH box, so no headless calibration for other games either.)

The final answer is runtime HUD OCR inside the emulator: each frame,
read the visible page's MPH box and match the glyphs against 10 baked
digit templates (midvunit_hud_ocr.h, generated from the user's
calibration drive). The exact C++ algorithm (simple bilinear 12x18 + L2
nearest template, reject >0.035) was mirror-validated offline first:
822/823 frame agreement with the reference OCR. Blip suppression
(>25mph jumps need 2 frames) + missing-box decay to 0. crusnusa wired;
World/Off Road need one gameplay HUD capture each to pin their box
coords + confirm the shared font.

ALSO CONFIRMED autonomously: crusnusa RPM 0x0E632.lo16 vs the on-screen
tach gauge fill, r=+0.91 (existing capture data - no drive needed).

Verification state: attract emits 0/0 correctly (no box, no player).
IN-GAME verification = the user's next normal drive with SimHub: the
dash should now read exactly what the screen reads.

## 2026-08-24 — FIRST game-code widescreen on V-Unit (offroadc right edge)

See docs/widescreen-research.md for the full write-up. Summary: located
offroadc's TMS32031 poly clip/cull screen-bound table ($11235 = x-max =
511, read at 10 clip sites), widened it to 597 via MIDV_PATCH (ROM
untouched). Result: 4:3 content bit-identical (center quads 430674 both
runs - projection unchanged), right margin gains real geometry (+19%
quads, an opponent vehicle + canyon revealed - proof/offroadc-gamecode-
widescreen.png), 120s stable. patch/game/offroadc-widescreen.txt. This is
the "proper Hor+" the A2 research chased, proven viable. Left/top edges
(sign-tested min bounds) need a small code patch for full symmetry;
crusnusa/crusnwld need their own bound-table hunts (same method).

Try it live: MIDV_PATCH=<repo>/patch/game/offroadc-widescreen.txt
python harness/run_rig.py --rom offroadc

## 2026-08-24 — Game-code widescreen SHIPPED (rig-verified)

The user drove offroadc with the widened clip live: "looked great" - right
margin fills with real geometry, no gameplay side effects observed.
run_rig now auto-applies patch/game/<rom>-widescreen.txt at 16:9 FULL
(the ASPECT setting is now the real mechanism switch: 4:3/TRIMMED skip
the patch). Exotica needs nothing (native wide via the Zeus chip).
Remaining: crusnusa/crusnwld bound hunts (their clip structure differs
from offroadc's [0,511] table - likely centered coords; needs their
program disassembly), offroadc LEFT edge (sign-test code patch), and the
attract-showcase corner boxes (game composes sky 4:3-only there; B5).

## 2026-08-24 (late) — offroadc LEFT edge SOLVED: game-code widescreen on BOTH sides

Fresh-eyes session on the left-margin sky-through-ground wedges (the one
artifact the right-edge patch left behind). Full analysis in
`docs/offroadc-left-edge-handoff.md` (RESOLVED section); summary:

**Why right ≠ left.** The nine poly-emit loops do four trivial-reject tests
(no per-poly screen clip; the rasterizer clips). The right test subtracts
the vertices from a table constant (`$11235`, the word we widened). The
left test ANDs the four X values and rejects on the sign bit — "all four
x < 0" — with no constant anywhere. So the right could be widened with one
data word; the left had nothing to widen, and every ground/wall quad whose
right edge fell short of x=0 kept being discarded. The previous session's
"0 quads with max_x < 0 ⇒ nothing is culled" reading was a tautology:
rejected quads never reach the DMA stream.

**Fix (patch/game/offroadc-widescreen.txt, 21 new words).** Each site's
`BLTD <exit>` becomes `CALLLT $2224` into a 12-word routine in unreachable
alignment padding (28 NOPs after `BU $2240`) that re-tests `x + 86` on all
four vertices and, on reject, loads R1 (the x-max bound the site tests
next) with INT_MIN so the site's own right-edge test discards the poly.
One routine serves all nine sites without knowing their exits or return
points; the not-rejected path is untouched. Mirrors the right exactly:
reject only if all four x < −86.

**Measured (attract oracle, frame 3398, frames < 3397 as multisets):**
- records removed vs the right-only build: **0** (centre + right identical)
- records added: **36,011** — 36,003 with bbox in `[-86, 0)` (the exact
  class the game discarded) + 8 with a vertex at x = 0 it over-rejected
- artifact frame, bottom-half sky-blue: left **5.5 % → 0.0 %**, right
  0.0 % → 0.0 %; proof `results/proof/offroadc-left-edge-FIXED.png`
- the naive alternative (NOP the nine branches = reject never) was
  measured and rejected: +70,628 records, 34,569 entirely off-canvas, and
  42 wrapped through the 16-bit DMA port (game-space x < −32768 → strip at
  x ≈ 10k–32k) — on-screen garbage waiting to happen. The mirror cannot
  emit such a quad (a kept quad touches −86; the game subdivides extents
  ≥ 0x800).
- exact mode: capture + capture-8000 both still 100.0000 % (no renderer
  change; the margin cover/extend paths stay OFF)
- loader "22 applied, 0 skipped"; attract stable to frame 12000

**Pending:** the user's live drive (attract can't load the subdivider or
stack the way a race does). Same wiring as the right edge: 16:9 FULL
auto-applies the file.

## 2026-08-24 — v0.2.0 cut

User verdict on the both-edges Off Road widescreen: "not perfect but
honestly the closest we've gotten to perfect this whole campaign." Shipped:
`CHANGELOG.md` (everything since v0.1.0), `docs/release-notes/<tag>.md`
now feeds the GitHub release body (workflow step), README status
refreshed. Tag `v0.2.0` → CI builds MAME 0.286 + the 57-patch series from
scratch (patch hash changed since v0.1.0, so no cache hit) and publishes
the zip. Remaining Off Road imperfections go on the minor list.

## 2026-08-24 (post-v0.2.0) — the user's minor list: four fixes in one pass

User's live drive after v0.2.0 flagged four issues; all root-caused and
fixed the same night (pending their next drive; batch = v0.2.1 candidate).

1. **Windows "ding" at (re)launch** — Event Log showed EVERY vunit exit
   tonight AV'ing in teardown (9 Application Error + WER pairs, 8:21-10:19
   PM): the FFB plugin's dinput8.dll detach race, with the round-4
   SetErrorMode suppression evidently reset inside the process. Real fix:
   env-gated MIDV_FAST_EXIT (winmain) — after the frontend returns cleanly
   (cfg/nvram written), fflush + TerminateProcess so DLL_PROCESS_DETACH
   never runs. run_rig sets it; captures don't. Smoke: the frame-300
   headless run went exit 0xC0000005 → exit 0, and teardown drag 7.5s → 3.1s.
2. **Exotica launches unfocused (click to fix)** — instrumented probe:
   direct-launch holds fg from t=0 for 55 s straight, so the failure is
   shell-path-specific (Exotica alone skips make_fullscreen, so it has no
   strong activation event if the shell/overlay interleaving goes wrong).
   Fix: session-long focus watchdog in run_rig — if the foreground lands on
   OUR OWN ecosystem (shell process / GL overlay popup / null), reclaim for
   MAME; a real alt-tab to another app is never fought.
3. **World: bound-to-Radio button fired on the wrong input** — real bug in
   WHEELMAP_PORTS since the wizard shipped: V-Unit is Radio=BUTTON1,
   View1-3=BUTTON2-4 (midvunit.cpp), our table had view1=BUTTON1...
   radio=BUTTON4 (all shifted). Fixed; Exotica's table was already correct.
4. **World: black dithered "texture" floating at the right edge** — it's
   the RADIO PANEL (dithered translucent box + red/white station dots), a
   screen-space UI element that PARKS fully off-screen at x 544+ and
   slides in when Radio is pressed (attract timeline: parked x 600-700 f
   1304-1568, slides 544→470 f 1569-1611, deployed on-screen x 400-470 f
   1613+). The hardware raster crop hid the parked position; our 16:9
   margins revealed it. Fix: meta bit 2 in the vertex builders (python +
   C++) — untextured AND fully right of x=511 AND y 60-260 AND (dithered
   panel OR ≤8px dot) → shader discards. Wide builds only. Verified:
   flag-render pixel-identical to physically removing the records
   (100.0000% on the parked frame), USA margin traffic unaffected (naive
   rule matched 193 moving car quads — refined rule 0 on that capture, 244
   ≤8px specks on 71/7084 frames of capture-8000), offroadc 0 matches,
   exact mode 100.0000% x2. Deployed/sliding panel still renders (it
   straddles x=511) — matching original timing.

Also: FFBPlugin.ini Logging=1 had grown FFBlog.txt to 15 MB — set back to 0.

## 2026-08-25 (small hours) — translucency done right + the ding, round two

**v0.2.0 published** (CI success, CruisnCollection-v0.2.0.zip, 04:10 UTC).

**"Black textures" root cause, final:** the user's new Germany screenshots
(flag-girl backboard at the start line, deployed radio panel, ELAPSED
TIME/MPH boxes) revealed the real story - those are the hardware's
TRANSLUCENCY, faked as a per-pixel dither checkerboard that the CRT
blended into smoked glass. Our renderer applied that mask in COARSE pixel
space, so at 4x internal every dither cell became a 4x4 black block. Fix:
the scene shader now masks at FINE pixel granularity in the same y-down
space as px/py (at scale 1 the fine coords ARE px/py, so exact mode is
bit-identical by construction - first attempt used raw gl_FragCoord,
inverted the checkerboard phase via the y-flip, and the invariant caught
it at 99.84%/99.10%; fixed, re-verified 100.0000% x2). The crack-filler
learned the 1-px checkerboard signature (all four axis neighbours written,
all four diagonals unwritten = translucency, never fill). Offline s4
render: HUD boxes and the radio panel read as uniform smoked glass with
the scene visible through them. The parked-position suppression (earlier
tonight) stays - hardware showed nothing there.

**Ding, round two:** the user still heard it on FIRST launches, so the WER
theory only covered exits (fast-exit did eliminate those: the probe exit
logged ZERO new Application Error events vs one per exit before). New
lead: a dialog watcher during a live launch found a "Game Controllers"
(joy.cpl) panel open since Aug 20 23:12 - spanning every dinging session -
and our enforce_foreground tapped a synthesized ALT into the foreground
window every 500 ms while MAME wasn't foreground yet. An ALT landing in a
menu-less dialog rings the system ding. enforce_foreground now uses the
silent AttachThreadInput unlock (ALT only after 6 failed cycles), and the
user should close the stray joy.cpl. Verdict pending their next launch.

## 2026-08-25 — Cruis'n World sky: game-code widescreen no. 2

The user's "black area in the very corner - clearly the sky not rendering"
is fixed game-side. World tiles its sky (three 256px panorama tiles,
streamed raw to the quad DMA port - no cull anywhere) sized for the 512px
hardware screen; 689 of 1047 attract sky frames left a left-margin gap and
232 a right one (worst: sky ends at x=506 → 92px of black). The engine at
$9623 now draws FIVE tiles from one tile further left (bank-wrap table
extended in unreachable padding, saved-centers array relocated, all three
loops RC=4, horizon fill widened): coverage [phase−388, phase+888] covers
the 16:9 canvas at any yaw. England test frame: corner black 40.0% → 0.1%,
seamless clouds; centre pixel-identical (modulo ~6 edge columns the
original left black under CRT overscan); zero records removed. Details in
docs/widescreen-research.md; auto-applies at 16:9 FULL via the existing
patch/game/<rom>-widescreen.txt mechanism. The hunt tools that cracked it:
work-RAM descriptor search in the telemetry RAM dumps, then a direct-
addressing grep ($D5xx) - the MAME-debugger watchpoint runs were too slow
and unnecessary in the end. Remaining World work: terrain-side cull (its
reject code differs from offroadc's - no signature match; future hunt).

## 2026-08-26 (overnight) — telemetry speed: World calibrated, Off Road provisional

B1 HUD-OCR expansion from the user's evening drive captures:
- **Ported the in-emulator OCR to python** (same bilinear 12x18 + L2 vs the
  baked templates; self-test on the USA calibration drive: 82/121 frames
  readable, clean accel traces). One parser trap: the template header's
  `// '0'` comments poison a naive digit regex - strip comments first.
- **crusnwld: MPH box (14,76,342,368)** found by rendering race frames from
  the drive dumps and grid-scanning candidate boxes with the OCR itself.
  USA's digit templates read World's digits AS-IS (shared font confirmed).
  Validated trace over the drives: 0→97 mph with physical accel/decel.
- **offroadc: the MPH box is at the TOP of the screen** - outside the
  rows-300-399 hud dump window (why the drive dump showed no digits).
  Provisional box (228,270,22,52) derived from the user's 4x screenshot
  geometry; safe because the runtime OCR rejects unreadable frames. The
  RAMDUMP hud window is now per-game (offroadc rows 0-99) for offline
  validation from the next drive.
- **World RPM (B2): attempted, inconclusive** - the volume-session drives
  had too much menu time (7 aligned race frames) and the tach-arc metric
  needs recalibrating. Logged the exact capture protocol needed.

## 2026-08-26 (overnight, late) — World terrain cull widened; C3 code complete

The remaining World margin voids (cow corner, crash cams) are now patched
game-side. Key enabler: MIDV_DMA_PCLOG (native emit-PC logger on the quad
DMA port; patch series 61) after two debugger-watchpoint attempts proved
hopeless at ~0.03x. World's 3D loops emit UNCULLED (backface only) - only
the big-poly subdivision path screen-rejects (sign-bit left, immediate
511 right), and its dropped sub-quads were the holes. Patch: 4 immediates
-> 597, 2 sign-branches -> CALLLT x+86 routines in padding. Verified: 0
records removed anywhere (frames 1900/2002 + full 12000-frame attract),
centre pixel-identical, +134 margin-only records over the full run.
Awaiting the user's live drive (crash cams are where it shows). Also this
wave: volume CMOS map all four games (no checksums; nvram_tool poke),
World speed OCR shipped, G2/G4/G8 fixes, settings redesign proposal.


## 2026-08-29 - World manual transmission: the answer was the ROM revision (rev 2.4 port)

The World shifter mystery is closed, and it was never a config problem.
**Cruis'n World rev 2.5 - the parent set MAME boots by default - removed
transmission select entirely.** The factory ROM labels in the 2.5 set read
`2.5_cruisn_world_automatic_u10` ("automatic" is Midway's own name for the
revision); a 2018 r/MAME thread the user surfaced confirms it (rev 2.4 is
the last revision with shifting options). Every CONF/DIP finding from
2026-08-25..28 was correct - H-Pattern raw pass-through, Sitdown cabinet
DIP applied and persisted - aimed at a game with the feature deleted.

Port of the widescreen patch to crusnwld24 (rev L2.4):
- Program images are 96% identical; ROM word offset == program-RAM word
  address (identity mapping, verified via the sky bank table).
- All 34 terrain/big-poly lines are **address-identical** in 2.4.
- The sky engine cluster moved **+0xB words** (table 95F1->95FC; pointer
  95F0->95FB, 255.0 float 95F9->9604, phase ops 9651/96BD->965C/96C8, tile
  counts 9657/96BF/97E5->9662/96CA/97F0, horizon quad 9689/968B->9694/9696).
  Saved-centers pointer value D539->D53F (+6 data shift). Four OLD words
  embed shifted addresses and were fixed up; every one of the 54 lines was
  verified against the interleaved 2.4 ROM image before shipping.
- Live check: `MIDV_PATCH` on a crusnwld24 boot logs **54 applied, 0
  skipped**.
- `crusnwld24` in the shipped romset is "best available" (known BAD_DUMP
  `c31boot.bin` -> red warning screen; `MIDV_SKIP_STARTUP_SCREENS` already
  handles it). Headless boot verified (reaches CALIBRATE CONTROLS; headless
  always re-demands calibration, expected).

Rig wiring:
- `patch/game/crusnwld24-widescreen.txt` (auto-applied by run_rig at 16:9
  FULL, same as the 2.5 file).
- run_rig: `base_rom()` normalization - clone revisions inherit the
  parent's SHIFTER_CFG (CONF H-Pattern + Sitdown DIP: the whole point),
  STEER_PORT, GAME_HEIGHT/GAME_MARGIN. Wizard wheel bindings already lived
  in the ctrlr `default` section, so they apply to any system name.
- collection: the CRUIS'N WORLD card now boots `world_rom` from
  collection.ini (**default crusnwld24**; set `world_rom = crusnwld` to
  return to 2.5). Settings keys and art stay on the crusnwld card identity.
- midvunit_v.cpp telem_init: table lookups are prefix-matched so
  crusnwld24 keeps World's HUD-OCR speed box (screen-space, rev-safe;
  all World RAM-address rows are 0, so nothing rev-specific can misapply).

Caveats to verify at the wheel:
- First 2.4 boot: one-time CALIBRATE CONTROLS (2.4 initializes its own
  CMOS - the 2.5 NVRAM doesn't carry over), then volume / free play need
  setting once for 2.4. The 2.5 CMOS byte map (volume 0x9C, free play
  0x1AC) may sit at different addresses in 2.4 - recalibrate the map from
  the new nvram before poking.
- The 2018 thread reports MAME rendering artifacts in 2.4 that 2.5 lacked.
  That was 2018-era MAME *and* our renderer replaces the rasterizer
  entirely - watch for artifacts on the first drive; the oracle can
  quantify 2.4 once a calibrated NVRAM fixture exists (copy
  rig/nvram/crusnwld24 to fixtures/nvram-crusnwld24 after first boot).


## 2026-08-29 (later) - volume bytes pinned, menu redesign, sequential paddles

Wheel-session verdicts: World rev 2.4 = **manual transmission working**
(G7 truly closed); NY margin wedges still visible (C3 stays open for a
dedicated session); Off Road and Exotica volumes were NOT at max - the
user maxed them at the wheel, and the nvram diffs against the 2026-08-26
snapshots pinned the real masters:

- **offroadc nvram 0x2FC = master volume, 0-255** (0xC8 -> 0xFF on
  menu-max; the earlier 0x7BC/0x92C candidates moved with play stats).
- **crusnexo m48t35 0x27 = master volume, scale 0-30** (0x0C -> 0x1E).
- crusnwld 0x9C reconfirmed (0x64 -> 0xFF); **rev 2.4's first-boot CMOS
  carries the same layout** - 0x9C volume, 0x1AC free play verified.
- crusnusa master still unpinned (in-game = / - keys meanwhile).

Shell menu redesign (G5, user's design) implemented:
- Game card ENTER opens a per-game submenu: PLAY (default row -
  ENTER-ENTER fast path preserved) + STEERING SENSITIVITY / CURVE +
  VOLUME + FREE PLAY (direct CMOS edits via the pinned bytes, cached
  reads, "AFTER FIRST PLAY" before a game's NVRAM exists) + for World a
  GAME REVISION row toggling world_rom 2.4/2.5. SETTINGS row is now
  global-only (CRT, crack fill, aspect, margin fill, FFB, controls).
- Steering wheel + gas navigate all menus (feature request): steer =
  left/right on cards, up/down in lists (0.5 enter / 0.3 exit hysteresis,
  0.45s then 0.28s auto-repeat); gas = OK on press edge honoring the
  wizard's recorded pedal direction (center-resting Moza pedals safe).
  Disarmed alongside button input during game teardown; re-parsed after
  each wizard run.

Sequential/paddle shifting (B7) implemented natively:
- midvunit already has a Sequential CONF mode (5) with its own virtual
  gear (shift_button: Shift Down = P1_BUTTON5, Shift Up = P1_BUTTON6) -
  no input translator needed. Wizard gained skippable SHIFT UP / SHIFT
  DOWN steps; apply_wheelmap arbitrates the BUTTON5/6 collision between
  H-pattern gears and paddles (full H-pattern wins); apply_shifter_config
  writes CONF=0 or 5 accordingly. Exotica (Zeus) has no sequential mode -
  paddle-only rigs keep automatic-select there.


## 2026-08-30 - wizard >32-button capture dead on re-entry (rawjoy fix)

User report after testing the new menus: Start / Test / Service (Moza
buttons 33-35) would no longer bind in the wizard - "back to the
32-button cap". Root cause was in rawjoy, not the redesign's code: the
`CruisnRawJoy` window class was registered with the FIRST
RawButtonListener instance's wndproc, and a Win32 class registration is
process-global and permanent. The listener is wizard-scoped
(created on CONTROLS SETUP entry, stopped on exit), so every wizard
entry after the first in one shell session created its raw-input window
with the dead first listener's callback - its own queue could never
fill. glfw binds (buttons <=32) kept working, raw-only binds (>32) went
silently deaf. The old flow (one wizard run per shell launch) never
re-entered; the redesign session's menu-wandering did.

Proved live on the rig with the wheel powered (axis chatter as signal):
listener #1 received 2304 raw events in 2 s, a re-created listener #2
received **0**, and GetWindowLongPtr showed #2's window proc == #1's
callback address. Fix: module-lifetime WNDPROC dispatcher routing
WM_INPUT to the currently-active listener (`rawjoy._active`, last one
wins), registered once; stop() clears it and is idempotent. After the
fix three consecutive create/stop cycles each received the full stream
(2307 / 2282 / 2333 events per 2 s).

Note: the rig's saved [wheelmap] still carries the good pre-redesign
bindings (start=btn:34, test=33, service=32) and no shiftup/shiftdn -
the failed re-bind attempt never completed, so nothing was overwritten
and in-game Start/Test/Service were never at risk. Paddle binding still
needs one full wizard run.


## 2026-08-30 (later) - continue-screen vertical line: root-caused + fixed

User report: a vertical black line on crusnusa's PRESS START TO CONTINUE
map after playing a round. Root-caused end-to-end and fixed at the
source; the G4 offroadc track-select lines share the same root cause.

**New capability unlocked along the way**: `lua/coinup.lua` - scripted
COIN1/START1 injection via ioport `field:set_value()`, which WORKS
headless (`-video none`). The parked transmission_probe's "inputs don't
land" verdict was a script bug, not an API limit - its snapshots didn't
land either. Gameplay-only screens are now capturable unattended: 3
coins ("3 CREDITS TO START") + START at deterministic frames rides
through transmission/car/track select, races idle to TIME EXPIRED, and
lands on the continue screen (~frame 8600-9400 of the scripted run).
This also unlocks future NY-wedge (C3) captures.

The hunt (all headless):
- Attract sweep (41 snaps): the US map screen never appears in attract -
  gameplay only.
- MAME native snapshot of the continue screen: NO line. Ours: line.
- `results/capture-continue` (new instrumented capture at frame 8798):
  exact mode = **100.0000% bit-exact** - the FIRST verified 2D scene
  (fourth verified scene overall).
- Offline quality mode reproduced the line after all (a blue seam my
  first darkness-only column scan missed - detector error, not absence);
  live repro via MIDV_GL_SNAP + coinup showed the same seam blue (the
  user's black = their entry-transition page content; the seam color is
  whatever lies under the tile gap).
- Geometry: the map is drawn as ~128px-wide tiles (x1..129 | x130..256)
  over a full-screen base quad. Hardware DDA fills endpoint pixels
  INCLUSIVELY - tile A owns column 129, tile B owns 130, no gap.
  Quality mode's continuous coverage ends at vertex CENTERS: columns
  129/130 each get half-covered and the base quad grooves through as a
  1-hw-px seam (proven with a 2-tile synthetic render: 4,4,2,2,4,4
  fine-px coverage around the boundary).

Fixes (mame-src 200e986e; renderer.py is source of truth for the python
side, no shader changes):
- **dilate_rect / _dilate_rect(+fast)**: strict axis-aligned rectangles
  get every side expanded to the pixel's OUTER edge (0.5 + 0.001 tie
  guard) in QUALITY mode only - coverage now equals the hardware DDA
  span; adjacent tiles partition fine pixels with no gap and no
  overlap. Exact/DDA mode untouched by construction.
- **complete_run merge**: the game writes page_control every frame but
  changes it every TWO on 2D screens, so one logical scene arrives as
  two runs (base+tiles / text) and skip-to-latest could drop the
  undrawn background half. Same-pc runs now merge instead.

Verified: exact mode 100.0000% x3 (capture, capture-8000,
capture-continue); scalar==fast vertex builders bit-identical; offline
wide+crackfill+CRT seam gone; live overlay re-run clean on the continue
screen AND mid-race 3D; patch series refreshed.


## 2026-08-30 (later) - C2 render distance: research round 1 (crusnusa)

Deep-RE session while the user was away. No lever found yet - but the
object system is now MAPPED, the tooling grew a major capability, and
one attractive hypothesis was properly falsified.

**coinup.lua grew GAS injection** (`GAS_FRAME` env; ioport
field:set_value(0xff) on :ACCEL): the scripted run now coins up, starts,
AND DRIVES - 97 mph, place changes, full world streaming, all headless
and deterministic. This unlocks driven-gameplay captures generally
(offroadc track lines, NY wedges, telemetry hunts).

The render pipeline skeleton (found via MIDV_DMA_PCLOG + a scripted
debugger call-chain session; recipe below):
- 0x53C-area: quad packer (STI to *AR7=0x600000; FIX-packed verts).
- 0x140-0x166: per-object vertex transform + emit loop; 1/z LUT indexed
  by depth>>4, index clamped to 0x1387 (=5000 -> depth 80000 - the LUT
  and the 80000 constant were designed together).
- 0x91/0x166: linked-list object walker (node: +0 next, +1..3 pos
  floats, +0xD geometry ptr into maindata ROM, +0xE flags, +0x1C
  integer view depth, +0x1D per-object distance BIAS).
- 0x64: frame renderer - walks FOUR lists (page-0 vars 0x43,0x40,0x42,
  0x44; sentinels 0xC9B2-0xC9B7; rebuilt per frame, torn down after).
- 0x70BE: insert-object - computes view depth (dot with camera fwd,
  camera block at 0x809800/0x980F), stores +0x1C, depth-sorted insert;
  0x727F: per-frame migration between near/far lists with hysteresis.
- Node pool alloc/free at 0x7050/freelist ($C9B3); builder push caught
  live at PC 0x70DD.

**Falsified**: word 0x727E holds 80000 (companion 0x727D = 75000), read
by insert (0x70C6) and migration (0x7280) as the near/far threshold.
MIDV_PATCH applies cleanly (old-value verified). But patching it to
20000 AND 160000 produced BIT-IDENTICAL output (quad streams + native
snapshots) on attract AND on a driven race. The attract demo doesn't
even run the live object engine (node pool empty - likely canned
playback). In driven gameplay the pool holds ~200 nodes with depths to
~193k and ~82 far-flagged - yet rendering is unaffected by the
threshold, so the far flag must gate LOGIC (AI/activity?), not drawing,
or the far list is drawn by an unmapped path (DP-relative addressing
makes the list wiring ambiguous statically).

Debugger scripting recipe (worked, with caveats): `-debug -debugger
windows -log -debugscript <f>`, output via `logerror fmt~,args`
(NEVER argless), `wpset ADDR,1,w[,cond]` + chained `g` lines works
reliably; `gtime <long>` after boot-era is flaky (script silently
dies) - prefer wp+g. `-debugger none` never runs scripts. save syntax
unresolved - use MIDV_RAMDUMP_DIR instead.

Next-session plan: driven capture + MIDV_DBG_QUADID at a visible
pop-in event (the gray slab building on Golden Gate right edge is a
reliable specimen) -> attribute the popping quads to their emitting
node -> wp the node's list-membership write at the pop-in frame -> the
REAL distance gate, whatever it is.


## 2026-08-30 (later still) - C2 round 2: THE GATE FOUND + self-healing patcher

Round 2 blew the case open. Dense RAM-dump time series over a DRIVEN
race (340 dumps, every 20 frames) showed far->near list flips
clustering at depth ~76k (= 80000 minus per-object bias) - real
migration at the magic number - while patching 0x727E stayed
bit-identical. The contradiction broke on a second copy of the
constant: **word 0x55, inside the renderer's parameter block
(vars 0x40-0x61), read by the walker's per-object test at 0xC5-0xCC:**

    depth > 8000  -> geometry = node[0x18]   (MED LOD)
    depth > 15000 -> geometry = node[0x19]   (LOW LOD, flag bit 2)
    depth - radius > ($0055)=80000 -> SKIP   (THE DRAW-DISTANCE CULL)
    then 1/z LUT + screen-bounds culls

**Why every experiment null'd**: the game's own startup code
(0x4B48-0x4B50) re-copies 0x10000 words from maindata ROM 0xC00040 ->
RAM 0x40 AFTER machine_reset ran MIDV_PATCH - every patch below
0x10040 was silently reverted (widescreen patches at 0x11235+ survive,
which is why they always worked). Caught via a debugger wp chain on
word 0x55: exactly one write, PC 0x4B4F, boot-era.

**Fix shipped (mame-src 784bdfc6): self-healing MIDV_PATCH** - parsed
entries are re-asserted once per frame from screen_update, rewriting a
word only when it reads the verified OLD value again (per-track
runtime overrides stay respected; "*" entries reset-only). This also
unblocks future low-word patches (C1 coinage lives down there too).

**Verified with the healed patcher, driven-race A/B (bit-level)**:
- 0x55 -> 20000 (control): 1989 -> 600 quads/frame, ~11k px differ per
  snapshot - the world visibly truncates. THE KNOB IS REAL.
- 0x55 -> 160000 (extend): mostly identical - beyond 80k the course's
  objects largely don't EXIST yet (spawn-depth stats: p75 71.8k, max
  136.6k); one +218-quad early-draw event (frame 4200) shows the
  benefit class. The SECTION STREAMER's spawn window is the next wall
  (round 3 target).
- LOD thresholds (words 0xBF/0xC3, CMPI immediates) -> 32000: quad
  deltas confirm high-detail geometry held farther; per-pixel effect
  needs eyes at the wheel.

Try-me file: patch/game/crusnusa-renderdist-experiment.txt (NOT
auto-applied; crusnusa has no widescreen patch so MIDV_PATCH env is
free). Perf: no measurable slowdown unthrottled at x2 distance.


## 2026-08-30 (review) - second-set-of-eyes pass over the day's work

Cold re-read of all nine commits, backed by measurements. Findings:

1. **Tile dilation was stretching textures (real regression, fixed).**
   Moving the rect vertices out by 0.501 px without touching the vertex
   UVs shrank du/dx, so every textured 2D tile sampled its texture up
   to half a texel inward at the edges. New metric (quality S=4 index
   buffer vs the bit-exact S=1 buffer upsampled 4x nearest, on
   capture-continue): dilation OFF 15.29% of fine pixels differ,
   dilation ON (as shipped) **30.56%** - doubled. Fix: extrapolate the
   texture params along each axis by the same amount (scalar,
   vectorized and C++ builders): dilation ON now **14.04%** - closer to
   hardware than before the seam fix, seams included. Exact mode still
   100.0000% x3; scalar==fast bit-identical (scalar now mirrors the
   fast path's float32 multiply-by-reciprocal - u/v sit near 2^23 where
   float64 differed by 0.5).
2. **Snapshot writer heap overflow (latent, exposed today).** The
   MIDV_GL_SNAP path read the backbuffer into a tight cw*ch*3 buffer
   with GL_PACK_ALIGNMENT left at 4: any window width with cw*3 % 4
   != 0 pads rows and overruns the vector -> crash at the first snap.
   Every earlier run happened to open a 2352-px window (aligned); with
   the user back at the desk the window opened at 1535 and every
   live run died at ~8 s with 0 snaps. Bisected via a 2x2 of
   overlay x coin-up (all survive) then env (only MIDV_GL_SNAP
   crashes). Fix: PixelStorei(PACK_ALIGNMENT, 1). Live run now exits 0
   with 70 snaps at 1535 wide.
3. **complete_run merge was unbounded** - a stalled GL thread would
   accumulate every same-pc scene into one growing draw. Capped at
   16384 quads; past that it falls back to skip-to-latest.
4. **coinup.lua exited at frame 1 without SNAP_FRAMES** (last=0). Now
   never self-exits when unset (-seconds_to_run bounds the run).
5. Verified-clean on re-read: rawjoy dispatcher, TRANSMISSION plumbing
   (row indices/hints/handlers), merge-save semantics, run_rig
   arbitration, self-healing patcher (midvplus_state chains to the
   base reset, so Off Road is covered).


## 2026-08-30 (later) - TRANSMISSION setting; USA volume row dropped

User design call before wheel testing: replace the shifter-mode
*inference* (full H-pattern outranks paddles) with an explicit global
**TRANSMISSION** setting - the inference made sequential unreachable on
a rig with both a DS-8X and paddles, and going into the wizard already
knowing the mode simplifies binding. Implemented:

- SETTINGS row 5: TRANSMISSION < H-PATTERN SHIFTER / PADDLE SEQUENTIAL >
  (page is 8 rows now, spacing 0.062; hint notes Exotica has no paddle
  mode). Stored as [collection] transmission = hpattern|sequential; when
  the key is absent, load_config/run_rig.transmission_mode() infer it
  exactly like the old arbitration so paddle-only rigs upgrade cleanly.
- The wizard only asks the active mode's shift steps (17 steps in
  H-pattern, 15 in sequential, of 19) and **save_wheelmap now MERGES**
  into [wheelmap]: hidden steps and BACKSPACE-skipped steps keep their
  saved binding - switching modes never costs the other mode's binds,
  and both sets persist side by side.
- run_rig: apply_wheelmap's skip-set and apply_shifter_config's CONF
  value (0/5) both key off transmission_mode(); the active mode still
  requires its own bindings present (no-op otherwise), Exotica still
  refuses sequential (no CONF port on Zeus).
- Verified offscreen (settings renders both modes) plus an end-to-end
  scratch-rig ctrlr test: hpattern -> P1_BUTTON5/6 = shifter gears 1/2 +
  CONF 0; sequential -> P1_BUTTON5=shift-down / 6=shift-up paddles +
  CONF 5; crusnexo sequential -> untouched; START btn:34 -> ADDSW3 in
  both modes.
- Per-game submenu: the Cruis'n USA VOLUME row is REMOVED (it could only
  point at the in-game = / - keys - not a setting; user call). The row
  reappears automatically if USA's master byte ever gets pinned into
  VOLUME_CMOS.


## 2026-09-02 - onboarding review for the first external alpha tester

Walked the release/setup path as a stranger would and fixed what broke.

**Traps found (all fixed):**
1. **Cruis'n World 2.4 is a MAME clone** and the setup GUI both refused
   to install `crusnwld24.zip` ("this file will NOT work") and never
   checked for the four 2.4 game ROMs - a tester with ordinary split
   sets got a World that silently failed to launch. The rig only works
   because its `crusnwld.zip` is a MERGED set nesting the 2.4 files under
   `crusnwld24/` (MAME matches ROMs by hash, not name). Now:
   `run_rig.world24_available()` checks the four 2.4 CRCs across
   `crusnwld*.zip`; `resolve_world_rom()` falls back to 2.5 with an
   on-screen notice; the identifier matches by name OR CRC, scores clones
   on their unique files, installs crusnwld24, and the World row reports
   2.4 availability. Verified on merged / split-parent+clone / 2.5-only
   layouts.
2. **Launch failures were invisible** (console print only). vunit's
   output now goes to `rig/launch.log`; a startup exit surfaces its last
   meaningful line as a menu notice ("COULDN'T START ... : required files
   are missing" class).
3. **Set ranking**: one redumped file (the rig's Exotica u18/u19) let a
   two-file clone outscore the parent -> "does not look like this game".
   Parents now win coverage ties and installed sets are judged against
   their own list (`identify(..., want=rom)`): "installed (2 checksum
   oddities)".
4. **Force feedback needs the wheel GUID** - confirmed from the plugin's
   DllMain: a blank `DeviceGUID=` matches nothing and haptics stay NULL;
   the GUID is SDL's `SDL_JoystickGetGUIDString`. In-process SDL
   enumeration from Python returned zero devices on every driver hint
   (and the base was offline at the time), so the automation harvests
   the plugin's OWN log instead: `detect_ffb_devices()` runs the emulator
   ~30 s with `Logging=1` (it enumerates only once the game is up -
   a 10 s run never reached `numJoysticks`), parses "Joystick: n / Name / GUID" lines,
   `pick_ffb_device()` chooses the wizard's steering device by name (or
   the only device; else a chooser dialog) and writes `DeviceGUID=`.
   Setup GUI: "Detect wheel (FFB)" button + a wheel status row.
5. **`make_release.ps1` reused a stale `build\dist`** (an Aug-20 frozen
   launcher would have shipped). Always re-freezes now.
6. **No `fixtures/nvram-crusnwld24`** -> every tester hit CALIBRATE
   CONTROLS on the first World boot. Seeded from the rig's calibrated
   2.4 CMOS (same layout as 2.5: volume 0x9C, free play 0x1AC).
7. Docs were stale/dev-centric (setup.ps1 vs CruisnSetup.exe, WHEEL
   SETUP vs CONTROLS SETUP, a calibration note that no longer applied, no
   TRANSMISSION, no clone note, E:\ paths up front). README rewritten
   player-first; INSTALL.md rewritten (requirements incl. OpenGL 4.3, ROM
   table, launcher/wizard/in-game keys, FFB, troubleshooting, bug-report
   recipe); v0.3.0 release notes drafted.

8. **World 2.4 still shows CALIBRATE CONTROLS in a release-layout boot**,
   fixture or not (tested with and without the rig's wheel bindings; the
   base was powered off): the game validates its stored ADC calibration
   against what it reads at boot, so ANY hardware change - including a
   tester's different wheel - re-demands the one-time calibration. The
   fixture only spares the rig itself. Not fixable from outside without
   forging ADC ranges; documented instead (INSTALL Controls +
   troubleshooting, release notes "expected on first boot") and the
   launcher's LAUNCHING screen for World now says "press F2 and follow
   the prompts". USA / Off Road do not gate on calibration.
9. **DSP boot ROMs** (see the commit): a release-layout launch aborted on
   `c31boot.bin NOT FOUND` - the tms320c31/tms320c32 device zips are now
   identified, installable, a setup-window row, a ROM-table entry and a
   pre-launch notice. Re-verified: World 2.4 boots from the assembled
   release folder (fresh rig dir, no dev ctrlr) at 100% and exits clean.


## 2026-09-02 - first tester feedback: FFB "comes and goes" -> packaging bug

Tester (Fanatec CSL DD 8 Nm, GTX 1080): all three Cruis'n games run at a
steady 60 fps, controls fine, but CruisnSetup reported `dinput8.dll`
missing; he dropped in one from an older FFB plugin and forces became
intermittent.

Root cause, confirmed from the CI log ("[!] dinput8.dll not found beside
vunit.exe") and the published zip: release.yml picked the plugin files
from the folder of the FIRST `MAME64.dll` found - `Flycast/`, which has no
`dinput8.dll` and a Flycast ini. The plugin archive (v2.0.0.53) is one
folder per game; "MAME 64bit Outputs/" is the one with all four 64-bit
files. So v0.3.0 shipped: no hook DLL, a Flycast ini with `GameId=22`
stamped on, SDL2/MAME64 from Flycast. The Flycast ini lacks the Cruis'n
per-game keys (`FeedbackLengthCrusnUSA/CrusnWld`), so the plugin used its
120 ms default effect length - forces expire between the game's output
updates: exactly "comes and goes". The mismatched `dinput8.dll` version on
top of that made it worse, not better.

Plugin facts learned (from its source): `GameId=22` is the generic MAME
outputs mode and branches by ROM name (`crusnusa*`, `crusnwld*` incl.
`crusnwld24`, `offroadc*`), so one id covers all three V-Unit games;
`DeviceGUID` is SDL's joystick GUID string and a blank one matches
nothing.

Fixes (v0.3.1): release.yml and setup.ps1 select "MAME 64bit Outputs";
`ffb/FFBPlugin.ini` (repo-owned template: the plugin's MAME 64-bit
defaults + GameId=22, Logging=0, BeepWhenHook=0, blank GUID, 500 ms
effects, AlternativeFFB=0) is what ships - NOT the rig's Moza-tuned copy;
make_release throws if dinput8.dll is absent. Diagnostics: MIDV_FFB_TRACE
in the driver (every output change, ms-stamped, via the shared global
notifier), `[collection] ffb_diag=1` in run_rig sets it + plugin
Logging=1, CruisnSetup toggle + status row, support bundle collects
`ffb_trace.csv` and `launch.log`.


## 2026-09-02 - tester: "Off Road incredibly slow" (other three fine) - not reproducible

Measured on the dev rig with the same build the tester has:
- Headless emulation (`-video none`, 30 emulated s of attract): crusnusa
  325% (18 procs) / 511% (1 proc), crusnwld 348 / 546, **offroadc 671 /
  829** - Off Road is the CHEAPEST to emulate, and MAME's poly work queue
  costs more than it saves on this machine (1 proc faster than 18).
- Live overlay (`MIDV_GL=1`, attract, unthrottled): crusnusa 269% @4x,
  crusnwld 316% @4x, **offroadc 466% @4x and 465% @2x** - not GPU-bound
  at all here; the offroadc widescreen patch was applied.
- GPU scene pass (renderer.py --bench, 4x wide): USA canyon 3.57 ms/scene,
  Off Road canyon 2.81 ms - a 4x slower card still fits 57 fps.
- Sound on vs off: no difference for either game (DCS2 not a cost).
- Wheel-force output cadence (MIDV_FFB_TRACE, driven): USA 9.2/s, Off
  Road 1.2/s - Off Road updates the plugin LESS often.

Nothing Off-Road-specific in our stack is slow here. Plugin-side note: the
FFB Arcade Plugin runs Off Road in its "RacingFullValueActive2" mode
(different from USA/World) - a per-loop effect strategy on the tester's
Fanatec driver is the one Off-Road-only variable we cannot measure from
here. Shipped levers for a one-line A/B on his machine (v0.3.2): SETTINGS
INTERNAL SCALE 2X-4X (GPU), FFB STRENGTH 0% now idles the plugin
(GameId=0 - no game handler at all), ASPECT 4:3 (no patch/margins), CRT
off; the support bundle's launch.log ends with MAME's measured speed and
midv_gl.log carries a periodic speed readout. Ask: CPU model + a bundle
after an Off Road session.


## 2026-09-02 (evening) - v0.3.3: steering sensitivity was a no-op, direct launch, quit-all key

**Finding (tester confusion about STEERING SENSITIVITY / CURVE).** MAME's
per-port `sensitivity` cannot affect an absolute analog device: ioport.cpp
stores `m_accum = apply_inverse_sensitivity(raw)` at capture, and read()
runs `apply_min_max` (whose bounds are pre-scaled by the same inverse) and
then `apply_sensitivity` - an exact identity for wheels/pedals; the value
only governs keyboard/relative increments. Our STEERING SENSITIVITY row
wrote that value into `rig/cfg/<rom>.cfg` since the G5 menu redesign, so
it never changed a wheel's feel (the curve, our own patch, did). Fixed by
making it real: `MIDV_STEER_GAIN` (percent, 25..400, 100 = off) joins
`MIDV_STEER_CURVE` in the env-gated IPT_PADDLE block - the normalized
deflection is multiplied by the gain, clamped to +-1 (full lock), then
curved. Shell row is now 50..300% in steps of 10, "GAME DEFAULT (100%)";
stored pre-v0.3.3 values (MAME units, default 25) are discarded on load.
`write_steer_cfg`/`STEER_PORT` retired. Headless boot with GAIN=200
CURVE=70: clean, 695% unthrottled. Wheel feel of the gain: **needs the
user's rig test** (math reviewed only). INSTALL.md gained a "Steering
feel" section written for a player.

**Direct launch.** `CruisnCollection.exe --game usa|world|offroad|exotica`
(or MAME names, `crusnwld24` -> World card) runs `launch_game_async` with
the saved settings, no glfw window; polls Shift+F12 -> WM_CLOSE; releases
FFB on exit; returns vunit's exit code (2 + stderr note when the DSP boot
ROM is missing). Live-tested: Off Road up in ~40 s, WM_CLOSE -> exit 0,
launch.log "Average speed: 100.00% (102 seconds)"; injected Shift+F12 ->
exit 0 within 15 s.

**Shift+F12 = quit game AND launcher.** Shell's game-watch loop polls
GetAsyncKeyState(F12)+SHIFT, posts WM_CLOSE (clean: forces released,
NVRAM written) and sets `window_should_close` after the usual teardown.
Plain F12 unchanged (MAME UI_CANCEL -> back to the launcher). Legend and
INSTALL keys table updated.

**Old-name DSP boot ROM sets.** A tester's romset has `tms32032.zip`
(pre-rename device set name; identical `c32boot.bin` inside). The setup
identifier already maps it to `tms320c32` by content (verified on the
rig's own 2022 zip); `boot_rom_available` now also copies an old-name zip
to the 0.286 name at launch (`BOOT_ROM_OLD_NAMES`), tested on a temp dir.


## 2026-09-03 - tester FFB "works once per session" (Fanatec CSL DD): out-of-process release

Report sequence: FFB present on the first USA launch; exit; no FFB in any
game after; wheel power-cycle no help; Detect wheel no help; running
another emulator (Model 2 + its plugin copy) restores it for exactly one
of our launches again. Reading: the broken state lives in OUR long-lived
launcher process. The only exit-time action no other emulator performs is
`release_ffb` (G8): ctypes-loads the plugin's SDL2.dll into the shell,
SDL_Init(JOYSTICK|HAPTIC), opens every haptic device (SDL's DirectInput
backend = exclusive+background acquire, DISFFC_RESET, gain 10000,
autocenter off), StopAll, close, SDL_Quit. On the rig's Moza that leaves
nothing behind; on the Fanatec driver it evidently does (exclusive
acquire or SDL device state surviving SDL_Quit) until the process dies -
consistent with "first launch per shell session works" and with Detect
(shell still open behind the setup window) not helping. Plugin binaries
confirm the two handles at stake: MAME64.dll finds MAME's output window
by name (`FindWindowW("MAMEOutput")`, `MAMEOutputRegister`), dinput8.dll
opens the wheel via `SDL_HapticOpenFromJoystick`.

Changes: `release_ffb_detached` runs the release in a throwaway process
(`CruisnCollection.exe --release-ffb` when frozen, `run_rig.py
--release-ffb` from source; falls back in-process if it cannot start),
used after every exit (shell reap thread, direct launch, blocking
launcher) and BEFORE every launch (the "other emulator" effect, made
routine; ~1 s). `wait_or_kill` ends a game process still alive 15 s after
its window closed; `kill_stale_vunit` (EnumProcesses + image path = our
exe) ends left-over copies before a launch - live-tested against a
deliberate headless zombie (pid ended, none remaining). Support bundle
adds `processes.txt`. Not reproducible on the rig; verification is the
tester's next session.


## 2026-09-03 - in-app updates (GitHub Releases, private repo)

`harness/updater.py`: check() hits `releases/latest` with a fine-grained
PAT (Contents: read-only on this repo; testers are collaborators) stored
in rig/collection.ini [update] token; version from `version.txt` that
make_release.ps1 now stamps (`-Version`, CI passes the tag; "dev" from
source, never offered an install). download() takes GitHub's asset
redirect by hand and fetches the CDN URL WITHOUT the Authorization header
(the CDN rejects two credentials) - verified against the real v0.3.2
asset: 89,344,636 bytes, exact. apply() writes rig/update/apply.ps1 and
starts it with CREATE_NO_WINDOW (a DETACHED_PROCESS powershell never
runs - no console host; that cost one silent failure): waits up to 120 s
for every process running from the install folder to exit, Expand-Archive,
robocopy /E /XD rig roms over the folder, cleanup, Start-Process the
launcher. Fake-install test: exe replaced, version.txt stamped, rig/ and
roms/ untouched, extract dir and zip removed. Surfaces: setup window
"Updates..." (token entry, check, download+install with progress; closes
itself, the script waits for the launcher too) and SETTINGS -> CHECK FOR
UPDATES (Enter per stage, notice line; the shell quits once the script is
launched). Token never leaves the machine except to api.github.com.

Addendum (same evening): the repository goes public tonight, so the token
path was removed before it ever shipped - anonymous `releases/latest` +
`browser_download_url` (plain urlopen, redirects allowed since no auth
header is involved). `CRUISN_GH_TOKEN` env stays as a developer-only
escape from the 60/hour anonymous rate limit. Setup "Updates..." now
checks on open; no token row, no [update] section in collection.ini.
