# Off-Road: preserve verified camera depth for appearance policies

Off-Road's host renderer now has an optional path that retains each projected
vertex's actual camera depth and maps it to the emitted polygons after back-face
culling. It does not change admission, geometry, materials, draw order or any
guest state. Existing calls retain the default behavior. No MAME build or live
fade is enabled by this standalone change.

The projection already calculates Z for the reciprocal lookup, but previously
discarded it. The guest projected buffer has a three-word stride; its third word
is stale data, not current Z. The new side stream retains the actual C31 transform
result before reciprocal-index clamping. Optional outputs fail atomically and
reject mismatched or unpaired depth vectors.

Three saved original model windows qualify1,399 captured records,15,094 vertices
and9,602 ordered polygons against independent Python C31 arithmetic. All original
XY and DMA bytes remain exact. Those captures have no clamped vertices; a native
synthetic test separately confirms that a clamped reciprocal lookup still retains
the unclamped camera depth. It also checks back-face ownership, malformed later
polygons, mismatched streams and host projection bounds.

Three complete saved El Paso3× host scenes at3360/6240/8760 qualify2,819 polygons
with exact ordered source/model/LOD/material/geometry fields and independently
equal depth words. Both uncached and cached passes match. Earlier canonical
outputs remain byte-exact when depth capture is disabled. The observed depth
ranges are41,741..167,308;30,456..145,737;45,236..107,893 respectively.

This also makes an important adapter difference explicit: Off-Road's3× sphere
admission is141,888 units, while projection permits vertices below191,040.
Geometry belonging to an admitted sphere can extend beyond the admission plane.
World's240,000-unit plane and road classification cannot simply be copied.
The remaining policy must cover that distinction and preserve road/foreground
ownership before a live fade can be judged useful.

The canonical model analyzer accepts `--depths` with optional `--prepared`.
The scene analyzer accepts `--depths` with its existing scene/admission options.
`harness/verify_offroad_depths.py` reuses saved capture validation and reports
independent depth equality. Three native tests and eight focused Python tests
pass; no full-game run was needed.

Local evidence: `results/diagnostics/offroad-model-20260909/depth-qualified/`
contains `early.json`, `middle.json`, `late.json`, `scenes.json`, standalone
executables and complete scene outputs. These are source-only helpers, not a new
frozen emulator. Native e534, personal87d and publicv0.5.0 remain unchanged.
Next assess the far envelope against actual visible surfaces, then connect a
game-qualified transport/profile rather than relax existing material guards.

The subsequent isolated depth-envelope screen uses a 141,888-unit plane and
11,824-unit transition width, treating every host surface as eligible only to
measure an upper bound. At3360 it finds821 partial-opacity pixels and9,976 zero
pixels;6240 and8760 have none. Indexed colors and masks remain exact. This is
not a road policy or a completed-image benefit. The later
[partial-frontier study](2026-09-15-offroad-partial-frontier.md) links the optional
depth helpers into its native candidate with live depth retention disabled.
