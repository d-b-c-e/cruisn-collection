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

This proves project regeneration and native linking from the current working
checkout, plus byte-identical reset shader source. It is not a clean-clone
build, a new live machine-reset replay, a renderer promotion or a release.
The personal Stream Deck executable remains UX707 and public v0.5.0 is
unchanged. Fresh-clone build and packaging remain separate release gates.
