# Exotica reset shader and MAME project regeneration

MAME's `scripts/build/makedep.py` lexer does not understand the C++ raw string
delimiters previously used for the two Exotica reset GLSL shaders. A forced
`REGENIE=1` project build had stopped while reading `exotica_reset.h` with an
"unterminated character literal" error. The default local build target was
changed separately to reuse the existing generated projects for ordinary
source edits, but public source builds still need a working generator.

Native commit `46e14e3354791ccf1d92a2b986c707acf8287513` expresses those
two shaders as adjacent ordinary C++ string literals. The compiled GLSL bytes
are unchanged: vertex length 126, SHA-256
`062afa7aad80669dd38762b31012df91963755941a2977699ea11db2324cbdf3`;
fragment length 335, SHA-256
`1efda9e80bd807ef99963d09db03573a6256dfb8f6d077c9ae9af94216ec47d4`.
The shader verifier now parses these literals and requires those hashes.
Two focused Python tests, the native reset-boundary test with compiled string
length checks, and a standalone OpenGL program link pass. The earlier
exhaustive 16,777,216-code D24 seed test remains applicable because the
shader bytes did not change; it was not repeated.

A corrected Windows MSYS2 MinGW64 run with `REGENIE=1` regenerated **34/34
MAME projects**, compiled the affected sources and linked `vunit.exe`.
The first invocation lacked `MSYSTEM=MINGW64` and failed before generation
because Python was absent from that shell's path; its raw log is retained.
After committing the source, an incremental rebuild linked the final binary.
The one-time 281-patch export reconstructs native tree
`066d00100d6633ae994a5060fe3e1e33135feb22`; the frozen diagnostic
candidate is `build/candidates/46e14e33547/vunit.exe`, SHA-256
`1ed851dd17836d56e36c2c4699f3200fb67e173f590155d55f65df39fcaec238`.
Local receipt `regenie-shader-native-export.json` binds the build and patch
series. **Do not rerun its exporter.**

An independent **clean detached Git worktree** at native commit `46e14e33547`
then built V-Unit from an empty build tree with `REGENIE=1`. It regenerated
34/34 projects, compiled and linked with no error lines, and produced a
115,650,978-byte binary (SHA-256
`b536e95039ba2c5c8f4be18179e11ceecd5da9f41e8027b713cb8af71c984d06`).
The binary answers `-listfull offroadc` with exit 0 and the expected game
name. Local `fresh-worktree-build-attestation.json` binds the source commit,
build log and binary hashes. The worktree is isolated at
`E:/Source/mame-fresh-build-20260924`; it has not replaced the frozen
candidate or personal emulator.

This proves a clean source-tree build on this PC and byte-identical reset
shader source. It is not a separate network clone, a new live machine-reset
replay, a release package or a renderer promotion. The personal Stream Deck
executable remains UX707 and public v0.5.0 is unchanged. Packaging and
attended product checks remain separate release gates.
