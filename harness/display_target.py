"""Choose a monitor matching a Zeus completed-frame reference without resizing it."""
import ctypes
from ctypes import wintypes as wt
import os


def monitors():
    if os.name != 'nt': raise ValueError('Zeus monitor-bound captures require Windows display enumeration')
    class MonitorInfo(ctypes.Structure):
        _fields_=[('size',wt.DWORD),('monitor',wt.RECT),('work',wt.RECT),
                  ('flags',wt.DWORD),('device',wt.WCHAR*32)]
    user=ctypes.windll.user32
    user.GetMonitorInfoW.argtypes=[wt.HMONITOR,ctypes.c_void_p]
    result=[]
    @ctypes.WINFUNCTYPE(wt.BOOL,wt.HMONITOR,wt.HDC,ctypes.POINTER(wt.RECT),wt.LPARAM)
    def visit(handle,dc,rect,data):
        info=MonitorInfo();info.size=ctypes.sizeof(info)
        if user.GetMonitorInfoW(handle,ctypes.byref(info)):
            result.append({'device':info.device,'primary':bool(info.flags&1),
                'size':[info.monitor.right-info.monitor.left,info.monitor.bottom-info.monitor.top]})
        return True
    if not user.EnumDisplayMonitors(None,None,visit,0):raise ValueError('Cannot enumerate capture displays')
    return result


def choose(reference_frames, available):
    sizes={tuple(row['size']) for row in reference_frames.values()}
    if len(sizes)!=1:raise ValueError('Zeus reference must have one fixed presentation size')
    size=next(iter(sizes))
    matching=[m for m in available if tuple(m['size'])==size]
    if not matching:
        raise ValueError(f'No display matches Zeus reference {size[0]}x{size[1]}; exact pixels cannot be compared at another size')
    selected=next((m for m in matching if m['primary']),matching[0])
    return {'reference_size':list(size),'selected':selected,'available':available}
