# Zeus screenshot packing and timeout diagnostics

Zeus allocated screenshot storage as `width * height * 3` bytes but left OpenGL
readback at its default four-byte row alignment. Widths whose RGB rows are not
multiples of four can therefore require more storage than allocated. V-Unit
already explicitly requests tightly packed readback.

Native commit `6864d3c6cde623fd4dc87b0b77d309ebe3c70864` adds the same explicit
`GL_PACK_ALIGNMENT = 1` before Zeus screenshot readback. It changes screenshot
storage handling, not game projection or texture coordinates. It is separately
built and pushed, with frozen candidate `build/candidates/6864d3c6cde/vunit.exe`,
SHA256 `84b0a06ad448d1307fe145fcdc315f6220daca300a61a34751a0c56717fb1454`.
The154-patch export reconstructs tree `08bc48e10649281dc6aab1d009c8dda49a044b7f`.

The reusable `harness/verify_gl_readback.py` fixture calls the actual Windows
OpenGL readback functions for eight widths, including both aligned and unaligned
RGB rows. It deliberately overallocates guarded storage. Legacy alignment
changes the tightly packed image and writes into the expected guard at every
unaligned width. Explicit alignment one preserves every expected byte and all
guards. The fixture never writes outside its actual allocation.

All local checks pass:281 Python tests without skips,32 native helpers, the
existing shader fixtures and the16 new alignment cases, across92 commands.
The429-file source identity is
`c50cdc7b9607c2f9e7dd14d00dd667208124a0be43025b8386b25458e29bd14a`.
Native4K boundary verification passes: all49 completed captures250..298 match
the previous build exactly, and the original300-input prefix passes. All-seven-default acceptance
still belongs to parent2b55; it will be renewed on the final diagnostic candidate.
The current physical monitor has an aligned width, so the native odd-width
memory case is demonstrated by the guarded OpenGL fixture.

This does not explain the earlier Amazon timeout. That failure occurred at an
aligned3840-pixel width and remains preserved. The next change will identify
the consumer's phase and measure capture readback, file writing and presentation
time. The queue's failure threshold should remain unchanged while diagnosing it.
The current harness explicitly rejects `--gl-stall` for Exotica as a V-Unit-only
experiment; extending that acknowledged fault test is a separate change. The
earlier local note suggesting it silently set ineffective variables was wrong:
the early validation rejects the request before those assignments.

No release, deployment or personal-setting change occurs. The Stream Deck
executable remains v0.5.0/SHA87d04de4. Evidence stays local under
`results/diagnostics/exotica-amazon-20260909/packing-*` and `readback-padding.*`.
