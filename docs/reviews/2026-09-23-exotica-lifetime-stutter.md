# Exotica Mars: lifetime bursts and recurring pauses

The owner changed to three 2560×1440 displays, so the frozen 4K comparison
cannot run unchanged: Zeus's completed-frame checker requires a display matching
the recorded 3840×2160 reference. A single new replay used the existing Mars
input at 1440p with native `4df727db105`, continuous quiet 3×, CRT on and
literal `MIDV_FFB=0`. No attended drive or physical force was used. The
recorded input/time and native snapshots match, six completed 2560×1440 GL
images were captured without drops, and the renderer drained and joined on
normal exit. These six images are **not** compared with the 4K reference;
Zeus's native images do not show its GL gameplay.

The bounded 3700..5690 profiler recorded 1,236 lifetime source completions in
14 frame/scene buckets. Those callbacks took 206.3874 ms total, about 167 µs
per callback on average. Installing their temporary read taps took 1.5049 ms
total, about 1.22 µs each. The ten largest completion buckets took 14.5–17.6 ms
each. This total covers registry binding, endpoint binding, owner insertion,
buffered lifetime logging and `m_lifetime_ready_tap.remove()`; it does **not**
isolate the last operation. MAME's tap installation invalidates read caches,
and removal invalidates read/write caches, so removal is a plausible cost, not
yet an established cause.

The saved callback-clock analysis associates each native event frame with the
next recorded callback interval. All 14 event-adjacent intervals exceed 25 ms
in the new run; 12 other intervals in the window do too. At the **same frame
ordinals** in the earlier 4K `1fccd423f39` run, all 14 exceed 25 ms, versus
three others. This repeatability predates the new timing probes. Native scene
frames and callback frames are distinct clocks, however, and 1440p/triple-monitor
load differs from the older 4K environment. Adjacency is strong evidence of
a recurring contributor, not an exact latency decomposition or a matched
performance comparison. Other pauses remain independently open.

`harness/analyze_lifetime_stutter.py` validates native installation/completion
bucket pairing and consecutive monotonic callback timestamps, retains source
hashes and rejects incomplete windows. The focused synthetic test checks the
one-frame attribution and missing next callback. The initial test fixture
placed its long interval one frame late and failed; it was corrected before
the passing two-test run. No game was rerun for the test.

Local evidence:

- `results/diagnostics/exotica-mars-timing-20260923/lifetime-1440-prepared`:
  FFB-disabled plan with exact executable and primary 1440p display.
- `lifetime-1440-run/report.json`: passing input/native and owned shutdown;
  six completed 1440p frames. One frame4800 was inspected visually as a valid
  Mars gameplay image, without a defect/benefit claim.
- `lifetime-1440-qualified.json`: event and callback adjacency with raw CSV
  hashes; earlier `lifetime-1440-adjacency.json` is retained.

Next, split the completion timer around tap removal in a new isolated native
candidate. If removal dominates, evaluate a static or less frequently changed
hook without losing exact source ownership; if it does not, investigate the
binding/logging portion. Reuse the recording, keep FFB0, and require matching
input/visible pixels before treating an optimization as a product change. The
pending exact 4K comparison remains for a 4K display session. Do not deploy
this profiler to the personal build.
