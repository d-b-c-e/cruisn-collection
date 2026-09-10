# Original-only live Zeus depth mirror — September 10, 2026

The standalone [depth diagnostics](2026-09-10-zeus-depth-domain.md) are now
connected to a separately built native candidate. The live prototype mirrors
original rendering into a private color/D32F target. It continues displaying
the original target and inserts no future scenery.

Native `25228b19d59bf434817b998134a042637b16075b` is built separately, frozen at
`build/candidates/25228b19d59/vunit.exe`, and pushed to the fork. SHA256:
`2267c6502d17e6c8efe73d7a2daecda4e752267f26bcbf25af088bb3488f321f`.
The 177-patch export reconstructs tree
`2ec2d719b45267c9fece2bfeacd1f68420cd780c`.
Personal v0.5.0 / SHA87d04de4 remains unchanged.

## First live result — retained coverage failure

The first 6,000-input Amazon trial requested frame markers 1 through5990.
Actual completed markers begin at2. The harness rejects that one-frame coverage
gap even though the native consumer completes its processing and all snapshots.
This original request remains a **FAIL**. A fresh run with the observed2..5990
interval now passes all5,989 markers, six independent color/depth pairs, original
camera/input-read timing, ten original resources and25 completed4K images.

Independent postchecks on the completed first run pass all six full private
color/depth comparisons at300,1800,3500,5072,5604 and5990. The framebuffer is
2736x4096 at internal4x. Each original depth code maps exactly into the private
depth representation, and every color byte matches. Original camera/input-read
timing and25 completed3840x2160 images also match the control. This completed
prefix evidence does not retroactively make the requested interval pass.

## Implementation and acceptance still required

`--zeus-depth-mirror observe` requires an explicit candidate, Exotica/liveGL,
physical FFB0, bounded first/last frames and no late host-margin pass. Optional
snapshot frames are bounded to16. Absent settings preserve old recordings;
`off` removes the mirror settings. Controls round-trip in recording metadata.

The mirror starts at renderer initialization, regardless of the diagnostic
logging interval. Every original batch uses the same vertex buffers, textures,
palettes, blending, depth-test/write state, scissor and order in both targets.
Startup and explicit margin-page clears also affect both targets. Only the
private shader's depth normalization changes. Attribute locations and actual
32-bit floating depth storage are checked before use.

Snapshot requests read four owned buffers through the bounded asynchronous writer.
Native comparisons are checked again independently in Python. The harness rejects
missing frame markers, missing/short raw files, color/depth differences, nonfinite
values and incomplete writer counts. Four focused configuration/completion/
corruption tests pass. No full local-suite or seven-default renewal on this
native candidate is claimed yet.

Next: finish the aligned short trial, disabled control, full Amazon/repeat and
Hong Kong; inspect raw comparisons and original resources, then run the complete
local suite and seven defaults. Only after that consider true wider original
depth and early future insertion. The compatibility sentinel policy is not a
finished extended-distance policy. No release or personal deployment.
