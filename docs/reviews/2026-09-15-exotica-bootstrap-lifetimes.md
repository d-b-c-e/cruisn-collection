# Exotica lifetime tracking starts from verified guest state

The candidate now supports `--exotica-bootstrap lifetimes`. It begins ownership
tracking at the first proven complete guest pool rebuild instead of waiting for
the configured frame-1,799 observation window. This remains an explicit,
capture-only diagnostic mode with physical FFB disabled. Scene rendering still
starts at its configured frame; ordinary continuous exit remains separate work.

The registry starts with the rebuilt pool known free. Unobserved frees inside
that pool reject, while the existing verified external-adoption path remains.
No pending transaction, owner map or queued renderer state is cleared to force
startup. The harness resolves the effective first frame only after independently
checking the actual bootstrap proof, then folds the full lifecycle into waiting
and handover verification. Three bootstrap and nine lifetime tests pass.

One 5,300-input Amazon replay on the primary4K display passes. Startup occurs at
frame1,385 and adds457 allocations,383 releases,two global clears and two pool
rebuilds before the previous start. The later50,689 events retain their actual
game fields and times, with the expected+844 sequence and+4 epoch offsets.
Twenty releases previously marked unknown now have observed allocations.

All186 compared camera/ADC, endpoint operand, geometry, material and saved target
files are byte exact to the previous captured control. Eight ownership journal
or snapshot files carry changed IDs and are independently folded rather than
claimed byte exact. All four completed3840x2160 CRT images at5220/5224/5228/5232
are byte exact. This is startup/lifecycle compatibility, not new distance gain,
performance or all-course acceptance.

The first extra offline qualification used the wrong report key for waiting
verification and failed after the geometry comparison. Its corrected successor
passes against the saved run; no game was rerun for that checker typo.

Native `ffec5a90359`, SHA256
`eaa9ef109cca4d2bbfa24839fe3ec05af18d57ca6bc42aeb5e4c307015d11587`;
241patches reconstruct tree `e4b7e3cfb926fd4ac5d9f4e02511c0831132e9e0`.
Local evidence under `results/diagnostics/exotica-amazon-20260909`:
`bootstrap-lifetimes-4k`, `bootstrap-lifetimes-qualified-v2.json`, and
`bootstrap-lifetimes-native-export.json`. Export script already ran.

Next: activate the scene pipeline at an actual verified guest scene boundary,
then remove diagnostic end windows through explicit coordinated drain/exit
handling. Do not merely raise limits or bypass ownership guards. Personal
Stream Deck installation and publicv0.5.0 remain unchanged.
