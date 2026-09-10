# Private texture ownership — September 10, 2026

The standalone page-image implementation reconstructs every byte of five captured
16 MB Exotica texture-memory snapshots, even when all updates are queued before
the consumer runs. It is not linked into MAME yet. No new native build, deployment
or seven-default renewal is implied; those checks still belong to native86deac.

`native/page_image.h` owns changed 4 KB pages and validates their sequence, sizes,
ordering and integrity before modifying the receiving image. Staging does not
advance the producer baseline: the caller must successfully queue the whole scene
before committing. A full first image establishes the baseline; unchanged images
still advance the generation. Truncated, missing, duplicate, reordered, corrupted
and incompatible-baseline updates fail without partially changing the consumer.
Indexed FNV page hashes detect accidental corruption; they are not authentication.

The bounded PIM1 wire format uses explicit little-endian fields and exact lengths.
It carries no pointers into game memory. `harness/page_image.py` independently
decodes the native packets, calculates page hashes, and reconstructs complete
images. A Python-generated first packet also matches native serialization exactly
and passes the native decoder. The analyzer queues at most eight snapshots and
rejects oversized inputs before allocating their contents.

## Evidence

The sequence is Hong Kong5000, Hong Kong5990, Hong Kong5000 again, Amazon5072,
then Hong Kong5990. Changed-page counts are **4096, 4, 4, 1376, 1376**. All
**83,886,080 reconstructed bytes** match their source snapshots. The first packet
is 16,793,664 bytes; four-page updates are 16,464 bytes. No UV-footprint estimate
or texture allowlist is used.

The local harness passes **311 Python tests without skips, 37 native programs
and 107 commands**, including existing GPU checks. Source identity:
`c5e43b05b42a4783d6a3b0548fab632dffe7f4a24d823aa769ecfff1f6fd6716`.
The native page analyzer SHA256 is
`d6f303b39960cb9d2abd76d49ff6894abb06605bbadce7687d7a6642f253010a`.
Public proof contains hashes and sanitized timing data; raw texture images and
packets remain in ignored local diagnostics.

## Cost and remaining work

A standalone 705-sample CPU microbenchmark checks both reconstructed images after
every sample. Comparing unchanged 16 MB images averages **1.049 ms** over500
samples; alternating the two Hong Kong snapshots averages **1.151 ms** for staging
over200 samples, with four changed pages each time. This is not a live frame-time
or emulation-speed measurement.

Initial full-image work is expensive: staging20.455 ms, serialization2.771 ms,
producer validation18.481 ms, decoding3.243 ms and consumer validation18.783 ms.
Track changes also cost more. Initialization/prewarming and whole-scene queue
budgets therefore need explicit handling before normal gameplay use. No live
hitch-free claim is made. Preserve the complete benchmark, not just its steady
state average.

Next connect the owned image to private GPU texture and palette resources, verify
uploads and readiness, and preserve the original renderer's textures, palettes
and depth. The existing 64 MiB ring must accept each complete bounded scene before
the producer advances. Structural sky/foreground insertion, source eligibility,
fade and handover remain separate requirements. This cache alone neither fixes
Amazon's missing ground nor increases draw distance.

Evidence is under `results/diagnostics/exotica-amazon-20260909/material-page-*`
and `page-image-benchmark.*`. Earlier draft checks and the final bounds acceptance
are retained. Continue directly toward useful live scenery; do not pause for the
recovery heartbeat.
