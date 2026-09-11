# Steering evidence for strength-50 normalization

Run `python results/proof/2026-09-11-ffb-steering/verify.py` from the repository.
This checks the relevant current source hashes and aggregate receipt consistency.
It does not rerun MAME, reconstruct private input data, exercise a physical wheel
or establish completed FFB normalization. No INP, game RAM or raw ADC is included.

The local analyzer reconstructs 32,785 recorded frame values exactly on the common
native795fc build. It also matches all 7,060 captured Exotica steering reads;
25 of these differ by one byte from the preceding frame snapshot. V-Unit actual
ADC sampling and physical rim-angle equivalence remain open. All 390 Python tests
pass with no skips; seven new tests cover input reconstruction and rejection.

The Python suite's full source identity describes the captured local working
tree, including unrelated standalone rendering drafts. This receipt validates
Python checks and the listed FFB sources; it makes no new native-build or GPU
acceptance claim. The existing force calibration and deployed build are unchanged.
