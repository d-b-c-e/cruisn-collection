# Exotica impact detection: source threshold is unreachable on Amazon

The optional **steering-axis Impact Cues** path cannot recognize an event from
the current Amazon recording with its shared detector settings. All 7,476 raw
motor writes stay between -60 and +62. After the actual signed-motor mapping,
the largest detector input is **0.49205**, below its **0.8 arrival threshold**.
Changing the strength slider cannot fix this: detection occurs before strength.

This is a concrete issue for the four-game normalization candidate. It does not
mean Exotica has no force feedback, that its legacy rumble path is necessarily
inactive, or that every track has the same raw range. It applies to the optional
enhanced path and this complete source stream. Polarity changes the sign, not
the magnitude or this bound.

## Strong constant force, absent enhanced impacts

Exotica's constant-force adapter applies a large gain before its byte clamp. The
enhanced detector uses the separate raw signal so that clamping does not erase
an impact. That raw channel is still normalized with the same 126-byte reference
as the V-Unit games. Here it never reaches the shared arrival requirement.

The enhanced mixer reserves 25% of the constant-force budget for an impact
envelope. With no recognized event, this run gets that lower structural-force
ceiling but no steering-axis burst. At nominal50, Exotica's explicit 0.8 trim gives
effective40, and the idealized enhanced algorithm peaks at0.30. These are requested
software values, not measured rim torque.

## Four-game evidence and regression checks

The analyzer now reports the largest detector input across **every source write**
and separately across its idealized 4 ms ticks, arrival reachability, and the
number of sampled ticks reaching arrival. This distinguishes an unreachable
threshold from a brief peak missed by fixed-rate sampling. Reaching arrival alone
does not establish a rise, a collision or physical delivery.

| Source recording on native795fc | Raw range excluding stop | Enhanced source peak | Arrival reachable? | Idealized enhanced waveform events |
|---|---:|---:|---|---:|
| USA | -110..126 | 1.00000 | Yes | 4 |
| World Germany | -126..126 | 1.00000 | Yes | 29 |
| Off Road El Paso | -124..124 | 0.98413 | Yes | 45 |
| Exotica Amazon | -60..62 | 0.49205 | **No** | 0 |

These counts include unreviewed boot/menu/driving intervals and are waveform
candidates, not collision counts. Do not fit gains or a collision threshold to
this table. The source bound is stronger than the idealized event count: if every
possible held input remains below arrival, worker timing or a gate that only
inserts zero cannot make this source reach arrival.

All eight new/previous analyzer comparisons preserve complete stage CSVs and
every pre-existing metric across four games, in legacy and enhanced modes at
nominal50. The added metrics are observation only. Thirty-five new compiled cases
cover five strengths, low raw/high adapted signals, both sides of arrival,
reserved neutral, peaks between ticks and a high plateau with no rise. The six
existing adapter/alias cases also pass. No production force logic or game binary
was changed or deployed.

## Next calibration work

Calibrate detector source units separately from constant-force gain and user
strength. Retain raw detail before clamping, and require labeled car/wall contacts
plus clean turns before choosing arrival/rise settings. Do not divide by the
observed maximum just to make events appear: ordinary full-lock steering can also
generate large motor commands. Actual device-free worker capture and matched
windows remain the next near-term steps.

LOCAL evidence is under `results/diagnostics/exotica-amazon-20260909/` in
`ffb-exotica-impact-reachability` and `ffb-impact-reachability-comparison`.
[Public receipts](../../results/proof/2026-09-11-ffb-impact-reachability/README.md)
check code/hash and aggregate consistency; raw algorithm execution and physical
force acceptance remain separate.
