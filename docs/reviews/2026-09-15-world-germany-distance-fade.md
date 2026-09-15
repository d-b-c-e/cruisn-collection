# Germany: no visible distance-fade benefit in the late-race window

The same-candidate World2.4 Germany off/on pair preserves all7,400 recorded
inputs and original native images. All31 completed presentations7060..7360,
every10 frames, are pixel-identical. The new outer20,000-unit distance fade has
**no visible benefit in this window**. The appearance comparison correctly remains
FAIL for lack of an effect; it must not be advertised as a successful pop-in fix.

The current monitor is3840×2160; the maximized V-Unit client captures are
3824×2073 with CRT enabled and2736×1600 internal indexed buffers. Frame7340 was
viewed: the known black wedge at the left road margin remains. A spatial fade at
220,000..240,000 units does not repair missing nearby geometry.

Both runs transport9,008,212 host metadata packets, including1,154,698 authored
road quads. All2,796 host-scene rows are exact except the eight explicitly named
duration fields. All eight indexed/mask planes at7340 match, including the four
original-only planes. Both opacity pages are entirely one at that snapshot.
This does not establish whether other Germany windows have visible far-band
coverage, nor whether every admission transition occurs within the fade band.

The initial control report failed because the verifier required at least one
metadata packet at the capture frame. This part of World draws on odd frames:
7339 and7341 contain host geometry;7340 contains none. Both boundary files contain
only their valid VFD1 header. The corrected verifier allows an empty capture only
when the scene log has no quads for it, while requiring positive and complete
aggregate packet/road coverage. Focused tests reject missing packets for an actual
draw and incomplete aggregate coverage. This snapshot provides aggregate coverage,
not per-quad depth proof. The earlier World2.5 nonempty capture retains that proof.

The original failed report remains intact. A saved recheck executes all applicable
receipt guards, recorded-reference integrity, input/native comparison and all31
completed-image checks. No control replay was needed for this analyzer correction.
The new canonical comparison tool reproduces the earlier World2.5 positive result
from saved artifacts and rejects settings/binary/force differences beyond the
explicit fade toggle and relocated runtime paths.

In the preselected capture-free6500..6800 interval, control/candidate emulation
ratios are100.091%/100.007%. This is one instrumented comparison, not broad release
performance acceptance. No repeat is justified to seek a favorable result.

Evidence under `results/diagnostics/world25-roads-20260914/`:
`distance-fade-germany-control/report.json` (initial FAIL), its
`report-rechecked.json` (input/native/capture PASS), `distance-fade-germany-on`,
`distance-fade-germany-qualified.json` (appearance FAIL),
`distance-fade-germany-cost.json`, and `distance-fade-canonical-pair.json`
(saved World2.5 PASS). Seven focused Python tests pass.

Native remains e5344546a8e, SHA
`8e09bf779f582adcfbfbcfb18ce41304e5eedd2e82aad9a787f5205ca484699d`.
Personal87d/publicv0.5.0 are unchanged. No deployment, release, hosted CI or
physical force output. Continue independent Off-Road depth preservation and
game-specific appearance-policy work; no claim of four-game fade parity.
