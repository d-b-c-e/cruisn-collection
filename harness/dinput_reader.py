"""Read an explicitly selected DirectInput instance for binding/calibration.

Uses fixed DIJOYSTATE2 axis slots, not a guessed GLFW-to-instance association.
Never opens a haptic interface, enumerates effects, or changes driver gain/range.
Any lost device/read closes this reader; reconnect requires explicit refresh.
"""
import ctypes
import ctypes.wintypes as wt
import math

import dinput_axes as di
from control_preferences import canonical_identity


class State(ctypes.Structure):
    _fields_ = [('axes', wt.LONG * 8), ('pov', wt.DWORD * 4), ('buttons', ctypes.c_ubyte * 128),
                ('velocity', wt.LONG * 8), ('acceleration', wt.LONG * 8), ('force', wt.LONG * 8)]


class ObjectFormat(ctypes.Structure):
    _fields_ = [('guid', ctypes.POINTER(di.GUID)), ('offset', wt.DWORD),
                ('type', wt.DWORD), ('flags', wt.DWORD)]


class DataFormat(ctypes.Structure):
    _fields_ = [('size', wt.DWORD), ('object_size', wt.DWORD), ('flags', wt.DWORD),
                ('data_size', wt.DWORD), ('count', wt.DWORD), ('objects', ctypes.POINTER(ObjectFormat))]


class Range(ctypes.Structure):
    _fields_ = [('header', di.DIPROPHEADER), ('minimum', wt.LONG), ('maximum', wt.LONG)]


class PropertyDword(ctypes.Structure):
    _fields_ = [('header', di.DIPROPHEADER), ('value', wt.DWORD)]


def prepare_raw_axes(device):
    """Match MAME's per-interface DirectInput preprocessing before calibration.

    Device-level deadzone/saturation must not distort the UI samples while the
    native reader removes them. These properties do not set FFB gain/effects or
    alter the advertised axis ranges. DI_PROPNOEFFECT is accepted like MAME.
    """
    for property_id, value, name in ((5, 0, 'deadzone'), (6, 10000, 'saturation')):
        prop = PropertyDword(di.DIPROPHEADER(ctypes.sizeof(PropertyDword),
            ctypes.sizeof(di.DIPROPHEADER), 0, 0), value)
        setter = di._method(device, 6, di._HRESULT, ctypes.c_void_p, ctypes.POINTER(di.DIPROPHEADER))
        if setter(device, ctypes.c_void_p(property_id), ctypes.byref(prop.header)) not in (0, 1):
            raise OSError('Cannot match game input preprocessing: device '+name)


def data_format():
    """Same optional position-axis/button layout as DIJOYSTATE2; keep refs alive."""
    guids = {name: di.GUID.from_buffer_copy(raw) for raw, name in di.AXIS_GUIDS.items()}
    guids['POV'] = di.GUID.from_str('A36D02F2-C9F3-11CF-BFC7-444553540000')
    objects = (ObjectFormat * 140)()
    for i, slot in enumerate(di.SLOT_ORDER):
        objects[i] = ObjectFormat(ctypes.pointer(guids['SLIDER' if slot.startswith('SLIDER') else slot]),
                                  i * 4, 0x80000000 | 0x00FFFF00 | 2, 0x100)
    for i in range(4):
        objects[8+i] = ObjectFormat(ctypes.pointer(guids['POV']), 32+i*4, 0x80000000 | 0x00FFFF00 | 16, 0)
    for i in range(128):
        objects[12+i] = ObjectFormat(None, 48+i, 0x80000000 | (i << 8) | 12, 0)
    fmt = DataFormat(ctypes.sizeof(DataFormat), ctypes.sizeof(ObjectFormat), 1, ctypes.sizeof(State), 140, objects)
    return fmt, objects, guids


def normalized(value, low, high):
    if not all(math.isfinite(v) for v in (value, low, high)) or high <= low:
        raise ValueError('Invalid device axis range')
    return max(-1., min(1., (value-low)*2./(high-low)-1.))


class Reader:
    def __init__(self, record, window):
        self.api = self.device = None
        self.ranges = {}
        identity = self.identity = canonical_identity(record['identity'])
        self.instance = di.GUID.from_str(identity['instance_guid'])
        self.product = di.GUID.from_str(identity['product_guid'])
        try:
            library = ctypes.WinDLL('dinput8.dll', winmode=0x800)
            create = library.DirectInput8Create
            create.restype = di._HRESULT
            create.argtypes = [ctypes.c_void_p, wt.DWORD, ctypes.POINTER(di.GUID),
                               ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
            module = ctypes.windll.kernel32.GetModuleHandleW
            module.restype = ctypes.c_void_p
            module.argtypes = [ctypes.c_wchar_p]
            pointer = ctypes.c_void_p()
            if create(module(None), 0x0800, ctypes.byref(di.IID_IDirectInput8W), ctypes.byref(pointer), None) != 0 or not pointer:
                raise OSError('DirectInput unavailable')
            self.api = pointer.value
            make = di._method(self.api, 3, di._HRESULT, ctypes.POINTER(di.GUID),
                              ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p)
            pointer = ctypes.c_void_p()
            if make(self.api, ctypes.byref(self.instance), ctypes.byref(pointer), None) != 0 or not pointer:
                raise OSError('Saved device disconnected; reconnect and Refresh')
            self.device = pointer.value
            info = di.DIDEVICEINSTANCEW()
            info.dwSize = ctypes.sizeof(info)
            if (di._method(self.device, 15, di._HRESULT, ctypes.POINTER(di.DIDEVICEINSTANCEW))(
                    self.device, ctypes.byref(info)) != 0
                    or info.guidProduct.key() != self.product.key() or info.guidInstance.key() != self.instance.key()):
                raise OSError('Device identity changed; select the replacement explicitly')
            self.format, self.objects, self.guids = data_format()
            if di._method(self.device, 11, di._HRESULT, ctypes.POINTER(DataFormat))(self.device, ctypes.byref(self.format)) != 0:
                raise OSError('Device does not support the calibration input format')
            if di._method(self.device, 13, di._HRESULT, ctypes.c_void_p, wt.DWORD)(self.device, window, 2 | 8) != 0:
                raise OSError('Could not read the selected device non-exclusively')
            prepare_raw_axes(self.device)
            for slot in record.get('axes', []):
                index = di.SLOT_ORDER.index(slot)
                value = Range()
                value.header = di.DIPROPHEADER(ctypes.sizeof(value), ctypes.sizeof(di.DIPROPHEADER), index*4, 1)
                get = di._method(self.device, 5, di._HRESULT, ctypes.c_void_p, ctypes.POINTER(di.DIPROPHEADER))
                if get(self.device, ctypes.c_void_p(4), ctypes.byref(value.header)) != 0 or value.maximum <= value.minimum:
                    raise OSError('Cannot read the selected axis range: '+slot)
                self.ranges[slot] = (index, value.minimum, value.maximum)
            if di._method(self.device, 7, di._HRESULT)(self.device) < 0:
                raise OSError('Selected device is unavailable for calibration')
        except Exception:
            self.close()
            raise

    def sample(self):
        if self.device is None:
            return None
        state = State()
        try:
            attached = di._method(self.api, 5, di._HRESULT, ctypes.POINTER(di.GUID))
            if attached(self.api, ctypes.byref(self.instance)) != 0:
                self.close()
                return None
            if di._method(self.device, 25, di._HRESULT)(self.device) < 0:
                self.close()
                return None
            read = di._method(self.device, 9, di._HRESULT, wt.DWORD, ctypes.c_void_p)
            if read(self.device, ctypes.sizeof(state), ctypes.byref(state)) != 0:
                self.close()
                return None
            return dict(axes={slot: normalized(state.axes[i], lo, hi) for slot, (i, lo, hi) in self.ranges.items()},
                        buttons=tuple(bool(v & 0x80) for v in state.buttons))
        except (OSError, ValueError):
            self.close()
            return None

    def close(self):
        if self.device is not None:
            di._method(self.device, 8, di._HRESULT)(self.device)
            di._method(self.device, 2, ctypes.c_ulong)(self.device)
            self.device = None
        if self.api is not None:
            di._method(self.api, 2, ctypes.c_ulong)(self.api)
            self.api = None
        self.ranges.clear()
