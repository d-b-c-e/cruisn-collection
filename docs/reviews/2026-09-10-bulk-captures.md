# Checked bulk screenshot writes

Both enhanced renderers now encode their diagnostic BMP into a reusable buffer
and issue one bulk stdio write. The helper preserves the existing bottom-up BGR
format and zero row padding. Explicit little-endian header encoding replaces
unaligned pointer stores. Invalid dimensions, input lengths and oversized images
are rejected before a file is opened. A short write or failed close is reported;
the renderer does not then publish a successful capture entry or menu completion.

This is a diagnostic capture change, not a game-rendering or distance change.
It retains the queue capacity, timeout threshold, native frame ordering and
physical-force policy. Ordinary play without screenshots does not encode files.

Native `77a33a4b1e744c07f1783cb6375b7cab12bcdcd6` was built separately and frozen as
`build/candidates/77a33a4b1e7/vunit.exe`, SHA256
`e153d0147e3989a56e7b058872fec125bf9c6f40c4e4fa7e778fbc6f871040aa`.
The157-patch export reconstructs tree `bb809e66c981411f15ab8ecfb39e4791049bc493`.
Personal Stream Deck remains the released87d04de4 binary.

## Local checks

The complete1-by-2 BMP fixture checks every byte, including header and padding.
Ten widths exercise padding, aligned bulk copying and reuse of dirty storage.
Invalid dimensions and lengths preserve the previous buffer. The first fixture
used a C++14 overload despite the local suite's C++11 target; that compile failure
is retained. The corrected test and full suite pass286 Python tests without skips,
33 native helpers and94 commands at source identity
`e2bc726b7fbf4ddc6136079bbe087a63ccea063728b6efdc905896a27c673f8d`.
The native implementation already compiled; this correction changes only its test.

## Native comparisons: repeat fails

The first6000-frame Hong Kong run preserves original camera/ADC timing and all21
completed4K screenshots. Every BMP also matches the previous writer byte for byte.
The100ms requested stall is acknowledged and measured separately.

Its file-operation maximum is156ms, versus594ms in the earlier row-writing run,
but total file time is1513ms versus953ms. This is not evidence of a general speed
improvement: the maximum improved in this sample while total cost increased.
The repeat FAILED: file writes at5408/5409/5410 lasted1031/703/797ms. The producer
timed out after797ms with phase=file aged782ms and no consumer progress, at
presented frame5409. This directly identifies synchronous file writing as a
consumer bottleneck in this run. It does not retroactively prove the cause of
the earlier uninstrumented Amazon failure.

The failure timing analyzer was invoked after observing the failure to extract
its measurements; its `expected_timeout` field is an analysis argument, not
a predeclared successful fault test. The gameplay replay remains FAILED. The
full Amazon and V-Unit tests have not run on this intermediate build. Next move
I/O to a bounded background writer with explicit queue rejection, checked file
completion and final drain, then renew complete native acceptance. Do not hide
the failure by raising the stream timeout.

Final seven-default acceptance has not yet been renewed on this candidate.
No deployment, release or physical-force testing is authorized by these checks.
Raw evidence and initial failures remain local under
`results/diagnostics/exotica-amazon-20260909/bulk-*`.
