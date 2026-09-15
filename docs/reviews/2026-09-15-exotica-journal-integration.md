# Exotica journal integration and primary 4K check

The CPU and GPU now use `DiagnosticJournal` for 20 rendering/ownership journals.
The integration selects capture mode explicitly everywhere. It changes no draw
policy, frame window, ownership limit or diagnostic budget. An enabled journal
is separate from its file handle, preparing for optional evidence output.

The helper preserves compiler printf-format checking, closes owned files on
early returns and retains write/flush/close errors. The focused C++11 test passes
with warnings treated as errors. The MAME build succeeds. Existing resource,
queue, source-lifetime, admission and endpoint checks remain in place.

One 5,300-input Amazon replay qualifies capture compatibility. Against the
retained matching capture, 203 binary/resource/target files and deterministic
journals are byte-identical. All 3,429 scene and active rows, 10,287 CPU and GPU
material rows, and future/waiting/active GPU rows match after excluding the
explicit host-duration fields. No broad default suite was repeated.

The first local comparison incorrectly required exact GPU batch counts. It is
retained as a failed report. The consumer flushes after each available ring
drain, so scheduling affects batch partitioning. Final observed batch counts
were 141,849 and 141,779. All per-frame vertex/clear counters, and the captured
original/private color and depth targets, match. The corrected comparison
records this difference explicitly; it does not declare the batch counts exact.
No game was rerun for that analyzer correction.

The primary monitor is now 3840x2160, with the second display to its left.
Four completed CRT-on images at frames 5220, 5224, 5228 and 5232 have the full
3840x2160 dimensions. They were visually inspected around the previously studied
foliage transition: the foreground car, HUD, road and foliage appear intact in
these samples. This is a focused 4K check, not final all-game release acceptance
or a claim of increased distance. `--gl-every 4` selects global frame multiples;
the local plan's initial expectation of five images was corrected to four.

Native commit `d18bf17d820` is frozen separately with SHA256
`aa1baa4a4ab5e606286e864b8dbc4107c0c2480510dd6be5d986f9897f1ef9de`.
The exported 236-patch series reconstructs tree
`2cfce89cb53c4b2f6f37b2fa023a768e40a09dff`.
The personal binary and public v0.5.0 remain unchanged.

Local evidence lives under `results/diagnostics/exotica-amazon-20260909`:
`journal-integration-native-export.json`, `journal-integration-4k`,
`journal-integration-qualified-v2.json` and `journal-integration-4k-contact.png`.
The one-time export script has already run and must not be rerun.

Next is an explicit quiet policy with honest, narrower verification: native
completion summaries plus original inputs and captured output, without claiming
an independent per-event proof from journals that were deliberately not saved.
Keep the current bounded windows until continuous lifecycle activation and
overflow-safe counters are separately implemented and qualified.
