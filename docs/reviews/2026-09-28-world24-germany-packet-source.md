# World 2.4 Germany: source packets behind the left-edge building

The [Germany 7280 ownership check](2026-09-28-world24-germany-overdraw.md)
showed that the active non-road margin candidate replaces 19,471 indexed
pixels of the game's upper panorama with a small left-edge building. The
existing matched mirror runs also retain detailed host-quad traces, so I
used them to identify the candidate source without another game replay.

`harness/screen_world_added_packet_coverage.py` validates the saved control,
candidate and original-DMA reports on frozen diagnostic native
`f762e01d63b`: input/native comparison, physical 2560×1440 display,
literal FFB0, owned shutdown, completed source clock/page, scene counts and
ordered fingerprints, original-only planes and 4:3 center; it uses and hashes
the captured texture.
The completed 7280 image selects source frame **7277**, page control **513**.
The exact old scene has **2,485** packets and the candidate **2,715**. All
old packets remain an ordered subsequence; **230** packets from **85**
active objects are added.

Isolating those added packets with the saved completed-frame texture
reproduces the candidate index at **all 19,471 changed indexed pixels**.
Nine source objects actually contribute to these changed pixels; the
largest, `0xc0010e20`, accounts for **11,867**. The prior original-DMA
screen attributes every replaced control index to the game's first two
upper panorama strips. Thus this one cross-course change is explained by
added active geometry over backdrop, rather than a missing texture or
merely a count of submitted quads. The left-edge building is visible in
the completed candidate image.

This is one indexed frame and an isolated added-packet raster. It does not
reconstruct the full original/host draw order or per-fragment depth, qualify
every Germany turn or foreground occlusion, repair the reported black road,
move distant mountain/tree activation, or establish physical 4K/release
safety. No game replay, native code, deployed renderer, personal installation
or public release changed.

The source-hashed local result is
`results/diagnostics/world-new-york-20260927-live-1/germany-7280-added-packet-screen-v1.json`.
It joins the previously saved `germany-7280-mirror-{control,nonroads}-run`
and `germany-7280-original-dma-run` evidence.
