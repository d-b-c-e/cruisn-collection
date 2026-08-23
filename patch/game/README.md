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
OLD is verified before writing (mismatch = skipped, logged). This makes a
patch safe to ship for one game version and inert on others.

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
