"""Which DirectInput axis SLOTS each game controller really has.

Why this exists (2026-09-03, tester with a Fanatec CSW 2.5 base and pedals
on a separate HID joystick: "pedals bind fine in the wizard but do nothing
in game"): the wizard binds through glfw, which hands out a COMPACTED axis
list (the axes the device has, in slot order, sliders last: index 0, 1,
2...). MAME's DirectInput module names axes by their fixed slot - X Y Z RX
RY RZ SLIDER1 SLIDER2 - and simply skips a slot the device lacks ("Unable
to get properties for joystick ... axis 3" in -verbose). So a pedal set
exposing Y, RZ and a slider is glfw axes 0/1/2 but MAME tokens
YAXIS/RZAXIS/SLIDER1 - the launcher used to write XAXIS/YAXIS/ZAXIS and
the game read axes that never moved. Dense devices (this rig's Moza: all
eight) never showed it.

layout() asks DirectInput 8 directly (the same API glfw and MAME use):
  {instance name: ["YAXIS", "RZAXIS", "SLIDER1"]}   present slots in order
glfw axis index i on that device == the i-th token of its list. Sliders
come after the six axes in both glfw's sort and MAME's slot order.

Pure ctypes COM; no dinput8.dll beside us any more (the FFB plugin's copy
is gone), so this resolves to System32. Every failure returns {} and the
caller falls back to the old positional table.

CLI: python harness/dinput_axes.py   -> prints the layout
"""
import ctypes
import ctypes.wintypes as wt
import json
import sys

_HRESULT = ctypes.c_long


class GUID(ctypes.Structure):
    _fields_ = [("Data1", ctypes.c_uint32), ("Data2", ctypes.c_uint16),
                ("Data3", ctypes.c_uint16), ("Data4", ctypes.c_ubyte * 8)]

    @classmethod
    def from_str(cls, s):
        s = s.strip("{}")
        p = s.split("-")
        g = cls()
        g.Data1 = int(p[0], 16)
        g.Data2 = int(p[1], 16)
        g.Data3 = int(p[2], 16)
        tail = bytes.fromhex(p[3] + p[4])
        for i in range(8):
            g.Data4[i] = tail[i]
        return g

    def key(self):
        return bytes(self)


class DIDEVICEINSTANCEW(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("guidInstance", GUID), ("guidProduct", GUID),
                ("dwDevType", wt.DWORD), ("tszInstanceName", wt.WCHAR * 260),
                ("tszProductName", wt.WCHAR * 260), ("guidFFDriver", GUID),
                ("wUsagePage", wt.WORD), ("wUsage", wt.WORD)]


class DIDEVICEOBJECTINSTANCEW(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("guidType", GUID), ("dwOfs", wt.DWORD),
                ("dwType", wt.DWORD), ("dwFlags", wt.DWORD), ("tszName", wt.WCHAR * 260),
                ("dwFFMaxForce", wt.DWORD), ("dwFFForceResolution", wt.DWORD),
                ("wCollectionNumber", wt.WORD), ("wDesignatorIndex", wt.WORD),
                ("wUsagePage", wt.WORD), ("wUsage", wt.WORD), ("dwDimension", wt.DWORD),
                ("wExponent", wt.WORD), ("wReportId", wt.WORD)]


IID_IDirectInput8W = GUID.from_str("BF798031-483A-4DA2-AA99-5D64ED369700")
# axis object types -> MAME token and slot order (c_dfDIJoystick2 places them
# exactly like this; two slider objects become SLIDER1, SLIDER2)
AXIS_GUIDS = {
    GUID.from_str("A36D02E0-C9F3-11CF-BFC7-444553540000").key(): "XAXIS",
    GUID.from_str("A36D02E1-C9F3-11CF-BFC7-444553540000").key(): "YAXIS",
    GUID.from_str("A36D02E2-C9F3-11CF-BFC7-444553540000").key(): "ZAXIS",
    GUID.from_str("A36D02F4-C9F3-11CF-BFC7-444553540000").key(): "RXAXIS",
    GUID.from_str("A36D02F5-C9F3-11CF-BFC7-444553540000").key(): "RYAXIS",
    GUID.from_str("A36D02E3-C9F3-11CF-BFC7-444553540000").key(): "RZAXIS",
    GUID.from_str("A36D02E4-C9F3-11CF-BFC7-444553540000").key(): "SLIDER",
}
SLOT_ORDER = ["XAXIS", "YAXIS", "ZAXIS", "RXAXIS", "RYAXIS", "RZAXIS", "SLIDER1", "SLIDER2"]

DI8DEVCLASS_GAMECTRL = 4
DIEDFL_ATTACHEDONLY = 0x00000001
DIDFT_AXIS = 0x00000003
DIENUM_CONTINUE = 1

ENUM_DEVICES_CB = ctypes.WINFUNCTYPE(wt.BOOL, ctypes.POINTER(DIDEVICEINSTANCEW), ctypes.c_void_p)
ENUM_OBJECTS_CB = ctypes.WINFUNCTYPE(wt.BOOL, ctypes.POINTER(DIDEVICEOBJECTINSTANCEW), ctypes.c_void_p)


def _method(obj, index, restype, *argtypes):
    """COM vtable call helper: obj is the interface pointer (c_void_p)."""
    vtbl = ctypes.cast(ctypes.c_void_p(obj), ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
    proto = ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)
    return proto(vtbl[index])


def layout():
    """{instance name: [present axis tokens in slot order]} for every attached
    game controller. {} when DirectInput is unavailable."""
    out = {}
    try:
        dinput8 = ctypes.WinDLL("dinput8.dll")
        k32 = ctypes.windll.kernel32
        k32.GetModuleHandleW.restype = ctypes.c_void_p      # 64-bit HMODULE, not int
        k32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
        dinput8.DirectInput8Create.restype = _HRESULT
        dinput8.DirectInput8Create.argtypes = [ctypes.c_void_p, wt.DWORD, ctypes.POINTER(GUID),
                                               ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
        di = ctypes.c_void_p()
        hr = dinput8.DirectInput8Create(k32.GetModuleHandleW(None), 0x0800,
                                        ctypes.byref(IID_IDirectInput8W),
                                        ctypes.byref(di), None)
        if hr != 0 or not di:
            print(f"dinput_axes: DirectInput8Create failed (hr 0x{hr & 0xffffffff:08x})", file=sys.stderr)
            return {}
        instances = []

        def on_device(inst, _ref):
            instances.append((GUID.from_buffer_copy(bytes(inst.contents.guidInstance)),
                              inst.contents.tszInstanceName))
            return DIENUM_CONTINUE
        # IDirectInput8W::EnumDevices(dwDevType, callback, pvRef, dwFlags)
        enum_devices = _method(di.value, 4, _HRESULT, wt.DWORD, ENUM_DEVICES_CB,
                               ctypes.c_void_p, wt.DWORD)
        cb = ENUM_DEVICES_CB(on_device)
        hr = enum_devices(di.value, DI8DEVCLASS_GAMECTRL, cb, None, DIEDFL_ATTACHEDONLY)
        if hr != 0:
            print(f"dinput_axes: EnumDevices failed (hr 0x{hr & 0xffffffff:08x})", file=sys.stderr)
        create_device = _method(di.value, 3, _HRESULT, ctypes.POINTER(GUID),
                                ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p)
        for guid, name in instances:
            dev = ctypes.c_void_p()
            if create_device(di.value, ctypes.byref(guid), ctypes.byref(dev), None) != 0 or not dev:
                continue
            present = []
            sliders = 0

            def on_object(obj, _ref, present=present):
                nonlocal sliders
                tok = AXIS_GUIDS.get(bytes(obj.contents.guidType))
                if tok == "SLIDER":
                    sliders += 1
                    if sliders <= 2:
                        present.append(f"SLIDER{sliders}")
                elif tok and tok not in present:
                    present.append(tok)
                return DIENUM_CONTINUE
            enum_objects = _method(dev.value, 4, _HRESULT, ENUM_OBJECTS_CB, ctypes.c_void_p, wt.DWORD)
            ocb = ENUM_OBJECTS_CB(on_object)
            enum_objects(dev.value, ocb, None, DIDFT_AXIS)
            _method(dev.value, 2, ctypes.c_ulong)(dev.value)   # Release
            present.sort(key=SLOT_ORDER.index)
            # duplicate instance names (Fanatec bases expose two): first wins,
            # matching MAME's mapdevice (first device whose id matches)
            out.setdefault(name, present)
        _method(di.value, 2, ctypes.c_ulong)(di.value)       # Release
    except Exception as e:   # any COM/ctypes trouble: caller falls back
        print(f"dinput_axes: {e}", file=sys.stderr)
        return {}
    return out


def sparse(lay):
    """Devices whose present axes are not simply the first N slots - the
    ones the old positional mapping got wrong."""
    return {n: a for n, a in lay.items() if a != SLOT_ORDER[:len(a)]}


if __name__ == "__main__":
    lay = layout()
    print(json.dumps(lay, indent=1))
    s = sparse(lay)
    print("sparse (positional mapping would be wrong):", list(s) if s else "none")
