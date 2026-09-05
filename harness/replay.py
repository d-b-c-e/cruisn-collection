"""Replay a recorded driving case with physical outputs disabled.

Uses the same executable by default. --candidate explicitly permits a changed
binary for experiments; that report is a regression comparison, not an identity
replay. Every run keeps its input/time comparison, frame timings and snapshots.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from diagnostic_runtime import execute, new_run
from session_case import compare_evidence, prepare_run, session_evidence, tree_hashes
from verification import sha256_file, write_json


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case", type=Path)
    ap.add_argument("--output", help="new evidence directory (must not exist)")
    ap.add_argument("--headless", action="store_true", help="native snapshots, no GL presentation")
    ap.add_argument("--candidate", type=Path, help="explicit candidate executable for regression experiments")
    ap.add_argument("--timeout", type=float, default=900)
    args = ap.parse_args(argv)
    if args.timeout <= 0:
        ap.error("timeout must be positive")
    try:
        work = new_run("replay", args.output)
    except OSError as exc:
        ap.error(str(exc))
    report = {"schema": 1, "kind": "candidate-regression" if args.candidate else "identity-replay",
              "case": str(args.case.resolve()), "passed": False,
              "presentation": "native-headless" if args.headless else "recorded-settings"}
    print(f"replay evidence: {work}")
    try:
        case = args.case.resolve()
        manifest = json.loads((case / "case.json").read_text(encoding="utf-8"))
        if manifest.get("schema") != 1 or manifest.get("status") != "recorded":
            raise ValueError("case is not a completed schema-1 recording")
        if tree_hashes(case / "initial") != manifest["initial_hashes"]:
            raise ValueError("initial configuration has changed since recording")
        if sha256_file(case / "record" / "input" / "session.inp") != manifest["inp_sha256"]:
            raise ValueError("input recording has changed")
        for name, digest in manifest["dependencies"].items():
            if sha256_file(case / "binary" / name) != digest:
                raise ValueError(f"archived binary dependency has changed: {name}")
        for path, digest in manifest["rom_containers"].items():
            if sha256_file(path) != digest:
                raise ValueError(f"recording dependency has changed: {path}")
        reference = session_evidence(case / "record", manifest["every"], manifest["returncode"])
        if reference != manifest["evidence"]:
            raise ValueError("reference evidence has changed")
        if args.candidate:
            manifest["command"][0] = str(args.candidate.resolve())
        runtime = work / "run"
        command, env = prepare_run(case, manifest, runtime, playback=True, headless=args.headless)
        invocation = execute(command, runtime, env, args.timeout)
        # Recording uses the product launch log; normalize the replay's stdout
        # path so the same strict evidence validator serves both paths.
        if (runtime / "stdout.log").exists():
            (runtime / "launch.log").write_bytes((runtime / "stdout.log").read_bytes())
        if invocation["error"]:
            raise ValueError(invocation["error"])
        report["evidence"] = session_evidence(runtime, manifest["every"], invocation["returncode"],
            require_gl=not args.headless and bool(manifest["settings"].get("MIDV_GL_SNAP")))
        report["comparison"] = compare_evidence(case / "record", runtime, reference, report["evidence"])
        report["passed"] = report["comparison"]["passed"]
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        report["error"] = str(exc)
    write_json(work / "report.json", report)
    print(("PASS" if report["passed"] else "FAIL") + f": {work / 'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
