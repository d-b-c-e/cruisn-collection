# Strict output selection: implementation checkpoint

Native successor `25ff0fa7947` is committed/pushed on `codex/ux-native`, after
the separately frozen stop candidate091. It is not built, deployed or accepted
on physical hardware. Personal87d and the renderer parity lineage remain separate.

The selector no longer chooses the first wheel when no requested device exists.
It counts exact full-name, validated VID:PID or explicit `path:` matches before
opening haptics. Missing, ambiguous, malformed and known virtual selections stay
inactive. After opening the selected joystick, it checks attachment, the SDL
session instance and the requested identity again before opening haptics. This
closes selection/reorder races; it does not yet prove runtime hot-unplug behavior.
Legacy names/VID:PID remain compatibility selectors, not stable physical IDs.

`native/ffb_device_selection.h` is canonical. The isolated sync command is
`python harness/sync_native.py --ux --mame E:/Source/mame-ux`; the ordinary parity
helper list is unchanged. Unit coverage includes duplicate names, duplicate
VID:PID, substring refusal, malformed fields, instance paths, reorder and virtual
devices. `tests/native/check_ffb_selection.py` also extracts and compiles the
**actual** native `select_device` function against fake SDL calls. It verifies
that rejection opens no actuator, including a disappeared device, changed
session instance, changed path and an already latched user stop. No physical
enumeration or haptics occurs. The initial standalone compiler invocation
returned1 with no diagnostics; adding the MinGW runtime directory to the child
PATH allowed compilation. The actual-function receipt retains its build/run logs.

The bundled SDL2.dll reports2.32.10. Its DirectInput backend queries
DIPROP_GUIDANDPATH, normalizes the path and exposes it through the joystick path
API. This provides a specific bridge from DirectInput inventory to SDL selection;
it avoids assuming product GUIDs identify physical instances.
[SDL2.32.10 DirectInput source](https://github.com/libsdl-org/SDL/blob/release-2.32.10/src/joystick/windows/SDL_dinputjoystick.c)

New `dinput_axes.inventory()` retains backend `dinput8`, product GUID, instance
GUID, name, fixed axis slots, optional HID path and read-only FFB capability.
It opens no haptic interface. Three fake-COM tests verify GUID byte order,
property structure/dispatch, missing-property behavior and preservation of twins.
The old name-indexed `layout()` compatibility view remains explicit; this is
not yet a fix for missing-device JOYCODE fallback or full calibration wiring.

Local actual-selector evidence:
`results/diagnostics/ux-20260919/selector-dispatch/qualified.json`.
No game/device calls or native build have been made for this successor.
Shared guidance483bebd and12df6b3 were read: transactional edits, held-input
handoff and current/previous/effective disconnect neutralization remain required
in the eventual UI/input integration. The owner's World force exceptions remain.
