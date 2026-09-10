# Exotica private scene assembler receipts

Run `python results/proof/2026-09-10-exotica-assembler/verify.py` from the repo
root. It verifies archived receipt hashes, the source-identity digest and
reported cross-checks. It does not rerun local captures or recompute raw game
geometry. No ROM/model/palette data is included.

Three captured scenes pass eight native/Python comparisons each: 1/2/3x and a
3x repeat, with original and completed fade flags. Every instance and quad is
compared, after rechecking original captured geometry and state. The source
passes 295 Python tests, 35 native test helpers and 99 local commands.

This assembler is standalone. Live material ownership, sky/foreground insertion,
source handover and useful visible extension remain separate requirements.
No new MAME build, deployment, release or physical FFB test is implied.
See the [review](../../../docs/reviews/2026-09-10-exotica-scene-assembler.md).
