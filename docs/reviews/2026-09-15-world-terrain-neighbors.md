# World Hawaii: adjacent mesh search

The saved exposed terrain edge still has no matching continuation in the ordinary
scene data examined here. This strengthens the authored-coverage diagnosis; it
does not establish that every World gap has the same cause.

The search starts with the5,057 previously qualified future descriptors, including
1,108 road descriptors, then reads five guarded allocated lists from the same
frame5900 RAM. Those lists contain354 active and43 pending objects. Linked-list
addresses, cycles and counts are bounded; no guest state is changed.

After explicitly excluding billboard transforms and alternate codecs, the spatial
screen covers4,712 descriptors,965 original models,76,588 vertices and117,006
unique-per-model index edges. Full original road models are included. All selected
meshes decode without errors. Double-precision world coordinates are derived from
the captured transforms; this is spatial analysis, not a new guest-exact transform
claim. Earlier exploratory variants included billboard objects with their ordinary
matrix and are superseded by the explicitly scoped `v3` result.

The previously proven target edge32/33 is about3,960 world units long. No other
edge overlaps more than1% of its length while keeping both endpoints within8 units
of its line. This also checks partial collinear edges rather than requiring two
identical vertex indices. The closest endpoint-pair match from another model is
about8,742 units away; the nearest other model edge to its midpoint is about7,461
units away. That other model is already emitted by the host renderer.

Custom initializer classes and unsupported codecs remain outside this screen.
The result does not rule out a different backdrop, additional generated geometry
or intentional overlap rather than a shared mesh edge. It does rule out a simple
matching seam among these captured ordinary road/scenery meshes. No skirt,
texture stretch, culling bypass or additional far-distance patch is promoted.

Local evidence: `results/diagnostics/world25-roads-20260914/terrain-neighbors-v3/`
and its script. One saved RAM/ROM scene; no new game or native build.
