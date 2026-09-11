# World speed evidence for FFB normalization

Run `python results/proof/2026-09-11-ffb-world-speed/verify.py` from the repository.
It checks current source hashes, receipt hashes, reported coverage and paired
trace identities. The full Python suite receipt contains 383 passing tests with
no skips. No ROMs, game RAM, pixels or raw input/motor traces are included.

The underlying local Germany replay preserved 9,269 inputs/times and 154 native
snapshots on frozen native795fc. All 3,486 speed conversions match the independent
C31 calculation; 3,656 actual MPH HUD reads consume an observed writer. The 126
reads before the first captured writer are explicitly excluded. All 8,270 frame
memory samples match earlier independent evidence. Existing source/gate/speed/
drivetrain CSV files are unchanged.

Verified memory speed supplies 117.248 seconds of eligible World conditions.
This is source measurement, not a completed calibration: both-direction matched
turns, contact labels, output conditioning and attended wheel acceptance remain
open. Runtime telemetry and deployed force settings are unchanged.

The verifier does **not** rerun MAME, reconstruct private game data, measure
physical torque, or certify the reported raw execution from hashes alone.
Earlier proof folders bind their own historical source; changed source files do
not retroactively update those receipts.
