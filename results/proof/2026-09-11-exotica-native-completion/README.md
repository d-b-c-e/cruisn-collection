# Native waiting-cohort completion receipts

Run `python results/proof/2026-09-11-exotica-native-completion/verify.py` to verify
the committed code against the recorded full-check source identities and the
aggregate build/replay/repeat/disabled receipts. The export contains 187 patches
for nativebc384. The observer records every cohort at proposal and reconciles it
against actual CPU-end/device-ready lifecycle watermarks; it does not draw extra
waiting geometry.

The verification command does **not** rebuild MAME, execute ROMs, replay private
recordings, read raw lifetime/cohort/geometry files or perform GPU comparisons.
Those actions were performed locally; these files retain their checksums and
reported outcomes. Binary/source reconstruction is also an execution receipt.
The disabled control preserves the original drive with no waiting/completion
artifacts. Full/repeat preserve 21 sampled 4K/CRT images of the original target.

Raw game data stays under LOCAL
`results/diagnostics/exotica-amazon-20260909/waiting-completion-*`. The local
`waiting-completion-trial.py` and `check-waiting-completion.py` preserve the exact
commands and comparisons. The canonical replay CLI exposes explicit
`--exotica-host-handover off|observe` with parent waiting/fence/lifetime gates and
physical force disabled. A private recording and the frozen executable are
required for another actual run.

See [the review](../../../docs/reviews/2026-09-11-exotica-native-completion.md)
for scope, counts and the remaining private drawing/material/fade work. No
deployed feature, new visible waiting draw, performance or physical FFB acceptance
is claimed by this checkpoint.
