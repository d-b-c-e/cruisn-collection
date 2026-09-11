# Native Exotica lifetime observation

Read-only native pool/source/first-submission hooks are compared to the original
Lua trace, repeated, and disabled for a full-drive control. Raw event rows,
guest resources and pixels remain local. See the
[review](../../../docs/reviews/2026-09-10-exotica-native-lifetimes.md).

At this source checkpoint run
`python results/proof/2026-09-10-exotica-native-lifetimes/verify.py`.
It recomputes source/file hashes, coverage, stored hash equality and receipt
consistency. Native execution, raw event joins, actual route/pixel comparisons,
build reconstruction, local tests and defaults are receipts; it does not rerun
them. No waiting-object drawing, material lifetime, fade handover, deployment
or physical-wheel acceptance is claimed by this checkpoint.
