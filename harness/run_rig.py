"""Rig launcher - play Cruis'n USA through the live GPU renderer, today.

Starts the viewer fullscreen-borderless on the primary display (it never
takes focus), then MAME focused in a small window so the wheel and keyboard
work exactly as they do in the racing build. Sound ON, throttled, wheel
mappings pulled from the racing build's ctrlr directory.

Known gaps at this stage (Phase 1 step 1 - by design, closed by step 2):
  - two processes/windows; MAME's little window must keep focus for input
  - FFB Arcade Plugin is NOT loaded (it lives as a dinput8.dll proxy next to
    the racing build's mame.exe, not next to vunit.exe) - wheel input works,
    force feedback does not, yet
  - quitting: Esc into the MAME window ends both (viewer exits when the ring
    goes quiet and its window is closed manually, or pass --seconds)

Usage: python harness/run_rig.py [--scale 4] [--rom crusnusa]
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

POC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RACING = r"E:\Source\launchbox\Launchbox-Racing\Emulators\mame286"
VUNIT = r"E:\Source\mame-src\vunit.exe"

ap = argparse.ArgumentParser()
ap.add_argument("--rom", default="crusnusa")
ap.add_argument("--scale", type=int, default=4)
ap.add_argument("--mame", default=VUNIT)
args = ap.parse_args()

rig = os.path.join(POC, "rig")
ini = os.path.join(rig, "ini")
for d in (ini, os.path.join(rig, "cfg"), os.path.join(rig, "nvram")):
    os.makedirs(d, exist_ok=True)
open(os.path.join(ini, "mame.ini"), "w").write("skip_gameinfo 1\nvideo gdi\n")
open(os.path.join(ini, "ui.ini"), "w").write("skip_warnings 1\n")
seed = os.path.join(POC, "fixtures", f"nvram-{args.rom}")
dst = os.path.join(rig, "nvram", args.rom)
if os.path.isdir(seed) and not os.path.isdir(dst):
    shutil.copytree(seed, dst)   # persistent from then on - scores survive

# In-process GL (Phase 1 step 2): one window, one process. The external
# viewer path still works - set MIDV_LIVE=1 and start live_viewer.py instead.
mame = subprocess.Popen(
    [args.mame, args.rom,
     "-rompath", os.path.join(RACING, "roms"),
     "-inipath", ini,
     "-ctrlrpath", os.path.join(RACING, "ctrlr"),
     "-ctrlr", "EmuEzRacing",
     "-nvram_directory", os.path.join(rig, "nvram"),
     "-cfg_directory", os.path.join(rig, "cfg"),
     "-window", "-maximize", "-nokeepaspect",
     "-skip_gameinfo"],
    env=dict(os.environ, MIDV_GL="1", MIDV_GL_SCALE=str(args.scale)),
    cwd=os.path.dirname(args.mame))
print("Single window: MAME with the in-process GL overlay. Esc quits.")
mame.wait()
