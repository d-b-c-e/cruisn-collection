# Bind saved host preparation to completed presentation

The mirror frame number is not necessarily the preparation frame of the visible
host scene. A new harness check follows the renderer's completed auxiliary-quad
count through the ordered host journal and selects the last submitted scene for
each physical framebuffer page. This prevents using a newer camera snapshot to
explain an older displayed scene.

Four saved checks match an independent per-quad expansion of the journals:

| Capture | Mirror frame | Last page0 source | Last page1 source | Captured source matches visible page |
| --- | ---: | ---: | ---: | --- |
| Off-Road early El Paso |2520|2518|2516|No|
| Off-Road middle El Paso |3360|3358|3356|No|
| USA opacity observer |3501|3501|3499|No|
| World metadata observer |5900|5896|5898|No|

The Off-Road original DMA completion fence independently identifies the displayed
page's original group at2516..2517, consistent with the host source2516. The
recent saved billboard prototype used frame2520 operands, so its correspondence
with the older completed image cannot establish occlusion or visible benefit.

The earlier completed opacity measurements remain valid for those completed
images, and the separately reconstructed source geometry remains valid for its
preparation. Their relationship was not proven by sharing a requested frame
number. In particular, the earlier statement that all52 eligible Off-Road2520
source quads failed to survive into that completed image was too strong.

## Harness change

vunit_host_completion.py selects both physical pages from the consumed prefix,
retains partial-scene status and reports prepared versus consumed counts.
require_preparation_frame rejects absent, different or partially consumed scenes.
Full original-mirror verification now includes this binding and an explicit
captured_preparation_matches_visible field when depth metadata is present.
A passing transport report still does not become a passing visual comparison.

Four focused selector tests and the ten existing original-mirror tests pass.
Saved evidence: LOCAL world25-roads-20260914/host-completion-qualified.json.
No game run, emulator change or broad suite was needed.

This is necessary alignment, not complete framebuffer reproduction: subsequent
clears, ordinary geometry, CPU writes, materials and pixel ownership still matter.
The next small diagnostic change should separate metadata preparation capture
from mirror presentation capture, then require this match for a paired analysis.
Personal87d and publicv0.5.0 remain unchanged.
