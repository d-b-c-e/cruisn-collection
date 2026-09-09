# Launch regression evidence

Code commit `41a8ba9`. `before-fix.log` reproduces the user's unbound `env` error
in ten normal-launch cases (five ROM revisions, cheats on/off). The corrected
process-boundary tests cover thirty paths including recordings and explicit trials.
Popen is replaced, so no emulator or haptic device was started by these tests.

The complete local runner passes 187 Python tests/no skips, all native helpers,
10,081 C31 vectors and 24 GPU quality fixtures. Its original report, source
identity, commands and evidence files are retained in the ZIP. The manifest
binds every archived file. These are execution receipts, not full gameplay or
rank-cheat semantic acceptance. No new emulator build or release was created.

Run `python results/proof/2026-09-08-launch-environment/verify_archive.py` to verify
the bytes and recorded results without ROMs or compiler/GPU access.
