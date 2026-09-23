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

## Removal subphase, later September 23

Native `54dfc723b04` adds one nested timer around `m_lifetime_ready_tap.remove()`.
Canonical `native/phase_timing.h` is synced to MAME. The new build passes the
focused six Python timing/adjacency checks and the compiled native boundary
test; its269-patch export is attested in `lifetime-removal-native-export.json`.
The personal UX707 binary is unchanged. The first direct PowerShell invocation
of MSYS `g++` returned1 before an executable was produced; the project-standard
MINGW64 login-shell compile and test passed. The postcommit MAME build linked
successfully, and its log is retained. Prior export scripts were not rerun.

One matching 1440p replay of the same8,209 inputs passes input/time/native
comparison, six completed1440p GL frames **byte-exact** against the prior1440
profiler, zero dropped frames, and quiescent joined shutdown. Its1,236
completion callbacks still occupy14 buckets. The nested removal timer records
208.0799 ms of209.3094 ms completion time, **99.4126%**. The other binding,
logging and state checks account for the remaining1.2295 ms of the measured
callback interval. Temporary tap installation is1.5364 ms total. All14
subsequent callback intervals exceed25 ms again. This isolates where the
observer spends time; it does not yet prove how much full-frame time will be
recovered by replacing removal or establish matched 4K performance.

Local new evidence under `results/diagnostics/exotica-mars-timing-20260923`:
`removal-1440-prepared`, `removal-1440-run/report.json`,
`removal-1440-qualified.json`, native export and two build logs. The first
qualified adjacency report retains its source hash; the new report validates
that nested removal cannot exceed its enclosing completion bucket. Seven
focused Python timing/adjacency tests pass after that analyzer change.

Next trial: retain the verified owner/source keys but replace per-object tap
installation/removal with one fixed hook at the known constructor-completion
instruction. Keep it opt-in and reject the exact ROM signature if it differs.
The C31 fetch path uses an opcode cache, so a fixed read tap may fail to observe
the instruction; an early bounded replay must prove coverage before any longer
trial. Preserve the dynamic path as control and do not deploy the trial.

## Fixed completion opcode trial, later September 23

Native `bbcb4db7bd9` retains the dynamic slot tap by default and adds an
explicit Exotica-only `MIDZ_LIFETIME_READY=opcode` trial. It validates the exact
ROM instruction signature before installing one fixed opcode read hook and
still checks the dynamic owner and source key before completing a lifetime.
The collection wrapper accepts `--exotica-lifetime-ready opcode|slot` only
with the exact frozen candidate, Exotica, and literal `MIDV_FFB=0`. The
270-patch export is attested in `fixed-ready-native-export.json`; the personal
UX707 binary remains untouched.

The original Mars 8,209-input case passes input/time/native comparison, joined
quiet shutdown and six completed 2560×1440 GL captures **byte-exact** to the
removal-profile control. The fixed hook observes the same 1,236 completions in
14 buckets; total completion time falls from 209.3094 to 0.5454 ms. Subsequent
callback intervals above 25 ms at those buckets fall from 14 to 1. Other
long intervals fall from 12 to 6, including a 65.4718 ms outlier next to a
0.0392 ms hook bucket. This is a substantial matched 1440p improvement, not
proof that every remaining pause is fixed or that 4K behaves identically.
One scheduling-dependent depth-mirror batch count differs; all requested
visible images and deterministic source/ownership evidence match.

The first short replay plan failed **before launch** because its frame limit
conflicted with the preset's mandatory reference endpoint. The full case was
then used once; the failed plan remains in `fixed-ready-scout-prepared`.
The passing run and analysis are `fixed-ready-full-run/report.json` and
`fixed-ready-1440-qualified.json`. The native boundary test and focused Python
timing/wrapper contracts pass.

For a second route, the existing Amazon/name-entry/next-race recording ran
11,260 inputs with the same binary and explicit slot control, then with the
opcode option. The slot run passes. The opcode run preserves all recorded
inputs/timing/native images, lifetime counters, quiescent shutdown and six of
seven completed GL images **byte-exact**. Its raw report correctly **FAILS**
display-size validation: at frame 6300 the overlay captured 7680×1440,
spanning the width of all three 2560×1440 monitors. Frames 5400 and
7200–10800 were 2560×1440 and exact. This cannot be called a passing visible
comparison. The anomaly is in the overlay's per-present monitor rectangle,
which supplies the framebuffer viewport and readback size; the recorded
evidence does not establish whether Windows transiently exposed a combined
monitor or why the parent window's nearest monitor changed. The source
at that candidate reselected that rectangle each present. The two raw reports and
`captures.csv` files are retained under `amazon-slot-run` and
`amazon-opcode-run`. A narrow one-monitor guard is being evaluated separately;
do not rerun the whole drive just to seek a favorable frame.

## Triple-monitor presentation trials, later September 23

The host's display enumeration changed during this work. It initially showed
three separate 2560×1440 monitors, then one 7680×1440 monitor, then one
2560×1440 monitor, and later the merged 7680×1440 monitor again. The oversized
Amazon frame matches the merged desktop width, but there is no timestamped
Windows mode-change record proving exactly when the switch happened in that
run. The renderer's rectangle is obtained from Windows monitor information;
the failure cannot be attributed to the opcode hook from current evidence.

Native `7ba534e7b5e` pins the default overlay to its launch monitor and rejects
a later rectangle more than twice its launch dimensions. Its271-patch build and
export are attested; no personal deployment occurred. An Amazon replay with
this candidate **FAILS** at presented frame2646 with an owned waiting-queue
consumer timeout, before requested images. That raw failure remains in
`amazon-guard-run/report.json`; it does not validate the guard or condemn the
opcode hook. The graphics log shows zero dropped quads and one dropped state
message on teardown, and the shutdown joins after the fatal queue rejection.

Native `4c6af67ae1a` adds an opt-in `MIDZ_GL_PRESENT_SIZE=WIDTH:HEIGHT`.
At the exact physical size it uses the monitor; on an exact three-panel-wide
merged monitor of the same height it uses the center third. Other geometries
are rejected. The replay harness now permits this merged layout only for
explicit Zeus `--display-size`, passes the target size to native and still
requires completed captures at the requested size. A standalone compiled
region test covers physical, merged, offset and invalid geometries; the
17 focused Python display/lifetime tests pass. Its272-patch export is attested.

The first Mars replay under the merged 7680×1440 desktop logs the expected
selected rectangle, `(2560,0)..(5120,1440)`. It then **FAILS** at presented
frame706 with an owned future-queue consumer timeout before any requested GL
capture. The original input comparison could not complete. Preserve
`mars-single-panel-run/report.json` and its native log. This proves the
initial panel-selection calculation ran in the real emulator; it does **not**
qualify a full drive, topology transition, or stable presentation. The two
queue failures occurred at different frames and have no established common
cause. Repeating long routes while the host changes display layout would be
low-value. Resume a bounded visual replay when the monitor topology is stable,
then return to the pending exact 4K candidate comparison when a 4K display is
available. Neither candidate is promoted to the Stream Deck installation.
