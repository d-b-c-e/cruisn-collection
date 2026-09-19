# Opt-in control calibration: native integration in progress

Source native33d44e2c85c adds exact instance mappings and per-axis calibration to
the isolated UX lineage. It is committed/pushed, **unbuilt and undeployed**.
The independently frozen091 stop replay remains separate. No physical device or
game was used for these calibration tests.

The pure control-preferences model is integrated with24 passing tests. The
provider now uses its nested inventory contract: name/axes plus identity backend
`dinput`, product/instance GUIDs, and only available HID/capability metadata.
The instance-bound reader consumes that record directly. This corrects the
earlier flat `dinput8` staging shape before UI integration.

Canonical helpers `native/input_identity.h` and `control_calibration.h` sync into
the isolated native `src/lib/util` through `sync_native.py --ux --mame ...`.
The existing parity helper list remains untouched. Strict input mapdevice IDs
are `strict-dinput:<product-guid>:<instance-guid>`. They apply after legacy
mappings; missing/ambiguous/invalid identities fail startup rather than leave an
unrelated device in the old JOYCODE slot. Friendly renaming/reordering does not
change identity. These are opt-in mappings, not a rewrite of legacy bindings.

`MIDV_INPUT_PROFILE` names a bounded `cruisn-calibration-v1` snapshot. Each row
contains product GUID, instance GUID, fixed axis, kind, three endpoint fields,
inversion and deadzone. Duplicates and invalid ranges/schema fail. The new backend
normalizes raw DirectInput values once using the saved model; only matching
calibrated axes bypass MAME's additional deadzone/half-axis conversion. Legacy
axes retain their old path. Failure/reset releases buttons/POVs and sets exact
neutral effective values for all calibrated roles on the same device, including
inverted pedals. Native startup rejects a calibrated device axis with no range.

The compiled math matches all57 independent samples in10 shared golden cases.
`check_control_pipeline.py` compiles the actual DirectInput reset/poll and actual
MAME absolute-read methods with fake providers. It checks one calibration pass,
no second deadzone/half-axis, uncalibrated legacy behavior, invalid neutral, and
disconnect release of steering/pedals/high buttons on one shared device. Local
`control-pipeline-v2/qualified.json` supersedes the earlier core-only stage:
normalization moved to the backend so disconnect can produce exact neutral,
without reconstructing a rounded inverse raw sample. Prior evidence is retained.

Remaining work: launcher snapshot/XML transport, supported-binary feature check,
record/replay isolation, the Simple device/calibration workflow, full native
compilation and bounded runtime/interaction checks. Passing pure/native fixture
tests does not yet mean calibration reaches an actual game or wheel.
