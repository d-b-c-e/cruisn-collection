"""Replay a motor trace through the vendored native FFB algorithms, without a wheel."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from diagnostic_runtime import ROOT, new_run
from verification import sha256_file, write_json


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("trace", type=Path)
    ap.add_argument("--profile", default="cruisn-vunit@2")
    ap.add_argument("--strength", type=int, default=50)
    ap.add_argument("--output")
    ap.add_argument("--impacts", action="store_true", help="evaluate the explicit steering-axis impact mix")
    ap.add_argument("--labels", type=Path, help="labelled emulated-time coverage and contact intervals (JSON)")
    ap.add_argument("--compiler", default=shutil.which("g++") or r"E:\msys64\mingw64\bin\g++.exe")
    args = ap.parse_args(argv)
    if not 0 <= args.strength <= 100:
        ap.error("strength must be 0..100")
    work = new_run("ffb-analysis", args.output)
    compiler = Path(args.compiler).resolve()
    env = dict(os.environ, PATH=str(compiler.parent) + os.pathsep + os.environ.get("PATH", ""))
    exe = work / ("analyzer.exe" if os.name == "nt" else "analyzer")
    library = ROOT / "lib" / "toolkit"
    source = ROOT / "native" / "analyze_ffb.cpp"
    report = {"schema": 1, "kind": "offline-force-algorithm", "profile": args.profile,
              "trace": str(args.trace.resolve()), "trace_sha256": sha256_file(args.trace),
              "profiles_sha256": sha256_file(library / "profiles" / "force-profiles.ini"),
              "toolkit": (library / "VERSION").read_text().splitlines(), "passed": False,
              "scope": "zero-order-held motor trace at 4ms; no device output or collision labels"}
    report["steering_impacts"] = args.impacts
    try:
        with open(work / "build.log", "w") as log:
            subprocess.run([str(compiler), "-std=c++11", "-O2", "-Wall", "-Wextra",
                "-I" + str(library / "include"), str(source), "-o", str(exe)],
                env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
        run = subprocess.run([str(exe), str(args.trace.resolve()), str(library / "profiles"),
            args.profile, str(args.strength), str(work / "stages.csv")] + (["--impacts"] if args.impacts else []), env=env,
            capture_output=True, text=True, check=True, timeout=120)
        report["metrics"] = json.loads(run.stdout)
        if args.labels:
            from collision_labels import evaluate
            report["labels_sha256"] = sha256_file(args.labels)
            report["collision_evaluation"] = evaluate(report["metrics"]["events_ms"],
                json.loads(args.labels.read_text(encoding="utf-8")))
            report["scope"] = "offline force algorithms and explicitly labelled coverage; no device output"
        report["passed"] = True
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report["error"] = str(exc)
        if isinstance(exc, subprocess.CalledProcessError):
            report["stderr"] = exc.stderr
    write_json(work / "report.json", report)
    print(("PASS" if report["passed"] else "FAIL") + f": {work / 'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
