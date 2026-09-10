# Zeus wider-depth foundation — September 10, 2026

Two reusable GPU diagnostics now pass on the RTX 5080: an exhaustive original
depth comparison and an original-only mirror of synthetic commands through the
actual Zeus material shader. This is **not integrated into MAME**, does not draw
farther scenery and is not evidence of 3x distance parity.

## Why a simple precision change failed

The original shader normalizes an integer depth by 16,777,215 and writes D24.
The initial proposal mapped the integer directly into a larger D32F range using
a power-of-two denominator. CPU arithmetic preserved the integer ordering, but
the real GPU test failed: the old path merges two pairs of adjacent input values
that the naive replacement separates. With LEQUAL, that changes polygon winners.

The diagnostic captures the actual stored D24 codes. On this driver the result
matches a float reciprocal multiplication followed by D24 quantization. The
exceptional equality pairs begin at 8,388,607 and 16,777,214, but **no special-case
list is used**. The replacement keeps the original float normalization, computes
its normalized-integer quantization with a double intermediate, then maps that
code into D32F with a denominator of 2^26. The maximum original code and clear
depth both retain the 1.0 sentinel.

`harness/verify_zeus_depth_domain.py` checks all 16,777,216 original inputs on the
actual GPU, then compares closer, equal and farther draws. It derives expected
private depths and equality counts from the captured original buffer rather
than assuming this driver's two ties. All three comparisons pass. This still
needs validation on other GPUs/drivers; the observed quantizer is not a universal
OpenGL implementation guarantee.

`gpu/zeus_depth.py` produces a diagnostic shader variant without changing the
original shader. `harness/verify_zeus_depth_mirror.py` exercises 18 material/depth
cases at scales 1 and 4 on pages 0 and 400: **72 cases / 360 ordered steps**.
After each step, colors match and the private depths equal the mapped original
codes. Cases include depth ties, negative bias, depth floor, depth clear, disabled
depth testing/writing, blending, zero alpha, three palette texture modes, embedded
alpha, RGB555, transparent texels and raw framebuffer writes. A nonblank base
fixture prevents two empty render targets from becoming a false pass.

Initial local fixture failures are retained: a texture byte-count mismatch, then
clear/state handling and a deleted framebuffer restoration issue in the test
wrapper. Explicit GL target/clear state and a live scratch target corrected the
fixture. The original mathematical/GPU mismatch remains a separate retained
failure, not attributed to those fixture mistakes.

## What must follow

1. Mirror the complete original live command stream into a private color/D32F
   target, including startup and page clears, direct writes, palette changes,
   texture uploads and all original polygons. Keep the displayed target intact.
2. Compare original-only full-drive images, resources and route, with independent
   depth checks at bounded snapshots. Measure the additional GPU/CPU cost.
3. Prove the early scene insertion boundary relative to sky and foreground work,
   then insert decoded farther sources with checked material lifetimes.
4. Implement and test true pre-clamp farther depth separately. Saturated original
   geometry cannot remain a clear sentinel during a seamless transition into
   the wider range. Original/future overlap, transparency and handover need their
   own acceptance. More storage range alone does not solve these problems.

Native remains the separately accepted margin candidate 50a / SHAa4e4cd4d;
personal v0.5.0 / SHA87d04de4 is unchanged. The new checks are standalone Python/GL
tools. They do not renew or invalidate the previously recorded seven-default
native result by pretending a different executable was tested.

The final local suite passes332 Python tests with no skips,46 native checks and
129 commands at source identity
`9f38afb5a71c39b54602cca9aca3a7e848dc3002cf22588498f448c6dbd8235d`.
Only the three standalone diagnostic/helper files and local-suite registration
change from the accepted margin source. Public
[proof](../../results/proof/2026-09-10-zeus-depth-domain/README.md) recomputes
source identity, recorded clocks, timing and ordered fingerprints; actual GPU
and local-test outcomes remain hash-bound receipts.

## Performance without heavy captures

Three full Amazon replays preserve the original camera route and actual input
sampling times with screenshot/model/raw-host captures disabled. Ordinary session
and motion logging remain enabled. Their measured overall emulation speeds are:

| Mode | Speed |
|---|---:|
| Baseline rendering | 99.99% |
| 3x future geometry observer, no extra drawing | 94.90% |
| Future observer plus current-distance margin drawing | 93.06% |

The observer builds 15,907,490 quads across 5,290 scenes. After initialization,
mean source preparation is 0.076 ms, geometry assembly 1.973 ms, ordered hashing
0.676 ms and material processing 0.059 ms per scene. The margin run reproduces
the accepted current-margin fingerprints. These are one run per mode, not a
statistical performance study or GPU-present latency measurement.

**Performance remains open.** The earlier costly screenshots did not explain
all slowdown. A normal current-margin mode should avoid building unused future
geometry; a useful future renderer also needs cheaper construction/diagnostics
or GPU-side model work. Do not turn off correctness checks silently to advertise
a faster equivalent result, or treat an input-verification pass as a speed pass.
