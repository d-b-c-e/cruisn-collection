# Zeus stream timing and controlled stalls

The renderer now reports its consumer phase when backpressure occurs, plus
readback, file-writing, presentation and injected-stall counts, totals and maxima.
Logging is enabled by `MIDZ_GL_LOG`; ordinary launches retain their existing
path. The queue capacity and500-iteration wait threshold are unchanged.

The phase and its start time are published together in one atomic value. A
producer timeout reports the last presented frame, message size, queued bytes,
consumer progress, elapsed wait, observed phase and that phase's age. Slow
operation logs and completion summaries provide a second view. These are host
wall-clock measurements using `GetTickCount64`, with its timing resolution;
they are not emulated CPU cycles or sub-millisecond GPU profiling.

Native timing commit `e3e8d23de5b` and the separate stall-control commit
`34b24a2fef31469e96fa55882c19527bb42cc171` are pushed to the fork. The final
separate candidate is `build/candidates/34b24a2fef3/vunit.exe`, SHA256
`2ebe8aeb7f1b7a67edd56b7feaa59c29ce60ada3f833d5916fd51db4c57abcea`.
The156-patch export reconstructs tree `1e1c6ef674dbf8b764d32e29697bf655a25d898b`.

## The fault test now checks that its stimulus happened

`--gl-stall FRAME:MILLISECONDS` supports Exotica with an explicit candidate,
live GL and physical force zero. Stalls must lie before the final frame and
last1..5000 milliseconds. The emulator acknowledges the requested controls and
reports the actual application once at the requested frame. The harness rejects
missing, duplicate or conflicting receipts. Old recordings with no stall
controls retain their prior behavior. Exotica previously rejected this option
as V-Unit-only; it did not silently ignore it.

Two6000-frame Hong Kong trials exercise recovery and failure:

| Requested stall at5400 | Result |
|---|---|
|100ms|Replay passes; original4191camera/12573ADC samples and all21 completed4K images remain exact. The coarse clock reports94ms.|
|5000ms|Gameplay replay correctly fails with a consumer timeout. The separate fault test passes because the failure is explicitly expected and measured. Original motion remains exact.|

The long case reports67,108,800 bytes queued in the67,108,864-byte ring, no
consumer progress during its797ms wait, and phase `stall` aged2688ms. The stall
completion reports5000ms. The emulator restores its native renderer and exits
normally at the end of the drive; this is not a game crash or a passing visual
replay. Both failed replay evidence and the distinct expected-fault verdict
are retained.

An actual300-frame run with the older6864 candidate, which lacks stall support,
is rejected for its missing acknowledgment. It cannot be reported as a
successful recovery test merely because the game launched and exited.

## A measured capture bottleneck

The short-stall run also records a594ms file-writing operation at frame5417.
Its21 readbacks total140ms with a16ms maximum; file operations total953ms with
that594ms maximum. The requested stall is measured separately. This establishes
a real synchronous capture I/O delay. It does not prove that the earlier
unmeasured Amazon8460 timeout had exactly the same cause.

The next isolated change should encode and write each BMP in one block, using
a shared helper for Zeus and V-Unit, then compare complete file bytes and native
pixels. Preserve the wait threshold while evaluating that change. If slow I/O
still blocks presentation, evaluate a bounded writer queue with explicit failure
and drain semantics; never silently discard requested captures.

All local checks pass286 Python tests without skips,32 native helpers, the GPU
fixtures and92 commands at431-file identity
`9c7fe842d424d46b95c1cbd749bc37758e7869fe1205eaf7970d83693ff485b5`.
Seven-default acceptance remains with2b55 and will be renewed on the final
I/O candidate. No release or deployment occurred; Stream Deck remains87d04de4.
Raw test evidence is local in `results/diagnostics/exotica-amazon-20260909/stream-*`.
