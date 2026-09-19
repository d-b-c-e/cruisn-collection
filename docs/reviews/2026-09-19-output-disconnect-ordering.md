# Output-device loss and cancellation ordering

The isolated native successor `707fd6a8f0a83379e6c96b5b87ee1e24b305bb44`
built successfully and is frozen at `build/candidates/ux-707fd6a8f0a/vunit.exe`.
SHA256: `f1f908e66784b657d892e651850693c99e606ffcf093397f9a994975f1c51c01`.
The complete 142-patch export reconstructs tree
`ad238a7f6bf08cdc6213dcba6ced5d4b49286764` exactly. Export already ran.
The personal native87d and separate rendering-parity series remain unchanged.

## Device loss

The force-output owner refreshes SDL joystick state and checks its selected
attachment, session instance and HID path. Checks are spaced by at least50ms;
this is a polling policy, not a bound on driver or scheduler latency. Startup,
ordinary worker ticks and the existing diagnostic sign-test loop all use it.
No physical sign test was run. The device-free observer returns before SDL.

Loss or identity change latches Off and cancels game requests. Reattachment
does not enumerate, reopen, choose a replacement or resume force. Recovery
requires the existing explicit saved On followed by a new game launch. Force
math, gains, tunes and World's menu behavior are unchanged.

## Review found and corrected a stop-order defect

The first implementation, `e5e7777be4f`, built and was exported as141patches.
Independent source review found that the sole owner called the general stop
function, which could block writing/flushing the durable marker before calling
SDL cancellation. That candidate is retained with a rejection sidecar and is
not eligible for Controls capability activation or package staging. Its export
and prior test reports have not been rewritten as successful acceptance.

The successor separates latch from persistence. The output owner attempts
constant-force zero, StopAll and rumble stop **before** any potentially blocking
file write. Only successful StopAll/rumble calls acknowledge cancellation.
Failed API stops remain retryable on subsequent ticks after persistence returns;
failed persistence remains visibly unsaved. Startup/sign-test, steady-state and
shutdown use the same service function. UI-originated stops wake the separate
owner before independently persisting. An atomic pending flag prevents duplicate
file writes. This narrow source-order finding was independently reviewed closed
on exact source SHA256
`24ab8649adf7f28a8a360b2cf938ec14f7caad37cf647d56c6fef347a015de84`.

## Focused evidence

`tests/native/check_ffb_disconnect.py` compiles the actual native device/latch/
persistence/output/service functions against fake SDL and filesystem APIs.
It checks detached/changed/invalid identity, cadence, no reconnect resumption,
suppression across force families, failed API retry and failed persistence.
A separate fake owner thread deliberately blocks FlushFileBuffers; all three
stop calls must already have occurred before that block is reached. There are
no device opens, actual actuator calls or filesystem calls in the fake sink.

Local evidence is under `results/diagnostics/ux-20260919/native-build/`:

- `disconnect-ordering/qualified.json`: actual integration PASS.
- `selector-dispatch-v5/qualified.json`: startup identity rejection still PASS.
- `build-4.log`, `build-4.status.json`, `707fd6a8f0a-export.json`: successful
  reviewed successor build and exact reconstruction.
- Earlier `disconnect-dispatch` failed to link because SDL renamed the test
  entry point; `selector-dispatch-v3` extracted too much source after the new
  function was inserted. Corrected harness receipts are separate. They did
  not require any game rerun.

No additional full drive, physical unplug/torque trial or timing claim is made.
The previous bounded3300-input observer replay remains evidence for its recorded
source only. Live keyboard/menu routing and physical wheel acceptance are still
separate gates. This successor is not deployed or publicly released yet.
