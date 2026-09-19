# Control preferences and calibration contract — 2026-09-19

Implemented as a pure module for the owner to wire into Cruis'n's frontend and
native input adapter. This is **not** a claim that either runtime integration is
complete. Only the four assigned new files changed. No UI/native source, World
force tune/gate, game, device or build was touched.

Source base: `codex/ux-simple-advanced` at
`a14d50d28228318c558b874f4f2868c6c9f921bf`.
Worktree: `E:/Source/cruisn-collection-control-preferences-20260919`.
Branch: `codex/ux-control-preferences-20260919`.

The 2026-09-19 identity audit remains the rationale. Shared guidance is UX-04,
UX-05 and UX-01-S, observed at toolkit commit
`6f9c662e330af1ab790ca291a799265e0a50ef8a`. Device selection must use saved exact
identity; unknown/missing/ambiguous selection is inactive. Calibration stays in
Simple, with a proposal, readable normalized preview, Save calibration and
Cancel. This module supplies the contract and persistence, not the renderer.

## Public API

All imports are Python standard library only. Importing the module performs no
I/O, device enumeration or process/window creation.

| Entry point | Result / ownership |
|---|---|
| `canonical_identity(mapping)` | Validated detached copy of a backend-qualified DirectInput identity |
| `resolve_device(identity, inventory)` | `{status, device}`; resolved only for exactly one product+instance match; otherwise missing/ambiguous/invalid with device=None |
| `output_path(resolution)` | Current matched inventory HID path, or None if missing/unresolved/known non-FFB; never a name/VID:PID fallback |
| `propose_legacy_identity(name, inventory)` | Whole-name case-insensitive unique match yields status=proposal and identity; never auto-resolves or writes |
| `validate_calibration(mapping_or_none)` | Validated clone; None explicitly means no calibration/passthrough |
| `normalize(raw, calibration=None)` | Steering[-1,1], pedal[0,1], or unchanged raw for None; finite raw[-1,1] required |
| `make_proposal(action, identity, axis, calibration=None, legacy_binding=None)` | Detached unsaved `{action,record}`; optional legacy_binding changes only that action when explicitly committed |
| `CalibrationDraft(...)` | Ordered capture and unsaved review; original is immutable to callers; cancel/device loss discards draft |
| `load_records(path)` | Per-action records; old wheelmap alone returns{} without migration or writes |
| `commit_proposals(path, proposals, expected_original=bytes_or_None, inventory=rows)` | One atomic replacement for all requested action records and optional legacy bindings; returns records+backup only on success |

The arguments after `calibration` in make_proposal, and expected_original /
inventory in commit_proposals, are keyword-only. Inventory is a snapshot of
**DirectInput records**, supplied by the owner's provider; this module never
queries hardware. A malformed row invalidates resolution rather than hiding a
possible duplicate. No inventory is persisted automatically.

Inventory shape:

```python
{
    "identity": {
        "backend": "dinput",
        "product_guid": "0006346e-0000-0000-0000-504944564944",
        "instance_guid": "11111111-2222-3333-4444-555555555555",
        # Optional, populated only by the verified provider:
        "hid_path": r"\\?\HID#VID_346E&PID_0006#fixture",
        "ffb_capable": True,
    },
    "name": "Friendly wheel name",
    "axes": ["XAXIS", "YAXIS", "ZAXIS", "RXAXIS", "RYAXIS", "RZAXIS", "SLIDER1", "SLIDER2"],
}
```

GUIDs canonicalize to lowercase hyphenated, unbraced nonzero values. Matching
uses **backend+product_guid+instance_guid**, never friendly name, index, product
GUID alone or VID:PID. Reorder and friendly-name changes do not change identity.
Two rows with the same exact identity are ambiguous even if one looks better.
Unsupported backends and malformed identifiers fail closed.

Optional HID path canonicalizes to uppercase Windows device-interface spelling.
It is bridge metadata, not the input identity key. Resolution returns **current**
inventory metadata, so a stale saved path is not silently reused. No path means
no output selector. A path does not prove SDL presence, constant-force capability,
physical-device status or output readiness; the native strict selector still
validates these. `ffb_capable=False` suppresses output_path; absence of this
metadata requires native capability verification. Extra identity metadata is
preserved but does not participate in matching or grant verification.

The owner reported bundled SDL2.32.10 exports SDL_JoystickPath/PathForIndex and
its DirectInput backend obtains DIPROP_GUIDANDPATH, permitting an exact HID-path
bridge. This helper only transports that provider-supplied path; it does not
invent the association or use GLFW's product-derived GUID as an instance ID.

## Versioned saved representation

The existing `[wheelmap]` remains unchanged unless a proposal explicitly includes
legacy_binding. Existing unrelated keys/sections, explicit FFB Off, strength,
tunes, telemetry targets and unknown metadata are retained.

```ini
[control_preferences]
version = 1

[control:steer]
record = {"version":1,"identity":{"backend":"dinput","product_guid":"0006346e-0000-0000-0000-504944564944","instance_guid":"11111111-2222-3333-4444-555555555555"},"axis":"XAXIS","calibration":{"version":1,"kind":"steering","left":-0.8,"centre":0.2,"right":1.0,"invert":false,"deadzone":0.1}}
```

A control record contains version, identity, fixed DirectInput axis slot and an
explicit calibration object or JSON null. Actions are lowercase identifiers up
to32 characters. This version supplies **axis records**; keyboard/button legacy
bindings are retained, but do not gain a new button schema from this work.

Known action kinds are checked: steer requires steering calibration; gas, brake,
clutch and handbrake require pedal calibration. Other identifiers remain available
for adapter-defined axis roles; the adapter must validate their expected domain.

Calibration fields are exact for version1; unknown versions/fields, missing
schema declaration, malformed JSON or nonfinite/degenerate data cause an error
without rewriting the file. Extra INI options and record/identity metadata are
preserved. ConfigParser uses interpolation=None and preserves key spelling, so
literal percentages and unknown owner values survive. Successful writes may
normalize INI whitespace/comments/encoding; backups preserve original bytes.
Failed saves retain original bytes. DEFAULT does not supply an omitted schema
version or an omitted action record.

No legacy name is persisted as a verified identity on load. The UI may display a
unique migration proposal; only explicit Save accepts it. If two devices have the
same friendly name, keep the old record and request an explicit selection.

## Calibration math and capture stages

Raw units are finite doubles in **[-1,+1]** from the selected backend axis.
The adapter must first use the same advertised-range normalization as the input
provider. Out-of-domain raw values, booleans, strings, NaN and infinity are errors,
not successful samples. A reading outside the **captured** interval but inside
the raw domain clamps to its captured endpoint. A rejected sample must make the
caller neutralize/invalidate that input rather than continue a stale value.

Steering captures left, centre and right. Either raw orientation is valid;
centre must lie strictly between the ends. Each side spans at least0.05 raw
units. Let direction be+1 when right>centre, otherwise-1. Signed displacement
is `(raw-centre)*direction`; divide it by the corresponding left/right span,
then clamp to[-1,1]. This preserves asymmetric travel and off-centre sensors.

Pedals capture released and full with a span of at least0.05 raw units in either
orientation. Output is `clamp((raw-released)/(full-released),0,1)`. This handles
both full-range and centre-rest pedals without guessing a half-axis from sign.

Explicit inversion then negates steering or replaces pedal value by`1-value`.
Pedal inversion deliberately swaps the normalized released/full interpretation;
normal high-rest hardware is already handled by endpoint orientation and does
**not** require inversion. The UI should preview that override before Save.

Deadzone is a finite fraction`0 <= d < 1`, applied **once after inversion**:
steering uses `sign(v)*max(0,(abs(v)-d)/(1-d))`; pedals use
`max(0,(v-d)/(1-d))`. No-calibration (`null`) returns the raw sample unchanged,
including negative values; it is not an implicit pedal rescale or a default tune.

`CalibrationDraft(action,identity,axis,kind,original=record_or_none,...)` accepts:

- Steering steps: centre, left, right, return.
- Pedal steps: released, full, return.

The return reading must be within0.10 normalized units of the pre-inversion,
pre-deadzone centre/released position. Each capture names its current exact
identity. Wrong order or invalid samples are rejected; a changed/invalid identity
cancels the draft as disconnected. `observe_inventory(rows)` also cancels on
missing/ambiguous identity or missing selected fixed axis. Reappearance does not
revive a cancelled draft. `cancel()` clears samples and returns the original.
`proposal(invert=...,deadzone=...)` is available only after all stages; it creates
an unsaved copy without replacing original/active state.

The caller owns input stability windows, detection of multiple moving axes or
simultaneous buttons, timeout, Esc, and inventory refresh. Use cancel on timeout
or Esc; supply current representative samples only after stable capture. This
module cannot infer unplug events from an old inventory snapshot.

## Atomic save and adoption sequence

1. Read exact original bytes when opening the edit; retain the old effective
   records. Build one or several proposals in memory.
2. Before saving, refresh the DirectInput inventory and cancel drafts whose
   identity/axis is unavailable. Pass that snapshot to commit_proposals.
3. Commit validates every proposal and exact identity/axis before filesystem
   mutation. Duplicate actions and ambiguous old legacy keys are errors. It
   requires the original bytes still match, prepares all changes in memory,
   writes a unique byte-exact `.before-controls.<uuid>.bak`, then writes and
   fsyncs a temporary file beside the target.
4. It rereads the target immediately before one os.replace. Failed validation,
   ordinary concurrent edits, backup/temp/replace errors never update caller
   objects or active records. Temporary files are removed; recovery backups stay.
5. Only after success should the UI adopt the returned records, rebuild its
   effective mapping snapshot and show saved calibration. The native adapter
   must acknowledge support/version before the product calls that input Ready.

The byte check is optimistic concurrency, not an OS-wide compare-and-swap lock.
UI/native callers must keep a single settings writer. This does not eliminate
an uncooperative writer racing between the final check and os.replace. Runtime
identity must likewise be revalidated by the native consumer after launch; the
frontend inventory cannot close the enumerate-to-native-start race by itself.

## Native golden vectors and integration boundary

`fixtures/control-calibration.json` contains **10 cases / 57 independent golden
samples**, absolute tolerance1e-12. Cases cover passthrough, symmetric/asymmetric/
reversed steering, explicit inversion, one deadzone, full-range/centre-rest/
high-rest/partial-range pedals, and clamping beyond captured ends. Expected
values were specified directly, not generated from the implementation.

The owner should port the math against these vectors and expose effective input
after native transport. The normalized result must **not** receive the old
half-axis transform or another MAME deadzone. Preserve the legacy native path
byte-equivalently when calibration is null/absent; do not globally disable
existing deadzones for other controls. Require the supported native schema and
an identity-bound fixed axis. No World force behavior, arcade ADC/NVRAM calibration
or renderer change is included here.

The module deliberately does not choose a native transport, edit collection.py /
run_rig.py, generate MAME XML, set environment selectors, enumerate hardware,
create force effects or claim device/game acceptance.

## Focused evidence

Executed only:

```powershell
python -B -m unittest discover -s tests -p test_control_preferences.py -v
```

**24 pure tests passed** on Python3.14. Tests cover strict/reordered/missing/
ambiguous identity; legacy proposal-only matching; optional current HID path;
57 golden normalized samples; invalid versions/ranges/types; cancellation,
identity/axis loss, reversed/asymmetric capture and return checks; independent
multi-action persistence; byte-exact backup/failed-save preservation; explicit
legacy update in one replacement; unknown metadata and saved Off; concurrent
edits, unsupported schema, and no-calibration fresh state without runtime defaults.
No UI, DirectInput, SDL or emulator was imported by this suite. Native parity,
physical capture and actual game-final input remain the owner's integration work.
