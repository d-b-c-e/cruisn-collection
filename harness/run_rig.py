"""Rig launcher - play the V-Unit games through the in-process GPU renderer.

One process, one window: vunit.exe with the GL overlay (MIDV_GL=1), sound on,
wheel mappings from a sanitized copy of the racing build's ctrlr, FFB Arcade
Plugin loaded from vunit.exe's directory (dinput8.dll proxy), MAME outputs on
(the plugin reads Windows outputs - no outputs, no forces).

After launch the MAME window is made borderless-fullscreen on its monitor and
forced to the foreground, so keyboard (Coin=5, Start=1, Esc quits, F9 toggles
the CRT pass) and the wheel's foreground-mode DirectInput work no matter how
we were started - terminal, Stream Deck, or LaunchBox all leave focus on
their own console otherwise. --windowed keeps the normal maximized window.

A launch that never shows a responsive MAME window within ~20 s (the FFB
plugin's known ~50% first-launch device-enumeration hang) is killed and
relaunched once automatically - safe because the hang happens before any
force effect is created.

Importable: the collection shell calls launch_game(rom=..., crt=...), which
blocks until the game exits and returns vunit's exit code.

Usage: python harness/run_rig.py [--scale 4] [--rom crusnusa] [--windowed]
                                 [--crt]
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET

# Frozen (PyInstaller release folder): everything lives beside the exe.
# Dev checkout: this repo + the racing build's assets. All overridable via
# CRUISN_* env vars (see docs/INSTALL.md + setup.ps1).
FROZEN = getattr(sys, "frozen", False)
if FROZEN:
    POC = os.environ.get("CRUISN_HOME", os.path.dirname(sys.executable))
    RACING = os.environ.get("CRUISN_MAME_DIR", POC)
    VUNIT = os.environ.get("CRUISN_VUNIT", os.path.join(POC, "vunit.exe"))
    ROMPATH = os.environ.get("CRUISN_ROMS", os.path.join(POC, "roms"))
    CTRLR_SRC = os.environ.get(
        "CRUISN_CTRLR", os.path.join(POC, "ctrlr", "EmuEzRacing.cfg"))
else:
    POC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RACING = os.environ.get(
        "CRUISN_MAME_DIR",
        r"E:\Source\launchbox\Launchbox-Racing\Emulators\mame286")
    VUNIT = os.environ.get("CRUISN_VUNIT", r"E:\Source\mame-src\vunit.exe")
    ROMPATH = os.environ.get("CRUISN_ROMS", os.path.join(RACING, "roms"))
    CTRLR_SRC = os.environ.get(
        "CRUISN_CTRLR", os.path.join(RACING, "ctrlr", "EmuEzRacing.cfg"))

# ---- win32 window management ------------------------------------------------
u32 = ctypes.windll.user32
u32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(wt.DWORD)]
u32.IsWindow.argtypes = [ctypes.c_void_p]
u32.IsIconic.argtypes = [ctypes.c_void_p]
u32.IsWindowVisible.argtypes = [ctypes.c_void_p]
u32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(wt.RECT)]
u32.GetClassNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
u32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
u32.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
u32.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint]
u32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_int, ctypes.c_int, ctypes.c_int,
                             ctypes.c_int, ctypes.c_uint]
u32.MonitorFromWindow.argtypes = [ctypes.c_void_p, wt.DWORD]
u32.MonitorFromWindow.restype = ctypes.c_void_p
u32.GetMonitorInfoW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
u32.SendMessageTimeoutW.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                    ctypes.c_void_p, ctypes.c_void_p,
                                    ctypes.c_uint, ctypes.c_uint,
                                    ctypes.POINTER(wt.DWORD)]
u32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.GetForegroundWindow.restype = ctypes.c_void_p
u32.AttachThreadInput.argtypes = [wt.DWORD, wt.DWORD, wt.BOOL]
u32.SetFocus.argtypes = [ctypes.c_void_p]
u32.GetGUIThreadInfo.argtypes = [wt.DWORD, ctypes.c_void_p]

WS_OVERLAPPEDWINDOW = 0x00CF0000
GWL_STYLE = -16
SWP_FRAMECHANGED = 0x0020
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SW_RESTORE = 9
SMTO_ABORTIFHUNG = 0x0002
MONITOR_DEFAULTTONEAREST = 2
VK_MENU = 0x12
KEYEVENTF_KEYUP = 0x0002
WM_NULL = 0


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT),
                ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("flags", wt.DWORD),
                ("hwndActive", ctypes.c_void_p), ("hwndFocus", ctypes.c_void_p),
                ("hwndCapture", ctypes.c_void_p), ("hwndMenuOwner", ctypes.c_void_p),
                ("hwndMoveSize", ctypes.c_void_p), ("hwndCaret", ctypes.c_void_p),
                ("rcCaret", wt.RECT)]


def find_mame_hwnd(proc, timeout):
    """First visible top-level window of class MAME owned by proc (the GL
    overlay popup is class MidvGLOverlay in the same process - skipped)."""
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(h, _):
        wpid = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(wpid))
        if wpid.value != proc.pid or not u32.IsWindowVisible(h):
            return True
        cls = ctypes.create_unicode_buffer(64)
        u32.GetClassNameW(h, cls, 64)
        if cls.value == "MAME":
            found.append(int(h))
            return False
        return True

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and proc.poll() is None:
        u32.EnumWindows(cb, 0)
        if found:
            return found[0]
        time.sleep(0.25)
    return None


def responsive(hwnd, tries=3):
    """Distinguish a live MAME from the FFB plugin's enumeration hang."""
    res = wt.DWORD()
    for i in range(tries):
        if u32.SendMessageTimeoutW(hwnd, WM_NULL, None, None,
                                   SMTO_ABORTIFHUNG, 3000, ctypes.byref(res)):
            return True
        time.sleep(2)
    return False


def window_responding(hwnd, timeout_ms=1000):
    """True while the window's thread is pumping messages. MAME answers a
    WM_NULL within a frame during play; once teardown starts the pump stops
    and this times out - the collection shell uses that as its exit signal,
    because the window object can outlive the pump by seconds while the FFB
    plugin exit race and WER dump writes drag teardown out."""
    res = wt.DWORD()
    return bool(u32.SendMessageTimeoutW(hwnd, WM_NULL, None, None,
                                        SMTO_ABORTIFHUNG, timeout_ms,
                                        ctypes.byref(res)))


def make_fullscreen(hwnd):
    """Strip the frame and span the window's monitor; the GL overlay tracks
    the client rect every present, so it follows to fullscreen on its own."""
    u32.ShowWindow(hwnd, SW_RESTORE)
    style = u32.GetWindowLongW(hwnd, GWL_STYLE) & 0xFFFFFFFF
    u32.SetWindowLongW(hwnd, GWL_STYLE, style & ~WS_OVERLAPPEDWINDOW)
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    u32.GetMonitorInfoW(u32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST),
                        ctypes.byref(mi))
    r = mi.rcMonitor
    u32.SetWindowPos(hwnd, None, r.left, r.top,
                     r.right - r.left, r.bottom - r.top,
                     SWP_FRAMECHANGED | SWP_NOZORDER | SWP_NOACTIVATE)


def enforce_fullscreen(hwnd):
    """MAME resizes its own window on video-mode changes (crusnwld does one
    after boot, snapping back to 4:3) - watch for the window's lifetime and
    reapply the borderless-fullscreen surgery whenever it deviates. Skips
    while minimized so a deliberate alt-tab isn't fought."""
    while u32.IsWindow(hwnd):
        if not u32.IsIconic(hwnd):
            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            u32.GetMonitorInfoW(
                u32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST),
                ctypes.byref(mi))
            r, m = wt.RECT(), mi.rcMonitor
            u32.GetWindowRect(hwnd, ctypes.byref(r))
            if (r.left, r.top, r.right, r.bottom) != (m.left, m.top,
                                                      m.right, m.bottom):
                make_fullscreen(hwnd)
        time.sleep(1.0)


def focus_state():
    """(foreground hwnd, focus hwnd of the foreground thread)."""
    fg = int(u32.GetForegroundWindow() or 0)
    gti = GUITHREADINFO()
    gti.cbSize = ctypes.sizeof(GUITHREADINFO)
    u32.GetGUIThreadInfo(0, ctypes.byref(gti))
    return fg, int(gti.hwndFocus or 0)


def enforce_foreground(hwnd, seconds=45, stop=None):
    """Keep claiming the foreground for MAME's window until it sticks.

    Keyboard and the wheel's foreground-mode DirectInput both die unless
    MAME's own window holds foreground AND focus - a Stream Deck launch
    (cmd -> start /min python) has no foreground rights of its own, boot +
    FFB-plugin init contest early claims, and Windows sometimes activates
    the owner's last-active owned popup (the GL overlay, whose DefWindowProc
    eats keys) instead of the owner. The ALT tap releases the foreground
    lock; never use SwitchToThisWindow here (it activates the overlay).
    Stops early once the state has been stable for ~2.5 s."""
    tid = ctypes.windll.kernel32.GetCurrentThreadId()
    mame_tid = u32.GetWindowThreadProcessId(hwnd, None)
    good = 0
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if stop is not None and stop.is_set():
            return False   # caller handed the foreground to someone else
        fg, focus = focus_state()
        if fg == hwnd and focus == hwnd:
            good += 1
            if good >= 5:
                return True
        else:
            good = 0
            u32.keybd_event(VK_MENU, 0, 0, 0)
            u32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
            u32.SetForegroundWindow(hwnd)
            fg, focus = focus_state()
            if fg == hwnd and focus != hwnd:
                # foreground landed on our window but focus sits elsewhere
                # in its thread (e.g. the overlay): move it explicitly
                u32.AttachThreadInput(tid, mame_tid, True)
                u32.SetFocus(hwnd)
                u32.AttachThreadInput(tid, mame_tid, False)
        time.sleep(0.5)
    fg, focus = focus_state()
    return fg == hwnd and focus == hwnd


# Zeus-hardware games: no GL overlay (midvunit hooks are inert), so no gdi
# constraint - give them d3d for decent scaling of MAME's own renderer
ZEUS_ROMS = {"crusnexo"}

# coarse scanline counts per game (offroadc runs a 512x401 mode; everything
# else is 400) - fed to the overlay as MIDV_GL_HEIGHT
GAME_HEIGHT = {"offroadc": 401}


# ---- rig preparation --------------------------------------------------------
def prepare_rig(rom):
    """Write the rig's ini set and seed NVRAM; returns (rig, inipath)."""
    rig = os.path.join(POC, "rig")
    ini = os.path.join(rig, "ini")
    for d in (ini, os.path.join(rig, "cfg"), os.path.join(rig, "nvram")):
        os.makedirs(d, exist_ok=True)
    # output windows: the FFB Arcade Plugin reads MAME's Windows outputs -
    # without it the wheel steers but never gets a force (racing build matches).
    # priority 1: raise MAME's thread priority - ambient load (Defender,
    # Pit House, Spotify) showed up as 94-97% average speed = audio crackle.
    # video gdi is REQUIRED under the GL overlay (V-Unit games only).
    video = "d3d" if rom in ZEUS_ROMS else "gdi"
    open(os.path.join(ini, "mame.ini"), "w").write(
        f"skip_gameinfo 1\nvideo {video}\noutput windows\npriority 1\n")
    open(os.path.join(ini, "ui.ini"), "w").write("skip_warnings 1\n")
    seed = os.path.join(POC, "fixtures", f"nvram-{rom}")
    dst = os.path.join(rig, "nvram", rom)
    if os.path.isdir(seed) and not os.path.isdir(dst):
        shutil.copytree(seed, dst)   # persistent from then on - scores survive
    return rig, ini


def sanitized_ctrlrpath(rig, rom="crusnusa"):
    """Rig-local TRANSLATED copy of EmuEzRacing.cfg.

    EmuEZ tokenizes high wheel buttons as JOYCODE_x_BUTTON33+, but MAME's
    items for buttons 33-48 carry the standard tokens ADDSW1..ADDSW16
    (ITEM_ID_ADD_SWITCH; buttons 49+ collapse into OTHER_SWITCH and cannot
    be addressed by number). BUTTONnn for nn>32 never parses, killing the
    whole sequence including keyboard alternatives (START1's KEYCODE_1 died
    this way). Translate 33-48 -> ADDSWn; strip 49+ alternatives; drop a
    port entirely when nothing survives so MAME defaults apply. Requires
    the winhybrid DIJoystick2 fix so the items exist at all. The racing
    build's file is never modified."""
    hi = re.compile(r"(JOYCODE_\d+_)BUTTON(3[3-9]|4[0-8])\b")
    bad = re.compile(r"JOYCODE_\d+_BUTTON(49|[5-9]\d|\d{3})\b")
    if os.path.isfile(CTRLR_SRC):
        tree = ET.parse(CTRLR_SRC)
    else:
        # no EmuEZ file (fresh install): bare ctrlr, wizard bindings only
        tree = ET.ElementTree(ET.fromstring(
            '<mameconfig version="10">'
            '<system name="default"><input/></system></mameconfig>'))
    for inp in tree.getroot().iter("input"):
        for port in list(inp.findall("port")):
            empty = True
            for seq in port.findall("newseq"):
                alts = [a.strip() for a in (seq.text or "").split(" OR ")]
                keep = [hi.sub(lambda m: f"{m.group(1)}ADDSW{int(m.group(2)) - 32}", a)
                        for a in alts if a and not bad.search(a)]
                seq.text = " OR ".join(keep)
                if keep:
                    empty = False
            if empty:
                inp.remove(port)
    # in-game Esc opens the overlay options menu (the GL thread polls the
    # physical key), so detach MAME's quit from Esc; F12 stays bound as the
    # emergency instant-quit and menu-back key. Zeus games have NO overlay
    # (the menu can never appear), so they keep MAME's stock Esc = quit -
    # rig test round 1: Exotica was unquittable without task manager.
    root = tree.getroot()
    for system in [] if rom in ZEUS_ROMS else root.iter("system"):
        if system.get("name") != "default":
            continue
        inp = system.find("input")
        if inp is None:
            inp = ET.SubElement(system, "input")
        port = None
        for p in inp.findall("port"):
            if p.get("type") == "UI_CANCEL":
                port = p
                break
        if port is None:
            port = ET.SubElement(inp, "port", {"type": "UI_CANCEL"})
            ET.SubElement(port, "newseq", {"type": "standard"})
        port.find("newseq").text = "KEYCODE_F12"
        break

    apply_wheelmap(tree, rig)
    out = os.path.join(rig, "ctrlr")
    os.makedirs(out, exist_ok=True)
    tree.write(os.path.join(out, "EmuEzRacing.cfg"),
               encoding="utf-8", xml_declaration=True)
    return out


# collection.ini [wheelmap] key -> ([MAME port types], keyboard alternative
# to preserve). Kept in sync with the shell's WIZARD_STEPS. The analog keys
# write every steering-style port type so all three games pick them up.
WHEELMAP_PORTS = {
    "steer": (["P1_PADDLE", "P1_DIAL", "P1_AD_STICK_X"], None),
    "gas":   (["P1_PEDAL"], None),
    "brake": (["P1_PEDAL2"], None),
    "coin":  (["COIN1"], "KEYCODE_5"),
    "start": (["START1"], "KEYCODE_1"),
    "view1": (["P1_BUTTON1"], None),
    "view2": (["P1_BUTTON2"], None),
    "view3": (["P1_BUTTON3"], None),
    "radio": (["P1_BUTTON4"], None),
    "gear1": (["P1_BUTTON5"], None),
    "gear2": (["P1_BUTTON6"], None),
    "gear3": (["P1_BUTTON7"], None),
    "gear4": (["P1_BUTTON8"], None),
}

# glfw axis index -> MAME axis token, positional. Both stacks enumerate
# HID axes in X,Y,Z,RX,RY,RZ,Slider order for DirectInput devices; XInput
# gamepads use glfw's fixed LS/RS/trigger order mapped to MAME's xinput
# item tokens. Approximation - the support bundle shows the truth when a
# device deviates.
AXIS_TOKENS_DINPUT = ["XAXIS", "YAXIS", "ZAXIS", "RXAXIS", "RYAXIS",
                      "RZAXIS", "SLIDER1", "SLIDER2"]
AXIS_TOKENS_XINPUT = ["XAXIS", "YAXIS", "RXAXIS", "RZAXIS",
                      "SLIDER1", "SLIDER2"]

# crusnexo (Zeus) wires its cabinet differently from the V-Unit games:
# gears are BUTTON2-5, radio BUTTON6, views BUTTON7-10 (midzeus.cpp JAMMA
# sheet; BUTTON1 is unused). Same wizard keys, game-specific port types -
# written into a <system name="crusnexo"> section, which wins over the
# default section in MAME's ctrlr merge. Without this the latched shifter
# held a wrong button down in-game (rig test round 1: throttle "flutter",
# dead shifter).
WHEELMAP_PORTS_CRUSNEXO = {
    "steer": (["P1_PADDLE"], None),
    "gas":   (["P1_PEDAL"], None),
    "brake": (["P1_PEDAL2"], None),
    "coin":  (["COIN1"], "KEYCODE_5"),
    "start": (["START1"], "KEYCODE_1"),
    "view1": (["P1_BUTTON7"], None),
    "view2": (["P1_BUTTON8"], None),
    "view3": (["P1_BUTTON9"], None),
    "radio": (["P1_BUTTON6"], None),
    "gear1": (["P1_BUTTON2"], None),
    "gear2": (["P1_BUTTON3"], None),
    "gear3": (["P1_BUTTON4"], None),
    "gear4": (["P1_BUTTON5"], None),
}


def _wheelmap_token(joyidx, val):
    """Translate one wizard value string to a MAME token, or None."""
    if val.startswith("key:"):
        return val[4:]
    if val.startswith("btn:"):
        n = int(val[4:]) + 1
        if n <= 32:
            return f"JOYCODE_{joyidx}_BUTTON{n}"
        if n <= 48:
            return f"JOYCODE_{joyidx}_ADDSW{n - 32}"
        return None
    if val.startswith("axis:"):
        parts = val.split(":")
        idx, gp = int(parts[1]), parts[2] == "1" if len(parts) > 2 else False
        table = AXIS_TOKENS_XINPUT if gp else AXIS_TOKENS_DINPUT
        if idx < len(table):
            return f"JOYCODE_{joyidx}_{table[idx]}"
        return None
    # legacy plain button index
    try:
        n = int(val) + 1
    except ValueError:
        return None
    if n <= 32:
        return f"JOYCODE_{joyidx}_BUTTON{n}"
    if n <= 48:
        return f"JOYCODE_{joyidx}_ADDSW{n - 32}"
    return None


def apply_wheelmap(tree, rig):
    """Overlay the shell wizard's press-to-bind results ([wheelmap] in
    rig/collection.ini, entries 'DeviceName|buttonIndex') onto the default
    system section. Device names resolve to JOYCODE indices via the file's
    <mapdevice> entries; unknown devices get a new mapdevice appended.
    glfw button index n (0-based) == DirectInput rgbButtons[n] == MAME
    BUTTONn+1 for n<32, ADDSW(n-31) for 32..47; 48+ cannot be addressed."""
    import configparser
    cp = configparser.ConfigParser()
    cp.read(os.path.join(rig, "collection.ini"))
    if "wheelmap" not in cp:
        return
    root = tree.getroot()
    default_inp = None
    for system in root.iter("system"):
        if system.get("name") == "default":
            default_inp = system.find("input")
            break
    if default_inp is None:
        return
    joycode = {}
    for md in default_inp.findall("mapdevice"):
        m = re.match(r"JOYCODE_(\d+)", md.get("controller", ""))
        if m:
            joycode[md.get("device")] = int(m.group(1))

    def resolve(val):
        dev, spec = val.split("|", 1)
        if dev == "KEYBOARD":
            return _wheelmap_token(0, spec)
        if dev not in joycode:
            idx = max(joycode.values(), default=0) + 1
            ET.SubElement(default_inp, "mapdevice",
                          {"device": dev, "controller": f"JOYCODE_{idx}"})
            joycode[dev] = idx
        return _wheelmap_token(joycode[dev], spec)

    def write_ports(inp, table):
        for key, val in cp["wheelmap"].items():
            if key not in table or "|" not in val:
                continue
            porttypes, kbd = table[key]
            tok = resolve(val)
            if not tok:
                print(f"wheelmap: {key} = {val!r} not addressable, skipped")
                continue
            seqtext = f"{kbd} OR {tok}" if kbd else tok
            for porttype in porttypes:
                port = None
                for p in inp.findall("port"):
                    if p.get("type") == porttype:
                        port = p
                        break
                if port is None:
                    port = ET.SubElement(inp, "port", {"type": porttype})
                    ET.SubElement(port, "newseq", {"type": "standard"})
                port.find("newseq").text = seqtext

    write_ports(default_inp, WHEELMAP_PORTS)

    # game-specific sections override default in MAME's ctrlr merge - remove
    # wizard-claimed ports from them so the wizard's bindings always win
    wiz_ports = {pt for k in cp["wheelmap"] if k in WHEELMAP_PORTS
                 for pt in WHEELMAP_PORTS[k][0]}
    for system in root.iter("system"):
        if system.get("name") == "default":
            continue
        inp = system.find("input")
        if inp is None:
            continue
        for p in list(inp.findall("port")):
            if p.get("type") in wiz_ports:
                inp.remove(p)

    # crusnexo gets its own translated section (see WHEELMAP_PORTS_CRUSNEXO)
    exo_inp = None
    for system in root.iter("system"):
        if system.get("name") == "crusnexo":
            exo_inp = system.find("input")
            if exo_inp is None:
                exo_inp = ET.SubElement(system, "input")
            break
    if exo_inp is None:
        sysel = ET.SubElement(root, "system", {"name": "crusnexo"})
        exo_inp = ET.SubElement(sysel, "input")
    write_ports(exo_inp, WHEELMAP_PORTS_CRUSNEXO)


# ---- launch -----------------------------------------------------------------
def launch_game_async(rom="crusnusa", scale=4, windowed=False, crt=False,
                      crackfill=True, mame=VUNIT):
    """Launch one game through the GL overlay; returns (proc, hwnd) once the
    window is up, fullscreen and focused. The caller decides how to wait -
    the collection shell watches the WINDOW (gone = player exited) so it can
    reappear instantly while vunit's teardown (FFB plugin exit races, WER
    dump writes) drags on for seconds in the background."""
    rig, ini = prepare_rig(rom)
    ctrlr = sanitized_ctrlrpath(rig, rom)
    # MIDV_SKIP_STARTUP_SCREENS: our vunit build boots straight past MAME's
    # game-info/warning screens (BAD_DUMP sets like crusnwld otherwise stop
    # at "press any key", which injected keys cannot dismiss)
    # the overlay writes its final live-toggle state (F9 / Esc-menu CRT)
    # here at teardown; the shell reads it back so settings stay truthful
    statefile = os.path.join(rig, "gl_state.txt")
    try:
        os.remove(statefile)
    except OSError:
        pass
    env = dict(os.environ, MIDV_GL="1", MIDV_GL_SCALE=str(scale),
               MIDV_GL_CRT="1" if crt else "0",
               MIDV_GL_CRACKFILL="1" if crackfill else "0",
               MIDV_GL_HEIGHT=str(GAME_HEIGHT.get(rom, 400)),
               MIDV_GL_STATEFILE=statefile,
               MIDV_SKIP_STARTUP_SCREENS="1")
    # UDP telemetry: env wins, else collection.ini [telemetry] udp=host:port
    if "MIDV_TELEM_UDP" not in env:
        import configparser
        cp = configparser.ConfigParser()
        cp.read(os.path.join(rig, "collection.ini"))
        telem = cp.get("telemetry", "udp", fallback=None)
        if telem:
            env["MIDV_TELEM_UDP"] = telem

    def start():
        cmd = [mame, rom,
               "-rompath", ROMPATH,
               "-inipath", ini,
               "-ctrlrpath", ctrlr,
               "-ctrlr", "EmuEzRacing",
               "-nvram_directory", os.path.join(rig, "nvram"),
               "-cfg_directory", os.path.join(rig, "cfg"),
               "-window", "-maximize",
               "-skip_gameinfo"]
        if rom in ZEUS_ROMS:
            # MAME's own d3d presents these: keep 4:3 (rig test round 1:
            # -nokeepaspect stretched Exotica to 16:9), sharpen the upscale
            # (default prescale 1 + bilinear = fuzz), and show only the
            # screen - the internal lamp/7seg panel ate the bottom fifth
            cmd += ["-keepaspect", "-prescale", "4", "-view", "Screen 0"]
        else:
            cmd += ["-nokeepaspect"]   # the GL overlay owns presentation
        return subprocess.Popen(cmd, env=env, cwd=os.path.dirname(mame))

    proc = hwnd = None
    for attempt in (1, 2):
        proc = start()
        hwnd = find_mame_hwnd(proc, timeout=20)
        if hwnd and responsive(hwnd):
            break
        if proc.poll() is not None:
            sys.exit(f"vunit.exe exited during startup (code {proc.returncode})")
        proc.kill()   # pre-FFB hang: no force effects exist yet, kill is safe
        proc.wait()
        hwnd = None
        if attempt == 1:
            print("no responsive MAME window in 20s (FFB plugin first-launch "
                  "enumeration hang) - relaunching")
    else:
        sys.exit("no responsive MAME window after 2 attempts - "
                 "check FFBPlugin.ini / midv_gl.log beside vunit.exe")

    if not windowed:
        make_fullscreen(hwnd)
        threading.Thread(target=enforce_fullscreen, args=(hwnd,),
                         daemon=True).start()
    focused = enforce_foreground(hwnd)
    # park the pointer in the bottom-right corner: the arrow glyph hangs
    # below-right of its hotspot, so at the corner it renders off-screen.
    # Nothing in these games uses the mouse, and MAME won't hide it for a
    # borderless -window window.
    u32.SetCursorPos(32767, 32767)
    print("Single fullscreen window%s. Coin=5 Start=1, Esc=options menu "
          "(Exit inside), F9=CRT, F12=force quit." %
          ("" if focused else " (WARNING: could not take foreground - "
           "click the game once for keyboard/wheel)"))
    return proc, hwnd


def launch_game(rom="crusnusa", scale=4, windowed=False, crt=False,
                crackfill=True, mame=VUNIT):
    """Blocking wrapper: launch and wait for full process exit."""
    proc, _ = launch_game_async(rom=rom, scale=scale, windowed=windowed,
                                crt=crt, crackfill=crackfill, mame=mame)
    return proc.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default="crusnusa")
    ap.add_argument("--scale", type=int, default=4)
    ap.add_argument("--mame", default=VUNIT)
    ap.add_argument("--windowed", action="store_true",
                    help="keep MAME's maximized window (skip borderless fullscreen)")
    ap.add_argument("--crt", action="store_true",
                    help="start with the CRT pass on (F9 toggles live)")
    args = ap.parse_args()
    return launch_game(rom=args.rom, scale=args.scale, windowed=args.windowed,
                       crt=args.crt, mame=args.mame)


if __name__ == "__main__":
    sys.exit(main())
