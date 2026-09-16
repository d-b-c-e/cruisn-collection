# Off-Road static billboard sources and first draw command

The static billboard decoder and first-polygon emitter now match397 actual
original observations in both Python and compiled C++. This closes the source
and command-format gap for the two qualified classes. It does not enable earlier
billboards in the emulator or establish their visible benefit.

## Original behavior and qualification

The source decoder accepts only classes0x804 and0x800804. The latter queries the
indexed current damage bit used by the original9C8C hook. A clear bit leaves
the descriptor unchanged; a set bit can change flags, orientation and callbacks,
so damaged objects remain unsupported. Dynamic, custom and alternate-binding
classes are not relabeled as ordinary scenery.

All397 static observations join uniquely by their section/ordinal tags to ROM
definitions, with all relevant render fields equal to the captured objects.
Their original bindings are supplied explicitly. Another108 dynamic observations
are excluded. Each emitted16-word polygon command matches exactly one original
DMA command at the recorded native frame, in strictly increasing DMA order.
The first billboard polygon bypasses ordinary backface rejection at1F94;
applying the ordinary polygon helper would therefore be incorrect.

Four focused Python tests and two native executables pass for the combined
billboard helpers. The independent compiled source and quad analyzers also match
all397 actual records. No broad suite or new MAME build was needed. Evidence:
LOCAL results/diagnostics/world25-roads-20260914/
offroad-billboard-source-qualified.json and qualify-offroad-billboard-source.py.
The source/DMA capture and resource capture are separate motion-equivalent
recordings; their original image/motion equivalence is qualified separately.

## Saved-scene screen and remaining work

A local frame2520 prototype reconstructs205 future billboards from592 eligible
static definitions;387 lie beyond the existing3x sphere boundary. It retains the
prior ordered host-object subset and uses the current billboard basis, which the
original prepares before the host insertion point. There are no pending
billboards in this particular scene.

The isolated GPU merge changes811 RGB pixels. None coincide with pixels whose
current completed host-owned index matches the old isolated host result.
That correspondence test is not a replay of subsequent original rendering.
New billboards could replace sky or other non-host background, so this is neither
completed visibility acceptance nor proof of zero benefit.

Next inspect the changed areas and other already-saved views, then prove source
ownership, pending handover, current material residency and completed ordering
before a live candidate. No frame or model allowlist is proposed. Native083,
personal87d and publicv0.5.0 remain unchanged.
