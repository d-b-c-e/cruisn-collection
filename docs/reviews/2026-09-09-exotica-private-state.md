# Exotica private rendering state — September 9, 2026

The standalone Exotica renderer can now reconstruct CPU setup commands and
advance a private Zeus context. It does not submit extra scenery or mutate the
real device. Material requests describe required loads; they do not certify
palette colors, microcode bytes, WaveRAM residency or upload completion.

## Evidence

Independent Python and native setup implementations match **40,093** original
Hong Kong calls, **537** Amazon calls around frame 7215, and **19,445** Amazon
calls across four reported defect windows. They compare complete setup/transform
packets and all three before/after CPU caches, including all six setup branches.

The private hardware-state transition also matches **278**, **170** and **164**
consecutive original model pairs respectively. Each pair starts from the preceding
captured device context, advances its model-local writes, and applies independently
reconstructed next-object commands. All 128 device registers, 80 render registers,
16 transform/light floats and six scalar fields match. Nonordinary or unmatched
intervening calls are excluded explicitly. This is bounded pair coverage, not a
claim that an entire future scene can already be rendered in isolation.

Hong Kong's 6,000-input state replay preserves 4,191 camera samples, 12,573 actual
ADC reads/times and all 21 original completed 3840x2160 images. Amazon's 8,860-input
probe drives preserve 7,051 camera samples and 21,153 ADC reads/times. The dense
Amazon run completes 61 images across frames 7110..7290, every three frames.
Those newly sampled images require visual analysis; completing them is not a pass
on the reported artifact.

Amazon's two original-binary controls repeat 58 of 59 4K images. **Frame 3600
fails**, with different sky/material colors despite identical driving motion.
Keep that pair and investigate it separately from added drawing distance. The
recording reaches the finish, so no new recording is requested for now.

## Failures that improved the implementation

- The first full setup oracle failed on a reused state key with flag `0x800`.
  Three delayed-branch instructions still invalidate cache `FF4` on that path.
  Both implementations now preserve that behavior, with a regression test.
- The initial hardware-state comparison omitted the FIFO register's last model
  word. The private transition now reproduces that register and both counters.
- Amazon exposed a raw address register with high bits set. The C32 has 32-bit
  registers and a **24-bit program bus**. The probe now checks the bus width,
  masks reads exactly as the CPU does, retains raw pointers in evidence, and
  reports alias reads. It still rejects unmapped effective addresses; no broader
  memory access or silent call skipping was added. The formerly failing three
  frames now match actual model emissions and private state.
- A local Lua composition attempt contained literal newline escapes and failed
  to load. It is retained as a diagnostic failure, not called a game crash.

The light branch inherits depth register `0x15`. Its former description as a bias
reflects our current legacy renderer, not an established hardware fact. The
[fresh upstream review](2026-09-09-zeus-upstream.md) identifies an open PR that
instead interprets it as a floor. Packet reconstruction and pixel interpretation
are separate checks.

## Checks and scope

All **269 Python tests without skips**, **28 native test programs**, 10,081 C31
and 137 yaw vectors, and **32 GPU checks** pass across 78 local commands.
The 404-file source identity is
`6c59e8c9e91a979571d2b00f4c98ce190d0b39e17aad65bc48e2b65bd03852f2`.
[Public proof](../../results/proof/2026-09-09-exotica-private-state/README.md)
recomputes five input/motion traces, selected Hong Kong 4K pairs and the retained
Amazon visual failure. Full command/state/resources and native/GPU executions
remain hash-bound receipts; raw game operands stay local.

Reusable code: `exotica_state` reconstructs CPU setup, `zeus_state` advances
private device context, their two verifiers compare original captures, and the
bounded Lua model probe optionally captures setup state. Unsupported material
writes/programs fail explicitly. Native output can safely reuse its previous
private context, including when the input aliases the result object.

Native MAME remains eb17cf2/SHAee2bd4d0. The seven-default gate belongs to its
earlier model-codec milestone, not this standalone work. Stream Deck remains
v0.5.0/SHA87d04de4. No deployment, release, hosted workflow, physical FFB,
World force tuning or experiment-menu removal occurred.

Next: isolate upstream depth/blend semantics on Amazon/Hong Kong, diagnose the
repeatability failure, then bind private materials and integrate future scenery.
Continue directly; the one-minute heartbeat is recovery only.
