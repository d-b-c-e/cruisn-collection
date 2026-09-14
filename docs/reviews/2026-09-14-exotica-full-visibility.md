# Exotica full-drive visibility coverage

The first full Amazon early-visibility replay completed with the original inputs
and native images intact. Endpoint coverage is incomplete: 5,548 marked original
draws fell back to their original appearance. A passing replay report is therefore
not release acceptance for extended drawing.

The explicitly gated `--exotica-endpoint-scope marked` tracks only marked CPU
commits while still consuming every actual device command through the ownership
queue. The default all-command scope retains its 120-frame limit. Marked scope
has bounded journals, 65,536 commits, one million GPU pairs and 200,000 sealed
active permissions. The first rejected model automatically saves its owned
operands, even outside the requested snapshot frame.

Native `0a0a04b7de4c318a2af00239c1eaa5f986671225` is separately frozen at
`build/candidates/0a0a04b7de4/vunit.exe`, SHA-256
`f8c03e665645eada7f35c8df29d3eec429560ac5685b46ecbae10fa82397bb6b`.
The 207-patch export reconstructs tree `4890246bd034c9f9cc8894a1d2ade24edf6477e6`.
The personal executable and public v0.5.0 are unchanged.

## Evidence

Local evidence is under `results/diagnostics/exotica-amazon-20260909`:

- `marked-fifo-qualified`: 45 marked commands joined to actual CPU/device
  traffic; 22,323 FIFO writes consumed, 22,369 commands, maximum three pending
  owners, none remaining. Thirteen later marked commands are explicitly outside
  that old CPU capture interval. The initial overly broad expectation is retained.
- `full-early-visibility`: all 8,860 original inputs pass, 6,953 scenes,
  109,804 sealed active permissions and 13,906 admission packets (31,184,196 bytes).
  There are 30,308 marked original commands: 24,760 prepared and 5,548 rejected;
  1,475,312 other commands remain untracked. The GPU receives 194,893 replacement
  quads. Fifty-five completed presentation frames are captured with pacing.
- The first failure is model 18,418 at frame 6,538, flags `0x04008530`.
  `endpoint-rejection-diagnosis` reproduces its exact rejection from saved owned
  operands: completion switches program `0x29b` to `0x22b`, both 12-word layouts.
  A narrowly qualified fix is being checked separately. Failures also include
  flags `0x04208530` and `0x04000130`; the first cause does not establish all causes.

Current display is 3440×1440, not the final 4K target. Paced capture is not a
performance measurement. No new broad suite or physical force-feedback test was
run for this coverage expansion. The next step is to verify the program transition
against independent decoding, build separately and renew the full drive, retaining
any remaining failure operands for diagnosis.
