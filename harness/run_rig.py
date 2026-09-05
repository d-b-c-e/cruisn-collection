"""Rig launcher - play the V-Unit games through the in-process GPU renderer.

One process, one window: vunit.exe with the GL overlay (MIDV_GL=1), sound on,
wheel mappings from a sanitized copy of the racing build's ctrlr, and the
emulator's own force feedback (MIDV_FFB=1: the games' wheel-motor byte goes
straight to the wheel through SDL2 haptics - no plugin, no output hooks).

After launch the MAME window is made borderless-fullscreen on its monitor and
forced to the foreground, so keyboard (Coin=5, Start=1, Esc quits, F9 toggles
the CRT pass) and the wheel's foreground-mode DirectInput work no matter how
we were started - terminal, Stream Deck, or LaunchBox all leave focus on
their own console otherwise. --windowed keeps the normal maximized window.

A launch that never shows a responsive MAME window within ~20 s (a hang in
device enumeration was a known plugin failure; kept as a safety net) is
killed and relaunched once automatically.

Importable: the collection shell calls launch_game(rom=..., crt=...), which
blocks until the game exits and returns vunit's exit code.

Usage: python harness/run_rig.py [--scale 4] [--rom crusnusa] [--windowed]
                                 [--crt]
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dinput_axes  # noqa: E402  (DirectInput axis slots per device)

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
    """Distinguish a live MAME from a window whose message pump is stuck."""
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
    exit races and WER dump writes drag teardown out."""
    res = wt.DWORD()
    return bool(u32.SendMessageTimeoutW(hwnd, WM_NULL, None, None,
                                        SMTO_ABORTIFHUNG, timeout_ms,
                                        ctypes.byref(res)))


def vunit_processes(exe=None):
    """[(pid, path)] of every running copy of our emulator exe (by image
    path, so a developer's other MAME builds are never touched)."""
    exe = os.path.normcase(os.path.abspath(exe or VUNIT))
    psapi, k32 = ctypes.windll.psapi, ctypes.windll.kernel32
    arr = (wt.DWORD * 4096)()
    got = wt.DWORD()
    if not psapi.EnumProcesses(arr, ctypes.sizeof(arr), ctypes.byref(got)):
        return []
    out = []
    buf = ctypes.create_unicode_buffer(1024)
    for pid in arr[:got.value // ctypes.sizeof(wt.DWORD)]:
        if pid == os.getpid():
            continue
        h = k32.OpenProcess(0x1000, False, pid)   # QUERY_LIMITED_INFORMATION
        if not h:
            continue
        try:
            size = wt.DWORD(len(buf))
            if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                if os.path.normcase(buf.value) == exe:
                    out.append((int(pid), buf.value))
        finally:
            k32.CloseHandle(h)
    return out


def wait_or_kill(proc, mame=VUNIT, timeout=15.0):
    """Wait for a game process that has already closed its window; a
    teardown that hangs past `timeout` (crash-at-exit race) is terminated
    so it cannot hold the wheel for the next launch."""
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"emulator: still running {timeout:.0f} s after its window "
              "closed - terminating (would hold the wheel's FFB)")
        proc.kill()
        return proc.wait()


def deploy_force_profiles(vunit_exe):
    """Put force-profiles.ini beside vunit.exe, without stepping on a tune.

    The emulator reads this file at startup, so a feel can be swapped by editing
    text rather than rebuilding. The repo's copy is the shipped one; anything the
    player writes goes in force-profiles.user.ini, which is never touched and
    whose sections win.

    A tune arrived at by driving must survive a routine update, so the shipped
    file is only rewritten when it differs, and an edited shipped file is copied
    aside first rather than silently replaced.
    """
    try:
        src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "lib", "toolkit", "profiles", "force-profiles.ini")
        if not os.path.isfile(src):
            return
        dst = os.path.join(os.path.dirname(vunit_exe), "force-profiles.ini")
        if os.path.isfile(dst):
            with open(src, "rb") as a, open(dst, "rb") as b:
                if a.read() == b.read():
                    return
            stamp = time.strftime("%Y%m%d-%H%M%S")
            shutil.copy2(dst, dst + ".replaced-" + stamp)
            print(f"ffb: force-profiles.ini differed; previous kept as "
                  f"force-profiles.ini.replaced-{stamp}")
        shutil.copy2(src, dst)
        print(f"ffb: deployed force-profiles.ini beside {os.path.basename(vunit_exe)}")
    except Exception as e:                     # never block a launch over this
        print(f"ffb: could not deploy force-profiles.ini ({e}); "
              f"vunit will fall back to its built-in values")


def kill_stale_vunit(exe=None, why="stale"):
    """End any copy of our emulator still running from an earlier launch
    (a crash-at-exit leaves a zombie that keeps the wheel's force-feedback
    device - the next game then steers but has no FFB). Returns the pids
    ended. The OS releases a killed process's DirectInput effects."""
    k32 = ctypes.windll.kernel32
    ended = []
    for pid, _path in vunit_processes(exe):
        h = k32.OpenProcess(0x0001 | 0x100000, False, pid)  # TERMINATE|SYNC
        if not h:
            continue
        try:
            if k32.TerminateProcess(h, 1):
                k32.WaitForSingleObject(h, 5000)
                ended.append(pid)
        finally:
            k32.CloseHandle(h)
    if ended:
        print(f"emulator: ended {why} vunit.exe process(es) {ended}")
    return ended


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
    device-init contests early claims, and Windows sometimes activates
    the owner's last-active owned popup (the GL overlay, whose DefWindowProc
    eats keys) instead of the owner. The ALT tap releases the foreground
    lock; never use SwitchToThisWindow here (it activates the overlay).
    Stops early once the state has been stable for ~2.5 s, and aborts as
    soon as the target window dies or stops answering messages - fighting
    for a dying window undoes the player's alt-tabs for the full budget
    and reads as a hard launcher hang (rig bug G2, 2026-08-25)."""
    tid = ctypes.windll.kernel32.GetCurrentThreadId()
    mame_tid = u32.GetWindowThreadProcessId(hwnd, None)
    good = 0
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if stop is not None and stop.is_set():
            return False   # caller handed the foreground to someone else
        if not u32.IsWindow(hwnd) or not window_responding(hwnd, 500):
            return False   # target is gone or tearing down - stand down
        fg, focus = focus_state()
        if fg == hwnd and focus == hwnd:
            good += 1
            enforce_foreground._fails = 0
            if good >= 5:
                return True
        else:
            good = 0
            fails = getattr(enforce_foreground, "_fails", 0)
            # silent foreground unlock: attach our input queue to the
            # current foreground thread instead of tapping ALT. The ALT tap
            # lands as a real keystroke in whatever holds the foreground -
            # a menu-less dialog left open (e.g. joy.cpl) answers it with
            # the system error ding on every launch. ALT stays as a
            # last-resort fallback only.
            fgtid = 0
            if fg:
                fgtid = u32.GetWindowThreadProcessId(fg, None)
            if fgtid and fgtid != mame_tid:
                u32.AttachThreadInput(tid, fgtid, True)
            if fails >= 6:   # silent unlock isn't sticking - old ALT trick
                u32.keybd_event(VK_MENU, 0, 0, 0)
                u32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
            u32.SetForegroundWindow(hwnd)
            if fgtid and fgtid != mame_tid:
                u32.AttachThreadInput(tid, fgtid, False)
            enforce_foreground._fails = fails + 1
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

# per-game 16:9 margin width per side (overlay default 86 = full widescreen).
# All games default to full width now; the shell WIDESCREEN setting is the
# per-taste dial for the revealed-backdrop edge artifact (offroadc canyon
# water). Left as a hook for per-game tuning once the widescreen research
# lands (projection-aspect patch may change the calculus entirely).
GAME_MARGIN = {}


def base_rom(rom):
    """Parent-set key for per-game config tables. Clone revisions (e.g.
    crusnwld24, the 2.4 SHIFTER revision of Cruis'n World - 2.5 is the
    factory 'automatic' ROM set with transmission select removed) share the
    parent's shifter/steering/margin/height config."""
    for parent in ("crusnwld", "crusnusa", "offroadc", "crusnexo"):
        if rom.startswith(parent):
            return parent
    return rom


# Cruis'n World rev 2.4 (crusnwld24) is a MAME *clone* of crusnwld: only
# its four game ROMs differ. MAME finds ROMs by hash inside any zip in the
# rompath - a merged crusnwld.zip, a split crusnwld24.zip beside
# crusnwld.zip, or a non-merged crusnwld24.zip all work. These are the
# 2.4-only CRCs (MAME 0.286 -listroms crusnwld24 minus crusnwld).
WORLD24_CRCS = {0x551ec903, 0x4c57faf2, 0x3a4d9a30, 0xca6a0c94}


def world24_available(rompath=None):
    """True when the rev-2.4 game ROMs are present somewhere in the
    rompath (scans crusnwld*.zip central directories - cheap). .7z sets
    can't be inspected without extra deps and are assumed complete."""
    import zipfile
    rompath = rompath or ROMPATH
    found = set()
    for name in ("crusnwld24.zip", "crusnwld.zip"):
        path = os.path.join(rompath, name)
        if not os.path.isfile(path):
            continue
        try:
            with zipfile.ZipFile(path) as z:
                found |= {i.CRC & 0xFFFFFFFF for i in z.infolist()}
        except (zipfile.BadZipFile, OSError):
            continue
    if WORLD24_CRCS <= found:
        return True
    return any(os.path.isfile(os.path.join(rompath, n))
               for n in ("crusnwld24.7z", "crusnwld.7z"))


# The V-Unit games need the TMS320C31 boot ROM (c31boot.bin, MAME device
# set tms320c31) and Exotica the TMS320C32 one (c32boot.bin, tms320c32):
# tiny BAD_DUMP files MAME insists on, shipped as separate device zips in
# any full romset - and the first thing a tester with just the four game
# zips trips over ("c31boot.bin NOT FOUND ... cannot be run").
BOOT_ROM = {"crusnusa": ("tms320c31", "c31boot.bin"),
            "crusnwld": ("tms320c31", "c31boot.bin"),
            "offroadc": ("tms320c31", "c31boot.bin"),
            "crusnexo": ("tms320c32", "c32boot.bin")}


# MAME renamed the DSP device sets (tms32031/tms32032 -> tms320c31/
# tms320c32); romsets built for other versions carry the OLD names with the
# same file inside. MAME 0.286 only looks under the new name.
BOOT_ROM_OLD_NAMES = {"tms320c31": "tms32031", "tms320c32": "tms32032"}


def boot_rom_available(rom, rompath=None):
    """True when the game's DSP boot ROM exists by name in its device zip
    or inside the game's own zips (MAME searches both). An old-name device
    zip (tms32032.zip) is copied to the name MAME 0.286 expects."""
    import shutil
    import zipfile
    rompath = rompath or ROMPATH
    dev, fname = BOOT_ROM[base_rom(rom)]
    new_zip = os.path.join(rompath, dev + ".zip")
    old_zip = os.path.join(rompath, BOOT_ROM_OLD_NAMES[dev] + ".zip")
    if not os.path.isfile(new_zip) and os.path.isfile(old_zip):
        try:
            shutil.copy2(old_zip, new_zip)
            print(f"ROMs: copied {os.path.basename(old_zip)} -> "
                  f"{dev}.zip (MAME 0.286 device set name)")
        except OSError:
            pass
    for z in (dev + ".zip", base_rom(rom) + ".zip", rom + ".zip"):
        path = os.path.join(rompath, z)
        if not os.path.isfile(path):
            continue
        try:
            with zipfile.ZipFile(path) as zf:
                if any(i.filename.rsplit("/", 1)[-1].lower() == fname
                       for i in zf.infolist()):
                    return True
        except (zipfile.BadZipFile, OSError):
            continue
    return any(os.path.isfile(os.path.join(rompath, z))
               for z in (dev + ".7z", base_rom(rom) + ".7z"))


def boot_rom_note(rom):
    """User-facing notice when the boot ROM is missing, else None."""
    if boot_rom_available(rom):
        return None
    dev, fname = BOOT_ROM[base_rom(rom)]
    return (f"needs the DSP boot ROM {fname} - add {dev}.zip (MAME device "
            "set) to your ROM folder")


def resolve_world_rom(preferred):
    """The World set to boot: the preferred revision when its ROMs exist,
    else the parent (rev 2.5). Returns (rom, note-or-None)."""
    if preferred == "crusnwld24" and not world24_available():
        return "crusnwld", ("Cruis'n World 2.4 ROMs not found - running "
                            "2.5 (automatic transmission only). Add "
                            "crusnwld24.zip beside crusnwld.zip for 2.4.")
    return preferred, None


# ---- rig preparation --------------------------------------------------------
def prepare_rig(rom, crt=False, zeus_gl=False):
    """Write the rig's ini set and seed NVRAM; returns (rig, inipath)."""
    rig = os.path.join(POC, "rig")
    ini = os.path.join(rig, "ini")
    for d in (ini, os.path.join(rig, "cfg"), os.path.join(rig, "nvram")):
        os.makedirs(d, exist_ok=True)
    # output windows: MAME's Windows output module - the notifications every
    # external consumer reads (lamps, LED boards, SimHub / Buttkicker feeds).
    # MAME's default is "auto", which resolves to the "none" module, so
    # leaving the line out silences ALL of them. Dropping it along with the
    # FFB plugin in v0.3.6 is what killed the lamp outputs; our own force
    # feedback never used them (the driver calls midv_ffb_write directly).
    # priority 1: raise MAME's thread priority - ambient load (Defender,
    # Pit House, Spotify) showed up as 94-97% average speed = audio crackle.
    # video gdi is REQUIRED under the GL overlay (V-Unit games only).
    # Zeus games have no overlay, so their CRT look comes from MAME's bgfx
    # crt-geom-deluxe chain instead (boot-time only - the shell setting is
    # the toggle there; F9 does nothing on Zeus).
    if rom in ZEUS_ROMS and not zeus_gl:
        # fallback path: MAME's own renderer presents (MIDZ_GL=0)
        if crt:
            vid = "video bgfx\nbgfx_screen_chains crt-geom-deluxe\n"
        else:
            vid = "video d3d\n"
    else:
        # our GL overlay presents; gdi underneath is REQUIRED (V-Unit) /
        # cheapest (Zeus)
        vid = "video gdi\n"
    open(os.path.join(ini, "mame.ini"), "w").write(
        f"skip_gameinfo 1\n{vid}output windows\npriority 1\n")
    open(os.path.join(ini, "ui.ini"), "w").write("skip_warnings 1\n")
    seed = os.path.join(POC, "fixtures", f"nvram-{rom}")
    dst = os.path.join(rig, "nvram", rom)
    if os.path.isdir(seed) and not os.path.isdir(dst):
        shutil.copytree(seed, dst)   # persistent from then on - scores survive
    return rig, ini


def _collection_ini_set(section, key, value):
    import configparser
    path = os.path.join(POC, "rig", "collection.ini")
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(path)
    if not cp.has_section(section):
        cp.add_section(section)
    cp.set(section, key, value)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        cp.write(f)


def _collection_ini_get(section, key, default=""):
    import configparser
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(os.path.join(POC, "rig", "collection.ini"))
    return cp.get(section, key, fallback=default).strip()


def import_previous_install(src, progress=print):
    """Bring ROMs, settings, bindings, NVRAM (World calibration!) and the
    wheel GUID over from an older CruisnCollection folder. Never overwrites
    what already exists here; returns a summary string."""
    import shutil
    done = []
    src_roms = os.path.join(src, "roms")
    if os.path.isdir(src_roms):
        os.makedirs(ROMPATH, exist_ok=True)
        n = 0
        for f in os.listdir(src_roms):
            if f.lower().endswith((".zip", ".7z")) and                     not os.path.exists(os.path.join(ROMPATH, f)):
                shutil.copy2(os.path.join(src_roms, f),
                             os.path.join(ROMPATH, f))
                n += 1
        done.append(f"{n} ROM file(s)")
    rig_src, rig_dst = os.path.join(src, "rig"), os.path.join(POC, "rig")
    for sub in ("nvram", "cfg", "ctrlr"):
        s_dir = os.path.join(rig_src, sub)
        if os.path.isdir(s_dir):
            shutil.copytree(s_dir, os.path.join(rig_dst, sub),
                            dirs_exist_ok=True)
            done.append(sub)
    cfg = os.path.join(rig_src, "collection.ini")
    if os.path.isfile(cfg) and not os.path.isfile(
            os.path.join(rig_dst, "collection.ini")):
        os.makedirs(rig_dst, exist_ok=True)
        shutil.copy2(cfg, os.path.join(rig_dst, "collection.ini"))
        done.append("settings + wheel bindings")
    progress("imported: " + (", ".join(done) if done else "nothing found"))
    return done


def steer_device_name():
    """Device the wizard bound as steering ('' if none) - handed to the
    emulator as MIDV_FFB_DEVICE so force feedback goes to that wheel base."""
    import configparser
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(os.path.join(POC, "rig", "collection.ini"))
    v = cp.get("wheelmap", "steer", fallback="")
    return v.split("|", 1)[0].strip() if "|" in v else ""


def ffb_diag_enabled():
    """[collection] ffb_diag=1 in rig/collection.ini: launches trace every
    output the game makes (rig/ffb_trace.csv) and log every motor write the
    built-in FFB sends (midv_ffb.log) - both land in the support bundle."""
    import configparser
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(os.path.join(POC, "rig", "collection.ini"))
    return cp.get("collection", "ffb_diag", fallback="0").strip() == "1"


def set_ffb_diag(on, mame_dir=None):
    import configparser
    path = os.path.join(POC, "rig", "collection.ini")
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(path)
    if not cp.has_section("collection"):
        cp.add_section("collection")
    cp.set("collection", "ffb_diag", "1" if on else "0")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        cp.write(f)


# Shifter-type wiring (rig bug G7, 2026-08-25). MAME's CONF port "Shifter
# Type" defaults to "Buttons (sticky)" - built for players WITHOUT a
# shifter, and the reason a real H-pattern registered gears only when
# leaving them. When the wizard has all four gears bound (a real shifter),
# write H-Pattern (0) into the game cfg, plus the sitdown-cabinet DIP the
# games use to decide a shifter exists at all (World hides MANUAL and
# Exotica auto-selects transmission on shifterless cabinets).
SHIFTER_CFG = {
    # rom: list of (tag, type, mask, defvalue, value)
    "crusnusa": [(":CONF", "CONFIG", 7, 1, 0)],
    "offroadc": [(":CONF", "CONFIG", 7, 1, 0)],
    "crusnwld": [(":CONF", "CONFIG", 7, 1, 0),
                 (":DSW", "DIPSWITCH", 0x20, 0x20, 0)],   # Cabinet: Sitdown
    "crusnexo": [(":DIPS", "DIPSWITCH", 0x400, 0x400, 0)],  # Cabinet: Sit Down
}


def transmission_mode(cp):
    """'hpattern' or 'sequential' from [collection] transmission (the
    shell's TRANSMISSION setting). When the key is absent (configs from
    before the setting existed) infer it the way the old arbitration
    did, so paddle-only rigs stay sequential across the upgrade."""
    v = ""
    if cp.has_section("collection"):
        v = cp["collection"].get("transmission", "").strip().lower()
    if v in ("hpattern", "sequential"):
        return v
    wm = cp["wheelmap"] if cp.has_section("wheelmap") else {}
    hpat = all(g in wm for g in ("gear1", "gear2", "gear3", "gear4"))
    seq = "shiftup" in wm and "shiftdn" in wm
    return "sequential" if (seq and not hpat) else "hpattern"


# Cruis'n Exotica's TRANS SELECT screen ("A / AUTO / M") looked broken for
# months: it always confirmed AUTO, whatever the wheel, shifter or buttons
# did. It is gated on a DIP the manual barely documents - DS1 "Wheel Invert".
# With it OFF the game confirms immediately; with it ON the screen actually
# reads the wheel. (Found by Endprodukt, confirmed here headless 2026-09-04.)
# The same DIP mirrors the wheel for driving, which the driver patch cancels
# (MIDZ_WHEEL_INVERT) - so only the menu changes, and on that menu you turn
# the wheel LEFT for MANUAL.
EXOTICA_DIP_WHEEL_INVERT = 0x0800


def apply_exotica_dips(rig, rom):
    """Seed MAME's own cfg for crusnexo with Wheel Invert = On, merging into
    whatever is already there (MAME rewrites this file at exit, and a player
    can still change the DIP in MAME's own menu). [collection]
    exotica_manual = 0 opts out. No-op for the other games."""
    if rom != "crusnexo" or _collection_ini_get(
            "collection", "exotica_manual", "1") == "0":
        return False
    path = os.path.join(rig, "cfg", "crusnexo.cfg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except (OSError, ET.ParseError):
        root = ET.Element("mameconfig", {"version": "10"})
        tree = ET.ElementTree(root)
    system = next((s for s in root.iter("system")
                   if s.get("name") == "crusnexo"), None)
    if system is None:
        system = ET.SubElement(root, "system", {"name": "crusnexo"})
    inp = system.find("input")
    if inp is None:
        inp = ET.SubElement(system, "input")
    mask = str(EXOTICA_DIP_WHEEL_INVERT)
    port = next((p for p in inp.findall("port")
                 if p.get("tag") == ":DIPS" and p.get("mask") == mask), None)
    if port is None:
        port = ET.SubElement(inp, "port")
    port.set("tag", ":DIPS")
    port.set("type", "DIPSWITCH")
    port.set("mask", mask)
    port.set("defvalue", mask)
    port.set("value", "0")          # 0 = On
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return True


def apply_shifter_config(rig, rom):
    """Inject shifter CONF/DIP port values into rig/cfg/<rom>.cfg. The
    TRANSMISSION setting picks the style (CONF H-Pattern=0 or
    Sequential=5, V-Unit only); the active mode's bindings must exist in
    [wheelmap] (gear1-4 or shiftup+shiftdn). MAME loads the values at
    boot and rewrites the file at exit; re-injecting every launch keeps
    the intent stable. No-op when the active mode has nothing bound
    (release installs)."""
    entries = SHIFTER_CFG.get(base_rom(rom))
    if not entries:
        return
    import configparser
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(os.path.join(POC, "rig", "collection.ini"))
    mode = transmission_mode(cp)
    if mode == "hpattern":
        if not all(cp.has_option("wheelmap", g) for g in
                   ("gear1", "gear2", "gear3", "gear4")):
            return
        conf_val = 0
    else:
        if not (cp.has_option("wheelmap", "shiftup")
                and cp.has_option("wheelmap", "shiftdn")):
            return
        # Exotica has no CONF port (gears BUTTON2-5); in sequential mode
        # the driver's virtual gear (MIDZ_SEQ_SHIFT, launch env) stands in
        # for the H-pattern, so the sit-down DIP applies as well
        conf_val = 5
    entries = [(tag, ptype, mask, defv,
                conf_val if tag == ":CONF" else value)
               for tag, ptype, mask, defv, value in entries]
    path = os.path.join(rig, "cfg", f"{rom}.cfg")
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except (OSError, ET.ParseError):
        root = ET.Element("mameconfig", version="10")
        tree = ET.ElementTree(root)
    system = next((sy for sy in root.findall("system")
                   if sy.get("name") == rom), None)
    if system is None:
        system = ET.SubElement(root, "system", name=rom)
    inp = system.find("input")
    if inp is None:
        inp = ET.SubElement(system, "input")
    for tag, ptype, mask, defvalue, value in entries:
        for port in list(inp.findall("port")):
            if (port.get("tag") == tag and port.get("type") == ptype
                    and port.get("mask") == str(mask)):
                inp.remove(port)
        ET.SubElement(inp, "port", tag=tag, type=ptype, mask=str(mask),
                      defvalue=str(defvalue), value=str(value))
    tree.write(path, encoding="utf-8", xml_declaration=True)


def sanitized_ctrlrpath(rig, rom="crusnusa", zeus_gl=False):
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
    # (with the live Zeus overlay the Esc menu exists there too, so the
    # Esc->F12 remap applies to Zeus games as well)
    root = tree.getroot()
    for system in ([] if (rom in ZEUS_ROMS and not zeus_gl)
                   else root.iter("system")):
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

    def system_input(name):
        for system in root.iter("system"):
            if system.get("name") == name:
                inp = system.find("input")
                if inp is None:
                    inp = ET.SubElement(system, "input")
                return inp
        sysel = ET.SubElement(root, "system", {"name": name})
        return ET.SubElement(sysel, "input")

    def set_port(inp, ptype, text):
        for p in inp.findall("port"):
            if p.get("type") == ptype:
                ns = p.find("newseq")
                if ns is None:
                    ns = ET.SubElement(p, "newseq", {"type": "standard"})
                ns.text = text
                return
        p = ET.SubElement(inp, "port", {"type": ptype})
        ET.SubElement(p, "newseq", {"type": "standard"}).text = text

    # EmuEz binds SERVICE/TEST to wheel buttons that collided with Start
    # after translation (rig round 5: Test opened on every Start press and
    # the game was unenterable). Strip JOYSTICK alternatives from all
    # SERVICE-class ports; keyboard F2/9 stay, and the wizard's TEST /
    # SERVICE CREDIT steps add deliberate wheel buttons back.
    joyalt = re.compile(r"JOYCODE_\S+")
    for inp in tree.getroot().iter("input"):
        for port in inp.findall("port"):
            if str(port.get("type", "")).startswith("SERVICE"):
                for seq in port.findall("newseq"):
                    alts = [a.strip() for a in (seq.text or "").split(" OR ")]
                    seq.text = " OR ".join(
                        a for a in alts if a and not joyalt.search(a))

    # F8/F9 are MAME's frameskip hotkeys by default - F9 doubles as the
    # overlay's CRT toggle on V-Unit games (every CRT toggle was silently
    # bumping frameskip) and read as "some skip frame thing" on Exotica.
    # Stray frameskip changes only ever hurt here: unbind both everywhere.
    dflt = system_input("default")
    set_port(dflt, "UI_FRAMESKIP_DEC", "NONE")
    set_port(dflt, "UI_FRAMESKIP_INC", "NONE")
    # Every game in the collection has cabinet volume buttons whose level
    # persists to CMOS - a uniform = / - binding lets the player level all
    # four games once (Exotica boots much quieter than the V-Unit three)
    set_port(dflt, "VOLUME_UP", "KEYCODE_EQUALS")
    set_port(dflt, "VOLUME_DOWN", "KEYCODE_MINUS")

    apply_wheelmap(tree, rig)
    out = os.path.join(rig, "ctrlr")
    os.makedirs(out, exist_ok=True)
    tree.write(os.path.join(out, "EmuEzRacing.cfg"),
               encoding="utf-8", xml_declaration=True)
    return out


# steering analog port per game (tag/type; all use mask 255, defvalue 128).
# NOTE: the shell's STEERING SENSITIVITY used to write MAME's per-port
# "sensitivity" into rig/cfg/<rom>.cfg. For absolute devices MAME applies
# that value and then exactly un-applies it (ioport.cpp), so it never
# changed a wheel's response; it is now MIDV_STEER_GAIN (see launch env).


# collection.ini [wheelmap] key -> ([MAME port types], keyboard alternative
# to preserve). Kept in sync with the shell's WIZARD_STEPS. The analog keys
# write every steering-style port type so all three games pick them up.
WHEELMAP_PORTS = {
    "steer": (["P1_PADDLE", "P1_DIAL", "P1_AD_STICK_X"], None),
    "gas":   (["P1_PEDAL"], None),
    "brake": (["P1_PEDAL2"], None),
    "coin":  (["COIN1"], "KEYCODE_5"),
    "start": (["START1"], "KEYCODE_1"),
    # V-Unit button map (midvunit.cpp): BUTTON1=Radio, BUTTON2-4=View 1-3.
    # (Was shifted one slot until 2026-08-24: view1 landed on Radio.)
    "view1": (["P1_BUTTON2"], None),
    "view2": (["P1_BUTTON3"], None),
    "view3": (["P1_BUTTON4"], None),
    "radio": (["P1_BUTTON1"], None),
    "gear1": (["P1_BUTTON5"], None),
    "gear2": (["P1_BUTTON6"], None),
    "gear3": (["P1_BUTTON7"], None),
    "gear4": (["P1_BUTTON8"], None),
    # sequential / paddle shifting (midvunit CONF "Sequential"=5): Shift
    # Down is P1_BUTTON5 and Shift Up P1_BUTTON6 - the SAME port types the
    # H-pattern gears 1/2 use under CONF=0. The shell's TRANSMISSION
    # setting picks which mode's keys write ports (transmission_mode);
    # the inactive mode's are skipped so the ctrlr never binds both onto
    # one port, while both binding sets persist in [wheelmap].
    "shiftup": (["P1_BUTTON6"], None),
    "shiftdn": (["P1_BUTTON5"], None),
    "volup":   (["VOLUME_UP"], "KEYCODE_EQUALS"),
    "voldn":   (["VOLUME_DOWN"], "KEYCODE_MINUS"),
    "test":    (["SERVICE"], "KEYCODE_F2"),
    "service": (["SERVICE1"], "KEYCODE_9"),
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
    # sequential paddles -> the driver's virtual gear (MIDZ_SEQ_SHIFT=1):
    # Shift Up = BUTTON11, Shift Down = BUTTON12 (our midzeus patch)
    "shiftup": (["P1_BUTTON11"], None),
    "shiftdn": (["P1_BUTTON12"], None),
    "volup":   (["VOLUME_UP"], "KEYCODE_EQUALS"),
    "voldn":   (["VOLUME_DOWN"], "KEYCODE_MINUS"),
    "test":    (["SERVICE"], "KEYCODE_F2"),
    "service": (["SERVICE1"], "KEYCODE_9"),
}


def _wheelmap_token(joyidx, val, pedal=False, axes=None):
    """Translate one wizard value string to a MAME token, or None.

    axes: the device's PRESENT DirectInput axis slots in order (from
    dinput_axes.layout()). glfw compacts a device's axes (index 0, 1, 2 =
    whatever exists, sliders last) while MAME names them by fixed slot and
    skips missing ones - so on a pedal set exposing Y/RZ/slider, wizard
    axis 0 is YAXIS, not XAXIS. Without a layout the dense positional table
    is used (correct for wheels with all eight axes, this rig's Moza).

    pedal=True + a recorded press direction emits a HALF-axis token
    (_POS/_NEG_ABSOLUTE): pedals that rest at CENTER (Moza reports 0.0 at
    rest) otherwise read as 50% pressed in MAME - seen as Exotica's
    transmission screen instantly picking AUTO (gas "held")."""
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
        idx = int(parts[1])
        gp = len(parts) > 2 and parts[2] == "1"
        sgn = parts[3] if len(parts) > 3 else None
        table = AXIS_TOKENS_XINPUT if gp else (axes or AXIS_TOKENS_DINPUT)
        if idx < len(table):
            tok = f"JOYCODE_{joyidx}_{table[idx]}"
            if pedal and sgn in ("pos", "neg"):
                tok += "_POS_ABSOLUTE" if sgn == "pos" else "_NEG_ABSOLUTE"
            return tok
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


def axis_layout():
    """Present DirectInput axis slots per attached device (see
    dinput_axes.py), merged over rig/axis_layout.json so a device that is
    unplugged at this launch keeps its last known layout. Prints the devices
    whose layout is sparse - the ones the old positional mapping got wrong."""
    path = os.path.join(POC, "rig", "axis_layout.json")
    cached = {}
    try:
        with open(path, encoding="utf-8") as f:
            cached = json.load(f)
    except (OSError, ValueError):
        cached = {}
    live = dinput_axes.layout()
    if live:
        cached.update(live)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cached, f, indent=1)
        except OSError:
            pass
    for name, axes in dinput_axes.sparse(live).items():
        print(f"axes: {name} -> {' '.join(axes)} (sparse DirectInput layout; "
              "wizard axis indices translated)")
    return cached


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
    # H-pattern (gear1-4) and sequential (shiftup/shiftdn) share
    # P1_BUTTON5/6 - only the active mode's keys may write ports. The
    # TRANSMISSION setting picks the mode; both binding sets persist in
    # [wheelmap] so switching modes never costs the other's binds.
    skip = ({"shiftup", "shiftdn"} if transmission_mode(cp) == "hpattern"
            else {"gear1", "gear2", "gear3", "gear4"})
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
    layout = axis_layout()

    def resolve(val, pedal=False):
        dev, spec = val.split("|", 1)
        if dev == "KEYBOARD":
            return _wheelmap_token(0, spec, pedal)
        if dev not in joycode:
            idx = max(joycode.values(), default=0) + 1
            ET.SubElement(default_inp, "mapdevice",
                          {"device": dev, "controller": f"JOYCODE_{idx}"})
            joycode[dev] = idx
        return _wheelmap_token(joycode[dev], spec, pedal, layout.get(dev))

    def write_ports(inp, table):
        for key, val in cp["wheelmap"].items():
            if key not in table or key in skip or "|" not in val:
                continue
            porttypes, kbd = table[key]
            tok = resolve(val, pedal=key in ("gas", "brake"))
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
    wiz_ports = {pt for k in cp["wheelmap"]
                 if k in WHEELMAP_PORTS and k not in skip
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
                      crackfill=True, steersens=None, steercurve=None,
                      margin=None, ffb=None, marginfill=False, ffbclamp=None,
                      mame=VUNIT):
    """Launch one game through the GL overlay; returns (proc, hwnd) once the
    window is up, fullscreen and focused. The caller decides how to wait -
    the collection shell watches the WINDOW (gone = player exited) so it can
    reappear instantly while vunit's teardown (exit races, WER
    dump writes) drags on for seconds in the background."""
    # the live Zeus GL overlay is the default for Zeus games; MIDZ_GL=0
    # in the environment falls back to MAME's own d3d/bgfx presentation
    zeus_gl = rom in ZEUS_ROMS and os.environ.get("MIDZ_GL", "1") != "0"
    if zeus_gl and _collection_ini_get("collection", "exotica_gl", "1") == "0":
        zeus_gl = False   # [collection] exotica_gl = 0: MAME's own renderer (glitch A/B)
    rig, ini = prepare_rig(rom, crt=crt, zeus_gl=zeus_gl)
    ctrlr = sanitized_ctrlrpath(rig, rom, zeus_gl=zeus_gl)
    apply_shifter_config(rig, rom)   # G7: H-pattern + sitdown cab when bound
    exotica_manual = apply_exotica_dips(rig, rom)
    kill_stale_vunit(mame, why="left-over")
    # the shaper reads this at startup; keep it in step with the repo
    deploy_force_profiles(mame)
    # Game-code widescreen: when the presentation is full 16:9 and a per-game
    # widescreen patch exists (patch/game/<rom>-widescreen.txt), apply it via
    # MIDV_PATCH (memory-only at reset; ROM files untouched). The game then
    # DRAWS the margins instead of us approximating them. An explicit
    # MIDV_PATCH in the environment always wins (developer override).
    gw = os.path.join(POC, "patch", "game", f"{rom}-widescreen.txt")
    full_wide = (margin is None or margin >= 80)
    gamepatch = (gw if full_wide and os.path.isfile(gw)
                 and "MIDV_PATCH" not in os.environ else None)
    # [collection] gamepatch_<rom> = patch/game/<file>.txt: a chosen
    # in-memory game patch for that game (e.g. the crusnusa draw-distance
    # experiment) - wins over the widescreen default; env still wins over all
    cfg_patch = _collection_ini_get("collection", f"gamepatch_{base_rom(rom)}", "")
    if cfg_patch and "MIDV_PATCH" not in os.environ:
        cfg_path = cfg_patch if os.path.isabs(cfg_patch) else os.path.join(POC, cfg_patch)
        if os.path.isfile(cfg_path):
            gamepatch = cfg_path
            print(f"game patch ({base_rom(rom)}): {cfg_patch}")
        else:
            print(f"game patch {cfg_patch!r} not found - ignored")
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
    env = dict(os.environ, MIDV_FAST_EXIT="1",
               MIDV_GL="1", MIDZ_GL="1" if zeus_gl else "0",
               MIDV_GL_SCALE=str(scale),
               MIDV_GL_CRT="1" if crt else "0",
               MIDV_GL_CRACKFILL="1" if crackfill else "0",
               MIDV_GL_HEIGHT=str(GAME_HEIGHT.get(base_rom(rom), 400)),
               MIDV_GL_MARGIN=os.environ.get(
                   "MIDV_GL_MARGIN",
                   str(margin if margin is not None
                       else GAME_MARGIN.get(base_rom(rom), 86))),
               MIDV_GL_MARGINFILL=os.environ.get(
                   "MIDV_GL_MARGINFILL", "1" if marginfill else "0"),
               MIDV_GL_STATEFILE=statefile,
               MIDV_SKIP_STARTUP_SCREENS="1")
    if gamepatch:
        env["MIDV_PATCH"] = gamepatch
    if base_rom(rom) == "crusnexo":
        # sequential paddles on Exotica: the driver's virtual gear
        # (midzeus patch) - only when the shell is in sequential mode with
        # both paddles bound
        try:
            import configparser
            _cp = configparser.ConfigParser(interpolation=None)
            _cp.read(os.path.join(POC, "rig", "collection.ini"))
            if (transmission_mode(_cp) == "sequential"
                    and _cp.has_option("wheelmap", "shiftup")
                    and _cp.has_option("wheelmap", "shiftdn")):
                env["MIDZ_SEQ_SHIFT"] = "1"
        except Exception:
            pass
        # Exotica's spring byte peaks ~46/127 at full lock and ~11 at a
        # normal steering angle (V-Unit kicks reach 100+): x4 makes it
        # felt at normal angles and clamps at the stops; FFB STRENGTH
        # still scales on top (MIDZ_FFB_GAIN env overrides; 250 felt faint)
        env.setdefault("MIDZ_FFB_GAIN", "400")
        if exotica_manual:
            # cancels the Wheel Invert DIP for driving (see apply_exotica_dips)
            env["MIDZ_WHEEL_INVERT"] = "1"
    # Built-in force feedback (midvunit_v.cpp mvffb: SDL2 haptics on the
    # wheel's steering axis, Cannonball DX style). FFB STRENGTH scales the
    # level (0 = off entirely); the wizard's steering device names the wheel
    # base; [collection] ffb_invert = 1 flips the direction for a base whose
    # axis sign runs the other way.
    if ffb is None or int(ffb) > 0:
        env.setdefault("MIDV_FFB", "1")
        if ffb is not None:
            env["MIDV_FFB_STRENGTH"] = str(max(0, min(100, int(ffb))))
        dev = steer_device_name()
        if dev:
            env.setdefault("MIDV_FFB_DEVICE", dev)
        if _collection_ini_get("collection", "ffb_invert", "") == "1":
            env["MIDV_FFB_INVERT"] = "1"
        smooth = _collection_ini_get("collection", "ffb_smooth", "50")   # default 50 ms (rig verdict 2026-09-04)
        if smooth.isdigit() and int(smooth) > 0:
            # [collection] ffb_smooth = N ms: first-order low-pass on the
            # force level (the arcade motor's inertia); kills the V-Unit
            # damper's left-right limit cycle on a direct-drive base
            env["MIDV_FFB_SMOOTH"] = smooth
        # [collection] ffb_profile = <name@version>: which tune in
        # force-profiles.ini the shaper runs. The conditioning chain moved into
        # the shared toolkit (dbce::force::Shaper) and is described by that file,
        # which lives beside vunit.exe in mame-src and is read at startup - so a
        # tune can be swapped or edited without rebuilding the emulator.
        # cruisn-vunit@1 reproduces what mvffb did by hand; @2 is the crisper
        # centre being tested. If the file is missing, vunit falls back to
        # built-in values identical to @1 and says so in midv_ffb.log.
        profile = _collection_ini_get("collection", "ffb_profile", "cruisn-vunit@1")
        if profile:
            env["MIDV_FFB_PROFILE"] = profile
        rumble = _collection_ini_get("collection", "ffb_rumble", "100")   # plugin parity
        if rumble.isdigit() and int(rumble) > 0:
            # [collection] ffb_rumble = N %: a 100 ms vibration burst per
            # force update at |force| x N % - what the plugin did, and what
            # made crashes (single-frame full-force spikes) shake
            env["MIDV_FFB_RUMBLE"] = rumble
        for key, var in (("ffb_damper", "MIDV_FFB_DAMPER"),
                         ("ffb_friction", "MIDV_FFB_FRICTION")):
            # [collection] ffb_damper / ffb_friction = N %: condition effects
            # the base renders itself for the whole session - the arcade
            # wheel's mechanical resistance a direct-drive base lacks
            v = _collection_ini_get("collection", key, "")
            if v.isdigit() and int(v) > 0:
                env[var] = v
    slew = _collection_ini_get("collection", "ffb_slew", "")
    if slew.isdigit() and int(slew) > 0:
        # [collection] ffb_slew = N: the force may move at most N (of 127)
        # per game update - swells instead of slams (midvunit/midzeus patch)
        env["MIDV_FFB_SLEW"] = slew
    if ffbclamp:
        # FFB PEAK LIMIT: cap the games' force kicks at +-N of 127 (midvunit
        # WHLCTLZ write) - tames the damper loop on strong direct-drive
        # wheels while small road forces keep full strength
        env["MIDV_FFB_CLAMP"] = str(int(ffbclamp))
    if steersens is not None:
        # gain percent on the wheel deflection (ioport.cpp patch; MAME's
        # own cfg "sensitivity" is a no-op for absolute wheels): 200 =
        # full lock at half the travel, 50 = full travel gives half lock
        env["MIDV_STEER_GAIN"] = str(int(steersens))
    if steercurve is not None:
        # response-curve exponent percent for PADDLE fields (ioport.cpp
        # patch): <100 = more bite near center, 100 = linear
        env["MIDV_STEER_CURVE"] = str(int(steercurve))
    # UDP telemetry: env wins, else collection.ini [telemetry] keys.
    #   udp   = host:port  -> JSON stream (MIDV_TELEM_UDP)
    #   forza = host:port | on -> Forza Horizon "Data Out" packets
    #           (MIDV_TELEM_FORZA; "on"/"1" = default 127.0.0.1:5300, the
    #           port SimHub's Forza Horizon page listens on)
    if "MIDV_TELEM_UDP" not in env or "MIDV_TELEM_FORZA" not in env:
        import configparser
        cp = configparser.ConfigParser()
        cp.read(os.path.join(rig, "collection.ini"))
        if "MIDV_TELEM_UDP" not in env:
            telem = cp.get("telemetry", "udp", fallback=None)
            if telem:
                env["MIDV_TELEM_UDP"] = telem
        if "MIDV_TELEM_FORZA" not in env:
            forza = cp.get("telemetry", "forza", fallback=None)
            if forza:
                forza = forza.strip()
                if forza.lower() in ("1", "on", "true", "yes"):
                    forza = "127.0.0.1:5300"
                env["MIDV_TELEM_FORZA"] = forza

    if ffb_diag_enabled():
        env["MIDV_FFB_TRACE"] = os.path.join(rig, "ffb_trace.csv")
        env["MIDV_FFB_LOG"] = "2"   # every motor write into midv_ffb.log
        print("FFB diagnostics on: tracing outputs to rig/ffb_trace.csv "
              "and motor writes to midv_ffb.log")

    def start():
        cmd = [mame, rom,
               "-rompath", ROMPATH,
               "-inipath", ini,
               "-ctrlrpath", ctrlr,
               "-ctrlr", "EmuEzRacing",
               "-nvram_directory", os.path.join(rig, "nvram"),
               "-cfg_directory", os.path.join(rig, "cfg"),
               "-window",
               "-skip_gameinfo"]
        if not zeus_gl:
            # under the Zeus overlay MAME's window stays SMALL: its gdi
            # software-stretch to 4K cost ~3% speed; it only holds focus
            cmd += ["-maximize"]
        if rom in ZEUS_ROMS and not zeus_gl:
            # MAME's own d3d presents these: keep 4:3 (rig test round 1:
            # -nokeepaspect stretched Exotica to 16:9), sharpen the upscale
            # (default prescale 1 + bilinear = fuzz), and show only the
            # screen - the internal lamp/7seg panel ate the bottom fifth
            cmd += ["-keepaspect", "-prescale", "4", "-view", "Screen 0"]
        else:
            cmd += ["-nokeepaspect"]   # the GL overlay owns presentation
        # vunit's console output goes to rig/launch.log: a startup exit
        # (missing ROM files, bad ini) is explained by its last lines,
        # which the launcher surfaces on screen and the support bundle ships
        log = open(os.path.join(rig, "launch.log"), "w")
        # first line: what this launch actually applied (the support bundle
        # ships this file; "did the setting take?" is answered here)
        keys = ("MIDV_PATCH", "MIDZ_GL", "MIDV_GL_SCALE", "MIDV_GL_CRT",
                "MIDV_STEER_GAIN", "MIDV_STEER_CURVE", "MIDV_FFB_CLAMP",
                "MIDZ_FFB_GAIN", "MIDZ_SEQ_SHIFT", "MIDZ_WHEEL_INVERT",
                "MIDV_FFB",
                "MIDV_FFB_STRENGTH", "MIDV_FFB_DEVICE", "MIDV_FFB_INVERT",
                "MIDV_FFB_SMOOTH", "MIDV_FFB_RUMBLE", "MIDV_FFB_DAMPER",
                "MIDV_FFB_FRICTION", "MIDV_FFB_SLEW", "MIDV_FFB_TRACE")
        log.write("launch " + rom + ": " + " ".join(
            f"{k}={env[k]}" for k in keys if k in env) + chr(10))
        log.flush()
        return subprocess.Popen(cmd, env=env, cwd=os.path.dirname(mame),
                                stdout=log, stderr=subprocess.STDOUT)

    def launch_log_reason():
        try:
            lines = [ln.strip() for ln in
                     open(os.path.join(rig, "launch.log"), errors="replace")
                     if ln.strip()]
        except OSError:
            return ""
        # MAME prints the useful line(s) last: "... NOT FOUND", "required
        # files are missing", "Fatal error: ..."
        for ln in reversed(lines):
            if not ln.startswith("Average speed"):
                return ln[:160]
        return ""

    # the known-cosmetic teardown AV must not raise the WER UI:
    # its "app crashed" notification ding fired on every (re)launch. Error
    # mode is inherited by child processes. Trade-off: WER LocalDumps stop
    # collecting new vunit minidumps in rig/crashdumps.
    ctypes.windll.kernel32.SetErrorMode(0x8003)

    proc = hwnd = None
    for attempt in (1, 2):
        proc = start()
        hwnd = find_mame_hwnd(proc, timeout=20)
        if hwnd and responsive(hwnd):
            break
        if proc.poll() is not None:
            why = launch_log_reason()
            sys.exit(f"the emulator exited during startup"
                     f"{': ' + why if why else f' (code {proc.returncode})'}")
        proc.kill()   # pre-FFB hang: no force effects exist yet, kill is safe
        proc.wait()
        hwnd = None
        if attempt == 1:
            print("no responsive MAME window in 20s (device enumeration "
                  "hang) - relaunching")
    else:
        sys.exit("no responsive MAME window after 2 attempts - "
                 "check midv_ffb.log / midv_gl.log beside vunit.exe")

    if not windowed and not zeus_gl:
        make_fullscreen(hwnd)
        threading.Thread(target=enforce_fullscreen, args=(hwnd,),
                         daemon=True).start()
    focused = enforce_foreground(hwnd)
    # session-long watchdog: if the foreground ever lands back on OUR OWN
    # ecosystem (the shell/launcher process, vunit's GL overlay popup, or
    # nothing at all), reclaim it for MAME - keyboard and foreground-mode
    # DirectInput FFB die silently otherwise (seen on Exotica launched from
    # the shell: input dead until the player clicks the screen). A real
    # alt-tab to another app is left alone.
    def _focus_watchdog():
        me = os.getpid()
        while u32.IsWindow(hwnd) and proc.poll() is None:
            fg, _focus = focus_state()
            if fg != hwnd:
                fgpid = wt.DWORD()
                if fg:
                    u32.GetWindowThreadProcessId(fg, ctypes.byref(fgpid))
                if fg == 0 or fgpid.value in (me, proc.pid):
                    enforce_foreground(hwnd, seconds=5)
            time.sleep(2.0)
    threading.Thread(target=_focus_watchdog, daemon=True).start()
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
                crackfill=True, ffb=None, mame=VUNIT):
    """Blocking wrapper: launch and wait for full process exit."""
    proc, _ = launch_game_async(rom=rom, scale=scale, windowed=windowed,
                                crt=crt, crackfill=crackfill, ffb=ffb, mame=mame)
    rc = wait_or_kill(proc, mame)
    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default="crusnusa")
    ap.add_argument("--scale", type=int, default=4)
    ap.add_argument("--mame", default=VUNIT)
    ap.add_argument("--windowed", action="store_true",
                    help="keep MAME's maximized window (skip borderless fullscreen)")
    ap.add_argument("--crt", action="store_true",
                    help="start with the CRT pass on (F9 toggles live)")
    ap.add_argument("--ffb", type=int, default=None,
                    help="FFB overall strength 0-100%% (0 = off)")
    args = ap.parse_args()
    return launch_game(rom=args.rom, scale=args.scale, windowed=args.windowed,
                       crt=args.crt, ffb=args.ffb, mame=args.mame)


if __name__ == "__main__":
    sys.exit(main())
