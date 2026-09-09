# World host scenery cost and section milestone

Run `python verify_archive.py` from this directory. The verifier uses the standard
Python library and the archived project analyzers; no ROM or emulator is needed.

The 145-file archive recomputes five full Germany scene/timing/input controls,
137 numerical yaw vectors, 16,444 initial material lookup values plus 410 later
writes, and seven telemetry/four force verdicts. It verifies local-check receipts
and the exact three diagnostic files changed after the default suite began.

The full-polygon trace's 16.127-second callback stall and 88.633% interval speed
remain a timing failure. Summary runs preserve ordered fingerprints and recorded
motion, with callback maxima below 0.9 ms and interval speed above 99%. These are
CPU callback timings, not completed GPU latency or whole-game stutter acceptance.

The first two allocation probes have explicitly incomplete initial-write coverage.
Only the corrected third probe observes both initial bindings for all 8,222 objects.
The archive recomputes scalar lookup/write/ready-value equality; source addresses,
ownership checks and raw instruction context remain locally verified receipts.

Completed GL comparisons, detailed geometry equality, full section placement,
resource checks and native/build results are hash-bound receipts. The archive does
not contain raw section definitions, positions, game models/textures, instruction
dumps, ROMs or emulator binaries. It does not independently render the screenshots.

Candidate native `c1ef52c2dcc` / SHA256 `41b0fdf35edf3c61ec2448721a5d283061f1e310c794028a0ec1e83fd5c01690`
is built separately. Personal Stream Deck native remains v0.5.0 (`87d04de4…`).
No new distance geometry, cross-game 3x acceptance, menu removal, physical FFB test
or release is claimed. See the [review](../../../docs/reviews/2026-09-09-world-host-cost-and-sections.md).
