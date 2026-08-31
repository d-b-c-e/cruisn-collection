"""Raw Input HID button listener - the definitive >32-button capture.

Windows Raw Input delivers every HID input report from every game device
(joystick / gamepad / multi-axis usages) to a message-only window, and
hid.dll parses the report's button usages for us. No DirectInput, no
glfw, no 32-button anything: if a button exists in the device's HID
report descriptor, this sees it - up to 128+ buttons per device.

The wizard uses this alongside glfw: glfw presses win when both report
(its device names are proven to match MAME's mapdevice entries), raw
presses cover whatever glfw misses. Button numbering: HID button usage N
maps to DirectInput rgbButtons[N-1], i.e. our 0-based index is usage-1 -
the same space the ctrlr generator translates (BUTTONn / ADDSWn).

Usage:
    lis = RawButtonListener()          # spawns the listener thread
    ...
    for name, btn in lis.get_presses():   # drained each poll
        ...
    lis.stop()

Run standalone to monitor: python harness/rawjoy.py
"""
import ctypes
import threading
from collections import deque
from ctypes import wintypes as wt

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
hid = ctypes.windll.hid

WM_INPUT = 0x00FF
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
RIDEV_INPUTSINK = 0x00000100
RID_INPUT = 0x10000003
RIDI_DEVICENAME = 0x20000007
RIDI_PREPARSEDDATA = 0x20000005
RIM_TYPEHID = 2
HIDP_STATUS_SUCCESS = 0x00110000
HWND_MESSAGE = ctypes.c_void_p(-3)

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_void_p, ctypes.c_uint,
                             ctypes.c_size_t, ctypes.c_ssize_t)

u32.DefWindowProcW.restype = LRESULT
u32.DefWindowProcW.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                               ctypes.c_size_t, ctypes.c_ssize_t]
u32.CreateWindowExW.restype = ctypes.c_void_p
u32.CreateWindowExW.argtypes = [
    ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
u32.PostMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                             ctypes.c_size_t, ctypes.c_ssize_t]
u32.RegisterRawInputDevices.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                        ctypes.c_uint]
u32.GetRawInputData.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint),
                                ctypes.c_uint]
u32.GetRawInputDeviceInfoW.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                       ctypes.c_void_p,
                                       ctypes.POINTER(ctypes.c_uint)]
u32.GetRawInputDeviceInfoW.restype = ctypes.c_int
k32.GetModuleHandleW.restype = ctypes.c_void_p
k32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
k32.CreateFileW.restype = ctypes.c_void_p
k32.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_uint,
                            ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint,
                            ctypes.c_void_p]
k32.CloseHandle.argtypes = [ctypes.c_void_p]
hid.HidD_GetProductString.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.c_ulong]
hid.HidP_MaxUsageListLength.restype = ctypes.c_uint
hid.HidP_MaxUsageListLength.argtypes = [ctypes.c_int, ctypes.c_ushort,
                                        ctypes.c_void_p]
hid.HidP_GetUsages.restype = ctypes.c_uint
hid.HidP_GetUsages.argtypes = [ctypes.c_int, ctypes.c_ushort,
                               ctypes.c_ushort, ctypes.c_void_p,
                               ctypes.POINTER(ctypes.c_ulong),
                               ctypes.c_void_p, ctypes.c_void_p,
                               ctypes.c_ulong]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [("style", ctypes.c_uint), ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                ("hInstance", ctypes.c_void_p), ("hIcon", ctypes.c_void_p),
                ("hCursor", ctypes.c_void_p), ("hbrBackground", ctypes.c_void_p),
                ("lpszMenuName", ctypes.c_wchar_p),
                ("lpszClassName", ctypes.c_wchar_p)]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [("usUsagePage", ctypes.c_ushort), ("usUsage", ctypes.c_ushort),
                ("dwFlags", ctypes.c_uint), ("hwndTarget", ctypes.c_void_p)]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [("dwType", ctypes.c_uint), ("dwSize", ctypes.c_uint),
                ("hDevice", ctypes.c_void_p), ("wParam", ctypes.c_size_t)]


# The window class is registered ONCE per process and lives forever, so its
# wndproc must not belong to any listener instance: a second listener's
# window would be created with the first (dead) listener's callback and its
# queue could never fill - the wizard's >32-button capture silently dies on
# every re-entry after the first. Route through a module-lifetime proc that
# dispatches to whichever listener is currently active (last one wins).
_active = None


def _wndproc(hwnd, msg, wp, lp):
    if msg == WM_INPUT:
        lis = _active
        if lis is not None:
            lis._on_input(lp)
        return 0
    if msg == WM_DESTROY:
        u32.PostQuitMessage(0)
        return 0
    return u32.DefWindowProcW(hwnd, msg, wp, lp)


_PROC = WNDPROC(_wndproc)


class RawButtonListener:
    def __init__(self):
        global _active
        self._events = deque()
        self._devices = {}          # hDevice -> (name, preparsed buf, maxlen)
        self._pressed = {}          # hDevice -> frozenset of usages
        self._hwnd = None
        self._ready = threading.Event()
        _active = self
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(2.0)

    # ---- consumer API ----
    def get_presses(self):
        """Drain queued (device_name, button_index_0based) DOWN events."""
        out = []
        while self._events:
            out.append(self._events.popleft())
        return out

    def stop(self):
        global _active
        if _active is self:
            _active = None
        if self._hwnd:
            u32.PostMessageW(ctypes.c_void_p(self._hwnd), WM_CLOSE, 0, 0)
            self._hwnd = None
        self._thread.join(2.0)

    # ---- device info ----
    def _device(self, hdev):
        if hdev in self._devices:
            return self._devices[hdev]
        # product string ("MOZA R12 Base") via the HID device path
        name = "HID device"
        size = ctypes.c_uint(0)
        u32.GetRawInputDeviceInfoW(hdev, RIDI_DEVICENAME, None,
                                   ctypes.byref(size))
        path = ctypes.create_unicode_buffer(size.value + 1)
        if u32.GetRawInputDeviceInfoW(hdev, RIDI_DEVICENAME, path,
                                      ctypes.byref(size)) > 0:
            h = k32.CreateFileW(path.value, 0, 3, None, 3, 0, None)
            if h and h != ctypes.c_void_p(-1).value:
                buf = ctypes.create_unicode_buffer(127)
                if hid.HidD_GetProductString(ctypes.c_void_p(h), buf, 254):
                    name = buf.value.strip() or name
                k32.CloseHandle(ctypes.c_void_p(h))
        # preparsed data for usage parsing
        size = ctypes.c_uint(0)
        u32.GetRawInputDeviceInfoW(hdev, RIDI_PREPARSEDDATA, None,
                                   ctypes.byref(size))
        pre = ctypes.create_string_buffer(size.value)
        u32.GetRawInputDeviceInfoW(hdev, RIDI_PREPARSEDDATA, pre,
                                   ctypes.byref(size))
        maxlen = hid.HidP_MaxUsageListLength(0, 9, pre)   # input, Button page
        info = (name, pre, max(int(maxlen), 1))
        self._devices[hdev] = info
        return info

    # ---- the listener thread ----
    def _run(self):
        wc = WNDCLASSW()
        wc.lpfnWndProc = _PROC
        wc.hInstance = k32.GetModuleHandleW(None)
        wc.lpszClassName = "CruisnRawJoy"
        u32.RegisterClassW(ctypes.byref(wc))   # fails after the first: fine,
        # the registered proc is the same module-lifetime _PROC either way
        self._hwnd = u32.CreateWindowExW(0, "CruisnRawJoy", None, 0,
                                         0, 0, 0, 0, HWND_MESSAGE,
                                         None, wc.hInstance, None)
        rid = (RAWINPUTDEVICE * 3)()
        for i, usage in enumerate((4, 5, 8)):   # joystick, gamepad, multi-axis
            rid[i].usUsagePage = 1
            rid[i].usUsage = usage
            rid[i].dwFlags = RIDEV_INPUTSINK
            rid[i].hwndTarget = self._hwnd
        u32.RegisterRawInputDevices(rid, 3, ctypes.sizeof(RAWINPUTDEVICE))
        self._ready.set()
        msg = wt.MSG()
        while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            u32.DispatchMessageW(ctypes.byref(msg))

    def _on_input(self, lparam):
        size = ctypes.c_uint(0)
        u32.GetRawInputData(ctypes.c_void_p(lparam), RID_INPUT, None,
                            ctypes.byref(size), ctypes.sizeof(RAWINPUTHEADER))
        buf = ctypes.create_string_buffer(size.value)
        if u32.GetRawInputData(ctypes.c_void_p(lparam), RID_INPUT, buf,
                               ctypes.byref(size),
                               ctypes.sizeof(RAWINPUTHEADER)) != size.value:
            return
        hdr = ctypes.cast(buf, ctypes.POINTER(RAWINPUTHEADER)).contents
        if hdr.dwType != RIM_TYPEHID:
            return
        base = ctypes.sizeof(RAWINPUTHEADER)
        size_hid = int.from_bytes(buf[base:base + 4], "little")
        count = int.from_bytes(buf[base + 4:base + 8], "little")
        data_off = base + 8
        name, pre, maxlen = self._device(hdr.hDevice)
        usages = (ctypes.c_ushort * maxlen)()
        cur = set()
        for i in range(count):
            report = (ctypes.c_char * size_hid).from_buffer_copy(
                buf, data_off + i * size_hid)
            ulen = ctypes.c_ulong(maxlen)
            if hid.HidP_GetUsages(0, 9, 0, usages, ctypes.byref(ulen),
                                  pre, report,
                                  size_hid) == HIDP_STATUS_SUCCESS:
                cur = {usages[j] for j in range(ulen.value)}
        prev = self._pressed.get(hdr.hDevice, set())
        for usage in cur - prev:
            if usage >= 1:
                self._events.append((name, int(usage) - 1))
        self._pressed[hdr.hDevice] = cur


if __name__ == "__main__":
    import time
    lis = RawButtonListener()
    print("raw HID button monitor - press things (Ctrl+C to stop)")
    try:
        while True:
            for name, btn in lis.get_presses():
                n = btn + 1
                tok = (f"BUTTON{n}" if n <= 32 else f"ADDSW{n - 32}"
                       if n <= 48 else "OTHER_SWITCH(unaddressable)")
                print(f"DOWN  {name}  button {btn}  (JOYCODE_x_{tok})")
            time.sleep(0.01)
    except KeyboardInterrupt:
        lis.stop()
        print("bye")
