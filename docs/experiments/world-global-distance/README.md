# Archived global World distance draft

Follow-up: an improved implementation was built and tested in native commit
`9ea71f601b3`. Read the [trial assessment](../../reviews/2026-09-06-global-distance-trial.md).
These two patch files preserve the earlier draft; do not apply them over the
current source. The known missing work below describes that archived draft.

This is an archived implementation sketch, **not an accepted patch or a product
feature**. Research into whole-section drawing and native translation superseded
its immediate integration. See the [assessment](../../reviews/2026-09-06-global-distance-and-native-port.md).

`native-draft.patch` applies to mame-src `e8b8fc3be9c`.
`collection-draft.patch` applies to collection `37f698f`.
Both were checked with `git apply --check` against those source states. They have
not themselves been compiled or exercised. Neither belongs in the exported MAME
patch series. Their active source edits were removed at the time of archiving;
the later tested implementation was integrated separately.

The sketch accepts a World 2.4 global far value and optional pending lookahead,
supplies additional reciprocals from host memory, and contains no model allowlist.
It anticipates a separate checked RAM patch for the far word and clamp instructions.

Known missing work before an experiment:

- Produce and validate the matching checked game patch; do not just set an env var.
- Wire the per-frame diagnostic tick; the draft declares it but does not call it.
- Add explicit harness arguments, settings provenance and baseline controls.
- Validate arithmetic/guard boundaries and test actual runtime projection paths.
- Review reset/save-state behavior, log errors, tap overhead and lifecycle handling.
- Run far-only, pending-only and combined controls with physical FFB off.
- Measure guest timing and player/camera state as well as additional geometry.

This does not implement future-section decoding, capacity expansion, native
geometry transformation, or separation of visual objects from simulation.
The bounded Lua pending experiment in `lua/world_pending_distance.lua` is the
executed evidence; its result does not validate this native draft.
