# Exotica force polarity correction

The user reports positive feedback: turning slightly left makes the wheel pull
farther left, likewise on the right. The preserved launch uses Wheel Invert On,
steering mirror0, shared force invert0 and effective strength64 from the saved80.
The cabinet switch reverses the game's motor signal, but the corrected steering
path was still forwarding that motor signal with the shared V-Unit polarity.

Native97600e9597e normalizes this cabinet polarity in Exotica's force output.
The active-low0x0800 DIP is read from the actual input port at each motor write,
so imported settings and live switch changes are respected. Game polarity and
the physical wheel's inversion compose independently. No ADC/input mirroring,
strength, driver gain, shifter configuration or World force behavior changes.
Raw/adapted game telemetry stays unchanged; polarity is applied to the host force
and raw impact input. Stop commands and the existing Exotica driving gate remain zero.

The canonical helper is `native/motor_signal.h`. `force-gate.csv` now records
`game_invert` and `device_invert`; the adapter logs the cabinet polarity at boot
and on changes. The normal suite checks requested levels against the adapted
source, device direction and independently recorded DIP input. This keeps a sign
regression visible even when no physical wheel is being driven.

## Verified scope

- 115 Python tests and all four CI34187080921 jobs pass at3d990a5. Native vectors
  cover all256 motor bytes with both device directions, both game polarities,
  neutral/stop values and existing gain/slew/clamp behavior. Header sync passes.
- Full Exotica replay:6000 inputs and all21 completed GL images match. All4616
  force samples agree with the recorded cabinet switch. Exactly2082 nonzero host
  requests reverse sign, with identical magnitudes. The raw/adapted motor-source
  CSV is byte-identical to the previous verified run. UDP/drivetrain and startup
  force-gate checks also pass.
- World2.5 control:6000 inputs/100 native images, UDP and independent memory pass.
  All5534 force requests retain their prior values; game polarity remains0.
- The first Exotica attempt ended cleanly after1052 frames, before its scheduled
  GL captures, and is retained as a failed/incomplete run. The cause of that early
  exit was not established. The completed rerun supplies the evidence above.

Automated physical force stayed disabled. These checks establish output signs and
unchanged game behavior; the user still needs a brief low-strength centering test.
The desired response is force toward center when turning away from it. Overall
gain, damping and cross-game strength normalization remain separate open work.

Built native SHA256:
`b5ba0021a51a1f9ec50e105dde9c8112cb3c7e4ce71009ce4294841296383ee2`.
The123-patch export is refreshed; the correction applied to its verified parent
reconstructs tree`cb82b811cd0ceec182734950f7c8ad7ef83fc667`.
[The42-file proof archive](../../results/proof/2026-09-07-exotica-force-polarity/README.md)
retains exact derived traces, reports, analyzers and the original attended force logs.
Stream Deck uses this source executable. No new package/public release was made;
the preserved rc2 ZIP predates the World rollback and this correction.
