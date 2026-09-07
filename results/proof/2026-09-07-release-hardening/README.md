# Renderer and release hardening evidence

2026-09-07. These component checks precede the final release gate. Original
recordings remain immutable. Physical FFB was disabled for all emulator runs.

- Final native C925 / aef6d446: twelve full-window startup runs (3 per game),
  scale4 + CRT, all requested completed GL frames and repeat comparisons pass.
- Earlier GPU-copy prototype: 26 completed GL frames per paired V-Unit prefix
  exactly match the old renderer. Off Road has a separate correct401-row pair.
- Stall controls:100ms recovers with3/3 identical images. A1500ms stall with
  a short1804-frame run ends before two requested images: correctly FAIL. With
  a2404-frame run it triggers stream timeout at1829 (16MiB queue,750ms wait).
  A5000ms stall fails at1607 with0 consumer bytes during the765ms wait. Those
  are deliberate failures, not passing recovery claims. Watchdog unchanged.
- The116 exported patches reconstruct the native commit tree exactly.

`renderer-traces.zip` retains reports, callback timing, completed-frame receipts
and native logs. Every archived entry is verified in `renderer-trace-hashes.json`.
The reports describe their original binary/source versions; prototype results
are not relabelled as final-build acceptance. Full driving/frozen-package checks
will be attached separately.
