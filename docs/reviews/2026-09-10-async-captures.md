# Background screenshot writing and explicit offline pacing

A measured1.03-second file write caused a Zeus renderer timeout in the repeated
bulk-write trial. The next candidate moves BMP and capture-index writes onto a
single background thread shared by the two enhanced renderers. It owns encoded
host pixels and metadata only; no GL context, device state or guest memory is
passed to that thread.

The queue permits at most512MiB of encoded images and32 outstanding jobs,
including the write currently in progress. Files remain in request order. A
capture-index row appears only after its complete BMP has successfully closed.
Write, close, index or admission failures prevent a passing diagnostic. Final
receipts report submitted/written/failed/rejected counts, peak storage, write
cost and shutdown drain. A started writer without a final receipt is incomplete.
No screenshot requests means no writer thread. Ordinary play is unaffected.

The first unpaced49-frame V-Unit burst reached the bounded capacity:31 files
completed and18 were explicitly rejected, with523193220 peak bytes. The renderer
kept running and the harness correctly failed the capture. The old synchronous
baseline completed49. This failure remains evidence that an asynchronous queue
alone cannot guarantee arbitrary-rate, full-resolution screenshot capture.

`--gl-capture-pacing` is an explicit replay diagnostic requiring a candidate and
live capture range. Native pacing also requires physical force zero. It can wait
up to10seconds for screenshot storage. Its atomic signal identifies that
intentional wait to the producer; unannounced consumer stalls retain their
500-iteration threshold, and the overall ring wait is bounded at10seconds.
This can slow offline wall-clock playback. It does not advance an extra guest
frame, synthesize input or change emulated timing. The requested pacing must be
acknowledged in the final receipt. Ordinary recording remains nonblocking.

V-Unit's capture shutdown now gives its existing teardown handshake up to10seconds
and explicitly reports a timeout, instead of silently proceeding after one
second. Zeus retains its existing render-thread join. A stuck filesystem can
still fail the outer diagnostic timeout; bounded queue storage is not a promise
that arbitrary OS file operations will always finish quickly.

## Candidate and checks

The initial background-writer commit is515ba93691df71b35712dd10db0967c1b8fc6f4a;
the separate pacing commit isb3d82b67257ad8fe8738bfc4e0240647315318fd. The latter
was separately built and frozen as `build/candidates/b3d82b67257/vunit.exe`, SHA256
`e7780a7a3f1ff0b5d0efdff6f713c813fb9d2267a5ab7062108703ba5b1e02bb`.
The159-patch export reconstructs tree `c6ce30f836bf107233714792d9c003082d3d21bc`.

Portable tests cover active-write storage accounting, ordered completion,
nonblocking rejection, exceptions, actual fopen failure, empty shutdown, paced
admission, deadline rejection and signal cleanup. The harness rejects missing,
duplicate, inconsistent or failed completion receipts and unacknowledged pacing.
The full local suite passes290 Python tests without skips,34 native helpers and
96 commands at437-file identity
`6f98b85c5be1cc37d4e2427bf4509d162da7535080caad731137329d94ab8021`.

The paced49-frame V-Unit test now completes every requested image, with all BMPs
byte-identical to the old34b renderer. Peak encoded storage is523193220bytes;
21 capacity waits total1391123microseconds. The background writer takes
3883413microseconds in total, with a404917microsecond maximum and1764125microseconds
of final drain. This is intentional offline capture pacing, not a real-time
performance pass. The first unpaced6000 Hong Kong run also preserves original
camera/ADC and all21 whole BMPs, with preparation on the render thread at most
16ms. Its file I/O is measured separately on the writer thread.

Both unpaced Hong Kong runs pass all6000 inputs,4191 camera samples,12573 actual
ADC reads/times and21 complete4K BMPs byte for byte. The worker writes take
1741446/1665281microseconds total, with262025/169113microsecond maxima. The
render-thread preparation maximum is16ms in both, with no pacing or lost captures.

The full8860-frame Amazon run also passes with all117 BMPs byte-identical to the
validated sky-repeat run. All7060 camera samples/21180 actual ADC reads and ten
original model/device/resource files at7200 remain exact. It reports99.96%
average emulation speed. Writer peak storage is one24883254-byte frame; worker
file time totals8193875microseconds, maximum264363, and shutdown drain4669.
The renderer's capture-preparation maximum stays16ms. This covers the recorded
drive and sampled images, not every possible OS I/O stall or track.

With pacing enabled, an actual5000ms consumer stall at5400 still causes the
normal renderer timeout. The raw replay correctly fails; the separately planned
fault check passes, with original4191 camera/12573 ADC samples unchanged. The
writer has no capacity waits in that case: pacing does not excuse an unrelated
stalled consumer.

Real Esc/Cheats/Back/Resume/Exit tests pass in USA and Exotica: nine menu images
each, exactly one staged timer action, and successful input/action/GL replays.
Their recorded sessions complete2723/2724 frames. USA's15 recorded writes and
six replay writes all finish; Exotica's corresponding15/six also finish. The
Exotica menu test includes an actual509670microsecond worker write without
blocking menu capture progression. Both Cheats images were visually inspected.
All seven default cases pass on the same frozen source/candidate, including the
full Germany recording and Exotica's21 gameplay images, actual UDP/memory
telemetry and four software force-policy/polarity checks. Physical force stays0.
The [public proof](../../results/proof/2026-09-10-capture-writer/README.md) checks42
hash-bound receipts; it does not recompute unarchived images, resources or routes.
Raw failure evidence remains local under
`results/diagnostics/exotica-amazon-20260909/async-*` and `paced-*`.
No deployment, release or physical-force testing occurred; personal87d04de4 stays.
