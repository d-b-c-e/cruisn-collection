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

## Qualified static-light completion

Native `16e68b9362dbd531a2a5530ae7ffe3fee8306067` accepts only the known
`0x29b` → `0x22b` marked lighting completion, after checking the original setup
branch, selected program and unchanged 12-word layout. Geometry, material binding
and depth-test checks remain in force. The current renderer does not execute
these programs; their relevant interpretation is the packed layout, with no
Exotica z offset. This is not a general microcode equivalence claim.

The separate executable SHA-256 is
`027c6f4bf4d0ef9d1c4a1109ffaf1316fab6f9d047463379ca126e8ad2cdf984`.
The 208-patch export reconstructs tree `f97cd18b9c49f9a0e0045d732480b1c1398f5b04`.

`light-endpoint-qualified-v2` compares all original/replacement bytes for twelve
saved actual models to independent Python setup and decoding. The eleven old
accepted models remain exact. Synthetic tests reject changed layouts, unqualified
programs, palettes, textures and depth tests transactionally. The first negative
test used bit 0x100 instead of the actual depth-test bit 0x20; its failed receipt
is retained, and the test was corrected before acceptance.

`full-light-endpoint` and `full-light-endpoint-qualified` pass the full 8,860-input
drive and independent original camera/ADC/lifetime/admission joins. All 30,308
original command identities and previously accepted output counts remain exact.
The change fixes 5,176 rejections: 29,936 models prepare, 372 still reject, and
280,313 replacement quads reach the GPU. Saved original and private completed
pages 5,073/5,645 remain exact; these precede the lighting failures. Fifteen new
completed presentation frames cover 6,536–6,550. Capture pacing prevents a speed
claim. No repeated broad suite was needed.

Remaining failures: 240 plain-fade submissions and 132 lighting submissions.
The newly captured first plain failure, model 18,427 at frame 6,538, reproduces
an overly strict palette-load comparison: the current palette address matches,
but register 0x40 contains the last **program** load (`0x38550075`), not the last
palette load (`0x0084003f`). The private endpoint should preserve the already-bound
palette, validate its source identity and avoid proposing a redundant upload.
That correction and its full-drive validation are the next work item.
