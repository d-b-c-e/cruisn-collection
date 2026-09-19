# Physical identity and calibration launch transport

The isolated UX native successor `33d44e2c85c4ea5928fb643c51c4aec9ae2d6286`
built successfully. Its frozen executable SHA256 is
`33670eed264ddb3c4ac6266b8aa9f8eab9836cbf6031e25dc647efff5e283729`.
The 140-message complete export `patch/ux/33d44e2c85c.patch` reconstructs source
tree `8ba140ba8e43f951ef50023b5a6c764d8594dd98`. Export has already run;
never overwrite its candidate, series or receipt. Personal native87d and the
separate renderer parity series are unchanged.

Local evidence: `results/diagnostics/ux-20260919/native-build/build-2.log`, its
successful completion status, and `33d44e2c85c-export.json`. The candidate is
`build/candidates/ux-33d44e2c85c/vunit.exe`. A separate SHA-bound capabilities
receipt enables the opt-in controls UI. It states software capability, not
physical acceptance. The attestation helper accepts only this reviewed source
and verifies the frozen binary and patch hashes.

## Behavior

`control_launch.py` provides atomic explicit FFB selection (Follow Steering or
one current identity), clear, and legacy wizard replacement. It preserves saved
Off, strength, tunes and unrelated settings. Missing, ambiguous, unsupported or
unverified output paths do not select an arbitrary device. Current inventory
metadata supplies the DirectInput-to-SDL HID path; a saved stale path does not.

Clear removes both saved representations and writes an unbound tombstone so
an inherited controller file cannot restore the old axis. A new calibrated bind
or deliberate legacy wizard bind supersedes that tombstone. Launch writes
`NONE` for cleared role ports. Whole-result calibration conflicts are rejected
before saving, including a second role attempting different endpoints for the
same physical axis.

The common launch path overlays strict product/instance GUID mappings on the
private controller XML. It reuses a unique legacy logical slot to preserve its
button bindings and otherwise allocates a distinct slot. Saved device/axis
resolution must succeed before launch. Calibrated ports do not receive the old
pedal half-axis modifier; uncalibrated legacy half-axis intent is retained.
No per-game force normalization or World's menu behavior is changed.

The profile resides in the private controller directory. Recording freezes it
with the controller XML and hashes, then uses a run-local path. Playback and
synthetic INP continuations consume effective recorded ports, so they strip
strict physical mappings and omit calibration from only their disposable run
copy. `input-playback-policy.json` records that distinction. The immutable case
retains exact original settings; modified calibration fails its hash check.

## Focused validation

- Six control-launch tests: failed/stale atomic edits, exact backups and saved
  Off/tunes, explicit clear/rebind, slot/button retention, per-axis conflicts,
  missing/duplicate devices, and executable capability hash mismatch.
- All 24 model contracts still pass after whole-result conflict preflight.
- Twelve session tests pass, including a new freeze/rebind/playback/tamper test.
- Six launcher boundary tests pass. The new case exercises all four game
  families through mocked process creation with strict selectors and profiles;
  stale inherited selector/profile paths cannot win. These are device-free
  tests, not new gameplay runs.

The prior one-time 3,300-input all-family force-stop replay remains the bounded
native stop evidence; it was not repeated for this Python transport work.

## Remaining acceptance

Controls UI integration is being completed in a separate scoped worktree.
Live endpoint calibration, device reconnection, F8/menu interaction and physical
wheel feel have not been accepted. The new native has not been deployed. A
legacy-only installation needs an explicit identity selection before Follow
Steering enables output on this native; there is no silent migration from a
friendly name. Existing personal preferences are retained. A hash-qualified
package/deployment must include the capability receipt with the exact executable.

Follow-up: fresh-install and legacy-only clear/rebind fixtures found absent INI
section handling that the original six tests did not cover. `04d6782` fixes those
guards; seven control-launch tests now pass. Package staging now copies native
build/capability receipts and selects the exact exported source series by its
attested hash. Focused staging and ZIP-content tests reject a missing/mismatched
capability, wrong patch lineage, and leaked calibration/Off-marker state. No
full package was built for this transport-only change.
