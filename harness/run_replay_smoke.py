"""Prove INP capture/replay plumbing on attract mode with no physical outputs.

This does not replace a human-driven gameplay case or certify wheel recording.
All inputs are neutral. Run replay.py against a driving case for that evidence.
"""
import argparse
import shutil
import sys
from pathlib import Path

from diagnostic_runtime import ROOT, diagnostic_env, execute, new_run
from run_oracle import DEFAULT_MAME, DEFAULT_ROMPATH
from session_case import Recording
import replay


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mame", default=DEFAULT_MAME)
    ap.add_argument("--rom", default="crusnusa")
    ap.add_argument("--rompath", default=DEFAULT_ROMPATH)
    ap.add_argument("--frames", type=int, default=600)
    ap.add_argument("--every", type=int, default=60)
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--output")
    ap.add_argument("--initial-state", type=Path, help="copy calibrated ini/cfg/nvram from an existing case's initial directory")
    ap.add_argument("--gl", action="store_true", help="exercise this game's replacement renderer; still no wheel output")
    args = ap.parse_args(argv)
    if not 0 < args.every <= args.frames or args.timeout <= 0:
        ap.error("require 0 < every <= frames and a positive timeout")
    work = new_run("replay-smoke", args.output)
    rig = work / "seed"
    if args.initial_state:
        shutil.copytree(args.initial_state, rig)
    else:
        (rig / "ini").mkdir(parents=True)
        (rig / "ini" / "mame.ini").write_text("skip_gameinfo 1\n", encoding="utf-8")
    seed = ROOT / "fixtures" / f"nvram-{args.rom}"
    if seed.exists() and not args.initial_state:
        shutil.copytree(seed, rig / "nvram" / args.rom)
    recording = Recording(str(work / "case"), every=args.every, stop_frame=args.frames)
    command = [args.mame, args.rom, "-rompath", args.rompath,
               "-video", "none", "-sound", "none", "-nothrottle", "-nojoystick",
               "-nomouse", "-nolightgun", "-skip_gameinfo",
               "-seconds_to_run", str(args.frames // 50 + 30)]
    settings = {"MIDV_SKIP_STARTUP_SCREENS": "1"}
    if args.gl:
        from session_case import set_option
        command = set_option(command, "-video", "d3d")
        command += ["-window", "-resolution", "1280x720", "-throttle", "-nokeepaspect"]
        key = "MIDZ" if args.rom == "crusnexo" else "MIDV"
        settings.update({key + "_GL": "1", key + "_GL_SCALE": "4", key + "_GL_LOG": "1"})
        if key == 'MIDV':
            from graphics_options import VUNIT_HEIGHT, family
            settings['MIDV_GL_HEIGHT'] = str(VUNIT_HEIGHT.get(family(args.rom),400))
    command, env, runtime = recording.prepare(command, diagnostic_env(settings), rig)
    result = execute(command, runtime, env, args.timeout)
    if (runtime / "stdout.log").exists():
        shutil.copy2(runtime / "stdout.log", runtime / "launch.log")
    recording.finish(result["returncode"])
    if recording.manifest["status"] != "recorded":
        return 1
    presentation = [] if args.rom == "crusnexo" and args.gl else ["--headless"]
    return replay.main([str(recording.path), *presentation, "--timeout", str(args.timeout),
                        "--output", str(work / "replay")])


if __name__ == "__main__":
    sys.exit(main())
