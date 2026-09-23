# World 2.5 Hawaii: authored edge extension trial

The detached lower edge at saved scene 5900 is **not** a 3× draw-distance
cutoff. The original terrain mesh is already inside the extended far plane;
its authored lower silhouette ends above the water. The earlier descriptor
and edge search did not find an adjacent ordinary mesh that closes it.

I tested a screen-space skirt against the saved indexed scene and actual
textures, using `results/diagnostics/world25-roads-20260914/prototype-terrain-skirt.py`.
The original scene reconstruction passed unchanged. A quad from the known
edge (vertices 32–33 of object 2147484204) to native y=230 changed 1,965
completed quality pixels and introduced 98 near-black pixels. Its image is a
narrow hanging strip. A broader seven-edge continuation to y=233 changed
7,994 pixels, introduced 1,092 near-black pixels and produced a conspicuous
rectangular wall. Lower extensions did not repair the texture or shape.

These are **rejected visual experiments**, not a renderer fix. The trial is
one saved view and does not prove how the authored edge behaves during motion.
The local `terrain-skirt-trial/report.json`, `candidate-230.png`, and
`chain-233.png` preserve the measurements and images. No native source,
installed binary, settings or release was changed. A credible fix needs a
course-aware continuation or background relationship that preserves the
terrain silhouette and texture; a generic skirt would make this scene worse.

See [terrain boundary](2026-09-14-world-terrain-boundary.md) and
[neighbor search](2026-09-15-world-terrain-neighbors.md) for the underlying
source and rejection evidence.
