"""Passive external clock following recorded emulation time, never wall time."""
import argparse
import csv
import json
import math
from pathlib import Path
import subprocess
import sys


def position(value):
    try:
        x, y = map(int, value.split(":"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("clock position must be X:Y in screen pixels") from exc
    return x, y


class FrameTail:
    """Read complete appended rows only; an interrupted write is not a frame."""
    def __init__(self, path):
        self.path = Path(path)
        self.offset = 0
        self.pending = b""
        self.latest = None

    def poll(self):
        try:
            with self.path.open("rb") as stream:
                if stream.seek(0, 2) < self.offset:
                    self.offset, self.pending, self.latest = 0, b"", None
                stream.seek(self.offset)
                data = stream.read()
                self.offset = stream.tell()
        except FileNotFoundError:
            return self.latest
        lines = (self.pending + data).split(b"\n")
        self.pending = lines.pop()
        for line in lines:
            try:
                fields = next(csv.reader([line.decode("ascii")]))
                frame, seconds = int(fields[0]), float(fields[1])
                if frame > 0 and math.isfinite(seconds) and seconds >= 0:
                    if self.latest is None or frame > self.latest[0]:
                        self.latest = frame, seconds
            except (ValueError, IndexError, UnicodeError, csv.Error):
                continue
        return self.latest


def clock_text(sample):
    if sample is None:
        return "Waiting for game...", "Emulated time / frame"
    frame, seconds = sample
    return f"{seconds:06.2f} s", f"Frame {frame:,}  |  emulated time"


class SessionClock:
    """Only the clock process may be terminated by close(), never the game."""
    def __init__(self, runtime, title, xy=(12, 12)):
        self.runtime = Path(runtime)
        self.process = None
        self.title, self.xy = title, xy

    def start(self):
        command = [sys.executable, str(Path(__file__).resolve()),
                   str(self.runtime / "frames.csv"), "--title", self.title,
                   "--stop-file", str(self.runtime / "clock.stop"),
                   "--position", f"{self.xy[0]}:{self.xy[1]}"]
        self.process = subprocess.Popen(command, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return self

    def close(self):
        if self.process is None:
            return
        if self.runtime.exists():
            (self.runtime / "clock.stop").touch()
        try:
            _, error = self.process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            _, error = self.process.communicate(timeout=2)
        if error:
            print("External clock: " + error.decode("utf-8", errors="replace"), file=sys.stderr)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("frames", type=Path)
    ap.add_argument("--title", default="Recording")
    ap.add_argument("--position", type=position, default=(12, 12))
    ap.add_argument("--stop-file", type=Path)
    args = ap.parse_args(argv)
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)
    root.configure(background="#14212d")
    root.geometry(f"340x104{args.position[0]:+d}{args.position[1]:+d}")
    root.attributes("-topmost", True)
    tk.Label(root, text=args.title, font=("Segoe UI", 11),
             bg="#14212d", fg="#8bbfe8").pack()
    timer = tk.Label(root, font=("Consolas", 25, "bold"), bg="#14212d", fg="white")
    timer.pack()
    detail = tk.Label(root, font=("Segoe UI", 10), bg="#14212d", fg="#c4d5e3")
    detail.pack()
    root.update_idletasks()
    show = lambda: None
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        api = ctypes.WinDLL("user32", use_last_error=True)
        api.GetParent.argtypes = [wintypes.HWND]
        api.GetParent.restype = wintypes.HWND
        api.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
        api.GetWindowLongW.restype = ctypes.c_long
        api.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
        api.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        hwnd = api.GetParent(root.winfo_id()) or root.winfo_id()
        # NOACTIVATE + TOOLWINDOW + TRANSPARENT + DISABLED: no focus, taskbar
        # button, or interception of wheel/keyboard/mouse input.
        api.SetWindowLongW(hwnd, -20, api.GetWindowLongW(hwnd, -20) | 0x080000A0)
        api.SetWindowLongW(hwnd, -16, api.GetWindowLongW(hwnd, -16) | 0x08000000)
        def show():
            api.SetWindowPos(hwnd, -1, *args.position, 340, 104, 0x0010 | 0x0040)
        # Show through Win32 without Tk's normal activation request.
        show()
    else:
        root.deiconify()
    tail = FrameTail(args.frames)
    updates, previous = 0, None

    def tick():
        nonlocal updates, previous
        sample = tail.poll()
        if sample != previous:
            updates += 1
            previous = sample
        value, caption = clock_text(sample)
        timer.configure(text=value)
        detail.configure(text=caption)
        if args.stop_file and args.stop_file.exists():
            (args.stop_file.parent / "clock.json").write_text(json.dumps({
                "source": str(args.frames.resolve()), "last_sample": sample,
                "display_updates": updates, "clock": "recorded-emulation-time",
                "position": args.position}, indent=2) + "\n", encoding="utf-8")
            root.destroy()
            return
        show()
        root.after(50, tick)

    tick()
    root.mainloop()


if __name__ == "__main__":
    main()
