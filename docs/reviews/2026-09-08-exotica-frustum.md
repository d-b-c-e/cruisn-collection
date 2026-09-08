# Exotica: CPU visibility before increasing far distance

The read-only gameplay probe identifies a useful global experiment: extend the
main CPU culler's projection reciprocal beyond its80,000-unit clamp, independently
of widening its horizontal sphere tests to match the Zeus GL canvas. Increasing
the unused204,800 far limit is not the first step. No rendering change is built
or exposed in the launcher at this checkpoint.

## Verified observations

The6000-frame Exotica replay retains all recorded frame inputs/times and matches
all21 completed3840×2160 GL references. The probe covers frames2500..4300 and
validates339,018 object tests, using cached object/fast-RAM position, actual float
register operands and an independent instruction after the rejection branches.

| Measurement | Result |
|---|---:|
| Objects passing the original CPU sphere tests | 215,946 |
| Far-limit rejects at204,800 | 0 |
| Samples whose true projection index exceeds4,999 | 85,350 |
| Maximum observed center depth | 140,424 |
| Predicted extra admissions from unclamped reciprocal alone | 4,051 |
| Predicted original admissions lost by that change | 0 |
| Predicted extra admissions from88-pixel horizontal margins alone | 21,717 |
| Predicted extra admissions from both changes | 28,610 |

These are repeated object instances across frames, not counts of unique scenery
objects or visible pixels. The tests are global and contain no model or level
allowlist. Model addresses in the report are attribution only. The dominant
original rejection is the right horizontal plane113,588 times; the other rejected
groups are left1,313, lowerY2,964 and upperY5,207.

The renderer defaults to88 pixels on either horizontal side of its512-pixel
canvas (`src/devices/video/zeus2.cpp`). The CPU culler still tests0..511. This
creates a separate widescreen-admission hypothesis, not proof that every rejected
sphere should draw. Existing sphere-radius and Zeus geometry/resource rules still
matter.

## Diagnostic validity

Object depth/radius/model and camera-space coordinates are cached at the67DA read
atPC6888. No table callback recursively reads overlapping object RAM. Float
operands atPC6890/6893/6898/689C match that captured pose/table within a small
float-export tolerance. Branch order and delay slots are explicitly validated.

The first acceptance probe used the0FF9 read atinstruction689D. That instruction
runs inside the final X-reject branch's delay slots, so it falsely marked some
rejected objects as accepted. Its replay still matched the game, while the
independent analyzer correctly rejected its interpretation. The corrected marker
is instruction68A3, observed atPC68A4, after all delayed rejection branches.
The complete rerun passes the analyzer; the old receipt/script and a rejected
sample are retained. Do not reuse the earlier acceptance marker.

Five focused analyzer tests cover unclamped admission, independent margin effects,
delayed Y branches, far rejection and inconsistent pose/acceptance. The
[ROM-free proof archive](../../results/proof/2026-09-08-exotica-frustum/README.md)
recomputes all339,018 decisions and checks native/input/GL receipt bindings.
Runtime evidence is `results/diagnostics/exotica-frustum-20260908`.

Native remains8b151aa9c2f, SHA638c74ff4227532d0ff42be4cd46cb8a358a1a343549abb107bb56050e91bd74.
No physical FFB, personal settings, ROMs or original recordings were changed.

## Next bounded experiment

Compare stock, unclamped reciprocal, widened CPU sphere bounds and both together.
Replace only the verified main-culler read atPC688C, using the true depth cached
outside that tap; preserve the short-range C371/C375 helper and underlying RAM.
Keep the204,800 far limit unchanged. For the horizontal experiment, adjust only
the culler's center/upper-plane reads, leaving other consumers of those constants
unchanged. Use completed GL captures during the affected interval, candidate
repeatability, timing and resource checks before any product promotion.
