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
