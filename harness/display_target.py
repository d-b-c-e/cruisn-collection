"""Choose a monitor matching a Zeus completed-frame reference without resizing it."""
import ctypes
from ctypes import wintypes as wt
import os
import argparse


def parse_size(text):
    try:
        width,height=map(int,text.split(':'))
        if width>=320 and height>=240:return width,height
    except ValueError:
        pass
    raise argparse.ArgumentTypeError('expected display WIDTH:HEIGHT, at least 320:240')


def choose_size(size,available,*,allow_merged_triple=False):
    matching=[m for m in available if tuple(m['size'])==tuple(size)]
    merged=False
    if not matching and allow_merged_triple:
        matching=[m for m in available if tuple(m['size'])==(size[0]*3,size[1])]
        merged=bool(matching)
    if not matching:
        raise ValueError(f'No display matches requested {size[0]}x{size[1]}; captures cannot silently use another display size')
    return {'reference_size':list(size),'selected':next((m for m in matching if m['primary']),matching[0]),
            'available':available,'merged_center_panel':merged}


def apply_window_target(command, target, *, zeus_overlay=False):
    """Select a display without scaling Zeus's covered GDI owner to that display.

    Zeus presents on its owner's entire monitor independently of owner bounds.
    VUnit and native controls present at their actual MAME window dimensions.
    """
    from session_case import set_option
    command = set_option(command, '-screen', target['selected']['device'])
    command = [arg for arg in command if arg not in ('-maximize', '-nomaximize')]
    if zeus_overlay:
        command = set_option(command, '-resolution', 'auto')
        command = [arg for arg in command if arg not in ('-window', '-nowindow')]
        return command + ['-window', '-nomaximize']
    command = set_option(command, '-resolution', 'x'.join(map(str, target['reference_size'])))
    return command + ['-maximize']


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
    return choose_size(size,available)


def verify_completed_size(size, completed):
    """Validate a monitor-sized Zeus output after capture, including transitions."""
    if not completed:
        raise ValueError('No completed Zeus captures validate the requested display size')
    mismatches=[(frame,row['size']) for frame,row in completed.items()
                if tuple(row['size'])!=tuple(size)]
    if mismatches:
        raise ValueError(f'Completed Zeus captures differ from requested {size[0]}x{size[1]}: '
                         f'{len(mismatches)} frames; first {mismatches[:3]}')
    return {'requested_size':list(size),'frames':len(completed),'passed':True}
