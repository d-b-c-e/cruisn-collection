# USA partial coverage: bounded preparation cost screen

The existing paired source-summary runs give a first cost estimate near the
Golden Gate bridge. Over source frames 10000..10469, 235 exact matched scenes
submit 895,053 auxiliary quads with ordinary continuous 3× and 904,413 with
partial far coverage: 9,360 additional quads. The native host-scene timer's
mean rises from **2,289 to 2,492 microseconds** per scene, about **+203 µs**
(8.9%). Medians are 2,267/2,476 µs; sampled p95 values are 2,465/2,639 µs.
This is a measurable preparation cost in this one instrumented window, not a
GPU or full-game performance verdict.

Both frozen `f762e01d63b` replays use the same 10,477 recorded inputs,
physical 2560×1440, literal FFB0, CRT on and no completed-image captures.
The source frames, emulated times and pages are exact pairwise matches, as are
recorded input/time clocks. The read-only source tap in the control does not
fire until frame 10473, beyond the measured window. Host elapsed time for
the 470-frame window is 8.10596/8.10675 seconds; near-100% synchronization
can hide extra work when there is headroom. This does **not** establish equal
throughput, GPU cost, stutter behavior, 4K performance or other-course cost.
No additional game replay was made for this offline screen.

The source-hashed local report is
`results/diagnostics/race-transitions-20260916/usa-bridge-cost-v1.json`;
the checker is `harness/screen_usa_bridge_cost.py`. It validates the
[exact matched candidate scene](2026-09-28-usa-bridge-source-projection.md),
both raw replay reports, source clocks, recorded inputs, display and the
capture-free interval. This cost should be weighed against the
[visible two-object gain](2026-09-28-usa-bridge-pixel-source.md) before any
default policy. No native code, installed renderer or release changed.
