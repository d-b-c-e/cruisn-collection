"""Capture the first few seconds of a game launch as fast desktop frames.

Some messages flash at the bottom of the screen during boot - before the
GL overlay covers MAME's window - too fast to screenshot by hand. This
launches the game and grabs the full desktop at ~30 fps for a few seconds
from the moment the process starts, into results/boot-capture/, then closes
the game. Review the frames to read the message.

Usage: python harness/capture_boot.py [--rom crusnexo] [--seconds 4]
                                       [--no-overlay]
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_rig  # noqa: E402

g32 = ctypes.windll.gdi32
u32 = ctypes.windll.user32
SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG),
                ("biHeight", wt.LONG), ("biPlanes", wt.WORD),
                ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", wt.LONG),
                ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD),
                ("biClrImportant", wt.DWORD)]


def grab(w, h):
    """Full-screen BGR grab via GDI BitBlt (fast; ~30fps)."""
    hdc = u32.GetDC(0)
    mdc = g32.CreateCompatibleDC(hdc)
    bmp = g32.CreateCompatibleBitmap(hdc, w, h)
    g32.SelectObject(mdc, bmp)
    g32.BitBlt(mdc, 0, 0, w, h, hdc, 0, 0, SRCCOPY)
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h   # top-down
    bmi.biPlanes = 1
    bmi.biBitCount = 24
    buf = ctypes.create_string_buffer(((w * 3 + 3) & ~3) * h)
    g32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bmi), DIB_RGB_COLORS)
    g32.DeleteObject(bmp)
    g32.DeleteDC(mdc)
    u32.ReleaseDC(0, hdc)
    return bytes(buf), (w, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default="crusnexo")
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--overlay", action="store_true",
                    help="use the GL overlay path (-window); default is "
                         "MAME's own fullscreen so the boot message shows")
    args = ap.parse_args()

    from PIL import Image
    out = os.path.join(run_rig.POC, "results", "boot-capture")
    for f in list(os.listdir(out)) if os.path.isdir(out) else []:
        try:
            os.remove(os.path.join(out, f))
        except OSError:
            pass
    os.makedirs(out, exist_ok=True)

    w = u32.GetSystemMetrics(0)
    h = u32.GetSystemMetrics(1)
    rowsz = (w * 3 + 3) & ~3

    # build the launch command (reuse run_rig's rig prep) but Popen raw so we
    # capture DURING boot instead of waiting for the window
    rig, ini = run_rig.prepare_rig(args.rom, zeus_gl=args.overlay)
    ctrlr = run_rig.sanitized_ctrlrpath(rig, args.rom, zeus_gl=args.overlay)
    # default: no overlay + MAME's OWN FULLSCREEN, so MAME covers the whole
    # screen from the first frame and its boot message is visible to the
    # desktop grab (the overlay path launches -window behind other windows
    # and covers MAME's boot anyway). --overlay forces the overlay path.
    overlay = getattr(args, "overlay", False)
    env = dict(os.environ, MIDV_GL="1", MIDZ_GL="1" if overlay else "0",
               MIDV_GL_SCALE="4", MIDV_SKIP_STARTUP_SCREENS="1")
    cmd = [run_rig.VUNIT, args.rom, "-rompath", run_rig.ROMPATH,
           "-inipath", ini, "-ctrlrpath", ctrlr, "-ctrlr", "EmuEzRacing",
           "-nvram_directory", os.path.join(rig, "nvram"),
           "-cfg_directory", os.path.join(rig, "cfg"),
           "-nokeepaspect", "-skip_gameinfo"]
    if overlay:
        cmd += ["-window"]
    print(f"launching {args.rom}, capturing {args.seconds}s of desktop...")
    ctypes.windll.kernel32.SetErrorMode(0x8003)
    proc = subprocess.Popen(cmd, env=env, cwd=os.path.dirname(run_rig.VUNIT))

    # find + force the game window foreground during capture (Windows blocks
    # a launching background app from stealing focus; the ALT tap releases
    # the foreground lock, same trick as run_rig.enforce_foreground)
    VK_MENU, KEYUP = 0x12, 0x0002

    def find_mame():
        found = []

        @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
        def cb(hw, _):
            cls = ctypes.create_unicode_buffer(64)
            u32.GetClassNameW(hw, cls, 64)
            if cls.value == "MAME" and u32.IsWindowVisible(hw):
                found.append(hw)
            return True
        u32.EnumWindows(cb, 0)
        return found[0] if found else None

    t0 = time.time()
    n = 0
    frames = []
    while time.time() - t0 < args.seconds:
        hw = find_mame()
        if hw:
            u32.keybd_event(VK_MENU, 0, 0, 0)
            u32.keybd_event(VK_MENU, 0, KEYUP, 0)
            u32.SetForegroundWindow(hw)
            u32.ShowWindow(hw, 3)   # SW_MAXIMIZE
        raw, _ = grab(w, h)
        frames.append((round(time.time() - t0, 3), raw))
        n += 1
    print(f"captured {n} frames; writing full frames + a contact montage")
    imgs = []
    for i, (ts, raw) in enumerate(frames):
        arr = Image.frombytes("RGB", (w, h), raw, "raw", "BGR", rowsz)
        arr.save(os.path.join(out, f"boot_{i:03d}_{ts:.2f}s.png"))
        imgs.append((ts, arr))
    # contact-sheet montage of downscaled frames so the whole boot is
    # scannable in one image to spot when/what the message is
    cols, tw = 6, w // 6
    th = h * tw // w
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
    for i, (ts, arr) in enumerate(imgs):
        thumb = arr.resize((tw, th), Image.BILINEAR)
        sheet.paste(thumb, ((i % cols) * tw, (i // cols) * th))
    sheet.save(os.path.join(out, "montage.png"))

    # close the game
    try:
        found = []

        @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
        def cb(hw, _):
            cls = ctypes.create_unicode_buffer(64)
            u32.GetClassNameW(hw, cls, 64)
            if cls.value == "MAME" and u32.IsWindowVisible(hw):
                found.append(hw)
            return True
        u32.EnumWindows(cb, 0)
        for hw in found:
            u32.PostMessageA(hw, 0x0010, 0, 0)
    except Exception:
        pass
    for _ in range(40):
        if proc.poll() is not None:
            break
        time.sleep(1)
    print(f"done -> {out}  ({n} bottom-strip frames)")


if __name__ == "__main__":
    main()
