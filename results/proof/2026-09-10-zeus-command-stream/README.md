# Bounded Zeus command/upload journal

Run `python verify.py` here. The verifier recomputes source identity and frame
coverage, compares the two journal hashes and independent playback result hashes,
and validates execution receipts. Game command bytes, materials, framebuffers and
images stay local; their execution and full comparisons are hash-bound receipts.

The first harness report remains FAILED: its parser expected every type6 message
to be a16-byte completed-frame marker. The original stream also contains a4-byte
display-address notification. The corrected parser distinguishes those formats
and still rejects missing/mismatched completion. The subsequent fresh run passes.
Independent original/private playback passes on both captures; this does not
erase the original failed run or renew defaults, performance or future drawing.
