"""Two independent native captures, with strict manifests and retained evidence.

Success means the requested attract frames matched, not that gameplay or the
replacement renderer is correct. Never replaces an approved reference implicitly.
"""
import argparse
from pathlib import Path
import re
import shutil
import sys

from diagnostic_runtime import ROOT, diagnostic_env, execute, new_run
from verification import frame_numbers, validate_snapshots, write_json

DEFAULT_MAME = r"E:\Source\mame-src\vunit.exe"
DEFAULT_ROMPATH = r"E:\Source\launchbox\Launchbox-Racing\Emulators\mame286\roms"


def capture_run(run, args, overrides=None):
    run = Path(run)
    for name in ("ini", "snap", "nvram", "cfg", "state", "input", "diff"):
        (run / name).mkdir(parents=True, exist_ok=True)
    seed = ROOT / "fixtures" / f"nvram-{args.rom}"
    if seed.is_dir():
        shutil.copytree(seed, run / "nvram" / args.rom)
    (run / "ini" / "mame.ini").write_text("skip_gameinfo 1\n", encoding="utf-8")
    (run / "ini" / "ui.ini").write_text("skip_warnings 1\n", encoding="utf-8")
    command = [str(Path(args.mame).resolve()), args.rom,
               "-inipath", str(run / "ini"), "-rompath", args.rompath,
               "-nvram_directory", str(run / "nvram"),
               "-cfg_directory", str(run / "cfg"),
               "-snapshot_directory", str(run / "snap"),
               "-state_directory", str(run / "state"),
               "-input_directory", str(run / "input"),
               "-diff_directory", str(run / "diff"),
               "-autoboot_script", str(ROOT / "lua" / "snap.lua"),
               "-autoboot_delay", "0", "-seconds_to_run", str(args.max_seconds),
               "-nothrottle", "-video", "none", "-sound", "none", "-nojoystick",
               "-skip_gameinfo", "-snapview", "native"]
    env = diagnostic_env(dict(overrides or {}, SNAP_FRAMES=args.frames,
                              SNAP_NAMED="1", MIDV_SKIP_STARTUP_SCREENS="1"))
    report = execute(command, run, env, args.timeout)
    log = run / "stdout.log"
    stdout = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    receipts = [int(n) for n in re.findall(r"snap.lua: snapshot at frame (\d+)", stdout)]
    if report["error"]:
        raise ValueError(report["error"])
    return validate_snapshots(run / "snap", frame_numbers(args.frames),
                              report["returncode"], receipts)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mame", default=DEFAULT_MAME)
    ap.add_argument("--rom", default="crusnusa")
    ap.add_argument("--rompath", default=DEFAULT_ROMPATH)
    ap.add_argument("--frames", default="300,600,900,1200,1800,2400,3000,3600")
    ap.add_argument("--max-seconds", type=int, default=120)
    ap.add_argument("--timeout", type=float, default=600)
    ap.add_argument("--output", help="new evidence directory (must not exist)")
    ap.add_argument("--reference-dir", help="explicit new reference directory; never overwritten")
    ap.add_argument("--keep", action="store_true", help="compatibility option; evidence is always kept")
    args = ap.parse_args(argv)
    try:
        frames = frame_numbers(args.frames)
        if args.max_seconds <= 0 or args.timeout <= 0:
            raise ValueError("time limits must be positive")
        work = new_run("oracle", args.output)
    except (ValueError, OSError) as exc:
        ap.error(str(exc))
    report = {"schema": 1, "kind": "native-attract-repeatability", "rom": args.rom,
              "frames": frames, "passed": False, "runs": {}}
    print(f"oracle evidence: {work}")
    try:
        for tag in ("a", "b"):
            report["runs"][tag] = capture_run(work / tag, args)
        a, b = report["runs"]["a"], report["runs"]["b"]
        report["mismatched_frames"] = [n for n in frames if a[str(n)] != b[str(n)]]
        report["passed"] = not report["mismatched_frames"]
        if report["passed"] and args.reference_dir:
            shutil.copytree(work / "a" / "snap", Path(args.reference_dir).resolve())
    except (ValueError, OSError) as exc:
        report["error"] = str(exc)
        report["passed"] = False
    write_json(work / "report.json", report)
    print(("PASS" if report["passed"] else "FAIL") + f": {work / 'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
