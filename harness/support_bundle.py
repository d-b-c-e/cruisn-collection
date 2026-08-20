"""Support-bundle generator: one zip a user can attach to a bug report.

Collects everything needed to debug "my wheel / stick isn't working":
  - MAME's view: every input device + item token + every resolved binding
    (lua/input_dump.lua run against the emulator; a game window appears
    for ~10 seconds) plus -verbose device/format lines
  - the launcher's view: connected joysticks per glfw (--joydump)
  - the FFB plugin log (FFBlog.txt), collection.ini, the generated ctrlr,
    the GL renderer log, basic system info
Output: CruisnSupport-<date>.zip beside the launcher (or --out DIR).

CLI: python harness/support_bundle.py [--rom crusnusa] [--out DIR]
Also callable from the CruisnSetup GUI ("Save support bundle").
"""
import argparse
import datetime
import os
import platform
import subprocess
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_rig  # noqa: E402


def collect(rom="crusnusa", progress=print):
    tmp = tempfile.mkdtemp(prefix="cruisn_support_")
    files = {}

    def add_text(name, text):
        p = os.path.join(tmp, name)
        with open(p, "w", encoding="utf-8", errors="replace") as f:
            f.write(text)
        files[name] = p

    def add_file(name, path):
        if os.path.isfile(path):
            files[name] = path

    progress("collecting system info...")
    add_text("system.txt", "\n".join([
        f"date: {datetime.datetime.now().isoformat()}",
        f"os: {platform.platform()}",
        f"machine: {platform.machine()}",
        f"frozen: {run_rig.FROZEN}",
        f"POC: {run_rig.POC}",
        f"VUNIT: {run_rig.VUNIT} (exists={os.path.isfile(run_rig.VUNIT)})",
        f"ROMPATH: {run_rig.ROMPATH}",
        f"CTRLR_SRC: {run_rig.CTRLR_SRC} "
        f"(exists={os.path.isfile(run_rig.CTRLR_SRC)})",
    ]))

    progress("launcher joystick view (glfw)...")
    try:
        if run_rig.FROZEN:
            cmd = [os.path.join(run_rig.POC, "CruisnCollection.exe"),
                   "--joydump"]
        else:
            cmd = [sys.executable,
                   os.path.join(run_rig.POC, "harness", "collection.py"),
                   "--joydump"]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        add_text("joysticks_glfw.json", p.stdout or p.stderr)
    except Exception as e:
        add_text("joysticks_glfw.json", f"failed: {e}")

    progress("emulator input dump (a game window appears for ~10 s)...")
    try:
        rig, ini = run_rig.prepare_rig(rom)
        ctrlr = run_rig.sanitized_ctrlrpath(rig)
        dump = os.path.join(tmp, "input_dump.txt")
        lua = os.path.join(run_rig.POC, "lua", "input_dump.lua")
        if not os.path.isfile(lua):   # frozen: bundled under _internal
            lua = os.path.join(getattr(sys, "_MEIPASS", ""), "input_dump.lua")
        env = dict(os.environ, INPUT_DUMP=dump,
                   MIDV_SKIP_STARTUP_SCREENS="1", MIDV_GL_LOG="1")
        p = subprocess.run(
            [run_rig.VUNIT, rom,
             "-rompath", run_rig.ROMPATH, "-inipath", ini,
             "-ctrlrpath", ctrlr, "-ctrlr", "EmuEzRacing",
             "-nvram_directory", os.path.join(rig, "nvram"),
             "-cfg_directory", os.path.join(rig, "cfg"),
             "-autoboot_script", lua, "-autoboot_delay", "0",
             "-window", "-sound", "none", "-seconds_to_run", "30",
             "-skip_gameinfo", "-verbose"],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.dirname(run_rig.VUNIT), env=env)
        verbose = [ln for ln in (p.stdout + p.stderr).splitlines()
                   if any(k in ln for k in
                          ("DirectInput", "buttons reported", "Input:",
                           "joystick", "Joystick", "RawInput", "XInput"))]
        add_text("mame_verbose_input.txt", "\n".join(verbose))
        if os.path.isfile(dump):
            files["mame_input_dump.txt"] = dump
        else:
            add_text("mame_input_dump.txt",
                     f"dump not produced (exit {p.returncode})")
        add_file("generated_ctrlr.cfg",
                 os.path.join(ctrlr, "EmuEzRacing.cfg"))
    except Exception as e:
        add_text("mame_input_dump.txt", f"failed: {e}")

    progress("logs + config...")
    vdir = os.path.dirname(run_rig.VUNIT)
    add_file("FFBlog.txt", os.path.join(vdir, "FFBlog.txt"))
    add_file("FFBPlugin.ini", os.path.join(vdir, "FFBPlugin.ini"))
    add_file("midv_gl.log", os.path.join(vdir, "midv_gl.log"))
    add_file("collection.ini",
             os.path.join(run_rig.POC, "rig", "collection.ini"))
    return files


def bundle(rom="crusnusa", out_dir=None, progress=print):
    files = collect(rom, progress)
    out_dir = out_dir or run_rig.POC
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = os.path.join(out_dir, f"CruisnSupport-{stamp}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, path in files.items():
            z.write(path, name)
    progress(f"support bundle written: {out}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default="crusnusa")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    bundle(args.rom, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
