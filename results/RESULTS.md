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


## 2026-09-03 - tester round 3: FFBReset.exe confirms the diagnosis; Exotica; clipping

Tester: the plugin's own `FFBReset.exe` run after exiting a game restores
FFB for the next launch - the out-of-process open/stop/close exactly as
v0.3.4's detached release does. The tool is in the plugin package (14 KB,
"FFB Reset Tool - Cleaning wheel status... Done. N device(s) reset.",
exit 0, ~0.3 s with the Moza base off); it now ships beside vunit.exe
(CI copies it from the plugin archive wherever it sits; make_release's
optional list) and `release_ffb_detached` prefers it, falling back to the
built-in helper. Exotica "no FFB at all": expected - midzeus.cpp has no
wheel-motor output (grep: only the "Wheel Invert" DIP) and the plugin has
no crusnexo handler; documented, ROADMAP item added. "Clipping all over"
on an 8 Nm Fanatec: FFB STRENGTH 100% saturates a direct-drive base -
docs now say start at 40% (rig runs 70% on the Moza). MAME 0.288 romset:
fine, sets are identified by content.


## 2026-09-03 - the V-Unit force law, measured (tester video: wheel slamming left-right)

Tester video (Fanatec CSL DD 8 Nm, USA, car static): the wheel violently
turns itself back and forth. Diagnosed headless: coinup.lua gained
`WHEEL_SWEEP` (park :WHEEL at a value from a frame on) and a scripted
race (3 coins @600/700/800, START @1000/1600/2200/2800, GAS @3400) ran
under MIDV_FFB_TRACE with steps of +-32/+-64/+-112 counts from center.
Result: NO static force at any parked position. Every step produced one
burst of 12-16 updates a few ms apart, ramping to a peak and decaying to
0 within ~100 ms, sign opposite to the movement, peak proportional to the
step: 32 -> 30, 64 -> 63, 112 -> 100 (of 127), all twelve steps matching.
Encoding: signed byte (255 = -1). So Cruis'n USA's FFB is a DAMPER (kick
against wheel velocity), not a spring; on the weak arcade motor that read
as heaviness. With a strong low-friction base the kick moves the wheel,
the game kicks back, and the loop is unstable - the video. Loop gain is
the lever: FFB STRENGTH (30-40% on 8 Nm), wheel-side damping, and now
`MIDV_FFB_CLAMP=N` in midvunit.cpp (env-gated, WHLCTLZ write: clamps the
signed byte to +-N; small forces untouched).

Template FFBPlugin.ini switched to AlternativeFFB=1 - the rig's live ini
(the tuned reference, 70%, AlternativeFFB=1, spring on) had never matched
what testers got (AlternativeFFB=0). `harness/ffb_trace_report.py`
summarizes a bundle's trace (bursts/s, peak, direction flips, verdict).

Process bug caught: running vunit with `-nvram_directory fixtures/
nvram-crusnusa` makes MAME create `crusnusa/nvram` INSIDE the fixture
folder (fresh CMOS -> CALIBRATE CONTROLS on every such run) and `git add
-A` swept it into dd8c456. Removed; captures must seed a scratch copy
(`<dir>/crusnusa/nvram` from the fixture's flat `nvram`), as run_capture
and prepare_rig do.

Same sweep on the other two V-Unit games (both reach a race with the
scripted coin-up; Off Road needs the coins after frame 1500 - at 600 the
game still shows CREDITS 0):
- **World** (Humvee, driving into walls/off-track with no steering):
  399 updates in 34 s, peak 126/127, 119 updates >= 64, 83 direction
  flips - and unlike USA it HOLDS force: +126 sustained ~500 ms, -126
  runs, +37/+112 plateaus (crash / rough-surface effects), plus USA-style
  kicks around them. The worst offender for a strong wheel by far.
  MIDV_FFB_CLAMP=40: peak 40, 264 updates, same 83 flips (the clamp only
  caps, never reshapes).
- **Off Road** (race): 121 updates, peak 82, mostly tiny -3 -2 -1 idle
  ticks and short kicks of 15-60; a 17-update burst to 75 once. The
  attract mode also drives the motor (small ticks) - Off Road sends
  forces without a coin.
The clamp lives in midvunit_state::wheel_board_w, shared by all three.


## 2026-09-03 - FFB STRENGTH was a no-op; the plugin reads per-game keys

Tester (v0.3.1 files in a folder named v0.3.0 - the FFBlog path explains
the "0.3.0"): "FFB set to zero in settings doesn't work, still full
force". dinput8.dll strings: the Cruis'n handlers have PER-GAME keys -
MaxForce/MinForce/AlternativeMin|MaxForceLeft|Right/FeedbackLength/
EnableDamper/DamperStrength/EnableForceSpringEffect/ForceSpringStrength/
PowerMode, each suffixed CrusnUSA, CrusnWld, OffRoadC. apply_ffb_strength
scaled only the bare keys (its docstring even noted the suffixed ones
"can never be hit"). Both the template and the rig's live ini carry the
per-game MaxForce/AlternativeMaxForce at 100 - so the rig's "70%" and the
tester's "0%" were both 100%. Fixed: the per-game trio is scaled too
(added under [Settings] when an older ini lacks it); verified on the
template at 40: twelve keys at +-40. Consequence for tuning: everything
measured "by feel" so far was at 100%; the rig's 70 will feel far lighter
now and needs re-tuning. His FFBlog also shows the plugin found the
FANATEC Wheel (haptic), hooked crusnusa as "RacingFullValueActive2", gain
100, autocenter off - the hookup was fine; the level was the problem.
Support bundle now carries version.txt (folder names lie).


## 2026-09-03 - the plugin runs inside the launcher (FFBlog); Exotica motor register found

Tester's FFBlog.txt (v0.3.1 files): after the vunit.exe block, dozens of
"DLLMAIN ENTERED / process name: ...CruisnCollection.exe" entries and a
"numJoysticks =" enumeration IN THE LAUNCHER PROCESS. The plugin's
dinput8.dll sits beside the frozen launcher; glfw's joystick backend
LoadLibrary("dinput8.dll") and the loader's search order hands it the
app-folder copy -> a plugin instance with its own FFB thread lives in the
launcher for the whole session. That is the cleanest explanation yet for
"FFB on the first game per launcher session only" (v0.3.4's out-of-process
release and stale-process guard stay). Fix: collection.py pre-loads
%SystemRoot%\System32\dinput8.dll by full path before glfw init; a later
load by name resolves to the already-loaded module. (A python.exe test
cannot reproduce the frozen search order - app dir first - so the proof
is the next tester FFBlog: no CruisnCollection.exe entries.)

Also in that log: the plugin found "FANATEC Wheel" as haptic, hooked
crusnusa as RacingFullValueActive2, gain 100, autocenter off - hookup
fine; level was the per-game-key bug.

Exotica motor: MIDZ_IOLOG (env-gated write log on the LED/lamp board,
analog board, disk ASICs, keypad select) during a driven race with the
wheel sweep on :ANALOG3 (coinup.lua learned Exotica's tags: ANALOG3
wheel, ANALOG2 gas): `crusnexo_leds_w` offset 0 - "unknown purpose" in
MAME - 8016 writes, 53 distinct values, and they track the sweep at 57 Hz
frame timing: wheel to 96 (-32) -> +10..+13 HELD (275 writes) until the
wheel returns; to 160 (+32) -> -12 held; center -> -1/-2 chatter. Sign
opposite to displacement, magnitude ~0.37/count, held while displaced: a
centering SPRING (the V-Unit games send decaying kicks instead). Race
start writes +33/-7 plateaus. Now exposed as output "wheel" on
crusnexo_state (output_finder, same MIDV_FFB_CLAMP treatment).


## 2026-09-03 - tester support bundle (v0.3.1 files): the "RomName = (empty)" signature

Bundle CruisnSupport-20260903-025536: collection.ini ffb=100, scale=2,
crt=1, steercurve_crusnusa=120, world_rom=crusnwld (no 2.4), a Fanatec
wheel + "Generic USB Joystick" button box bound, DeviceGUID set (Detect
worked). FFBPlugin.ini: AlternativeFFB=0, every per-game MaxForce 100
(the strength bug, confirmed in the wild). FFBlog.txt 2.2 MB: first
session "RomName = crusnusa / RunningFFB = RacingFullValueActive2" with
3218 "got value:" output updates (working); later sessions "RomName = "
(EMPTY) / "RunningFFB = (null)" x51502 - the plugin's MAME client never
received the game name from the output window it found, so it ran no
handler: THAT is what "no FFB after the first game" looks like from the
plugin's side (an empty id-string reply, i.e. it was talking to the
wrong/dead MAMEOutput window or a second plugin instance held the
registration). 16100 "RomName = crusnexo / (null)" = Exotica pre-v0.3.5,
expected. joysticks_glfw.json is 0 bytes: the frozen --joydump died -
glfw in that process also loads the plugin's dinput8.dll (preload moved
to the top of main() so --joydump is covered). mame_verbose_input: the
Fanatec base enumerates as two DirectInput joysticks (108 and 63
buttons) - the DIJoystick2 patch is what makes his 63-button unit usable.
The next bundle from v0.3.5 should show RomName = crusnusa in every
session and no CruisnCollection.exe entries.


## 2026-09-03 - rig smoke test of the frozen build: brake latch, Exotica FFB level, TRANS SELECT

Smoke install E:/Games/CruisnCollection-smoke (frozen zip + the rig's
rig/ + ROMs). Proven before touching anything: the frozen launcher's
--joydump lists all three devices, and the running launcher has
dinput8.dll loaded from System32 (the preload works in the frozen
layout).

USA "won't go past 2nd, tyres squealing, even in automatic" (screenshot:
41 mph, 2nd, smoke, straight road) = the burnout the game does with gas
+ brake. lua/inputprobe.lua (windowed, reads the real devices):
BRAKE=255 at rest, ACCEL=0. Minutes later, same NEG_ABSOLUTE binding:
BRAKE=0; full-range binding: 128 (rest at centre, as the ctrlr code
assumes). So the Moza load-cell brake reports fully pressed until it is
pressed once after coming up (the user "had to press it a couple of
times" in the wizard). Launcher guard: refuses to launch while a pedal
reads pressed (nav_spec now carries the brake axis).

Exotica FFB: with the smoke install's vunit + plugin, headless, plugin
logging on, MIDV_OUTPUT_NAME=crusnusa: "RomName = crusnusa / RunningFFB
= RacingFullValueActive2", Moza found, 216 "got value" updates - the
chain works; the level is the issue (11/127 at +-32 counts, 46 at full
lock, x0.7). MIDZ_FFB_GAIN added (midzeus WHLCTL write): launcher
default 250 felt faint on the rig -> 400.

Exotica TRANS SELECT stays AUTO: under all four Cabinet x Game Type DIP
combinations the screen appears (A / AUTO / M, ~1.5 s) and advances on
AUTO regardless of: wheel parked right + gas, wheel moving right, wheel
moving left, 1st gear held before, 1st gear pressed during. Button
brute force (gears 2-4, radio, views, START during the screen) running.
Virtual sequential shifter added to the driver meanwhile (gears_r():
GEARS/SEQ ports, MIDZ_SEQ_SHIFT=1) with the launcher binding paddles to
the new Shift Up/Down inputs in sequential mode.


## 2026-09-03 - Exotica operator menu mapped; TRANS SELECT resists everything; wheel power byte

Diagnostics menu: SERVICE (the "Test" input, IPT_SERVICE) during attract
opens it; VOLUME UP/DOWN moves, TEST activates, SERVICE1 exits (exit
reboots into the CPU board test). Adjustments list (rev 2.4): STANDARD
PRICING, CUSTOM PRICING, FREE PLAY, FIRST PLACE GETS FREE RACE, START
TIME BONUS SECS 75, CHECKPOINT BONUS TIME SECS 20, ATTRACT MODE SOUND,
INITIAL ENTRY 6, MIN VOLUME LEVEL 12, STEERING WHEEL POWER 5 (1-10),
SPEED IN MPH OR KMH, KEYPAD ACTIVE, MANUAL TRANS DISABLE OFF, SHOW
ROADKILL/ENDING/GIRLS, HIGHSCORE RESET 5000, GAME DIFFICULTY 5, MAX
CREDITS 30, MULTI PLAYER FREE RACE. Scripted edits + m48t35 diffs:
0x97 = KEYPAD ACTIVE (1=on), 0x9B = MANUAL TRANS DISABLE (1=on), 0xC7 =
STEERING WHEEL POWER (value 1-10). 0xCF increments per menu visit
(audit), 0xB7/0xDB flip on any edit, 0xDF moves with edits (checksum or
audit; the existing 0x27 volume poke ignores it without complaint).
Bytes are poked directly (cmos_write) - no checksum guard needed so far.

STEERING WHEEL POWER 10 vs 5 (sweep + trace, gain 100): held force at
+-32 counts 15-16 vs 11-13, peak 48 vs 46 - ~1.4x at small angles, not
2x; the spring saturates. Fixture m48t35 0xC7 set to 10; the shell pokes
10 into an existing rig NVRAM at every Exotica launch; MIDZ_FFB_GAIN 400
stays on top (FFB STRENGTH tapers).

TRANS SELECT (A / AUTO / M, ~80 frames, auto-advances): AUTO in every
one of these - Stand Up/Sit Down x Dedicated/Kit; wheel parked right +
gas, moving right, moving left; 1st gear before/during/late/from boot;
gears 2-4, radio, views 1-4, START during; MANUAL TRANS DISABLE ON/OFF;
Sit Down + wheel-right + gas, + gear1 during, + gear1 from boot. Lua
set_value demonstrably drives the track-select highlight, so the method
reaches the game. Lua cannot see IPT_UNKNOWN/UNUSED fields (port.fields
omits them) - the first "unused bit" sweep never applied; replaced by an
env-forceable IPT_CUSTOM over IN1's 0xF00D lines (MIDZ_FORCE_IN1=<hex>)
to test whether the real shifter lives on a line MAME calls unused
(the driver credits the gear mapping to the manual's pinout sheet,
unverified; crusnexo is NOT_WORKING upstream).


## 2026-09-03 (late) - config-save wipe; Exotica glitches are the overlay's; USA draw distance unverified

Two A/B switches added tonight (exotica_gl, gamepatch_crusnusa) were
wiped before they could act: save_config replaced [collection] with the
keys the shell owns, and the shell saves at every launch - so ffb_diag
was being cleared the same way (the tester's bundle had no ffb_trace.csv
because of this). Fixed (merge); launch.log now opens with the applied
env, which is how the next runs were validated.

Exotica, Amazon track, exotica_gl = 0 (launch.log: MIDZ_GL=0): the
glitches the user saw with the overlay are GONE on MAME's own renderer.
Conclusion: they live in our zeus2_draw_quad GL path, not in the Zeus2
emulation. No widescreen patch exists for Exotica, so it is the quad
handling itself. Queued (ROADMAP).

USA with gamepatch_crusnusa (draw-distance experiment, verified live in
RAM headless: 0x55=160000, LOD immediates 0x7D00): the user saw no
difference; launch.log was overwritten by the Exotica run before it
could confirm the launch env. Turned off; measure with quad counts
before drawing conclusions (ROADMAP).

Force-line hunt closed: MIDZ_FORCE_IN1 over all seven "Not Used" lines,
Sit Down cabinet, from boot through a race - AUTO every time.


## 2026-09-03/04 (overnight) - World NY "black textures" and Exotica Amazon glitches, both run to ground

**Reaching the spots headless.** Both games select tracks by wheel
POSITION, not scrolling (holding right parks on one item). Mapped:
World CHOOSE RACE wheel 16 Egypt, 40 Moscow, 64 Germany, **88 New York**,
112 England, 136 Cruise the World, 160 France, 184 Japan, 208 China,
232 Mexico (choose = gas). Exotica TRACK SELECT 16/40 Atlantis, 64
India, **88 Amazon**, 112 Alaska, 136 Cruise Exotica, 160 Korea, 184
Mars, 208 Holland, 232 Tibet.

**World, New York (crusnwld24, widescreen patch on).** Three instrumented
captures (frames 4500 / 6000 / 7600: expressway, Sin City wall, the
tunnel). Exact mode 100.0000% vs videoram at 4500. Wide 4x renders
(results/proof/night-2026-09-03/): margins fully populated - walls,
fences, tunnel - no black slivers in any of the three (C3's residual
stays "rare"). The one dark rectangle present in EVERY NY frame at the
right (with a red/white dot) is a HUD widget the hardware draws with
its 50% checkerboard translucency (exact render: alternating black and
scene pixels); at 4x it is the smoked-glass panel the 2026-08-25 fix
produces, average brightness identical to the CRT's blend. Verdict: the
"subtle black texture" is the game's own translucent panel, faithful.

**Exotica, Amazon.** Three MIDZ_CAPTURE captures during a scripted race
(frames 4200 start, 6420 bush close-up, 7200): CPU oracle 100.0000%
colour+depth; offline GPU renderer 100.0000% at scale 1 and 4 on all
three - the shared shader/batching is right, and the generated live
shader header is current (regenerated, no diff). Live overlay (windowed,
MIDZ_GL_SNAP, 74 frames + two dense 60-present windows via the new
MIDZ_GL_SNAP_EVERY/FROM_SEC/MAX): no flicker (consecutive presents ~2
grey levels apart in the jungle straight; the river section's 15-30 is
scene motion). The dramatic frames - a giant blurry green mass with
rectangular windows filling half the screen at ET 0:38 - are the car
(steered by the script PLUS the real Moza's offset in windowed runs)
driving INTO roadside plants: a small leaf texture magnified ~30x by the
hardware's bilinear filter, with transparent texels rejected at texel
granularity (rectangular holes). MAME's own d3d renderer, same script,
same crash, shows the identical picture (proof images: live overlay vs
MAME d3d, plus the fallen tree). Verdict: hardware-accurate; more
conspicuous at 4x/16:9 than on a native 4:3 frame, which is likely the
whole difference the user's A/B saw.

**Real bug found on the way (fixed, not the cause here):** the live
overlay's 64 MB record ring dropped ANY record when full. A dropped quad
is a one-frame blip; a dropped waveram span / palette load / display
tick left the GL texture mirror stale until the game rewrote that
region - the recipe for sprites drawn from wrong texture bytes.
ring_push2 now waits (bounded) for the consumer on essential records and
sets a resync flag that makes the next flush resend the whole 16 MB
texture memory if a span still could not be queued; counters logged at
exit. A full Amazon race logged 0 drops, so the Amazon report was not
this - but a heavier scene or slower GPU would have hit it.

Tools added: coinup.lua WHEEL_SWEEP/GEAR_FRAME/PRESS_FRAMES/PRESS_HOLD/
FORCE_FRAMES; lua/inputprobe.lua; MIDZ_GL_SNAP_EVERY/FROM/FROM_SEC/MAX;
the overlay's launch hang (FFB plugin enumeration, ~50%) needs a retry
loop in scripted windowed runs.


## 2026-09-03 (morning) - tester round 4: "FFB still sucks / clipping"; the plugin's mechanics read from source

Tester (Fanatec CSL DD): clipping and constant back-and-forth persist at
40%; "MAME doesn't clip" - his MAME uses an "endprodukt" fork of the
plugin (a "ConstantF mode"; not on GitHub, Discord-shared); swapping its
files into our folder gave no FFB. He wants at least stock-MAME parity.

Facts established:
- Our shipped plugin ini vs the plugin's own "MAME 64bit Outputs" ini
  (fetched from the Boomslangnz 2.0.0.53 release): the ONLY difference
  was AlternativeFFB=1 (my 2026-09-03 flip to match the rig). Reverted
  to 0. FFBReset.exe is NOT in the plugin archive (the vendored copy in
  ffb/ is our source of truth).
- Plugin source (DllMain.cpp TriggerConstantEffect, MAMESupermodel.cpp
  RacingFullValueActive2): per 'wheel' update it sets ONE persistent SDL
  constant effect to level = strength*(Max-Min)+Min with
  length=FeedbackLength (500 ms stock) AND calls Rumble(strength) (stock
  EnableRumble=1); values 0x00/0x80 are ignored (no stop); PowerMode =
  sqrt(strength); AlternativeFFB only swaps in per-direction min/max
  keys; no filtering anywhere; reversals are instantaneous.
- Therefore our FFB == stock MAME + stock plugin, byte for byte (the
  trace shows the game's bytes; the plugin is the same binary). What he
  prefers is the fork's behaviour, which we cannot see. Ask for the files
  (dll+ini+readme); his swap probably failed on ini keys/GameId, which
  our launcher rewrites at launch.

Shipped as opt-in knobs (no default changes): [collection] ffb_rumble,
ffb_alt, ffb_power, ffb_hold -> plugin ini keys at launch; ffb_slew ->
MIDV_FFB_SLEW (midvunit + midzeus): the force byte may move at most N per
update before the clamp - verified headless (slew 12: a 63-kick becomes
12,24,36,48,60 then decays; max step 12). This is the one thing the
plugin cannot do and we can, upstream of it. Recipe in INSTALL:
ffb_rumble=0 first, then ffb_slew=16, PEAK LIMIT 60, STRENGTH 40.


## 2026-09-03 - the "endprodukt" plugin found: Endprodukt/FFBPluginRacerMAME; adopted

GitHub: Endprodukt/FFBPluginRacerMAME, "FFB Plugin MAME", releases 1.99x
(1.995 = 2026-08-31, 105 MB zip: dinput8.dll 768,512, SDL2.dll,
MAME64.dll, FFBReset.exe (this is where the tester's reset tool comes
from), FFBPluginGUI, plus their own mame.exe). GPL-3 fork of Boomslangnz's
plugin, MAME-focused. Diff vs stock in the Cruis'n handler
(RacingFullValueActive2): (1) value 0 now STOPS the force in both
directions (stock ignored 0); (2) `UseConstantInf` (default 1) routes
constant forces to TriggerConstantInfEffect - one persistent constant
effect, stopped via SDL_HapticStopEffect when strength < 0.001, no
re-trigger pulse; (3) percentForce clamped to 1.0; rumble per update
unchanged. Same single [Settings] ini layout and key names (our launcher
rewrites are compatible).

Verified headless with OUR vunit.exe (scratch copy) + the fork's files +
our template after apply_ffb_strength(70): FFBlog "RomName = crusnusa /
RunningFFB = RacingFullValueActive2", 29 force updates received. The
tester's failed swap was therefore not an incompatibility (likely a
partial copy).

Adopted: release.yml downloads the fork's latest release and takes
dinput8/SDL2/MAME64/FFBReset from its folder; ffb/FFBPlugin.ini is now
the fork's shipped ini with our pins (GameId=22, DeviceGUID blank,
Logging=0, BeepWhenHook=0, AlternativeFFB=0, StartDelay=0,
UseConstantInf=1, FeedbackLength<game>=500); make_release fetches the
fork's LICENSE and credits it; [collection] ffb_constinf knob. The dev
folder and the smoke install got the fork's files (stock 2.0.0.53
backed up in mame-src/_plugin-backup-boomslangnz-2.0.0.53/).


## 2026-09-03 - Exotica FFB survives the plugin switch; the fork's SDL formats GUIDs differently (FFB-silent regression caught before release)

Question: did substituting FFB Plugin MAME (Endprodukt) lose Cruis'n
Exotica's force feedback? The Exotica chain is game -> `wheel` output
(midzeus.cpp, MIDZ_FFB_GAIN) -> MAME win32 output client with the id
string spoofed to `crusnusa` (MIDV_OUTPUT_NAME) -> the plugin's Cruis'n
USA handler. Only USA had been re-verified after the switch.

Headless Exotica against the fork's files (scratch copy of vunit.exe +
the fork's dinput8/SDL2/MAME64, Logging=1, MIDV_OUTPUT_NAME=crusnusa,
MIDZ_FFB_GAIN=400, coinup.lua coin/start/gas + wheel sweep 128-96-128-160
-128, 122 s): FFBlog `RomName = crusnusa / RunningFFB =
RacingFullValueActive2`, **235 "got value" updates**, and the value
histogram matches the game-side trace (MIDV_FFB_TRACE) one for one
(43x252, 31x248, 28x4, 26x0, 14x244, 12x192 ...). The fork's handler is
the stock one plus "0 stops the force", which for Exotica's held
centering spring is the correct behaviour (stock left the last force
standing at centre). Exotica FFB: kept.

The same run said **"No haptic device available"** although the Moza was
enumerated - because the scratch ini had DeviceGUID blank. Chasing why
the enumerated GUID looked unfamiliar found a real regression:

- SDL changed the joystick GUID layout in 2.26: bytes 2-3 carry a CRC16
  of the device name (older SDL: zero). Stock FFB Arcade Plugin 2.0.0.53
  ships SDL **2.28.5** -> Moza R12 Base = `030093e16e3400000600000000000000`;
  FFB Plugin MAME 1.995 ships SDL **2.24.2** -> `030000006e3400000600000000000000`.
  (The tester's Fanatec: `03001464b70e...` in his bundle, harvested under
  the stock plugin.)
- The plugin matches DeviceGUID= by `memcmp` of all 16 bytes (DllMain
  initialize loop) -> any GUID harvested under the stock plugin never
  matches under the fork -> "No haptic device available, FFB effects
  will be disabled" -> FFB silent in **all four games**. This is also what
  the tester's failed manual swap of the fork really was (not a partial
  copy). The rig's dev folder and the smoke install were in that state
  since the switch.

Fix (run_rig.py): `sdl_joystick_guids(mame_dir)` loads the SDL2.dll
beside vunit.exe through ctypes (SDL_JOYSTICK_RAWINPUT=0 like the plugin,
SDL_Init(JOYSTICK), SDL_JoystickGetDeviceGUID + GetGUIDString, SDL_Quit)
and `normalize_ffb_guid(mame_dir)` rewrites DeviceGUID= to that DLL's
string for the one connected device that matches on bus/vendor/product/
version (everything except bytes 2-3); called from `ensure_ffb_guid` at
every launch, so it self-heals in either direction (and after future SDL
bumps in the fork). Verified: dev folder and smoke install rewritten
`030093e1... -> 03000000...`, [ffb] device_guid updated. Both SDL builds
enumerated in one process for the record: 2.24 lists Stalk / R12 Base /
DS-8X Shifter, 2.28 listed only the R12 Base (second SDL in the process;
the string difference is the point).

Re-run of the headless Exotica test with the rewritten GUID in the
scratch ini: FFBlog **"Haptic joystick found: 1 / Name: MOZA R12 Base"**,
`RomName = crusnusa / RunningFFB = RacingFullValueActive2`, 235 updates,
Average speed 99.99% over 121 s (exit-time ACCESS VIOLATION afterwards =
the known plugin teardown race; FFBReset.exe released the base). Exotica
FFB through FFB Plugin MAME: proven end to end on the rig's hardware.


## 2026-09-03 - force feedback moves into the emulator; the FFB Arcade Plugin is retired

Trigger: Endprodukt (maintainer of the plugin fork we had just adopted),
asked by the user, said (1) he thought wanszai's ports were closed source
(we derive from MAME, not from wanszai - only the architecture is the
same), and (2) working at MAME driver level, we should avoid "the
clusterfuck that is ffb plugin" and drive the wheel ourselves the way his
Cannonball DX fork does, keeping only the plugin's interpretation of the
Cruis'n wheel byte. The user agreed ("get rid of ffb blaster").

Cannonball DX (Endprodukt/cannonball-dx, src/main/directx/ffeedback.cpp,
Windows backend): SDL2 haptics, select the bound steering device (else a
wheel-type device, else any with SDL_HAPTIC_CONSTANT), autocenter 0, gain
100, ONE constant effect with direction SDL_HAPTIC_STEERING_AXIS, infinite
length, level signed; per update SDL_HapticUpdateEffect + RunEffect(1);
zero = StopEffect; spring via a condition effect (not needed here - the
games ARE the spring/damper). "Modelled after Flycast's wheel path."

Implementation (mame-src midvunit_v.cpp, namespace mvffb; ~330 lines):
- SDL2.dll loaded at run time (LoadLibrary + 22 GetProcAddress) with
  SDL's headers for types only, so vunit.exe has no SDL import and runs
  without the DLL (FFB off, logged). Headers from MSYS2
  mingw-w64-x86_64-SDL2 (2.32.10); the same package's /mingw64/bin/SDL2.dll
  ships beside vunit.exe (zlib licence vendored as
  third_party/SDL2-LICENSE.txt). CI installs the package and copies the
  DLL; the plugin download step is gone.
- Drivers call midv_ffb_write(f) with the signed byte after gain/slew/
  clamp (midvunit WHLCTLZ case 4, midzeus leds offset 0). A worker thread
  owns SDL: condvar wake per write, apply = UpdateEffect + RunEffect,
  0 -> StopEffect. Interpretation = the plugin's RacingFullValueActive2:
  0 and 0x80 stop, |v|/126 clamped to 1, times MIDV_FFB_STRENGTH.
- Device: MIDV_FFB_DEVICE (name substring or vid:pid; the launcher passes
  the wizard's steering device name, "MOZA R12 Base" on the rig) ->
  wheel-type haptic -> any constant-force device; the named device not
  doing haptics = FFB off, never another wheel (Cannonball rule).
- Hold watchdog: MIDV_FFB_HOLD_MS (500) releases the force when the game
  stops writing. Measured: the V-Unit games AND Exotica write the motor
  byte every frame (~17 ms) even when it is 0, so the watchdog only fires
  on pause/menus/exit. Exit notifier stops and destroys the effect, closes
  haptic + joystick, SDL_Quit ("closed" in the log).
- Log midv_ffb.log in the cwd (device list, choice, errors; every write
  with MIDV_FFB_LOG=2, which FFB diagnostics sets). Support bundle ships it.

Measurements on the rig (Moza R12, headless, wheelprobe.py reading the
physical axis via glfw):
- MIDV_FFB_TEST=20 (raw +20% level, 1.5 s): axis went +0.98 -> -1.00,
  i.e. a POSITIVE SDL steering-axis level turns the Moza LEFT. (~1 s
  latency before the wheel started moving from the stop; then 0.6 s to
  the other stop.)
- Exotica's own spring (MIDZ_FFB_GAIN 400, wheel field parked by coinup):
  parked 96 (left of centre) -> byte +58; parked 160 -> byte -70. So a
  POSITIVE byte pushes RIGHT (toward centre from the left), consistent
  with the plugin mapping 1..0x7F = DIRECTION_FROM_LEFT.
- Therefore level = -sign(byte) * magnitude on this base; MIDV_FFB_INVERT
  and SETTINGS -> FFB DIRECTION flip it for bases with the other axis sign
  (symptom: Exotica runs away from centre, USA's damper becomes an
  anti-damper and shakes).
- Exotica run through the module at strength 30: 5588 motor writes in
  122 s, 1858 non-zero, levels up to +-9830 (30% of 32767), device
  "MOZA R12 Base" (pass 0, caps 0xd7fb, steering axis), clean "closed".

Launcher side (-660 lines): apply_ffb_strength, the FFBPlugin.ini /
DeviceGUID / SDL-GUID machinery (this morning's normalizer included),
release_ffb(+detached, FFBReset), detect_ffb_devices / pick, the
dinput8 System32 preload, --release-ffb, MIDV_OUTPUT_NAME spoof, "output
windows" in mame.ini, the setup window's "Detect wheel (FFB)" and wheel
row, setup.ps1's plugin download, make_release's plugin block, ffb/ dir.
New: MIDV_FFB / MIDV_FFB_STRENGTH (FFB STRENGTH %, 0 = not started) /
MIDV_FFB_DEVICE (steer device) / MIDV_FFB_INVERT ([collection] ffb_invert
<- SETTINGS FFB DIRECTION row, 14 rows now, spacing 0.040) / MIDV_FFB_LOG=2
with diagnostics; launch.log header lists them.


## 2026-09-03 - wizard axis numbering vs MAME's DirectInput slots (Endprodukt's inert pedals)

Report: Endprodukt (Fanatec CSW 2.5 base, pedals as a separate "HID
joystick") binds the pedals in CONTROLS SETUP without trouble; in game they
do nothing. The user confirmed wheel and pedals are separate devices.

Ruled out first: device identity. MAME's `<mapdevice device=... >` is
matched by `input_device::match_device_id()` and the first tester's
-verbose log shows it working on our name strings ("Remapped joystick #2:
Generic   USB  Joystick"), so a second device does get its JOYCODE index.

Cause: axis NUMBERING. glfw (the wizard) returns a compacted axis list -
the axes the device has, sorted X<Y<Z<RX<RY<RZ then sliders, indexed 0..n.
MAME's DirectInput module (input_dinput.cpp, `for axisnum 0..7`) names axes
by fixed slot XAXIS..RZAXIS, SLIDER1, SLIDER2 and SKIPS a slot the device
lacks ("Unable to get properties for joystick ... axis 3" - visible in the
first tester's log for his button box, which has X/Y/Z/RZ only). Our
`_wheelmap_token` translated glfw index i to the i-th slot token, which is
only right for dense devices. Pedal sets are the classic sparse device
(e.g. Y/RZ/slider): wizard axis 0 -> written XAXIS -> MAME reads an axis
that never moves. The rig's Moza has all eight slots, so it never showed.

Fix: harness/dinput_axes.py enumerates DirectInput 8 through ctypes COM
(DirectInput8Create, EnumDevices(DI8DEVCLASS_GAMECTRL, ...), CreateDevice,
EnumObjects(DIDFT_AXIS) -> object type GUIDs) and returns, per instance
name, the present slots in slot order - exactly the list glfw indexes.
run_rig.axis_layout() calls it at every ctrlr generation, caches to
rig/axis_layout.json (a device unplugged at launch keeps its last layout),
prints sparse devices to the launch console, and `_wheelmap_token(...,
axes=layout[dev])` indexes that list. Fallback = the old positional table.
The support bundle ships dinput_axes.txt. Two ctypes traps on the way:
GetModuleHandleW's HMODULE truncated to int without a restype (DirectInput8Create
E_INVALIDARG), and EnumDevices takes dwDevType FIRST, then the callback.

Rig check: Moza -> all eight slots (ctrlr unchanged), shifter and stalk ->
no axes; simulated sparse device ["YAXIS","RZAXIS","SLIDER1"]: wizard axis
0/1 -> JOYCODE_2_YAXIS_NEG_ABSOLUTE / JOYCODE_2_RZAXIS_NEG_ABSOLUTE. The
tester's own layout is unverified until his support bundle or a run.


## 2026-09-04 (00:15) - first rig drive on the native FFB: sign right, damper loop felt; smoothing / damper / friction knobs

User at the wheel, USA, 70% then 50%: "driving steady in a straight line
at constant speed it's constantly doing pulls to both left and right
alternatively"; FFB DIRECTION inverted = "significantly worse"; turning
right pulls back left "which is correct". Exotica not yet driven.

His support bundle trace (rig/ffb_trace.csv, 00:17 launch, strength 50):
1491 motor updates in 62 s, peak 126, 346 updates >= 64, 85 kick bursts.
Raw sequence 8.0-8.7 s: wheel 86 -> 128 (turning right) while the force is
-3..-14 the whole way, then decays -14 -> 0 over ~150 ms AFTER the wheel
stops; 10.7 s: wheel 120 -> 95 (left), force +7..+20, tail to 0 in 150 ms.
So the sign is right (force opposes velocity: a damper) and the kicks are
the game's real response to his own steering corrections (25-50 counts ->
20-80). What the arcade wheel's friction absorbed, a Moza R12 at 50-70%
turns into a pull after each correction; correcting the pull earns the
next kick the other way. The last 20 s show +-127 held 1-2 s at a time
with the wheel at 40..170: a crash/off-road stretch (game content).
Conclusion: not a bug in the path - the faithful signal on a frictionless
base. The stock plugin had blurred it (500 ms holds, zeros ignored).

Remedies added to mvffb (all env, launcher keys under [collection]):
- MIDV_FFB_SMOOTH=ms (ffb_smooth): first-order low-pass on the level in
  the worker (4 ms ticks, re-level on >= 0.1 % change, snap to stop when
  the target is 0 and |level| < 160).
- MIDV_FFB_DAMPER=% / MIDV_FFB_FRICTION=% (ffb_damper / ffb_friction):
  SDL condition effects (SDL_HAPTIC_DAMPER / _FRICTION, steering axis,
  infinite, coeff = pct of 0x7fff, saturation 0xffff) started once and
  stopped at exit - the arcade mechanism's resistance rendered by the
  base. Moza R12 caps 0xd7fb include both.
- Esc menu open -> midv_ffb_write(0) immediately (was: watchdog 500 ms).
Rig config set to ffb_smooth = 50 for the next drive; FFB DIRECTION
restored to NORMAL (it had been left INVERTED). Defaults to be picked from
the user's verdict.


## 2026-09-04 (00:45) - Exotica "only a weak spring": crash effects are 17 ms spikes; rumble channel, impulse bypass, per-game FFB STRENGTH

User (after v0.3.6 was tagged): Exotica far too weak (raised the base's
own gain in Pit House to feel it) and nothing but the centering spring -
no bumps or jerks on crashes or jumps.

Exotica's motor stream (headless race, traceC.csv, 227 updates): only 4
bursts >= 90/127, each ONE or TWO updates long (17-34 ms): -127 -116,
+127, -100, -100. The spring itself: |v| median 12, p90 72 at gain 400.
So the game's crash/jump "effects" are single-frame full-force spikes.
The arcade motor plus wheel inertia made a thump of that; a direct-drive
base renders 17 ms of torque as a tick, and the 50 ms low-pass (v0.3.6)
cuts it to ~30 %. The plugin path had two things this path lost: 70 %
strength (now 50) and a Rumble(|force|, 100 ms) burst per update - the
burst is what made crashes shake, and it also put a texture on the held
spring.

Changes (v0.3.7): (1) mvffb rumble channel: MIDV_FFB_RUMBLE=N -> on every
new force value SDL_HapticRumblePlay(|level|/full x N %, 100 ms), stop on
zero (Moza: rumble = sine on the steering axis); launcher default
ffb_rumble = 100 (plugin parity), 0 = off. (2) Smoothing bypass: a jump
of >= 60 % of full between consecutive values sets the filter state to
the new value, so spikes hit the constant channel at full size and then
decay with tau. (3) Per-game FFB STRENGTH row on each game card
([collection] ffb_<rom>, blank = SETTINGS); rig set to ffb_crusnexo = 100.


## 2026-09-04 - upstream sweep: #16046 backported (Exotica speed + fill decode); lamp-output regression fixed

Upstream check (standing task, before every tag). Findings:

1. **mamedev/mame#16046** (mourix, merged 2026-09-03, "Assisted by Claude
   Opus 5") - two Exotica fixes, both absent from our 0.286 base:
   - `tms320c32_control_r` hardcoded both fake C32 timers at 10 MHz. The
     games set CLKSRC, selecting the internal H1/2 = CLKIN/4 = 15 MHz, so
     **Exotica ran in slow motion**. Now
     `BIT(m_tms320c32_control[offset - 4], 9) ? unscaled_clock()/4 : 10000000`
     with `elapsed().as_ticks(rate)`.
   - Zeus register 5E bit 5 selects 24-bit colour + 24-bit depth vs 32-bit
     colour + 16-bit depth; the driver had one wrong combined layout, so the
     SGRAM fill read colour bytes as depth and the clear landed near enough
     to reject the terrain drawn against it (**the dark band over the
     background**). This supersedes the depth-clear workaround we took from
     #15723 - removed here too, including from our `midz_cap_clear` hook.
     `device_reset` now seeds `m_fill_depth = 0xffffff`.
   Applied by hand: upstream sits in `williams/`, we are still `midway/`,
   and the fast-clear hunk is where our capture/live hook lives.
2. **mamedev/mame#16055** (Endprodukt, OPEN, filed 2026-09-04) - upstreams
   the Exotica wheel-motor output at `crusnexo_leds_w` offset 0, the exact
   location this project found on 2026-09-03, plus the same for gaelco3d /
   itech32 / hornet / model2. His name is `wheel_motor`; ours was `wheel`,
   so both our drivers were renamed to converge. (His PR also carries an
   unconditional `show_warnings = false` in `ui.cpp` - a global behaviour
   change likely to draw review pushback; ours stays env-gated.)
3. Our #15723 backport matches what upstream actually merged (2778d32e):
   solid fills, translucency clamp, the `zeus2_write_pixel` refactor.
   Nothing new on midvunit since our base.

Verification after the build:
- **V-Unit oracle 100.0000% bit-exact** on `results/capture` and
  `results/capture-8000` (0 differing pixels of 204800 each) - the
  protected invariant is intact.
- Exotica headless, same coinup script and 122 s as the pre-backport run:
  digit outputs 742 -> 806, LED outputs 635 -> 757 in the same wall time,
  i.e. the game clock now advances faster. Average speed 99.62%.
- Wheel verdict on the new game speed still pending.

Separately, a **regression report from a user: lamp outputs stopped working
between v0.3.5 and v0.3.6**. Cause found in our own code: `prepare_rig`
wrote `output windows` into mame.ini only because the FFB plugin needed
it, and the v0.3.6 plugin removal deleted the line. MAME's `-output`
default is `auto`, which resolves to the `none` module, so every external
output consumer (lamps, LED boards, SimHub/Buttkicker) went silent while
our own FFB kept working (it calls `midv_ffb_write` from the driver, not
through outputs). Line restored with a comment saying why it must stay.


## 2026-09-04 - Exotica TRANS SELECT SOLVED: the "Wheel Invert" DIP (Endprodukt's find, proven here)

The user relayed from Endprodukt that the Exotica auto-transmission problem
is "a dip switch that isn't well documented - invert wheel". It is
`PORT_DIPNAME( 0x0800, 0x0800, "Wheel Invert" )` in crusnexo's DS1 block
(default Off), sitting immediately after Cabinet - the one DIP our
2026-09-03 sweep never tried (that sweep covered Cabinet x Game Type, every
wheel position and direction, gears, buttons, MANUAL TRANS DISABLE).

Added `DIP_SET="Name=value"` to lua/coinup.lua (sets DIP/config fields by
MAME name via `ioport_field.user_value` at boot) and tested headless,
identical runs apart from the DIP:

| DIP | wheel parked | TRANS SELECT at frame ~3240 |
|---|---|---|
| Off | 200 (right) | already past it, on CAR SELECT |
| Off | 56 (left) | already past it, on CAR SELECT |
| On | 200 (right) | up, **MANUAL** lit, "PRESS GAS TO CHOOSE" |
| On | 56 (left) | up, AUTO lit |

So the DIP does not merely mirror the selection: with it OFF the game
confirms AUTO immediately whatever the wheel does (which is why nothing we
tried ever worked), and with it ON the screen becomes interactive.

It also mirrors the wheel for DRIVING. Measured on the game's own centering
spring (parked position -> mean motor byte, gain 100; correct = spring
toward centre):

| configuration | parked 160 (right) | verdict |
|---|---|---|
| DIP Off (baseline, gain 400 scaled) | ~-17.5 | toward centre, correct |
| DIP On alone | **+16.8** | away from centre, steering mirrored |
| DIP On + our mirror | **-16.4** | toward centre, correct again |

Fix, both halves:
- Driver (`crusnexo_state::analog_r`, env-gated `MIDZ_WHEEL_INVERT=1`):
  mirror the ANALOG3 byte (`0xff - v`), cancelling the DIP's inversion so
  driving is exactly as before.
- Launcher (`apply_exotica_dips`): seed `rig/cfg/crusnexo.cfg` with
  `<port tag=":DIPS" type="DIPSWITCH" mask="2048" defvalue="2048"
  value="0"/>`, merging into the existing cfg (the Cabinet DIP we already
  set survives) - MAME's own format, so a player can still flip it in
  MAME's menu. `[collection] exotica_manual = 0` opts out. Verified
  idempotent.

Consequence to document: with the driving mirror in place the menu reads
backwards against its own layout - **turn the wheel LEFT to select MANUAL**
(M is drawn on the right). The alternative, an intuitive menu with reversed
steering, is worse. The virtual sequential shifter (MIDZ_SEQ_SHIFT, shipped
inert since v0.3.5) should now be live; a rig drive is the remaining check.


## 2026-09-04 - "the left arrow acts like ENTER": phantom wheel buttons, not the keyboard

User report: opening the launcher and pressing LEFT as the very first key
jumps into a submenu, as though ENTER had been pressed.

The menu key handler is clean (LEFT moves the selection, ENTER opens the
card), so the ENTER had to be synthesised elsewhere. Added
`CRUISN_INPUT_DEBUG=1`, which tags every action with its origin (keyboard /
hat / wheel button / steering / gas), and reproduced it by driving the shell
with SendInput (glfw takes normal Windows keyboard messages, unlike MAME's
rawinput, so a synthetic key does reach it):

```
[input]  209.40  keyboard: 263      <- KEY_LEFT
[input]  209.42 button j1b80: 257   <- KEY_ENTER, 20 ms later
```

Isolating the device with a bare polling probe (no launcher) showed the
cause has nothing to do with the keyboard: the **MOZA R12 Base reports 132
DirectInput buttons and pulses unused ones continuously** - 400 edges in
6 s, button 42 in one run, 43/44 in the next, i.e. a moving index. The
existing 0.6 s re-enumeration debounce swallows the fast stream, but an
isolated pulse after a quiet period passes it, and the menu's rule was "any
wheel button press+release = OK". So the phantom ENTER fires at random and
merely *appears* to be caused by whatever key was pressed at the time.

Fix: menu OK is restricted to buttons bound in `[wheelmap]`
(CONTROLS SETUP), gears excluded (an H-pattern shifter holds one closed);
an empty map still accepts any button so a fresh install works out of the
box. The allow-list is rebuilt when the wizard rebinds. On this rig the
allowed set is Moza {8,9,10,19,21,22,34,35,40,48} + shifter {9,10}, which
excludes the observed phantoms.

Verified by re-running the same reproduction: **0 ENTER events** (was 1 per
keypress), 3 phantom buttons logged as ignored, the keyboard LEFT arriving
alone.

Noted in passing: with the wheel parked at full lock (left there by the FFB
sign probe) the steering axis auto-repeats LEFT into the menu ~3.5x/s, which
is correct behaviour for a wheel held off centre but worth a troubleshooting
line.

## 2026-09-05 - Independent assessment baseline

Completed an independent source and evidence review of the collection,
modified MAME and wheel toolkit. Five dated reports in docs/reviews/ cover
product/reliability, widescreen and draw distance, recorded gameplay testing,
FFB collision quality, and speed telemetry beyond OCR. Six existing V-Unit
captures rechecked at 100.0000% native equality; both generated shader headers
and vendored force headers checked. No new live gameplay or wheel actuation
was performed. Native equality is explicitly a bounded reference result,
not acceptance of the user's moving-gameplay visual reports.

The user authorized committing/pushing the assessment baseline, then improving
implementation with emphasis on automated testing and diagnostic evidence.
The next work prioritizes tests that fail reliably and isolated recorded-drive
replay. Physical wheel output stays disabled during autonomous graphics tests.

## 2026-09-05 - Recorded gameplay and diagnostic foundation

After pushing the assessment baseline (collection d099c2f/tag
assessment-2026-09-05, MAME fork/poc/quadlog 58203bb1), implemented the first
diagnostic milestone authorized by the user. See
docs/reviews/2026-09-05-implementation.md for complete changes, measurements,
retained evidence and remaining findings; docs/DIAGNOSTIC-REPLAY.md for commands.

True MAME INP recording now retains effective analog/digital inputs, initial
NVRAM/config, executable/dependency fingerprints and native screenshot/time
evidence. A scripted USA drive reaches Golden Gate Park gameplay. All 6,000
input frames and 100 native snapshots match on identity replay and on the rebuilt
MAME candidate. Live GL recording also matches native playback; a bounded race
interval produced 32 backbuffer BMPs with stream/present/queue metadata and zero
reported drops in that interval. These labels are asynchronous, not scene fences.

Oracle/capture/renderer tools now fail on incomplete or mismatched evidence.
21 hardware-free Python tests pass. An actual one-pixel reference corruption
in a separate capture copy is rejected (99.9995%, exit 1); original capture-8000
remains 100.0000%. Strict Zeus comparison correctly fails at 93.6313% color /
75.6636% depth. Native equality does not clear live gameplay defects.

Toolkit v0.10.0 (47b06f08) provides shared source-force rise detection; its native
and managed tests/CI pass. MAME 1c420f32 uses pre-gain event detection including
idle, scales supplemental cues with strength and logs results. Offline replay
of 1,491 motor rows yields the same 13 candidate times at strength 25/50/100.
No actual collision labels or physical wheel acceptance are claimed.

OCR hold now counts consecutive missing frames; raw/fresh/held/age diagnostics
are visible. File-only telemetry initializes sources without UDP and logs
nonzero fresh USA speed during replay. Off Road speed remains unresolved.
Typed SDL emergency cleanup is checked with mocks. Source ownership and pin
checks cover collection and MAME together; the full patch series is refreshed.

USA selection interval 2600..3600: native headless 336.60% speed; live GL 99.99%
average but p99 host interval 77.64 ms and worst 124.41 ms. This instrumented
run identifies pacing to investigate, not a general explanation of the user's
unspecified car-selection slowdown. No speculative geometry, sky, seam or
draw-distance patches were added; ordered live resources and guest visibility
remain the highest rendering priorities.

Follow-up during final CI: Windows and Linux Python checks passed; the Linux
native analyzer exposed the toolkit profile loader's Windows-only separator.
Fixed in the canonical toolkit as v0.10.1 (c9b76b7), added actual file-loading
checks to its MSVC/Linux native tests, and updated both consumer pins. No force
math or profiles changed. The complete MAME export was also applied from
upstream files in an isolated repository and reproduced all 23 changed paths.

## 2026-09-05 - Recorded LA Freeway defects: measured fixes and reassessment

The user's human-driven `results/diagnostics/my-drive` (5,012 effective input
frames, 83 native snapshots) supplied the missing gameplay workload. It is
preserved unchanged. Findings and proof crops are in
`docs/reviews/2026-09-05-recorded-drive-findings.md`; compact machine-readable
evidence is `results/proof/2026-09-05-recorded-drive-milestone.json`. Experiments
continued into 6 September UTC, still 5 September on this rig.

Separate commits address the measured problems:

- `9451bb3`: raw snapshots with PNG encoding after exit. The original
  capture-adjacent callback median was 79.52 ms; raw capture on the same GDI/GL
  path reduced it to 18.25 ms. All 83 decoded native images match. Synchronous
  raw disk writes and optional GL BMP captures can still affect pacing.
- `18200e5`: D3D underneath the unchanged true-widescreen V-Unit GL overlay.
  Selection frames 1680..2280 improved from 77.59% to 100.00% emulation speed;
  race frames 2700..4800 improved from 83.73% to 99.99%, using raw capture in
  both runs. A launcher-created 600-frame recording also replays exactly.
- `e1bef95` / MAME `45a05364e11`: bounded quality-mode UV sampling fixes distant
  atlas bleed. At frame 3440, current road quad 782 maps 160 texture rows into
  one native pixel of height. Half-pixel rectangle expansion sampled unrelated
  red/blue atlas texels. Clamping to the quad's original UV domain changes the
  observed red index 0x1d36 to road index 0x1d19 without changing coverage.
  Six archived native captures remain 100.0000%; the rebuilt live executable
  passes all 5,012 original input frames and 83 native images.
- `fae3722` / MAME `eb4db8fc706`: whole-file patch validation before initial
  writes, backed by a shared native helper and negative integration evidence.
  The per-frame legacy self-healer remains per-word. The full exported series
  applies to upstream mame0286 files and reproduces all 24 historical paths.
- `0804eb8`, `9dc2723`: late patch application, effective program-RAM checks,
  matched-state scene-extension verification, and safe composition of configured
  experiments with widescreen defaults. Conflicting patch words fail.
- `28738f9`: USA full-widescreen object visibility, changing only the two
  horizontal culling operands and a guarded constant in unused padding. Three
  late-patched captures at 3440/3800/4880 add 50/5/5 entirely off-screen quads,
  preserve all original draws in order, and leave both native framebuffer
  pages, texture RAM and palette RAM byte-identical. Actual grass geometry now
  replaces blue backdrop through the missing left and right margin ground.

Applying the USA visibility patch from boot changes later guest execution:
32 original native snapshots differ, starting at frame 3120, with unchanged
effective inputs/time. Later car/traffic positions diverge. This is not proof
of unchanged physics, and that original comparison correctly fails. A separate
`usa-widescreen-candidate-case`, explicitly derived from the human INP with
archived candidate executable/patch provenance, passes all 5,012 frames and
83 images on identity replay. Do not overwrite the original case or conflate
candidate repeatability with equivalence to the older game execution.

The crack-filler reassessment is deliberately bounded: it changes zero pixels
in the investigated frame with production margin settings. Six other captures
show 0..594 changed pixels, including useful stale-gap removal and undesirable
copier streaks. Keep the reversible default unchanged, do not widen its radius,
and do not use it to mask missing geometry or wrong texture samples. Offline
`--crackfill` and `--marginfill` are now independent, matching the live controls.
The actual USA backdrop at 3440 has texture base 0x25f9, disproving the generality
of the old fixed low-byte 0x56 backdrop heuristic.

Distance remains open. Effective-RAM-verified stock/near/far gates of
80,000/20,000/160,000 produce 2,518/784/2,518 quads in the same sampled route.
The gate works but doubling it reveals no extra geometry here. Neither this
ineffective distance change nor the rejected polygon-only cull experiments
are enabled. Trace object residency, node creation, LOD and reciprocal lookup
around a specifically identified pop before proposing the next distance fix.

Validation includes 30 hardware-free Python tests, native patch helper tests,
nine ROM-free GPU quality checks on NVIDIA and Mesa CI, six 100.0000% native
GPU fixtures, actual rebuilt replay, and 240-frame launcher smokes for World
v2.4 and Off Road. Physical FFB stayed disabled. Remaining work includes thin
source-geometry seams, ordered live texture/palette/clear events and scene
fences, black-sky reproductions, new gameplay cases for the other games, and
attended collision-feel/wheel testing. The toolkit remains v0.10.1 / c9b76b7.


## 2026-09-06 — follow-through across graphics, replay, force and telemetry

Full evidence and limits: docs/reviews/2026-09-06-follow-through.md;
compact reports/images: results/proof/2026-09-06-follow-through/.

- V-Unit now applies quads/resource updates/CPU writes in order to persistent
  pages and presents only at a completed visible-frame fence. Atomic ring
  publication and process-private mappings replace volatile-only/shared names.
  USA 31 consecutive GL frames match across runs and a 100 ms/16 MiB stall;
  World v2.4 11 frames match. Five-second loading stall fails the stream and
  the harness rejects fallback. Zeus gains the same bounded lossless queue policy.
- Broad margin filling was suppressing valid skies and copying a boundary
  column across them. Gameplay A/B restores actual clouds in World and Off Road;
  22 GL frames preserve the core image exactly. MARGINFILL now defaults OFF,
  =1 is an explicit legacy experiment. Small crack-fill radius/default retained;
  thin source-geometry/near-tree seams remain. No universal artifact-free claim.
- USA's widened object culler changes a later player velocity/position write
  (3063 vs 3064; writer 9680 then 90AB). 20,001 hardware input reads and 1,921
  timestep-word writes agree; replaying all baseline timer values does not fix
  image divergence. Exact upstream cause remains open; no timer/physics hack.
- The object trace locates a traffic-car LOD switch at 8,000 units, distinct
  from the 80,000 far gate. Checked optional 12,000/22,500 LOD thresholds replace
  12 coarse quads with 60 detailed ones at frame 3058 (+48 total, same textures
  and palette). One car's image changes. No default far-distance extension.
- Optional bounded steering-axis impact mixer, explicit attended FFB recording,
  emulated-time raw/adapted motor traces, device API acceptance trace and labelled
  collision evaluation. No physical force tested. Candidates remain heuristics.
- USA numeric HUD text found at E632 (formatter A7C2, renderer 7A91). Guarded
  visible-page digit submissions now select numeric MPH with OCR fallback.
  Original 5,012-frame/83-image replay passes; 147 OCR misses recovered and 604
  readable OCR disagreements exposed. This is displayed speed, not physics/RPM.
  signals.csv adopts source/quality/time/units from shared telemetry contracts.
- Toolkit v0.11.1 released/pinned: native/managed impact and scalar contracts,
  strict managed instance selection (no missing/ambiguous/negative-index fallback),
  109 managed tests, MSVC/GCC checks and unchanged ten-profile conformance vectors.
- 35 Python tests and nine GPU quality fixtures pass. World v2.4/v2.5 and Off Road
  have 6,000-frame/100-image scenarios. Off Road's neutral first attempt is not
  driving coverage; the corrected H-pattern run moves onto the terrain. Exotica
  3,600-frame boot/attract replay matches recorded throttled settings; headless
  control diverges. Exotica gameplay/GL equivalence still needs its own cases.

MAME and collection changes are separate commits; patch export includes the full
mame0286 series. Original user recordings and rejected controls remain immutable.

Final force correction: the optional steering-impact detector consumes raw game
motor bytes before driver gain/clamp/slew. Structural force still uses adapted
bytes. A shared signed-byte adapter and compiled CI contrast verify a raw 126 /
adapted 20 pulse: enhanced detection at 100 ms, no legacy detection, both bounded
below 50% output. Both CSV formats pass. Menu cancellation also resets the shaper
tail. This is algorithm verification, not physical collision-feel acceptance.


## 2026-09-06 — Thin geometry, terrain ownership, Zeus gameplay oracle and distance follow-up

Detailed assessment: `docs/reviews/2026-09-06-seams-distance.md`. Compact proof:
`results/proof/2026-09-06-seams-distance/`; full immutable runs `next-*`.

- Fixed quality shader rejection of fine samples in native-empty integer spans.
  The new sliver fixture failed before the fix. Twelve GPU quality checks pass;
  both archived native captures stay **100.0000%** exact. Gameplay owner changes:
  Off Road 1,141 fine samples; World v2.5 181. These replace background pixels.
- Traced the Off Road diagonal sky seam to a 0.678435-pixel quantized T junction,
  matching material and UVs across polygons 125–127. Opt-in geometry alignment
  closes the tested seam using real terrain; final restricted blue count 634→0.
  It also alters interpolation inside adjacent triangles. Default OFF, native
  exact mode excluded. Python/C++ 12-case conformance passes. Local crack filling
  was not broadened; remaining large margins and World near-tree seams are open.
- IMPORTANT CORRECTION to prior Exotica conclusions: live Zeus skips CPU polygon
  rasterization, leaving black native race screenshots. Their equality was not a
  gameplay image oracle. Headless/live mismatch after 1440 did not establish
  emulation nondeterminism. Historical reports remain intact with this correction.
- Added completed-frame Zeus fences/receipts and explicit `--compare-gl`. A new
  6,000-frame first-gear Exotica drive has 21 real GL race images at 5400–5420.
  Complete repeats match all 21. One first replay exited at 4125 with 0x6E76003B,
  no retained stack/corresponding application-fault event found; cause OPEN.
- Double-rasterized Exotica control: 6,000 inputs and 21 GL images match; 77
  native images differ as expected because CPU polygons now exist. Injected
  consumer stop at 5500 restores CPU rasterization and exits cleanly at 6000;
  the diagnostic correctly fails the replay on fallback. Not an overflow stress test.
- Removed the old fabricated RPM mapping from packed speed text E632. Real
  loopback receives 5,012 JSON rpm_status=0 samples/Forza packets with RPM fields
  zero and speed still working; original human replay remains identical.
- Reopened distance over 293,609 samples / 500 object addresses. Nine objects
  reach 80,003–81,035 units in 15 samples; earlier short-window zero-candidate
  observation was incomplete. Late far-plane patch adds 97 quads at 4346 with
  every original draw preserved, but contributes ZERO final 4× owner pixels and
  changes no visible pixels. More quads alone does not prove better distance.
- Full remaining-drive LOD experiment (12k/22.5k after frame 2800) adds 5.2528%
  DMA workload at 99.9975% callback emulation speed. All inputs match; 37 native
  snapshots intentionally differ. Keep both distance experiments outside defaults.
- USA guest-state dependency narrowed to the player's orientation matrix near
  10AFB, copied into matrix multiplication at96D8, then the velocity transform.
  First difference remains stock3063/wide3064 despite identical hardware reads
  and timestep writes. Earlier causal producer remains open; no physics hack.
- Six-case serial local suite passes original USA, widescreen USA, World2.4,
  World2.5, Off Road and actual Exotica GL frames. Named callback ratios are
  ~100%, including USA's selection countdown. Missing/uniform reference cases
  fail explicitly. Forty-three harness tests and native conformance pass locally.
- MAME commits: 921bd047cc6 (RPM),53ad0796148 (optional joins),fd158fa8511 (thin
  coverage),377ddc06db1 (Zeus fences/fallback). Full105-commit mame0286 export
  reconstructs tree f3af6c85edc8c9df8b03e085662b6d472826f4c6 exactly.
  Toolkit stays at v0.11.1/b726d56, unchanged. No unattended physical force.


## 2026-09-06 - launcher graphics experiments and retirement of Margin Fill

Added Settings -> Display -> Graphics Experiments with a per-game selector.
Seam Alignment works for the three V-Unit families at enhanced scale; Detail
Distance and Draw Limit are gated to the verified USA v4.5 set. All default OFF.
The latter is labelled experimental with no visible gain in the tested scene.
The detail patch's prior measured DMA increase remains 5.2528%; no new distance
benefit is claimed by adding the controls.

Shared harness/graphics_options.py resolves every launch path and combines
selected USA words with the automatic widescreen patch, rejecting conflicting
custom patches. Explicit MIDV_PATCH remains a developer override. Turning flags
off stops using stale combined words. The launch log reports the effective seam
and margin settings. Missing selected/custom patch files now fail visibly.

Margin Fill was the broad edge-column stretching/background-suppression
experiment that harmed World/Off Road skies. It is now absent from the normal
shell; old INI values cannot re-enable it and are reset to zero on save. The
explicit developer environment/API path is retained for comparison. Crack Fill
is unchanged, with a corrected hint distinguishing small gaps from missing terrain.

Verification: 51 local Python tests pass, including eight new settings/patch/UI
persistence cases. Four actual offscreen shell renders inspected at 1920x1080;
proof in results/proof/2026-09-06-launcher-graphics. No C++ or shader change and
no new rendering-performance or physical-wheel claim. Stream Deck executes this
source tree; vunit.exe remains the prior verified hash and needs no rebuild.

## 2026-09-06 - Endprodukt/Fanatec cabinet and force-polarity review

See docs/reviews/2026-09-06-exotica-polarity.md for primary-source links and the
next test matrix. Identified FFBPluginRacerMAME, its GUI, and MameRacer289.2.
README requires Wheel Invert On, Sit Down AND Dedicated. Upstream PR16057 is
open and says the old Wheel Invert label means FFB/shifter polarity, not steering.
His plugin's c3f2ea6 explicitly negates Exotica force for that DIP setup.

Correction to interpretation in the September 4 chronology: reversed measured
motor force did not prove reversed vehicle steering. The input-mirror workaround
needs independent gameplay validation; it is not removed or declared broken here.
Actual current launcher functions against six temporary configs show Sit Down is
conditional on complete shift bindings, while Wheel Invert is set independently;
existing Kit survives. Local rig already has Sit Down/On/Dedicated. Small JSON
proof retained under results/proof/2026-09-06-fanatec-review. No emulator or
physical force launched by that check. Also flagged Exotica gain-before-stop-code
normalization, gain/clipping portability, and native MAME-menu visibility.
No FFB sign/gain/DIP runtime changes, no plugin install and no Fanatec cure claimed.


## 2026-09-06: Germany Level evidence, responsive Esc and external session clock

- User recorded a complete World2.4 Germany race with real wheel/FFB. Named
  Germany Level at results/diagnostics/world-germany-20260906: 9,269frames,
  160.00815328emulated seconds,154native snapshots. Preserve all original inputs,
  executable, initial state and trace data. Added as seventh local regression case.
- Fixed invisible paused V-Unit menu: completed-frame gate prevented UI rendering
  after Esc paused the producer. MAME daed6ea2a19 committed/pushed fork/built;
  SHA256923206d92188abe773f49a8abb7a5829a366966ea3898109081833307c23ca6c.
  Export106patches recreates d026555b2c855ed9bf489b07fd8bdc568d1c7e85. Normal
  Stream Deck executable path unchanged; racing mame.exe never touched.
- check_menu.py reproduces failure before fix; USA/World/Offroad now pass8visible
  states, paused-frame stability, CRT toggle, resumed frames and clean menu Exit.
  These are explicit no-force emulator key-handler tests, not OS input injection.
- record_drive.py preserves saved shell graphics and steering settings; force
  retained only with --with-ffb. External clock defaultsON and follows emulated
  seconds/frame, including boot/selection, stopping on pause. --no-clock disables;
  replay --clock opts in and fingerprints current Lua override. Flush every6frames,
  50ms external poll; passive Windows panel visually verified. 54Python tests pass.
- Germany archived identity and new full live candidate pass9269inputs/times and
  154native images. Candidate135GL captures document current defects without an
  original GL reference. Clocked dense prefix8240passes1141GL captures7080..8220,
  drop0. Earlier exact-end8220attempt correctly fails missing final GLframe8219+1.
- D/A transition1320/22.79s is corrupt natively and in GL; original-program-word
  control matches1380inputs/23native including that badframe. Not proven upstream
  or hardware-original. Black road at7280/125.67s isolated during off-road driving:
  state point(-61,275) has no current covering polygon, not a black texture fetch.
- New World state's exact check exposes2differing native pixels:99.9990%, at7,250
  and77,297. Recorded as a failure; no threshold relaxation. Existing capture8000
  remains100.0000%. No shader or distance patch changed in this batch.
- Live FFB trace:7358constantAPIacceptances/0rejections, peak0.800012;27impact/rumble
  candidates. Steering impact enhancement0.7468rawrace samples unchanged bydriver,
  range-126..126;8.9181%samples atlimits. Offline4msshaper29candidates differs in
  scheduling. No collision labels or physical torque measurement. Trace includes
  7.43shostgap near Escpause9201; don't call whole-run average a performance fault.
- Full report and compact proof: docs/reviews/2026-09-06-germany-level.md and
  results/proof/2026-09-06-germany-level/. World clipping, transmission texture
  lifetime, pop-in and perceptual crash differentiation remain open investigations.
- Follow-up matched-state control: bypass both existing World big-poly left reject
  calls0x387/0x3C9 at7276, verify2effectiveRAMwords at7280. Replay passes; geometry
  unchanged756quads, qualitypixelschanged0; geometry-extension check correctly
  fails for no additions. Do not loosen these bounds blindly or ship this bypass.

## 2026-09-06 — World route controls, shadow resolve and Off Road sky bounds

Full report: docs/reviews/2026-09-06-world-rendering-and-replay.md. Compact proof:
results/proof/2026-09-06-world-visibility/. Original Germany and failed controls
are intact. Automated runs disable physical FFB; toolkit remains v0.11.1.

- Native dd12bed67f0 fixes World7280 exact pixels (7,250)/(77,297): approximate
  reciprocal arithmetic shifted half-pixel edges by an ULP. Scale1 now rounds
  double reciprocals to float; quality mode retains fast math. World plus both
  USA captures verify 100.0000%. CPU oracle handles signed coordinates and wide
  palette arithmetic under NumPy2. Sloped-quad GPU fixtures match independent CPU.
- Native f40c28f8e0a also resolves tagged enhanced dither before output scaling.
  Alternating tag3 pairs blend; opaque checkerboard art stays intact. Exact masks
  remain1; Zeus shaders unchanged. 20 GPU checks and 59 Python tests pass.
- Built root vunit.exe SHA256 4553e2afb939e4fea88238b62c1180b9c2e3dcc9bee58c102fed49c878237893.
  The108-patch export reconstructs tree79f28f8dc867012d19be9807d4a3df7980c12372
  from mame0286. Regeneration has no shader diff; native helpers/toolkit match.
  Stream Deck uses this source/executable; racing mame.exe untouched.
- Off Road black corners reproduced at1560/1800: flat blue quad stopped at0..512.
  Existing instructions use dead R0 for-86, R3 for598, already-zero R2 mantissa
  for Y. No extra instructions/submissions. Matched1560 changes only four X words;
  all other draws/nativeVRAM/texture/palette identical. Full6000-frame final-exe
  replay passes100native images/all inputs,9completed sky captures, drop0.
- World object sphere-X tests B9/C0/C4 reject some terrain before DMA. Bounded
  helper108..10D adds173quads at7280, preserving originals/order. Two native-edge
  words change inside added coverage.5940 adds9, World2.5/4800 adds1, resources
  identical. Explicit --object-visibility attributes possible native writes but
  cannot certify appearance or physics equivalence.
- CRITICAL: full World extension changes route. User saw veering~54external sec.
  First camera diff2732 (~47.16s); all4503actual ADC values/PCs match1800..3300,
  read times differ40ns starting1802. Original and re-recorded INPs produce the
  same divergent camera. Original-bounds helper passes; wider left-only and
  right-only each diverge2732. Extra admitted guest geometry triggers it; exact
  timer/state dependency OPEN. Normal2.4/2.5 patches restored, experimental file
  isolated. Failed derived identity replay remains failed; do not bless it.
- Final original Germany live replay passes9269inputs/154native images. Driving
  comparison1800..9200 matches7401camera samples/22203ADC reads including exact
  times. compare_world_motion.py checks camera/ADC independently and rejects
  malformed or incomplete traces. derive_case.py promises repeatability only.
  No fresh recording needed.
- User1:37 means GAME ELAPSED TIME, around7340+ external frames. Final dense GL
 7200..7440 still reproduces a small left wedge near1:36.78. Neighboring offline
 7340 adds50offscreen quads with identical originals/resources (including a rival).
  Live/offline scenes differ slightly in time: not proof the transient is fixed.
- Clean official MAME0286/0289 reproduce D/A corruption1320:1380inputs/23native
  images match. Atlas byte398200/mappedBCC100..BD08FF is used through1358 while
  loaderB25/B27 overwrites18432words in overlapping blocks1282..1286. Fixed empty
  diagnostic: World submits15used words, not16.11482actual DMA records captured.
  Causal hold restores D/A, title still corrupt, garage normal1380; all1382inputs
  equal, only sampled1320changes. Frame-number hold NOT shipped; fix asset lifetime.
- World distance trace349365samples/900renderframes/701objects:15914samples from
 106objects beyond80k within160k, max122528,28model transitions. Global100k alone
  reads beyond5000-entry reciprocal table and makes stray giant polygons. Safe
  old-clamp control2060 adds163quads/all1750originals unchanged but mountain is
  oversized. Bounded read extension5000..6250 plus five clamp pairs makes2651hits
  and visibly corrects perspective without overwriting adjacent RAM. Diagnostic
  only; route behavior and mountain-base appearance remain open. Goal remains
  no noticeable pop-in over validated routes in every game, requiring projection,
  residency and guest-work dependency analysis.

Final executable cross-game checks also pass USA original/wide (5012 inputs and
83 native images each), World2.4/2.5 synthetic (6000/100 each), and Exotica (6000
inputs/21 completed GL images), including configured timing gates. Combined with
final Germany and Off Road runs above, all seven local cases pass at hash4553e2a.
See proof final-regressions.json; earlier world-renderer-final-suite used the
previous executable and is not the final-build evidence.

## 2026-09-06 — World outgoing UI assets and conservative road visibility

Follow-up: `docs/reviews/2026-09-06-world-assets-and-road.md`; compact evidence
in `results/proof/2026-09-06-world-assets-road/`. Native commit 2bf1048a1cf adds
display-only retention of World 2.4's outgoing transmission atlas. The actual
UI model list controls lifetime. Texture writes and native rendering remain
unchanged; the new atlas is uploaded after those models unlink. Scale 1, other
games and World 2.5 are gated out. Reset and state load discard retained assets.
Build SHA256: 7eaf9ce8888190a5a6b8c30dd698fb57175c644779d4c65bf52cc083c74263fb.

- Loader/model probes identify CD828E->BCA280 loading, D/A and header model
  owners, and byte span 393000..3C0FFF. A texture-only semantic write hold
  releases 30,080 words at frame 1379 and fixes both panels and header. Product
  retention begins at native frame 1276 and releases at 1378; Lua receipts use
  their own callback count.
- All 21 completed GL images at 1200..1400 match that semantic control exactly.
  On/off differs only at sampled frames 1280..1370. Full original Germany:
  9,269 input/time samples and 154 native images pass; 7,401 camera samples and
  22,203 ADC reads, including exact read times, match.
- The failed incomplete first GL capture and intentional native frame 1320
  difference in the guest-memory semantic control are retained.
- A Lua probe failure formerly skipped scheduled exit until timeout. Load and
  callback errors now request clean exit; evidence rejects Lua/snapshot errors
  even on exit code zero. Both real error controls exited cleanly and failed
  validation without reaching timeout.

Completed GL 7340 (HUD 1:36.78) matches offline dump 7338. Native (-82,355)
has no owning polygon and palette index zero. The previous +86 object extension
adds 50 draws but leaves the hole. Big-polygon bypass adds zero, slow face bypass
zero, clip-flag bypass eight, and all-face bypass 300; none fixes it. Bypassing
horizontal object checks C0/C4 adds 145 and restores road object 117A4, model
CA06A9, radius 2461, depth 2827.

The projected radius is too narrow for this nearby off-axis model. A 1.25 radius
factor (wide side-plane factor approximately 1.203), plus bounded X -86..598,
restores the hole with 77 new quads. All 966 original draws/order and native video,
texture and palette RAM remain unchanged in this matched scene. The recovered
pixel uses palette index 17982. Near/far, vertical, face and vertex clipping remain.
This is a separate checked game patch and optional World Terrain Visibility
control, not a far-plane increase or a crack filler.

The user accepts extra drawing work and a new recording when it improves play.
Old-route equivalence is diagnostic, not an absolute veto. Original Germany stays
immutable; candidate repeatability, performance and fresh attended evaluation
are required. The drawing-work/route dependency remains open, and derived cases
do not establish human acceptance.

The full derived Germany candidate and identity replay match 9,269 inputs and
154 native images, retaining 117 sampled differences from the parent. Driving
frames 1800..9200 run at 100.01%/100.00%, callback p99 26.14/25.56 ms, worst
68.63/69.86 ms. These are not GPU latency or a guarantee of stutter-free play.
World 2.5 headless candidate runs match 6,000 inputs and 100 native images; both
retain 29 differences from the parent. The launcher option is reversible and
restricted to verified World revisions in widescreen.

61 Python tests, 20 GPU quality fixtures and the retained-atlas native unit test
pass. USA/World exact captures remain 100.0000%. The full native export has 109
patches and reconstructs tree 1dc9cd3cb86a8599321a71286c8924906d6890bd.
Toolkit v0.11.1 is unchanged.

Final default-build checks pass all seven original local cases at hash7eaf9ce:
USA original/widescreen, World2.4 synthetic/Germany, World2.5, Off Road and Exotica,
including configured timing gates and Exotica's21 completed GL images. See
proof final-verification.json. These are separate from the new terrain candidate's
repeatability checks. Native atlas unit was rerun successfully. Initial branch
CI34062918005 passed all four jobs; final evidence commit receives its own CI run.

## 2026-09-06 — Fresh Germany baseline, impact controls and distance limits

Review: `docs/reviews/2026-09-06-world-distance-and-impacts.md`.
Proof: `results/proof/2026-09-06-world-distance-impacts/`.

- Attended `world-germany-extended-20260906`: World2.4, scale4/margin86,
  conservative terrain visibility ON, FFB80. Full read-only lifecycle identity
  matches8783 input/time rows and146 native screenshots. Original case preserved.
- User still reports distant pop-in and weak impact feel. Terrain visibility is
  side-edge repair, not distance. Renamed menu to Widescreen Terrain: ON/OFF.
- FFB trace:8317 raw/adapted writes, all equal, -126..126;6621 accepted constant
  updates,26 successful rumble receipts; Crisp2/20ms, steering impact mix OFF.
  No physical torque or confirmed collision detection is implied by API success.
- Offline80% standard peak0.799796164/RMS0.328623032 versus optional mix
  peak0.707636356/RMS0.246431708. Both26 candidates. Optional25% pulse budget
  also lightens sustained steering, so no claim of stronger crash feel.
- First candidate45.076s anchors to completed frame2612. DenseGL2520..2700
  shows hill crest/jump and no obvious nearby car contact; no labels invented.
- Added per-game launcher Impact Cues, defaults OFF, exact World revision saved.
  Shared resolver preserves explicitOFF precedence over family/global settings.
- Force analyzer --frames maps emulated candidates to completed frames; labels
  and anchors reject host-time input traces.65 Python tests pass, actual menu
  offscreen previews inspected. Native executable/shaders/toolkit unchanged.
- Lifecycle1750 frames/525032 visits/697 objects:13601 visits from94 objects
  beyond80k within160k; max depth-minus-radius117424,44 model transitions.
- Bounded Lua projection diagnostic parameterized to80,016..160,000. Matched
  control/100k/160k each101 completedGL frames; inputs/time equal, candidates
  correctly fail strict identity on4 changed images.100k uses143145 extended
  reads,160k182338; interval1952..2200 speed100.01%/100.09%/79.95% respectively.
  Mountain silhouettes change; clean pop-in removal not established. No distance
  candidate promoted. Next isolate a mountain model's first submitted geometry.
- Downloaded cheat0279 includes all four games and World2.4/2.5 XML. Revision
  addresses differ; reuse MAME XML engine with recording provenance next. Files
  are not installed/enabled/redistributed in this batch; Cheats submenu remains open.

## 2026-09-06 — Selective mountain admission and scenery provenance

- Review/next steps: `docs/reviews/2026-09-06-selective-scenery.md`.
  Proof: `results/proof/2026-09-06-selective-scenery/`.
- Read-only World2.4 object->DMA provenance1998..2040 passes2042 input/time rows
  and34 native images.36,395 matched submissions/1,158 explicitly unmatched.
- CB1A8B/object13E40 is the mountain above Germany's first bridge. It crosses
  the far gate at2027 (80019->79839), then15 polygons span107x103 native pixels.
  Isolated captured texture rendering confirms its identity; no LOD swap here.
- The global100k projection experiment shrinks this mountain to87x82 and changes
  already-visible mountains. More admissions do not automatically improve appearance.
- Selective PCA1 read override to160k for CB1A8B, with A8/A9 and projection clamps
  left original, admits it earlier at the existing size. This deliberately keeps
  far-clamped perspective. It is not a correct-perspective fix for all objects.
- Late matched trace1998..2040 adds exactly15 CB1A8B polygons per draw1999..2025,
  removes/changes zero originals; no submission differences2027..2039.
- Live1800..2200 experiment:15 earlier completed images differ only in mountain
  region; all86 completed images2030..2200 match. Timing1952..2200=100.03%.
  Native candidate comparison correctly fails on1860/1920/1980; inputs/time match.
  Full-route/earlier admission boundary/handling acceptance remains open.
- CA57F3 is a tree billboard, texture11066/palette18176/U3..83/V0..88; texture
  extraction confirms artwork. Resident object14118 at99830 depth-minus-radius
  draws5x11 under100k projection. Tree perspective/transitions need a separate test.
- Added two bounded diagnostic Lua probes; no native/shader/toolkit/product
  defaults changed. Prioritize scenery catalogue, guarded native candidate,
  pop-event clips, full-route repeatability, then cross-game adapters. Same Germany
  recording remains sufficient. Keep other FFB/Cheats stretch work in the queue.

## 2026-09-06 — Native selective scenery and full Germany repeat

Review: `docs/reviews/2026-09-06-native-scenery.md`; proof native-scenery directory.
Native3dc426ec75d, binary075d16a7cc7648b3dd61b19fd2fda264cc476ebf48584c76256847371ddc5ffb.
110 exported patches reconstruct b2b9bab9399b97521bfb2343435deaf76f5ef97a exactly.

- Identified mountainCB15F8/CB171E alongsideCB1A8B. Native World2.4-only policy
  admits these up to160k, preserves original far-clamped perspective. CA57F3 tree
  extension instead admits only originally rejected trees fitting wholly inside
  extended projection range, supplies valid reciprocal reads at six verifiedPCs.
  Original entries/clamps unchanged; no guest RAM writes. Context is save-state
  registered/reset; optional scenery.csv counts admissions/reads per frame.
- Tree provenance1998..2040 adds42quads across21drawing frames, zero originals
  changed/removed/reordered. Native path matches final Lua geometry exactly.
  Object14118 has5x9native extent at1999. First probe used DMA flags instead of
  object flags and changed nothing. Next nested-read probe generated giant quads;
  evidence retained, extent negative control fails. Final tap avoids nested reads.
- Full derived8783-frame Germany case and repeat match all inputs/time/146native
  images. Six earlier parent snapshots1680..1980 differ; all later sampled native
  images match. Driving1800..8780 speed100.005% both runs. Per run371extra mountain
  admissions/660tree admissions/5280virtual reads, maximumindex7361 of10000.
  Repeatability is not physical acceptance or proof of exact original route.
- Dense completedGL1600..2400 every4 gives201images per candidate/control.
  103images1620..2028 differ; all93images2032..2400 identical. Mountain appears
  through garage exit and during starting sequence, preserving its later shape.
  Conifer extension alone has not established a visible forest improvement.
- Added revision/scale/widescreen-gated Distant Scenery menu, defaultOFF. Added
  compare_scenery.py with duplicate/order/unknown-model and optional extent checks;
  replay/derive_case archive explicit native scenery settings.67Python tests pass.
- Identified next treesCA5833(mirrored conifer),CA5863/CA5896(broadleaf), radii
  1950/818/1252. They cross original far gate2031..2193 and need their own bounded
  geometry/GL validation before extending the native allowlist.

The default075d16a7 build passes all seven original multi-game cases, including
configured timing gates and Exotica21completed GL images.67Python tests and all
four branch CI jobs34067459020 at96ea041 pass (including20GPU fixtures and native
scenery unit). Full export reconstructs the native tree. No physical force was
used; the new option remains defaultOFF. See native-scenery/default-regressions.json.


## 2026-09-06 — Four tree variants and full-route appearance tracing

Review: `docs/reviews/2026-09-06-scenery-coverage.md`.
Native5ca501570a5 / binary2e3ac3f32e791516a7b0f8d0339cf7cf98c120e90a02b14b94ce0f34acc09f56.
Four verified tree cards now included in opt-in World2.4 Distant Scenery.
Bounded experiment adds289quads/21drawframes, zero originals changed/removed/reordered;
native matches Lua geometry exactly. Full8783/146 Germany candidate repeats,
~100.005% driving speed, maximum reciprocal index8120. Parent10native images differ.
Trees-only completedGL201frames vs scenery-OFF:109changed images, maximum49pixels;
a small horizon improvement, not a forest pop-in cure. All7defaultcases pass.
The long LuaGL attempt timed out at2252/164images; retained as failure. Native
completed201images and both full cases normally. Shared164images match native.

Read-only scenery-events fullrun matches8783inputs/time/146native images. Records
3584completed page-control runs,4578059matched quads,6700unjoined shared-path calls,
16323appearanceevents in about1.77MB CSV. Bounds ranking is a candidate locator,
not visible-pixel measurement or proof of a bug/LOD/asset loading. First gate
observation is not creation time. Activation trace finds CCF288 allocated2991,
pendingflags2000, becomesactive1000 at3017 and firstdraws3019 inside80k range.
Next candidates: additional mountainsCB2314/CB21A2 and groupedforestCB2375,
plus pending-list activation. No physical FFB or user preferences changed.


## 2026-09-06 — Expanded mountains/forest and activation mechanism

Review: `docs/reviews/2026-09-06-expanded-scenery.md`.
Native abe4b98aa38, binary SHA256
55578f8a06a81a78391119e4bad29b673b90e7e67ea2d6d29907adec1fe8ee90.
Adds mountains CB2314/CB21A2 and forest strip CB2375 to World2.4-only opt-in
scenery. Forest uses original clamped projection and its own counter. Small-tree
projection remains limited to the four verified cards. No guest RAM writes.

Bounded Lua adds938 quads across99 complete scenes, preserves originals/order.
Strict frame check retains two unchanged HUD quads spilling2171->2172. Native
new-model geometry matches Lua exactly; all native scenery adds2184 quads in the
same scene comparison, retaining every original in order. Bounded GL131completed
images:90change, max1214pixels at2144, all2184..2240match. Full native GL201images
vs firstnative build:143change, max1234pixels, last2192; all2196..2400match.

Full native Germany candidate/repeat8783inputs/time/146native images agree;
parent10images differ. Driving speed100.0041%/100.0048%, callbackp99 26.47/26.19ms.
Both912mountain/3964tree/277forest admissions,31712reads,maxindex8120.112patches
reconstruct native tree ae27265e06a1da7ae7646c9ea888857a538ad12f. Cross-game default
suite remains separately tracked; no physical FFB during automated runs.

Single-object activation experiment CCF288: pending2991, active3017, firstdraw3019
inside originalfar. Decrementing its activation-section comparison by1 moves
activation2999/draw3001, adds54quads. Original order changes in scene3019: geometry
validator correctly FAILs.41completed GLimages show9changes,max22pixels; nearby
trees obscure this hillside. Oddframe3019 isn't in the every2GLcapture. Not
promoted. Next stronger candidate: known mountain CB1A8B returns at6093, already
insidefar53744 and plainly visible over the road around elapsed1:15.

GL comparison now reports pixel counts/bounds and first/peak/last contact sheets,
validates sparse global-frame cadence and rejects overwritten/reused filenames.
README telemetry claims corrected: USA numeric HUD with OCRfallback, WorldOCR,
RPM unavailable (oldUSA RPM mapping was packed speed text).

Expanded-scenery final default suite: all seven cases PASS at55578f8a, including
timing gates and Exotica21completed GL images.71Python tests and native scenery
unit pass. CI34070790847 at e81bc4a passed all four jobs. Full proof in
expanded-scenery/default-regressions.json; continuing later mountain activation.


## 2026-09-06 — Earlier background activation and completed near-4K evidence

Native e8b8fc3be9c, deployed SHA256
 d520c414c8bae335abe316695f78ff4794513e97313b000b10b28ff24dfcec47.
Review: docs/reviews/2026-09-06-background-activation.md. Five known mountains and
forest CB2375 advance by up to8 pending track sections, World2.4 only, defaultOFF.
Lead0 retains prior distance/projection policy and reproduces its8783/146 case.
Guest performs list transfer; no hook writes RAM. Small-tree activation unchanged.
CB1A8B was allocated5985 but pending until6091, firstdraw6093 alreadyinside80k.
Single-model lead8 activates5991/draw5993; visible6041..6094 as bend uncovers it.

Full native candidate/repeat8783inputs/time/146native images agree; parent12images
change. Driving100.0050%/100.0045%,callbackp99~25.6ms. Both1049mountain/3964tree/
355forest admissions,31712recipreads,max8120;12early activations at5991,6003,7585,
7599 (3each).113patches reconstruct0c8391ca7c8749bef3da2d2d8458d422fad11474.
All7defaultcases PASS, including timing and Exotica21completedGL;72Python/native
unit pass. CI34073144803 atb06c26b passes all4jobs.

Geometry5900..6140 adds2578, changes/removes no original polygon, but strict order
FAILs scenes6077/6093/6119;6119 has49possiblyoverlappingpairs. Preserve that failure.
Initialsortkey80000 vs earlier updateddepth is a hypothesis still being traced.
DenseGL5940..6280:341completed at512x451 output/4xinternal;100change6023..6122,
max6839pixels6093; all158images6123..6280match. LateGL7540..7780every2:
121completed at3824x2073;11change7694..7714,max107075pixels7712 atleftedge;
all sampled7716..7780match. Near-4K initial attempts saved100/102of121 and FAILED
completion; extending stop7784->8000 let both finish. No dropped stream messages.
Capture overhead must not be confused with normal-play timing.

Harness e7e82b6 retains missing/unexpectedframes, dimensions and maxqueuedbytes
on incomplete capture, preserves independent native/input comparisons, rejects
insufficient budgets before launch and refuses legacy asynchronous receipts for
explicit completed-frame requests.74Python tests PASS;CI34074373829 all4PASS.
Narrow allocation probes that started too late correctly failed; explicit
watch-existing mode is being verified rather than weakening default requirements.
Broader pending-list diagnostic finds individual treecards pending2008 as well
as many unverified models. Investigate selectively; global change not promoted.


## 2026-09-06 — Global strategy and native-port reassessment

User returned and requested global distance solutions, research into other games,
and a fresh assessment of decompilation/recompilation. Review:
docs/reviews/2026-09-06-global-distance-and-native-port.md. This changes the next
priority from more individual-model exceptions to shared section loading and a
host-side static-scene draw path independent of guest simulation.

New primary-source finding: Jeff Harris's jeff-1amstudios/cruisin-usa native C/SDL2
port, inspected at 5eeeb65f0c716aa20435286f7d39ea0a99dbc17c. It is incomplete, not
built or independently play-tested here. Available USA 4.4 assembly plus source/ROM
walker for 4.5 gives a concrete source-assisted route. Original BACKGRND/OBJ code
documents separate group loading, active/inactive distance gates and finite pools.
World layouts differ; do not transplant USA addresses/fields. No comparable source
availability established for the other three games. Exotica uses C32, V-Unit C31;
CPU translation could share infrastructure but Zeus2 rendering remains separate.
OutRun2006 section-node union/dedup and OpenMW distant object paging are useful
precedents. Faithful recompilation alone preserves original distance limits.

Executed global pending 0/8 comparison with selective scenery OFF: both 201 completed
GL images 5900..6300 every 2, original-prefix control PASS through 6304. Candidate
images differ from 5910; seven native snapshots differ. 421 camera samples cover
5880..6300 each, first camera difference 6184. 1,263 ADC reads each with identical
frame/value/PC sequences, different timestamps first index 81. Route comparison
FAIL retained; later pictures include different driving state. Cause (execution
time vs activation effects) not isolated. Proof in
results/proof/2026-09-06-global-distance includes reports, hashes, baked scripts,
completed GL comparison/contact sheet and raw camera/ADC traces. Reanalysis of
archived traces reproduces the retained failed report exactly. This test does not
prove a global strategy impossible.

Explicit watch-existing activation mode verified on 11C04/CB2314: 189 control
writes, 575 candidate writes; initial assignment still required by default.
Wrong CB2315 negative correctly fails the model guard. These probes succeeded
diagnostically, while parent image identity FAILs remain. New mutating Lua pending
and four-tree probes are diagnostics only.

Unbuilt global far native draft archived as applicability-checked patches under
docs/experiments/world-global-distance, removed from active sources. Missing tick,
checked game patch, harness integration and runtime validation explicitly documented.
Deployed binary remains d520c414/native e8b8fc3be9c; no new launcher option or
preference changes. Native helper sync PASS; all 74 Python unit tests PASS.
No physical FFB tests.

Proof-byte check found Git newline conversion changed the archived source hashes.
Scoped attributes now preserve these evidence files verbatim. Extracting the raw
camera/ADC blobs from the Git index reproduces the complete failed comparison,
including source hashes; all archived proof bytes match their staged blobs.
Patch-artifact whitespace checks exclude only their required unified-diff context.


## 2026-09-06 — Global World distance trial, native counters and replay decision

User approved finishing the global native prototype, controlled Germany comparisons,
and a bounded decision before investing in a partial native scene path. Native
9ea71f601b3 adds explicit MIDV_WORLD_FAR80000/100000/160000, shared pending lead0..8,
and diagnostic CPU percent100/125/150/200. No model or level allowlist. Checked
far/clamp RAM patch plus virtual reciprocals in host memory; guards/log failures
fail the experiment. Canonical native/world_distance.h, synchronized to MAME.
Cold-start replay tested; no interactive reset/save-state certification yet.

Six full 8783-frame Germany runs completed with146 native images,321 completed GL
images each,7281 camera samples and21843 actual ADC reads. Zero-extension control
matches all native images; all frame inputs/times match. All candidates change the
original route. Normal CPU emulation speeds99.9996..100.0001%; 2x/lead8 records
7425141 extra reciprocal reads and347915 gate tests in the extra range, not unique
objects. The prior ~80% heavy-Lua result did not predict native performance.
Far-only1.25 camera matches again1702..3099 after selection divergence; actual ADC
values remain identical throughout. Lead4 has a real wheel-value difference at2299:
105->104, read delayed5.8us; camera diverges2300. Motion diagnostics now expose
matching intervals and actual ADC differences, without equating camera and scene.

Bounded Lua controls keep original history to5900, intervene5900..6140, and capture
201 GL images5900..6300 every2. Original prefix6304 PASS. Both candidates match
camera words through6183 and1263 ADC frame/value/PC sequences; timestamps differ,
then camera diverges6184. Projection restore does not undo earlier activation.
MountainCB1A8B first attributed submission6093 ->6037 ->5981 for original/1.25x4/2x8;
112 frames ~=1.93s, not first visible pixel. Corresponding model uses different
object slots between runs. Fullsize control/candidate each complete8/8 images at
3824x2073; frame6040 inspected, mountain/buildings visible earlier in2x candidate.
Traffic/render phase still differ despite matching camera words. Overview video
and PNG retained; no all-texture-correctness or pop-in-elimination claim.

125% CPU experiment also completes at full speed but clock alone changes138/146
native images and route. Camera cadence3500..5800 remains1150 updates/2300 intervals
at both100/125. Normal CPU retained. A separate full derived2x/lead8 case plus
identity replay matches8783/146; parent120 images differ. Full-size record99.7576%,
replay100.0003%, p99 callbacks26.588/26.423ms, worst312/126ms; frame pacing is not
certified by average speed. Original attended case untouched.

All seven default regression cases PASS: USA original/widescreen, World2.4
synthetic/Germany, World2.5, Off-Road, Exotica (21 completed GL images). These are
feature-OFF checks, not approval of applying World-specific addresses elsewhere.
79 Python tests PASS, native helper arithmetic/profile test with captured World
program PASS, CI34080307060 at42f1635 all four jobs PASS. No shader changes.

Native built/root deployed vunit.exe SHA256
050cf6ea393f1d44a1662ad191a5fc6d38be3084f49603ce8d7de2b379f736ce.
114 exported patches reconstruct tree cb136368d9bcdbebc482fab6e27d1e702b95715b
from mame0286. Native pushed to fork/poc/quadlog. Collection code commits cc9687e,
deb5c82,42f1635 separate experiment, motion diagnostics and attended recording.
Replay/derive_case/record_drive accept explicit global flags; the new matrix tool
separates completed experiments from visual acceptance. Attended recording keeps
saved display/wheel preferences and archives the combined temporary patch.
All automated physical FFB OFF; no new attended game left running.

Decision: 2x/lead8 at normal CPU is a useful attended-trial candidate. Keep normal
launcher settings unchanged pending a fresh Germany drive and second World level.
Continue toward a host static-transform oracle, then pending/future section drawing
independent of guest simulation; do not return to per-object allowlists as the main
strategy or jump straight to a whole-game port. See
 docs/reviews/2026-09-06-global-distance-trial.md
and results/proof/2026-09-06-global-distance-trial (reports, lossless proof frames,
video overview and compressed raw traces;184 archive entries verified and all six
full-trial camera/native-counter reports recomputed exactly).


## 2026-09-07 — 3x distance, earlier activation and release baseline

User approved3x/independent lookahead and a release roadmap, then requested
continued nighttime fixes and end-to-end validation. Native b0540e36189 adds
240000 far and lead12. Built SHA256:
aa92018876b8c07868057fdee7ccd1c7391dd1cad3d64f13134b3fbf977b8fec.
115 exported patches reconstruct tree4a0b575c717b94d8d4d3635cd4e2b653303e135e.
Five full Germany runs8783 frames/146native/321GL hold99.9004..100.0008% emulation.
3x8 repeats inputs/times/native/GL/camera/ADC exactly. At lead8, cameras2x/3x match
7281 samples; actual ADC values/PC match21843 reads but timestamps differ. Only
five small GL images change16..628 pixels. No useful additional mountain visibility.
Five bounded runs5900..6140 capture201 completed GL images:2x/3x identical at both
leads. MountainCB1A8B submission6093(original),5981(lead8),5925(lead12), independent
of2x vs3x. Background/forest6119->6005->5947. Submission is not first visible pixel;
lead8 vs12 cameras diverge5924. No clean full-second visual gain claim. Near4K
8 captures3824x2073 match2x8 vs logged3x8. First3x attempt lost the stream with zero
GL captures; largest callback gap789ms at584 before intervention5900. A successful
retry does not fix it. Keep3x/12 diagnostic; normal launcher distance unchanged.

Release roadmap, source-bound gate,39-item attended ledger, configuration contracts,
ZIP checks and workflow checks added in separate commits. Seven free-play setting
bytes fixed in fresh seeds. Real boot checks disproved the historical no-checksum
claim: Off Road1.63 sums47 settings words atECD5, comparing stored word35 atDB9B.
Stale sumC2AD77 vsC2AD78 reset free play atframe761. Fixed checksum byte0x35C77->78;
shared cmos_settings helper used by shell/tool/package checks. Failed boot and
read-only write-tap proofs retained; corrected attract screen says FREE PLAY.
User NVRAM preserved. New fresh-boots gate checks actual persisted settings after
both boot and replay; replay equality cannot hide a settings reset.

Final92 Python tests PASS; CI34095982029 at471ffd6 all four jobs PASS. All seven
final default regressions PASS, including Exotica's21 completed GL images. All five
fresh seeds boot/replay PASS; separate Off Road relaunch retains free play1 and a
valid sum. Three V-Unit menu-handler checks PASS. Physical Esc/manual/FFB remain
unaccepted. Gate automated_pass=true, ready_for_release=false with39 pending
attended/package items. All automated physical FFB OFF. World proof161 ZIP entries
verified, five summaries recomputed, two lossless PNG/BMP checks pass; release
proof124 runtime entries verified. See docs/reviews/2026-09-07-world-3x-and-release.md.
Old executable/SDL/profile archived locally before further renderer work. Next:
startup CPU upload batching with strict order, package rehearsal/artifact promotion.


## 2026-09-07 — Renderer backlog, complete package baseline and neutral-force fix

The startup stream problem was dominated by scattered CPU framebuffer uploads.
A contiguous-span prototype barely reduced upload count. Final masked GPU copies
reduce World420693 spans to196 copies in the bounded startup workload, USA425490
to330 and Off Road419788 to65. Preserve unwritten pixels and flush before ordered
non-CPU messages/presentation. Canonical cpu_upload_spans helper and GPU shader
fixtures cover holes/page selection/order. No guest geometry or simulation change.
MIDV_GL_BATCH_VRAM=0 retains the immediate control; watchdog threshold unchanged.
Nativeaef6d4465cd/C925 passes12 scale4 CRT full-window starts, three per game, all
36 completed images and per-game repeats. Correct Off Road height401 explicitly;
historical synthetic case used400. Earlier26-image paired prefixes agree exactly,
including separate401-row Off Road control. Artificial100ms stall recovers3/3.
1500ms short run ends before requested images and correctlyFAILs; longer2404-frame
run times out at1829,16MiB/750ms. 5000ms stall times out1607,zero consumerbytes/765ms.
Those are retained negative controls, not successful recovery. No stutter-free claim.

Packaging restores tracked menu art/music accidentally removed in5ea8b2d, obeys
NoMedia, retains custom user music, includes SDL/BGFX/source/MAME and toolkit licence
texts, and freezes both GUIs afresh with checked command failures. Timestamped ZIPs
and per-file manifests bind exact source/native bytes. Tag pushes no longer publish;
manual workflow builds candidates and promotion uploads only the reviewed ZIP.
No public tag/release created. Frozen support now writes JSON to a file, finds its
packaged input Lua, and disables physical force/graphics experiments. Read-only
setup-health/support CLI verifies the real package away from development paths.

Importing previous rig data fills missing files, preserving newer calibration,
bindings and scores. Updater validates ZIP paths/CRC/runtime/personal-file exclusions
and rechecks package hash in its helper. Real Windows tests cover apostrophes,
PS7 module-path inheritance and8.3 path cleanup. Corrected CI942 allfourjobsPASS.

Complete C925/source942 release baseline PASS: seven full recorded regressions,
five real fresh boots/replays with persisted freeplay/checksum, three VUnit menus,
24 GPUquality fixtures, both native-exact captures100.0000%, frozen allfourboots
with12 completed GL captures, eight UI pages and real setup/support output. ZIP
build/CruisnCollection-v0.4.0-rc1-20260907-034453.zip SHA256
23414805df1bb51c1529257a5463b9d5a386cac209ffd313b87614d6a10fb4be.
Full logs/proof retained in release-hardening/release-942;146 runtime ZIP entries
verified from committed Git blobs. Earlier renderer233-entry proof likewise
verified. Automated releasegatePASS;39attended/shared checks remain pending.

Subsequent native5bb965763b1 normalizes reserved raw motor-128 before gain/slew/
clamp in both driver families, clearing driver slew history. All61200 ordinary
vectors retain the prior formula;240neutral cases becomezero,216formerlynonzero.
Downstream smoothing still applies; no instant physical-stop/feel acceptance.
Retained Exotica4616raw writes contain zero-128, so this does not diagnose the
historical Fanatec report. Nativebuilt9D8 SHA256
9d8a8c14998777a15190ca76edd318380baec05e6dac6086d54929dcd2c62a86;
117patch export reconstructs treea611778155bbaef209f5523bb711ba8b1f127cb6.
Nativepushedfork; collectionneutralfixf197337 separatelycommitted.

e4384ec adds reversible exact-hash legacy dinput8 proxy retirement on update and
firstlaunch, catching old updaters/manual ZIPoverlay. Unknown DLLs remain untouched
and blocklaunch/update. Actual two historical binaries hashed/moved only in isolated
folders, exactbackups verified, neverloaded. Processinventory uses typed64bithandles
and canonicalimagepaths.98Python testsPASS locally. WindowsCI34105177890 exposes
an additional8.3 mismatch in the new proxy check: Refusing redirected input DLL.
Keepthisfailure; isolatedfix24cc1a2 canonicalizes allinputpaths inPython beforePS
scriptgeneration. CI34105656916 running; activee438fullruntimebaseline remains
unchanged during investigation. New ZIP041815/09cb7a7d is a runtime candidate,
not releaseaccepted. Finalsource/ZIP must include the CIpathcorrection.


## 2026-09-07 — Final portable release baseline and remaining public-access decision

Native5bb965763b1 / SHA9d8a8c14998777a15190ca76edd318380baec05e6dac6086d54929dcd2c62a86
is unchanged through final validation. All174 sampled completed GL frames match
oldaa920 across fullUSA43/Germany78/OffRoad53 comparisons atscale4/CRT; OffRoad401rows.
The source3720 actualZIP upgrade matched1616files and preserved its existing-state
fixture plus knowninputproxy backup. That fullbaseline is preserved in proof/
release-hardening/release-3720,288runtimeentries and33files verified fromGitblobs.

CI34102127057 built older942fromMAME0286 plus exportedpatches. DownloadedZIP SHA
c92da687b83c9871fee0b3590a33b0993d8808032754462911bc975c7bd7dc96 and all1614files
matchmanifest. Its80df9ae3 nativebinary was neverexecuted/deployed or certified by
local9D8 tests. Inspection revealed different sourceidentities for identical
committedtext because extensionlessLICENSE and ini.example had differentcheckout
lineendings. Source7cb6751 canonicalizes remainingknowntexttypes, retaining every
binaryfixturebyte. Newtests distinguishLF/CRLF fromactualtext andbinarychanges.
100Python testsPASS. CI34109534667 and34109710043 allfourjobsPASS; Windows/Linux/
local agree on every201sourceinputhash, identity
 e728e2463bc64d0695433007ec905f56ad93bf7966a791a9845412bf74d56921.

Final clean packagebe87237: build/CruisnCollection-v0.4.0-rc1-20260907-050908.zip,
SHAeaa8520998e8fc76d5fecdbbda86311455d96ee129ac783892a54962a765a139.
Renewed source-bound testsPASS:7drivingcases,5freshboot/replay/persistencechecks,
3VUnitmenus,24GPUfixtures,2exactcaptures100.0000%, frozen4boots/8UIpages/setuphealth/
support, actualZIPupgrade1617matchingfiles withrig/ROMmarker andknownproxybackup
preserved. Source,native,ZIPunchangedthroughout. Measuredregressionintervals
99.9290..100.0040% emulation, worstcallback44.7ms; no presentationlatency/stutter-free
claim. Finalproof/release-hardening/release-final retains221runtimeentries plus
sourceagreement, manifests, receipts andreproduction scripts. Earlier174GL proof
remains explicitly bound to the unchangednativebinary, not relabelledsource.

All automatedphysicalFFB OFF. No game/build/helper left running. GateautomatedPASS,
ready_for_releaseFALSE with39human/sharedcheckspending. Preparedledgerattaches
receipts while retainingpendingstatus. Morningmanualdrives, actualwheel/FFB/Exotica
polarity, cleanprofile/realupgrade/secondwheel/soak remainrequiredacceptance.
RepositoryisPRIVATE; directanonymouslatestreleaseAPIreturns404 whileauthenticated
latestv0.3.7exists. Updateralreadyreportsprivate/missingreleaseerrorcorrectly.
Publichostingneedsmaintainerdecision; no visibilitychange, token distribution,
publictag orrelease performed. StreamDeckstillpointstosourcecheckout/root9D8.
AllolderZIPs,originaldrives androllbackbinariesremainpreserved. See
 docs/RELEASE-MORNING.md and docs/reviews/2026-09-07-release-hardening.md.


## 2026-09-07 — Expose controlled distance trials in Graphics Experiments

User requested Crack Fill reclassification and access to tested3x. Sourcec753f4b
moves Crack Fill to Experiments, preserving shared preference/default.9ae9231
adds World2.4 Off/2x/3x with independent+0/+8/+12lookahead; defaultdistanceOFF,
lookahead8inactive. Widescreen/scale>1 only, normalCPU, guardedpatchcomposition.
Global/selectivescenery cannot combine; Terrain can. RecordingCLI and explicit
MIDV_PATCH precedence preserved. No native/shader/forceprofile changes.
104Python testsPASS. 1920x1080 menus inspected. Sharedlauncher resolver3x/+8
feeds a new2404-frame Germany-prefix recording/replay: inputs/times40native/3GL
images exact, nativeprofileOK, extendedreads1022175,pendingcomparisons378.
ActualGPUcaptures512x451 atinternalscale4/CRT; not4K or originalrouteacceptance.
Native5bb/9D8 unchanged, automatedphysicalFFB OFF, originalrecordings untouched.
Overnight050908ZIP preserved; it lacks these sourceUIchanges and must not be
relabeled with the newer source identity. See docs/reviews/2026-09-07-graphics-menu.md.


## 2026-09-07 — Internal USA revs/gears, contextual experiments, startup evidence

USA v4.5 tach-consumer tracing found player pointer E8A8, actual gear +38 and
C31 rev +39. 9E53..61 scales revs into 22 palette entries; 9D86..89 draws gear.
Native bf8821358d4 / SHA256 4d63433b45f492ae7dd6f982c0aca92afdf7d12283d19ee194bf5ec95e55fee4
reads guarded backing RAM, gates on fresh numeric HUD, maps the real rev signal
to an explicitly estimated 900..8000 RPM scale. Automatic gears now reach JSON/
Forza. No pixel RPM fallback or E632 RPM mapping. Other games unchanged.
Original 5012/83 and independent synthetic 6000/100 replays pass, all actual
Forza/JSON samples agree; 2483 independent RAM samples match. All 12 upshifts
across the two drives show drops within eight frames. RPM-off control3040 passes.
All7 game regressions pass on the initial telemetry binary82203f8f; final4d63
adds stable USA Forza gauge limits and is separately tested by those two drives,
the RPM-off control and World4x/3x/4x1804-frame boots. The latter retains9 completed
3824x2073GL images, matching repeated4x. 108Python tests/native helper pass.
World's reported fallback/artwork incident was not reproduced: its old failure
log was already lost. Screen-only fallback and bounded launch-history receipts
now help diagnose recurrence; don't claim a proven scale-initialization fix.
Experiments show Shared/USA/World/OffRoad/Exotica and only applicable settings;
6 menu previews inspected. User INI unchanged, automated physical FFB off.
Native full118-patch export reconstructs tree895aabd69d1efcbab19d63039157c076c4396b2e.
See docs/reviews/2026-09-07-usa-drivetrain-and-startup.md and its50-entry proof ZIP.
StreamDeck uses this source and mame-src/vunit.exe; older release ZIPs preserved.

## 2026-09-07 — All-game drivetrain telemetry, force-state gates and candidate rc2

Preserved the user's INI, launch history and surviving logs before tests. World2.4
New York3x/+12 launch20:40:21UTC confirms a guest fatal:
Unimplemented op @3EF9C170:15A3ED45. Following2x/+8 race exits normally; this is not
proof of cause or2x safety. No contemporary Windows dump; original race-end force
trace had been overwritten. Bounded launch archives now keep force logs/CSV tails.

Found World2.4/2.5 actual gear+51/rev+52 with separate guarded code/global layouts.
Exotica gear+62/rev+63 and internal speed1074; its Zeus screen path never previously
called the VUnit UDP emitter, so Forza was entirely absent. Off Road uses DP=1 globals:
player19D25 + BC*1C86C, gear+B/rev+36, HUD formatter speed19D11*19D77. Its previous OCR
reader failed. New guarded producers feed the same explicitly estimated900..8000RPM
scale as USA. No E632 RPM fallback. Off Road's initial6001-packet failure identified
duplicate partial-screen emission; final-visible-clip gating restores6000/6000.
World's real countdown/rapid shifts sometimes retain revs; the strict every-upshift
drop diagnostic fails honestly, while all emitted values match independent memory.

World driving state4/flags bit4 and Exotica HUD/control flags now gate constant force,
impact state, rumble and condition effects. Independent default-distance Germany
probe confirms1468 nonzero inactive motor commands, including the finish; all host
requests are gatedzero. Exotica suppresses2072 nonzero pre-drive commands. Actual
rim behavior remains untested. Exotica ADC mirror no longer follows the force/shifter
DIP; its default is0. Effective output is trimmed20% after driver byte conditioning
(saved80 becomes effective64), preserving preferences. Physical outputs never enabled.

Native f2e5b63dd72 / SHA80688f753070bffe5e55654fed1fd7ffdbd1158acd978e44c9a2a660b40fba57
is built/deployed at mame-src/vunit.exe and pushedfork. Full121patch export reconstructs
tree26264b1217f62b08aaab544658cda7a8e9128746 exactly. Final7 full cases PASS original
inputs/images plus live UDP and independent memory; Exotica21 completedGL. Timed
intervals99.9735..100.0070% emulation, not GPU presentation timing. All5fresh1800frame
boot/replay freeplay/checksum persistence checks pass. 113Python/native tests PASS.
CI34164817060 atba6cee5 all4jobs PASS; every217 Windows/Linux/local input hash agrees,
sourceidentity9eeaefe1defee4ac06ea198a1ea192499ab6785abe0c684774a9b504f642d7cd.

Clean bb62a22 ZIP build/CruisnCollection-v0.4.0-rc2-20260907-170505.zip,
SHAe8847b70fc9436a23aa38ffdb2f2756009c040c6acbaf7bff577a42a947224f8. All1632file hashes,
actual frozen CRT-on/full-wide/scale4/default-experiments-off check pass. Extracted
ZIP4neutralboots/12completedGL/eightpages/setup/support pass without development paths.
Source/ZIP remain bound to their exact identities; later docs/proof-only changes
do not relabel old code. Proof/release-feedback contains160derived entries, ZIP
SHA2e5e18d189982e99ded1ba1a3a8fe42d5e9b96900455610e195d6708c99821d9. Exact archived
bytes verified; all7telemetry and4forcegate verdicts recomputed from archived data.
No ROM/RAM/NVRAM dumps included. Original recordings, earlier ZIPs and userINI
b5c521b42433078a22e87b80753e8a44944ce8056949bee3c45c568b58780752 remain unchanged.

Gate automatedPASS,43attended/shared checks pending. OffRoad/Exo firstgear synthetic
coverage is not allgear acceptance. Need physicalExotica startup/steering/weight,
World finish/impact feel, allgame auto/manual gauges/tactile output and package/
secondwheel/soak acceptance. Public distribution decision remains open; no public
tag/release/visibility change. User requested NewYork blackflashes/crash recording,
cheats and othergame/consistent distance experiments afterrelease. See feedback
review, RELEASE-MORNING and RELEASE-CHECKLIST for next attended work.

## 2026-09-07 — Revert World force gating after attended regression feedback

User rejected loss of feedback in World's game menus and later cancelled the
proposed10% boost. World strength stays unchanged; recent20%trim was Exotica only.
Native b9bef299f6d removes the two World driving-state gate calls, restoring game
motor requests during selection/race-end. Driver adaptation, profiles, master
strength, telemetry and Exotica's independent gate/trim are unchanged. Defer further
World FFB tuning; oscillation and cross-game output normalization are KNOWN ISSUES.
Goal for later: roughly comparable80% output across games on the same wheel/base,
using measured common output units plus attended steering/contact/impact assessment.

Built/deployed native SHA093abbeb01ac779dbc81b734bea609a9a358eebc17a7cfbf2ad6002e017135af.
122patch export refreshed; rollback applied to verified native parent reconstructs
tree5f33ebed52f7fd7a707c74aeca885989400fdfde. Collection353afac updates the normal
suite to require World force passthrough instead of driving-state suppression.
114Python tests PASS. Germany9269inputs/154nativeimages andWorld2.5 6000/100 headless
replays PASS; actual UDP/independent drivetrain probes agree. All8803/5534 force
writes enabled;1332/1059 nonzero requests during independently sampled non-driving
states. Raw/adapted motor-source CSVs exactly match prior verified runs. No physical
force actuated, no renewed full release/othergame/feel acceptance claim.

UserINI2c5faf831d33e1b4213ab56db6e7fc40efd6dc04131ae290d9dc921c53ef78b0 unchanged.
Native/source fixes pushedfork/master. rc2 ZIP remains immutable but contains the
rejected World gate: source supersedes it, replacement package and acceptance needed
before publication. See docs/reviews/2026-09-07-world-ffb-rollback.md.

## 2026-09-07 — Correct Exotica cabinet force polarity without steering changes

User reports anti-centering on both sides. Preserved actual attended logs/config
hashes: WheelInvertOn, ADCmirror0, sharedforceinvert0, requested80/effective64.
Native97600e9597e normalizes Exotica's active-low DIP0x0800 motor polarity at each
write. Game and device inversion compose independently; raw/adapted motor values,
ADC steering, shifter configuration, gain/strength and World behavior unchanged.
Canonical motor_signal.h handles signed conversion; force-gate.csv adds game_invert
and device_invert. Analyzer checks actual inputDIP and adapted source against the
requestedlevel. Physical output was never enabled by automated tests.

Built native SHAb5ba0021a51a1f9ec50e105dde9c8112cb3c7e4ce71009ce4294841296383ee2;
123patch export updated, correction reconstructs treecb82b811cd0ceec182734950f7c8ad7ef83fc667
from verifiedparent. Native/source pushedfork/master (collection3d990a5). 115Python
tests, native256byte x bothdevice/gamepolarity vectors, sync and4CI34187080921 jobs PASS.
Full Exotica6000inputs/21completedGL/actualUDP/memory/gate/polarity PASS. All4616
samples match recordedDIP;2082nonzero requests reverse exactly with same magnitude,
raw/adapted motorCSV identical. World2.5 control6000/100 passes; all5534requests
retain prior values and gameinvert0. First Exoattempt endedcleanly at1052beforeGL
captures (causeunknown), retainedFAIL/incomplete; completedrerun supplies acceptance.

Proof/exotica-force-polarity retains derived traces/reports/analyzers, original
attended force logs and failed-attempt receipt, with exact archive hashes. These
are software-level checks, not proof of physical restoring torque. A brief attended
low-strength centering check remains needed. Cross-game strength normalization and
World oscillation stay deferred. No new ZIP/publicrelease; source supersedes rc2.
See docs/reviews/2026-09-07-exotica-force-polarity.md.

## 2026-09-08 — v0.4.0 release preparation and explicit sign-off

Maintainer authorizes cutting a new release and signs off current state. Native
97600e9597e / SHA b5ba0021a51a1f9ec50e105dde9c8112cb3c7e4ce71009ce4294841296383ee2
retains Exotica cabinet polarity correction and World menu-force rollback.
Release accounting now distinguishes explicit, enumerated maintainer waivers from
attended PASS observations; automated gates remain mandatory. Current sign-off and
known limitations are in docs/releases/v0.4.0-approval.md. Old rc2 must not ship.
Updated release notes consolidate previously contradictory unreleased chronology.
Queued postrelease: Cheats first, Experiments beside Display second, global distance
experiments for USA/World/Off Road/Exotica third. No unattended physical force.
Fresh release checks and exact ZIP publication are in progress, not yet claimed.

## 2026-09-08 — v0.4.0 published and downloaded-byte verified

Published https://github.com/d-b-c-e/cruisn-collection/releases/tag/v0.4.0 from clean
c098290aeaa1f19ca37d7bee56c747cbf51350b5; native97600e9597e remains unchanged.
ZIP CruisnCollection-v0.4.0-20260908-000947.zip is111,918,111bytes, SHA256
fd292b0d4ba4d2a97147c6ffc1fb95407e3891495dfb68fada2f899e3c31ba4a. Downloaded release
asset and GitHub digest match exactly; local tag resolves to packaged commit.
SHA256SUMS and package manifest uploaded too. Existing private visibility retained.

All117Python tests and4CI34189532162 jobs PASS. Linux/Windows/local217-file source
identity4c9dd0a3d246f9bfa1160360ad551e3af841da3ecf837200626def487d7eb30d matches.
Full7replays PASS, actual UDP/independent drivetrain memory, World passthrough and
Exotica cabinet polarity. All21ExoticaGL references match. Measured emulation
intervals99.9726..100.0069%; no blanket presentation-pacing claim. All5fresh-save
boot/replays preserve freeplay. Extracted frozen8pages/setup/support/4launches/12GL
PASS. Actual upgrade helper preserves isolated state and matches1637packagefiles.
24GPUfixtures/3pause-menu checks PASS. Both native exact comparisons100.0000%.

Release gate READY with10configuration contracts and41explicit human-check waivers,
not41observed passes. Maintainer's exact sign-off, known issues and package evidence
are retained. Physical FFB remained disabled throughout. No personal rig settings
or original recordings rewritten. Stream Deck still uses source launcher and
E:/Source/mame-src/vunit.exe SHA b5ba0021a51a1f9ec50e105dde9c8112cb3c7e4ce71009ce4294841296383ee2.
61derivedproof files archived at results/proof/2026-09-08-v0.4.0-release; archive SHA
ccd2d8d81680626187dafffd10b2cd57616724148c5731609d1c9cade9a67be2, all entries verified.

Overnight heartbeat cruisn-overnight-cheats-and-distance created, every30minutes,
08:00local checkpoint. Priority Cheats, top-level Experiments, global distance
across all4games. Nested downloaded cheat.7z has23entries for5supportedROMrevisions;
preflight only, runtime validation queued. MAME#16046 already backported; newer
Zeus2#16058 retained for separate postrelease study, no untested backport shipped.

### 2026-09-08 01:40 — Initial Cheats menu, top-level Experiments and display-target repair

Collection eea6ef5 adds exact-revision XML/ZIP/nested7z imports and a per-game
Cheats menu; continuous toggles/choices, hash-bound saved selections, reset OFF.
User archive imported into rig/cheats, all OFF. One-shots and off-script instruction
restoration remain unavailable pending live activation. Native44c3494d6af adds
copied metadata/guarded commands through MAME's original cheat engine. Built/pushed
vunit SHA eb2db42a90288bf37ac0dcce9b9ce2106c136fad198c52320ee2b3af3c435a97;
124patch export exactly reconstructs f7af3475d0ce0b6347e2be669338283437a81447.

Collection e6154e1 moves Experiments beside Display with Shared/game filtering and
Back returning to Settings; existing preference keys/defaults unchanged. Shared
Crack Fill remains ON by default; per-game trials OFF. f8a804f adds frozen import/
activation checks. No renderer or force changes. World normalization deferred.

Seven default binary controls have passing evidence: six initial cases pass;
Exotica initially FAILs21GL because automatic monitor choice produced1080p vs4K
references. 1baa99a binds Zeus --compare-gl to a matching display and reports size
mismatches. Separate6000frame Exotica rerun matches all21completed4K images and
passes memory/UDP/force/polarity/timing. Original aggregate FAIL remains intact.
These are binary-bound component checks, not a new source-bound release gate:
launcher/diagnostic edits continued during the first aggregate run.

Five4000frame cheat-on cases replay against the final binary; state/input/native
snapshot comparisons pass. Exotica headless snapshots are not visual evidence.
Five independent timer on/off memory probes pass. Early analyzer FAILs assumed
zero callback-phase ticks; revised checks require bounded correction and resumed
progression after OFF. Off Road separate seconds/hundredths writes preserved;
ON stays0.00..0.02, OFF advances. Rank/nitro/one-shot effects not yet accepted.
128Python tests/all4CI34195061384 PASS. Frozen devZIP at f8a804f SHA
f7a5a641affe81d7e44102d86cc9a6fa19411820a8b9d76607a99e7d08ecfdf5 has1649hashedfiles;
9pages,4defaultboots/12GL,1cheatWorldboot/3GL,import/setup/support/defaults PASS.
Published v0.4.0 ZIP SHA fd292b0d4ba4d2a97147c6ffc1fb95407e3891495dfb68fada2f899e3c31ba4a
verified unchanged. No additional release. No physical FFB or personal NVRAM edits.

75derivedfiles in results/proof/2026-09-08-cheats-and-experiments, archive SHA
ad9ff1881ca4e3e8003794c98a911369e9b6c7fce05451015ebf3da78988c951; verifier checks bytes,
native bindings and recomputes five timer effects without ROMs. Next overnight
work is global distance capability mapping/trials for all4games, World New York
artifacts/crash. Heartbeat active until08:00local. All current runs completed.


## 2026-09-08 02:05 — Cross-game distance capability baseline

Read docs/reviews/2026-09-08-distance-capabilities.md. New bounded read-only Lua
probe and ROM-free analyzer cover all five revisions. Four V-Unit 4305-frame
controls pass inputs/native images; Exotica full6000/21 completed4K GL passes.
The initial headless Exotica native-image FAIL remains retained; its measured
distance trace exactly matches live GL. Native44c3494d6af/eb2db42 unchanged.
131Python tests pass. World2.5 has 44807/223727 far rejects (all within2x); USA
has only3 plausible extension visits plus900 INT_MAX-like visits; OffRoad has
1173 within1.25x plus198 extreme distances; Exotica zero far rejects despite
85388 reciprocal clamps. Static activation/table evidence is revision-specific,
not a new visible-distance claim. No product/native/default/physical-force change.
Next: guarded World2.5 port, USA admission+projection, separate OffRoad/Exotica paths.


## 2026-09-08 02:40 — World 2.5 global adapter and USA residency

Native dae2569f793 / sourcevunit f06a160b57c72737e89aedcc159f87cbe173c82620722ea109e84dcdffe70252 built/pushed.
125patch export exacttree2f4f89c388ba380aa578036143049a723dcad00c. Source117e8fb adds
World2.5 revision guards and optional menu/CLI trials, defaults unchanged. Separate
b720b98 USA read-only probe measures22713 pending visits eligible within2x75k,
maxdepth-minus-radius117026; USA intervention is next, not built.
World25 original+2x/+8+3x/+8 each6000 frames/~100% speed; original identity passes,
extended route comparisons fail as retained. 2x separately repeats6000/100native/11GL.
2x/3x match100native+42GL but33camera samples and ADCtimes differ; no3x visual gain
or geometry/order/resource acceptance claimed. ExistingWorld24global2x8783/146passes.
All7 defaults, actualtelemetry/memory/Worldpassthrough andExo21GL pass; bounded
timing99.9731..100.0035%. 132tests/all4CI34199270158; all229 local/Linux/Windows
sourcehashes match85ad5a17558ffc18d7f3d8eac431151e6c7582ba6359bd3b8ad3392e573ee152.
67derivedfiles in results/proof/2026-09-08-world25-distance, ROM-free counters and
bindings verified. v0.4.0 exactZIP SHAfd292b0d4ba4d2a97147c6ffc1fb95407e3891495dfb68fada2f899e3c31ba4a unchanged.
No emulator running. No physicalFFB or Worldtuning. Native sourceusedbyStreamDeck
updated; no newrelease ZIP. See dated world25-distance, usa-residency and
distance-next-adapters reports. Heartbeat continues to08:00local.


## 2026-09-08 — USA global trials and complete Off Road table reconstruction

Native8b151aa9c2f / SHA638c74ff4227532d0ff42be4cd46cb8a358a1a343549abb107bb56050e91bd74
built/pushed;126patch export exacttree5e10f68c9badba2385d38d6178eaae1be02d48b6.
Collection9e70f6a adds optional USA global CLI projection/residency controls. Guarded
75k/80k pending/active reads remain guest-managed; all five projectionclamp groups
and attachedobject lookup covered, hosttail never overwritesRAM. No menu promotion.
Five5012frame trials ~100% complete;1x control exact. Projection2x-only changes
3native samples/3pixels in1of19GL, one camera sample3012; actualADCvalues equal,
timestamps differ. Residency1.25/2/3x changesroute from2222; all originalFAILs retained.
2x/3x camera first differs3902; no extra visible3x gain proven. Separate2xcase repeats
5012inputs/83native/19completedGL at1904x993. Matrix captures512x451, not4Kacceptance.
139tests/all4CI34202538087 at3628c96; all237 local/Linux/Windows sourcehashes match
946fc6523f110ddc2d91e5a481b4a6cbdd0cc067d73452cc3ab923e42023974c. All7default regressions
with telemetry/memory/forcecontrols pass; Exotica21completed4KGL exact. No physical
FFB. World2.5 explicitrecordguard fix92b6659; deriveGLfeaturefc24e0d/3628c96 catches
incomplete GL references and compares both completed runs. Nativevectors passed;
a receipt rerun first lackedMSYS DLLs, failedstart preserved separately.
107derivedfiles archived in results/proof/2026-09-08-usa-global-distance; ROM-free
verifier recomputes all five distance/input/motion comparisons and checks bindings.
Archive SHA725c393a7ae8257e5e3565534f65f5bfd12cfcb93adc57f2ff56465b05bc15fd.
Off Road table now reconstructed exactly for all67776 indices(-4096..63679):
index<503 linear2-(index+1)/504, otherwise504/(index+1), exact rational rounding to
8decimals ties-even, float32 thenC31. Naivefloat round fails2ties; retainednegative
control. Formula6/7/9 decimals has62856/56246/48268 nonnegative mismatches. Static
B725 geometryclip63680 and multiplevertexconsumers still needprofiling. Exotica
CPUfrustum boundedprobe outline updated; noOffRoad/Exotica intervention yet.
No newrelease; v0.4.0 ZIP rehashedunchanged. NativeusedbyStreamDeckupdated. Noemulator
orhelper remains. Read dated USAglobal-distance and next-adapters reviews. Overnight
heartbeat continues to08:00local. USA freshdrive/geometry/order/resource checks open.


## 2026-09-08 — Exotica CPU frustum audit

Read-only6000-frame replay retains inputs and21 completed3840x2160GL references.
Corrected probe validates339018 sphere decisions over2500..4300. Original accepts
215946, has0far rejects at204800 and85350projection clamps; maxdepth140424.
Counterfactual unclampedreciprocal adds4051instances with0losses; horizontal88margin
alone adds21717; combined28610. Admissions are not visiblepixels. No game/native
intervention yet. First acceptance marker689D was inside Xreject delay slots; its
replay PASS did not certify the probe. Independent analyzer rejected it; corrected
68A3/PC68A4 marker and full rerun pass. Retained negative sample and originalprobe.
Fivefocusedtests pass.15derivedfiles/16016714bytes proof archive
results/proof/2026-09-08-exotica-frustum SHA27aceebcab12aca0dcd1b28ec9fec56d8ef19d82f2deed74c04fb5fad3899d4b
recomputes all339018 decisions withoutROMs. Native8b/SHA638 unchanged; no physicalFFB.
Next: boundedstock/true-reciprocal/margins/both GPU matrix, then resources/repeatability.


## 2026-09-08 — Off Road coherent global trials, 04:25 checkpoint

Collection410ad43 diagnostics; native8b/SHA638 unchanged. Full6000-frame original/2x/3x
controls:4191camera samples and actualADCframe/value/PC equal, timestamps and original
pixels differ.1.25culler adds9011admissions/15pixels in3of42;2x16971/220pixels in5of42;
3x16977 and same42GL as2x. Maxindices95085/95782;11extended consumers. Guardedfiveword
interval includesinitializers because game reinitializeslimits fourtimes; initial
resetfailure retained. UnrelatedresourcePC1EA8 withstaleAR0 excluded by indexedaddress
guard after initialattributionfailure. Lua instrumentation costs94.2059%control,
54.2028%2x,53.1330%3x; no nativeperformance or launcherpromotion. Sample is short
syntheticElPaso, offcourse and slows, not attendedfullrace.
Matchedframe4400: textures/palette equal;715original quads same/order,onechanges3coords,
23new. StrictgeometryFAIL retained;386targetpage changes covered,384otherpage changes
outside narrowcurrentpagecoverage. TwoGLframes4399/4400 change186/202pixels.
147tests/4CI34209001116 at410ad43 pass.92file4128469byte ROM-free archive
results/proof/2026-09-08-offroad-global-distance SHAb6295bb08e60a39b6b8f2e8ed06919ad4b5df6c99ec789db87dc3e95c4445c2d
recomputes five distance/input/motion trials and commonquadorder, retains negatives.
Exotica5937063 audit separately15file proof; next true-reciprocal/margin/both GPUmatrix.
v0.4.0 ZIP fd292b0d and native638 both rehashed unchanged04:22. No emulator/helper
running, no physicalFFB, personalsettings or Worldforce tuning. Heartbeat continues
to08:00local. SourceStreamDeckstillhasCheats/top-levelExperiments; these distance
probes do not add launcheroptions.


## 2026-09-08 05:30 — Native Exotica visibility and strict Zeus capture proof

Collectiondc1f5af/0e758f3; native6a2b7ae93fa/SHAcec6d98afc732b7e1a268deb763a7afeab112c66e32a4a5ed643817f1f3fdc5a.
127patch export exactlytree6d2e8a22e8641bbf6709eb2f1d5a5092c6bd0dcc. All pushed.
Bounded Lua stock/projection/margins/both/bothrepeat6000 each; CPU admissions215946,
220008,238066,246902,246902.19GL pertrial, both trace/images repeat; strictlaterpose
FAILs retained. Native5x6000 atnormal speed; stock21original4KGL exact; each native
intervention matchesall19Lua images. Both fullnativecountertrace also repeats.
New margins/both cases each6000inputs/counterrows and35GL2500..5900 repeat. Margins
vsboth changes19/35, largelaterhistory differencesfrom5300; nooldroute/farbenefitclaim.
Frame3500 Zeus capture: margin preserves3691records/3532quads/effectivepalettes/order,
textureRAMunchanged; onepalette+onequad added outsideoriginalrightedge. Combined
changes42originalrecords, strictFAILretained. Newstrictparser rejects truncation,
unknownrecords/nonfinitevertices; nativebuffersremainnonoraclewhenGLskipsCPUdraws.
Native stock nowfinds3669actualfarrejects4686..5986 (noneearly2500..4300), givingnext
truefarplane target. MIDZ_VISIBILITY CPU controls stillkeepfar204800unchanged.
Exotica WidescreenScenery menudefaultOFF, enhancedwide only; projection/bothCLIonly.
replay/derive/attendedrecorder archiveoptions; derive--keep-patch supportsnopatch and
frozencheat/patchrebinding. Nativehelpertested againstactualprogram andCIvectors.
All7defaults actualtelemetry/memory/Worldpassthrough/Exo21GL PASS; configuredtimings
99.9714..100.0055%emulation (notpresentationlatency).157Pythontests/all4CI34213524599
pass; local/Linux/Windows255sourcehashes identicalfa5809b1880d4373652c68e2e034afa992c97d15a29b8f4698ba4cf3a0a121a3.
Proof results/proof/2026-09-08-exotica-visibility:170derived+3fulltraces; archiveSHA
b210c932d9b0de91c2048648b89be0f0623fe8402675a71014b8948175a43a22 and
cda97bfa190e28b157a8d562ecfe6f6f8b9da03b7e43daeafe2bac04b474b7c0.
Verifier recomputes spheredecisions/posefailures/nativecounters/inputs/geometryhashes;
GL/resource/CI verdicts remain boundreceipts, rawassetslocal. Verifierfield-name typo
corrected beforeacceptance; no emulator-testfailure. StreamDecksourceupdated,
personalsettings andv0.4.0tag/ZIP unchanged. NoFFB/Worldtuning, noemulatorleft.
Next overnight: OffRoadnativeadapter/cost/repeatability, thenlaterExoticafartrial.

## 2026-09-08 06:25 — native Off Road distance, full-size replay and menu

Core2669afe/menu ba3364c pushed. Native12e9ea6a3742643f5bbc57e7dc07073177594cd6,
root SHA9936c7160ddb708949d9e776c9197d833e868ffc921fd679153a72ab99735275.
129patch export reconstructs85f158eccb5f11308144513e77b8678f45a0317b; fork pushed.
OffRoad1.63 far47296/clip63680/table63679 scale together at1/2/3. Guarded read
substitutions leave guest limits/initializers and ROM resources intact. All59
projection consumers require exactPC/opcode/AR0/signedIR0/actualaddress. StaleAR0
resource PC1EA8 remains excluded. All67776 original reciprocalentries reproduce
with integer8decimal half-even rounding. Initial native781af835091 loggerduplicate
frame822 rejected; final12e emits onceperframe. Negative logs preserved.

Fourfull6000 matrix: stock6000inputs/100native exact. 2x16995extra far tests,
55113extendedreads/max95085, zeroceilingclamps.3x17005/55133/max96264. 2xrepeat
identicalnativeCSV/camera4191/actualADCevents/42GL. 2xvs3x42GLexact; bothchange
5samplesvsstock, matchingearlierLua. Nativeconfiguredtimings99.8321..100.0050%,
removingLua's~54%overhead. Originalcamera/actualADCvalues equal1800..5990 but
ADCtimesdiffer; strictFAILretained. SyntheticElPasocasegoesoffcourse/slows;
noattendedlongrace orpopineliminationclaim. Derived2x repeats6000/100native/
13completed3824x2073GL3500..4700. Newdisplay-sizeoption freezesactual4Kmonitor.

Paired4400:716->739quads,715commonordered;1oldquadchangeswords6/7/8 and23new.
Texture/paletteequal;386targetVRAMwordchangescovered,384otherpagehistorychanges.
StrictgeometryFAILretained. GL4399/4400changes10432/11055pixelson3824x2073.
OffRoad DrawDistance Off/2x/3x menuisdefaultOFF; supportedrevision/enhancedwide
gates,explicitpatch/environment/recordCLIprecedence tested; userpreferencesintact.

163Pythontests/all4CI34218719680(core)/34219090827(menu)PASS. Local/Linux/Windows
all262sourcehashes identical333901cdae9af35e404fc256ebc27170589c99927ceeb116024e081d00e4244b.
All7defaultregressions actualUDP/memory/Worldpassthrough/Exo21GLPASS; timing
intervals99.9693..100.0022%emulation,notpresentationlatency. ROM-free190entryproof
recomputesnative/input/motion/7telemetry/4force results, retainsnegativecontrols;
GL/resourceproofishash-bound,rawassetslocal. ZIP8,664,137bytesSHA
077b1aee432ddc754c7b7897cceef876732ba0ad48baae4ae0f27318d04638c6.
Archivebuilder correctedper-game memoryfilenames beforevalidation; notagamefailure.
StreamDecksourceupdated; releasedv0.4.0tag/ZIP andpersonalINI unchanged. NoFFB or
Worldnormalizationtuning. Next:Exoticatruefar/reciprocalextensionlate4686..5986;
currentWidescreenSceneryisnotadistanceincrease. Overnightdeadline08:00local.
