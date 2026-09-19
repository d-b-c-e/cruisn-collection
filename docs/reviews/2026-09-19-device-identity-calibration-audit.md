# Strict wheel identity and calibration audit — 2026-09-19

Read-only, bounded source audit requested by the coordinator and Cruis'n owner.
Only this document was written, in a new worktree/branch; no implementation,
build, test execution, game/device call, native export or deployment occurred.
The running native build in `E:/Source/mame-ux` was left untouched.

## Baselines and evidence

- Collection branch `codex/ux-simple-advanced`, commit
  `e3eca3b70fc8e901160cbfb9ee3e54a4f223097f`.
- Audit worktree `E:/Source/cruisn-collection-identity-audit-20260919`, branch
  `codex/ux-identity-calibration-audit-20260919`, created from that commit.
- Native source `0913925c858ec9297e8553b183da4850195fe183`, the accepted4ac lineage
  plus the native UX/observer work. No inference from the unrelated4df renderer.
- Shared toolkit guidance observed at commit
  `6f9c662e330af1ab790ca291a799265e0a50ef8a`. UX-04/05 and UX-01-S require exact
  saved identity, no reorder/missing-device fallback, independent bindings,
  Simple-accessible calibration and a direct FFB picker defaulting to Steering.

| Read file | SHA256 |
|---|---|
| harness/collection.py | `486999c51b01f1c9953eedfc1cf1bb0e75ce24b98162f3172aae9e951902406f` |
| harness/run_rig.py | `b0f07ba3816cadefffa5401a386d57b2826006ad04c98f738cab214313f2c75c` |
| harness/rawjoy.py | `5675872ac14f56f128f26a5373404ed2ea9bad8c2da59cbf760b33d117705b39` |
| harness/dinput_axes.py | `89186106ddbc7aad511d29b4ef7cb87e4ceee3086f20fbc9fff4a814d9904579` |
| Native src/mame/midway/midvunit_v.cpp | `81d3af0db925f569c1826f8e4120f4ad5947058b3bd0d260ada4e89d781bfb3e` |
| Toolkit docs/CONSUMER-UX.md | `b6ed90525b14cc970bbe2b0693ab88975a233fa9fd50c783518402ce1f6adc50` |
| Toolkit docs/CONSUMER-SETTINGS-VIEWS.md | `19fed6f93f98e8bd19803be85970a43925ce897f577f6a36635188fadac510ae` |
| Toolkit docs/CONSUMER-CONTROLS-CAMERAS.md | `7fc44eb3c969ccc21ba33fc63ad07c319aeb0d8d86da3b6f6301793f2a5ce7c7` |

Line references below use these baselines. They may move in the owner's successor.

## What is actually persisted and selected

| Layer | Persisted/current selector | Consequence |
|---|---|---|
| Frontend wheelmap | `rig/collection.ini` `[wheelmap] action=Device Name|axis:N:G:pos/neg`, `Device Name|btn:N`, or keyboard token; collection.py:869–876, 1933–2013 | Each action has its own name/axis, but no stable device instance, raw endpoints, centre or deadzone. `N` is a compact GLFW axis index; `G` records gamepad classification. |
| Frontend menu input | `nav_jid` searches GLFW IDs0..15 and returns first **exact name**; collection.py:1669–1690. Button confirmation is keyed by name; captured button/axis uses first qualifying event/movement | Enumeration reorder alone is tolerated for unique names; identical names silently change ownership. Held-state identity must also be cleared on disconnect/replacement. |
| Raw HID buttons | rawjoy.py:161–187 reads RIDI_DEVICENAME path and product string, but returns `(name, preparsed, maxlen)`; emitted events at239–248 contain only `(name, button)` | The potentially useful device path is discarded. Duplicate product names and split HID collections cannot be distinguished after capture. Runtime hDevice is a transient handle, not a persisted identity. |
| Axis layout cache | `rig/axis_layout.json` keyed by instance **name**, run_rig.py:1126–1150. dinput_axes.py keeps guidInstance internally, then `out.setdefault(name,present)` chooses first twin | Duplicate names can select the wrong sparse axis table. Missing devices keep cached layouts, but an enumeration failure also falls back to a dense positional table. |
| Generated MAME input | run_rig.py:1153–1220 appends `<mapdevice device="name" controller="JOYCODE_n">`, then writes action tokens | Logical indices are stable only if the intended physical device is actually remapped. No strict presence/uniqueness check exists here. |
| FFB launch | run_rig.py:714–721 returns Steering's name; 1371–1377 uses `env.setdefault('MIDV_FFB_DEVICE', dev)` | Missing Steering omits a selector. Inherited selector wins over displayed follow-Steering behavior. No persisted explicit FFB-device UI override currently exists. |
| FFB page | collection.py:1124–1126 displays Steering name and says replacement unavailable | Informational row, not the required direct picker. It does not prove connected, unique or FFB-capable identity. |
| Native FFB | midvunit_v.cpp:2186–2255: `MIDV_FFB_DEVICE` parsed as VID:PID or case-insensitive **substring** name. First matching SDL device wins | Missing named selector already returns false; a matching device without constant force also returns false. Duplicate selectors are never counted before opening haptics. No selector falls through first wheel, then any constant-force device. |

The native SDL import table at1954–1981 currently exposes name/type/VID/PID,
not a stable instance/path/serial bridge or attachment query. Selection runs once
at worker startup (2347–2348). The reviewed loop does not reselect another wheel
on failure, which is good; it also has no explicit identity/attachment status
check before subsequent output. Do not claim hot-unplug behavior from source.

## Findings, in implementation order

### 1. Strict missing and ambiguous selection is incomplete

Native name/VID:PID selector **not found** already disables FFB. Preserve that
behavior. The unsafe remaining cases are an absent/empty selector (automatic
fallback), substring collisions, duplicate names or duplicate VID:PID, and an
inherited selector overriding what Simple displays. `%x:%x` also accepts a valid
prefix with trailing junk and does not enforce16-bit components.

Small native first fix: split inventory matching from opening haptics; require
one exact, validated requested match before any `SDL_HapticOpenFromJoystick`,
SetAutocenter, SetGain or effect creation. Zero matches and multiple matches
must produce separate inactive reasons. No selector means inactive, not first
wheel. A unique name/VID:PID selector is a **legacy compatibility stage**, not
proof of exact saved physical identity: reconnecting a different identical model
must not silently satisfy a migrated stable selection. Block known virtual-device
classes/names conservatively; never equate a wheel-type flag with proven physical
identity. Preserve the one worker owner, stop latch, output locking and cleanup.

### 2. Missing input mapping can still address an unrelated device

Additional source check: MAME `input_device::match_device_id` at
src/emu/inputdev.cpp:369 performs case-insensitive **substring** matching.
`input_manager::map_device_to_controller` at src/emu/input.cpp:1190–1247 scans
until the first match; if none is found it leaves default logical slots intact.
Thus a saved missing wheel's generated `JOYCODE_1_XAXIS` can still point to
whatever device naturally occupies slot1. This is a source-derived failure path,
not a hardware reproduction. Merely changing the mapdevice text to a full GUID
is insufficient for the missing-device case.

Resolve identity once per inventory generation before writing active sequences.
For missing/ambiguous saved bindings, preserve the saved record but generate an
explicit neutral/NONE sequence for that role (retaining any intentional keyboard
alternative), or prevent launch with a clear recovery row for required axes.
Do not omit an override and let an old base/controller/default binding win.
Avoid stripping game-specific ports without also writing their intended disabled
replacement. For the enumerate-to-native-start race, add a narrow strict mapping
mode to the native consumer: unresolved/ambiguous IDs must disable their logical
slots or fail input preparation; do not change MAME's global legacy behavior.
Tests must cover failure between frontend enumeration and native startup.

### 3. Existing ID material makes a staged stable-input fix practical

MAME DirectInput IDs are already composed by input_dinput.cpp:1317–1325 as
`<instance name> product_<guidProduct> instance_<guidInstance>`.
`dinput_axes.DIDEVICEINSTANCEW` already exposes both GUIDs, although layout()
drops product/instance identity from its returned mapping. Return structured
records instead: stable backend-qualified identity, friendly name, fixed axis
slots, gamepad classification and explicit source/provenance. Key the cache by
identity, not name. Preserve independent identities for pedals and shifter.

GLFW IDs and SDL instance IDs are session handles. Product GUID, VID:PID and a
GLFW/SDL GUID are not automatically unique physical-instance identities. A raw
HID path may change with port/interface changes; retain it only with declared
backend scope and fail missing rather than guessing. Associate GLFW/RawInput,
DirectInput and SDL records only through a verified same-interface path or a
provider-specific identity bridge. Unique friendly names can present a legacy
migration proposal, but migration/replacement requires explicit Save; duplicate
names require a directly selectable disambiguated list. Do not present that
proposal as an already verified association.

Minimal persistent extension: retain existing wheelmap strings for compatibility
and introduce versioned per-action identity records plus `ffb_device_mode =
steering|explicit` and explicit output identity. Write identity, axis-slot,
calibration and legacy-compatible token in **one** atomic ConfigParser transaction
using the current fsync/replace/backup pattern in settings_view.py. Sequential
updates to separate sections would permit a mismatched binding/calibration pair.
Explicit FFB override survives Steering changes. Saved Off/strength/tunes remain
untouched. Simple offers Use steering wheel, connected eligible devices, retained
missing selection and Refresh; Refresh inventories, it does not emit force.

Do not assume the presently loaded SDL2 exports can supply the same DirectInput
instance identity. Inspect the exact bundled SDL source/exports before choosing
that bridge; if unavailable, report `Output identity not verified` and require
an explicit supported output association. Full cross-backend identity is the one
part that cannot honestly be finished by renaming existing string fields.

### 4. Binding capture is not endpoint calibration

The wizard's steady baseline and first delta>0.55 at collection.py:1955–2013
identify an axis and sign, then advance immediately. It picks the first axis
when several move, and first button event when several arrive. The review page
saves bindings atomically and Cancel retains old assignments; retain that good
behavior. There is no centre/both-end capture, released/full range, deadzone,
inversion editor or live normalized result. `Game calibration: F2 in game`
(collection.py:1089) is truthful arcade ADC guidance, not completion of UX-04.
No handbrake action is exposed in the current arcade port tables; record that
capability exception rather than manufacture an e-brake action.

A concrete current translation defect to cover: `_wheelmap_token` at1079–1112
uses recorded sign only for pedals. It always emits `_POS_ABSOLUTE` or
`_NEG_ABSOLUTE` for signed pedal bindings, even when captured rest was at an
extreme. MAME inputdev.cpp:1004–1018 first applies device deadzone/saturation,
then scales half-axis. For a raw pedal spanning-1..+1, positive-half mapping
collapses the negative half to released; direction alone cannot distinguish
that range from a centre-rest pedal. Steering ignores captured sign entirely,
so sign metadata does not implement steering inversion.

Minimal correction needs recorded rest/full and explicit range mode. Existing
ambiguous bindings keep their behavior until the player saves a calibration;
never reinterpret them silently. The Simple operation should be staged:
centre -> left -> right -> return-to-centre for Steering, or release -> fully
press -> release for pedals, followed by a live normalized preview and Save
calibration/Cancel. Require one device/axis, finite samples, a meaningful span,
consistent orientation and connected unchanged identity. Moving several controls,
Esc, timeout or disconnect keeps prior effective and saved values. Advanced gets
manual raw range/response tuning; ordinary inversion/deadzone stays Simple.

### 5. A frontend bar alone cannot apply a native calibration

The current native DirectInput poll normalizes advertised DIPROP_RANGE to
[-65536,+65536] (input_dinput.cpp:577–594); configure resets driver deadzone and
saturation and retains advertised min/max (622–655). Core inputdev.cpp:449–451,
475–490 subsequently applies the global joystick deadzone/saturation, and
1004–1018 applies reverse/half-axis modifiers. The launcher has no per-axis
endpoint or centre transport. Its MIDV_STEER_GAIN/CURVE at run_rig.py:1431–1435
are response tuning, not endpoint calibration. Per-port sensitivity is explicitly
not a substitute for absolute-wheel calibration (run_rig.py:996–1001).

Feasible implementation sequence without touching World force tuning:

1. Add pure capture/validation/normalization functions and draft UI, with a
   versioned persisted schema. Steering normalization maps its recorded left,
   centre and right to-1/0/+1 using separate spans; pedal normalization is
   clamp((raw-released)/(full-released),0,1). Apply inversion and deadzone once,
   explicitly; support either raw orientation, reject zero/near-zero spans and
   nonfinite values. Clamped readings must not silently bless invalid calibration.
2. Thread that exact calibrated model through launcher preview/navigation; use
   the same identity resolver for both. Label device preview separately from
   effective game input. A sample-generation mismatch cancels the draft.
3. Implement a small opt-in native calibration adapter at the device/axis input
   boundary, keyed by full supported backend identity and fixed slot, preserving
   byte-equivalent passthrough when no calibration exists. Alternatively choose
   the per-action input-sequence boundary if shared-axis actions need different
   calibrations; reject conflicting same-axis calibrations until supported.
   Do not calibrate twice through MAME global deadzone/half-axis conversion:
   specify and test the canonical signed/raw convention and the exact emitted
   token. Keep global behavior for uncalibrated controls unchanged.
4. Read calibration only from an explicit validated launch snapshot/config,
   bound to schema/hash and native support. Unsupported native versions must
   reject an unapplied calibration rather than show `Ready`. No ADC/NVRAM edit,
   World force scaling, spring, menu/race-end gate or renderer change is needed.
5. Add an observable final-input result after native normalization/token handling.
   A pure seam test establishes math/transport; attended device/ADC verification
   still remains before claiming in-game input acceptance.

## Offline test work the owner can implement next

No tests were run in this audit. These are proposed focused additions, using
synthetic records, temporary files and fake SDL calls only:

| Test seam | Required cases / assertions |
|---|---|
| Pure selection reducer in native helper + fake SDL dispatch | No selector, exact match, missing, duplicate name, duplicate VID:PID, substring collision, malformed/trailing/overflow selector, virtual device, unsupported constant force; rejected cases make **zero haptic-open/set/effect calls**. Reorder yields same saved identity. |
| Frontend identity resolver / cache | Unique old name produces pending migration, duplicates remain ambiguous, independent pedals/shifter, same name with different GUIDs, missing identity with another device at old slot, renamed display text with same supported ID, sparse layout keyed by identity, stale cache never proves presence. |
| Actual launch boundary | Extend tests/test_launch_boundary.py through mocked Popen for all five ROM profiles. Saved Off dominates, missing/unbound/ambiguous selection cannot set FFB On or inherit stale parent selector, explicit override survives Steering rebind, recording private stop marker retained. Existing World gate assertion stays unchanged. |
| Generated controller XML | Extend tests/test_release_contract.py with strict missing/ambiguous map behavior, explicit neutral override of stale defaults, full ID mapping/reorder, sparse axes, inactive shifter binds and keyboard alternatives preserved. Test native startup inventory differing from frontend inventory. |
| Capture state machine | Centre/asymmetric ends, normal/inverted/end-rest/centre-rest pedals, jitter, two moving axes, simultaneous buttons, timeout, Esc, disconnect/reconnect, identity change during draft. Save commits identity+range once; other roles untouched. |
| Calibration math/native parity | -1/0/+1 and0/50/100%, off-centre/asymmetric steering, both raw orientations, deadzone edges, beyond-end clamping, NaN/infinity/degenerate spans, no double deadzone/half-axis, old no-calibration passthrough exact. |
| Atomic settings and actual rows | Extend tests/test_settings_view.py: failed replace leaves file and active pair intact, unknown INI keys and saved Off retained, Simple contains direct picker/calibrate actions, ambiguous/missing status visible, view switching does not enumerate/open/output. |
| Disconnect reducer | Device loss releases only its input contributions, clears navigation held state, latches output inactive and never selects a replacement; a new session ID alone cannot establish old identity. Fake observer is not physical unplug acceptance. |

The current `tests/test_world_bindings.py` is about renderer object bindings,
not wheel bindings; it is not evidence for this task. Existing launch/settings/
release-contract seams are better targets. Stop-marker/native worker qualification
already underway remains separate; do not rebuild/replay it for this document.

## Delivery boundary

Implement strict no-fallback/ambiguity policy first, then stable input mapping
and the Simple picker. Full calibration needs both draft UX and an effective
native input adapter; shipping only capture fields/bars would leave the main
requirement open. Preserve legacy configurations and per-game NVRAM, keep
World's explicit force exception unchanged, and do not claim hardware acceptance
from offline tests. This proposal authorizes no game/device execution itself.
