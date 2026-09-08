# World FFB rollback and normalization backlog

The user found the new World force gate to be a regression: game menus need
feedback, even while excessive oscillation remains unresolved. The later
instruction superseded the requested10% increase. **World strength is unchanged;
no boost or reduction was applied.** The recent20% trim was Exotica-specific.

Native b9bef299f6d removes both World driving-state gate calls. World2.4 and2.5
again forward game motor commands during selection and race-end screens. Normal
pause/exit/watchdog behavior remains the prior implementation. Exotica's separate
startup gate and trim are unchanged, as are World motor adaptation, force profiles,
impact preferences, steering calibration and all telemetry producers.

Built source executable SHA256:
`093abbeb01ac779dbc81b734bea609a9a358eebc17a7cfbf2ad6002e017135af`.
The122-patch export includes the rollback; applying the rollback commit to the
previously verified native parent reconstructs tree
`5f33ebed52f7fd7a707c74aeca885989400fdfde`.
Stream Deck uses this source checkout and E:/Source/mame-src/vunit.exe.

## Verification

- 114 Python tests pass, including unchanged World strength and a regression
  that rejects accidental suppression of menu force requests.
- World2.4 Germany: all9269 inputs/154 native images match. All9269 Forza packets
  and7516 active independent memory samples agree. All8803 force writes remain
  enabled;1332 nonzero requests occur during independently sampled non-driving states.
- World2.5: all6000 inputs/100 native images match. UDP and independent memory
  checks pass. All5534 force writes remain enabled, including1059 nonzero requests
  during independently sampled non-driving states.
- Raw and adapted motor-source CSV hashes are identical to the prior verified
  runs in both cases. This restores forwarding without changing the game motor values.

All four CI34186139718 jobs pass at353afac. The
[33-file proof archive](../../results/proof/2026-09-07-world-ffb-rollback/README.md)
retains derived traces, analyzers, reports and exact hashes without game dumps.

These were headless replay checks with physical force disabled, not new wheel-feel
acceptance or a complete renewed release gate. The normal regression suite now
requires `force_gate_policy: passthrough` for World; Exotica retains `driving`.
The preserved rc2 ZIP still contains the rejected World gate and is superseded
by source. It needs a replacement package and renewed release evidence before publication.

## Known issue: cross-game force normalization

Defer further World tuning for now. World menu/race-end oscillation and inconsistent
strength between games remain known issues. The desired contract is that an80%
setting produces roughly comparable output strength across games on the same
wheel and base settings. A shared slider alone does not establish this: game motor
ranges, driver gains and force distributions differ.

Future work should establish a common output scale, then compare recorded steering,
car-contact and wall-impact events using the same wheel/profile/settings. Separate
game signal calibration from the user's master strength and wheel-base calibration.
Use measured requested levels and attended feel checks together; do not chase parity
with another arbitrary percentage adjustment or mute menu feedback to hide oscillation.
