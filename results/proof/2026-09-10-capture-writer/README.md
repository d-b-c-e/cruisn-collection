# Capture writer acceptance receipts

This archive records acceptance of the separate native candidate
`b3d82b67257ad8fe8738bfc4e0240647315318fd`, SHA256
`e7780a7a3f1ff0b5d0efdff6f713c813fb9d2267a5ab7062108703ba5b1e02bb`.
Its159-patch export reconstructs tree
`c6ce30f836bf107233714792d9c003082d3d21bc`.

Run `python results/proof/2026-09-10-capture-writer/verify.py` from the repository
root. It verifies42 archived receipt hashes and their declared consistency:
290 Python tests without skips,34 native helpers,96 local commands, all seven
default cases, both menu/action replays,49 dense V-Unit images, two21-image
Hong Kong runs and117 full-drive Amazon images. The accepted source identity is
`6f98b85c5be1cc37d4e2427bf4509d162da7535080caad731137329d94ab8021`.

These are execution receipts and recorded comparisons. The verifier does not
rerun native tests or recompute unarchived image bytes, resources or route traces.
Raw game resources, captures and complete traces remain in ignored local
diagnostics. Full comparison execution happened before this archive was made.

Two real failures remain explicit: synchronous bulk file I/O timed out in the
Hong Kong repeat, and the first unpaced V-Unit burst rejected18 of49 captures
when its bounded queue filled. The final paced burst completed all49. A separate,
predeclared5000ms consumer-stall test correctly fails its raw replay and passes
the fault check; enabling capture pacing does not excuse an unrelated stall.

The native writer uses a bounded background queue. Only explicit offline pacing
may wait for queue storage; normal capture remains nonblocking. Capture-index
entries require successfully completed BMP writes, and incomplete or failed
writer receipts fail validation. See the
[implementation and limitations](../../../docs/reviews/2026-09-10-async-captures.md).

No deployment, release or physical-force testing occurred. The personal Stream
Deck executable remains v0.5.0/SHA87d04de4.
