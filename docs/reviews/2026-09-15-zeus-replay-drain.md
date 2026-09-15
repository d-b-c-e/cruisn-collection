# Drain queued Zeus observations after the final screenshot

A5300-input Amazon check captured every requested4K image through5270 but failed
with `material queue did not drain every scene`. The renderer had received10233
of10287 queued material packets. Its capture-only drain target was5270, although
host scenery continued through5288 and private depth observation through5290.
The emulator exited normally; this was incomplete diagnostic consumption, not
a game crash or a missing screenshot.

The replay harness now requests completion through the last completed Zeus frame
before the input stop. This applies to explicit captures and to private depth
observation without screenshots. V-Unit keeps its existing capture-bound drain.
The native bounded drain already exists and still requires physical FFB disabled;
no new guest frame, renderer algorithm or native build is introduced. Older
binaries may ignore the request, so receipt checks remain mandatory.

Eleven focused GL tests pass, including the early-last-screenshot case, a depth
run without captures, unchanged V-Unit behavior and invalid completion bounds.
The corrected current-candidate run completes5300 inputs, drains through5299,
receives all10287 material packets, completes depth observation and writes all55
requested3840×2160 CRT images. No timing improvement is claimed: capture pacing
intentionally waits for disk storage.

The initial `combined-temporal4k-original` canonical failure remains unchanged.
Its already completed images and saved buffers may be qualified separately
against the successful `combined-temporal4k-drained-extended` run; this does not
turn the truncated GPU tail into a pass. Both live runs use frozen native
`c7e3e6b456f`. Personal87d and publicv0.5.0 remain unchanged.
