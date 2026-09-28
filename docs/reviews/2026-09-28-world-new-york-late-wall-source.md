# World 2.4 New York: source of the late right-wall pixels

The [late-wall sample](2026-09-28-world-new-york-late-wall.md) replaces
98,129 indexed pixels previously drawn by the game's upper panorama at
completed frame 6300. Its [nine-view turn screen](2026-09-28-world-new-york-late-wall-temporal.md)
shows a right-edge improvement, but neither check identified the added
objects. This bounded source check ties that one completed frame to exact
source-time native packets without two broad per-quad game journals.

Frozen diagnostic native `f762e01d63b` ran one additional read-only
source-tap replay through 6,302 inputs on the physical 2560×1440 primary,
literal FFB0, CRT on. Its raw report **PASS**es original input/native,
display watch and owned worker shutdown. The completed 6300 control BMP and
all eight indexed mirror planes are byte-exact to the saved 6,310-input
control mirror. The Lua tap fired at source frame **6296**, C31 PC `0x6a`,
read address `0x61ee`, and saved the program RAM, C31 RAM, texture and palette
at that actual host-scene read. Its texture hash is exact to the earlier
completed-frame resource capture.

Freshly compiled `native/analyze_world_future.cpp` reconstructed the same
source with the existing 240,000-unit far limit and road/far-coverage/active
road options. Without active non-road margins it emits **4,832** ordered
packets, fingerprint `3e6b61938542a74a`; with the option it emits **5,913**,
fingerprint `087a8d1f01b69ee4`. Both count and fingerprint exactly match
their respective **live completed-frame source scenes** (frame 6296, page
control 513). All old packets remain an ordered subsequence; the candidate
adds **1,081 packets from 132 objects**.

`harness/screen_world_native_source_pixels.py` checks those live fingerprints,
source receipt, saved run identity/input/display/FFB/shutdown, original-only
and 4:3 indexed preservation, packet order and texture hashes before raster
attribution. Isolating the 1,081 added packets with the source-time texture
reproduces the candidate index at **all 98,129 changed indexed pixels**. The
largest contributing source object is `0xc0011788` (model `0xf04d49`), with
57,980 pixels; 45 other objects contribute the remainder. The prior
original-DMA check attributes every replaced control index to upper-panorama
ordinal 3. This narrows the visible wall extension to current active non-road
geometry over authored backdrop, rather than an unspecified quad count.

The isolated raster does not reconstruct the full original/auxiliary draw
order, per-fragment depth, or visibility between the five-frame temporal
samples. It does not establish foreground safety on the full route or
another course, fix all black artifacts or distant pop-in, or qualify 4K,
physical wheel output, renderer deployment or release.

The existing `build/tests/analyze_world_future.exe` access-violated on the
new source and produced empty output/log files; it still passed the older
3596 source. A fresh optimized build from the current helper source and a
debug build both completed the 6296 scene. This points to the older local
helper binary as unsuitable for this input, not to a reproduced game crash.
The raw zero-byte output/log are retained. Its signed Windows exit code and
executable/source hashes are in
`active-nonroads-6300-stale-helper-failure.json`. The first quad-trace
prepare-only request failed because quiet journals exclude detailed geometry; corrected
prepare-only plans warned that `--world-host-first` would not limit the
continuous detailed journal, so **no** broad quad-trace gameplay was run.
The first source-tap preflight failed because it omitted the required
metadata toggle; its corrected preflight and replay passed. A deliberately
mutated native packet is rejected before rasterization with the expected
fingerprint error, and its raw negative output is retained. These failures
are distinct from the passing source replay and checker.

No native product code/binary, renderer deployment, personal installation or
public release changed. Local evidence under
`results/diagnostics/world-new-york-20260927-live-1` includes
`active-nonroads-6300-source-run/report.json`,
`active-nonroads-6300-native-{control,trial}-v2.txt`,
`active-nonroads-6300-native-source-pixels-v1.json`, the earlier matched
mirror/original-DMA reports, and preserved prepared/raw failures. Python
compilation and the positive/negative source checker were run against these
saved files.
