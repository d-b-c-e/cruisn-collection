# Game code patches (in-memory, ROM-safe)

The V-Unit games copy their whole TMS320C31 program from the `maindata`
ROM into program RAM at every reset (midvunit.cpp machine_reset). Our
patcher (`midv_apply_patches`, env-gated `MIDV_PATCH=<file>`) overlays word
patches on that RAM copy - **ROM files on disk are never modified**, so the
GPL/legal bright line stays intact.

## Format
```
# comment
WORDADDR OLD NEW      # hex; WORDADDR = program-RAM word index 0..0x1ffff
WORDADDR *   NEW      # * skips the old-value guard
```
Reset-time installation validates the whole group before writing; a mismatched
OLD rejects the group and logs an error. This guards one game revision. The
legacy per-frame self-healer still checks words individually; it is not a general
atomic runtime patch manager. Guarded installation does not establish behavioral
equivalence: run the original input/route comparison as well as geometry checks.

`crusnwld-object-visibility-experimental.txt` is diagnostic only. It recovers
real margin geometry but changes the Germany route despite identical recorded
inputs. Do not merge it into the normal World patches or adopt a derived case as
proof that the original route is preserved. Off Road's flat sky extension in its
normal patch changes existing coordinates without extra instructions or draws;
its full recorded native replay passes. See
`docs/reviews/2026-09-06-world-rendering-and-replay.md` for evidence and limits.

## Disassembling a game (for finding patch targets)
```
# via MAME's own debugger - the program RAM is populated at machine_reset
# before the first debugger stop:
vunit.exe <rom> -rompath <roms> -window -debug -seconds_to_run 3 \
  -debugscript dump.txt
# where dump.txt contains:
#   dasm out.asm,0,0x20000,1,":maincpu"
#   go
```

## Applying (rig)
`MIDV_PATCH=<file>` in the environment; run_rig can pass a per-game file.
`MIDV_GL_LOG=1` logs "N applied, M skipped" to midv_gl.log.

## Technique notes (learned on offroadc, 2026-08-24)

- **Data constant** (right edge, `$11235`): one word, done.
- **No constant** (left edge: sign-bit test, `AND` + `BLTD`): replace the
  conditional branch with a **`CALLcond`** (`0x7207xxxx` = CALLLT
  PC-relative, target = site + 1 + disp) into a routine placed in
  **alignment padding** (runs of `NOP` after an unconditional `BU`, no
  references — grep the disassembly for branch targets into the range).
  A non-delayed call means the original branch's delay-slot instructions
  simply run after the return.
- Make one routine serve many sites without knowing their exits: instead
  of branching to the exit, **poison a register the site is about to test
  anyway** (offroadc: R1 = x-max bound := INT_MIN so the site's own right
  test rejects). Only clobber registers the site rewrites on return.
- Encode by templating existing words from the disassembly (same opcode /
  addressing-mode bytes) and confirm semantics in MAME's
  `src/devices/cpu/tms320c3x/320c3x_ops.ipp` (conditions, shift-count
  sign extension, call/return push).
- Verify with the attract oracle: candidate stream minus baseline stream
  must REMOVE 0 records and add only the intended class (see
  `docs/offroadc-left-edge-handoff.md` for the multiset comparison).
