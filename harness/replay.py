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
import shutil

from diagnostic_runtime import execute, new_run, ROOT
from raw_snapshots import convert_raw_snapshots
from run_capture import ARTIFACTS
from session_case import compare_evidence, prepare_run, session_evidence, tree_hashes, set_option
from verification import sha256_file, write_json, required_files


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case", type=Path)
    ap.add_argument("--output", help="new evidence directory (must not exist)")
    ap.add_argument("--headless", action="store_true", help="native snapshots, no GL presentation")
    ap.add_argument("--candidate", type=Path, help="explicit candidate executable for regression experiments")
    ap.add_argument("--timeout", type=float, default=900)
    ap.add_argument("--gl-capture", help="capture live V-Unit GL backbuffers over FIRST:LAST stream frames")
    ap.add_argument("--gl-every", type=int, default=150, help="present interval between GL captures")
    ap.add_argument("--gl-max", type=int, default=120, help="maximum GL BMPs retained")
    ap.add_argument("--gl-log", action="store_true", help="enable live renderer diagnostic log")
    ap.add_argument("--gl-scale", type=int, help="explicit internal-scale experiment, 1..6")
    ap.add_argument("--no-crackfill", action="store_true", help="explicit experiment with crack filling disabled")
    ap.add_argument("--video", choices=("gdi", "d3d", "bgfx"), help="explicit underlying MAME video-backend experiment")
    ap.add_argument("--native-renderer", action="store_true", help="windowed control with replacement GL disabled")
    ap.add_argument("--snapshot-mode", choices=("png", "raw"), help="explicit capture experiment; raw defers PNG encoding until exit")
    ap.add_argument("--until-frame", type=int, help="explicit prefix replay ending at this frame")
    ap.add_argument("--capture-state", action="store_true", help="capture quads/RAM two frames before --until-frame")
    args = ap.parse_args(argv)
    if args.timeout <= 0:
        ap.error("timeout must be positive")
    if args.gl_every < 1 or args.gl_max < 1 or (args.gl_scale is not None and not 1 <= args.gl_scale <= 6):
        ap.error("GL intervals/budget must be positive and scale must be 1..6")
    gl_experiment = args.gl_capture or args.gl_log or args.gl_scale is not None or args.no_crackfill
    if args.headless and (gl_experiment or args.video or args.native_renderer):
        ap.error("live GL diagnostics cannot be combined with --headless")
    if args.native_renderer and gl_experiment:
        ap.error("native renderer control cannot enable GL diagnostics")
    if args.capture_state and (args.until_frame is None or args.until_frame < 3):
        ap.error("state capture requires --until-frame of at least 3")
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
        if args.until_frame is not None:
            if not manifest["every"] <= args.until_frame <= reference["frames"]:
                raise ValueError("prefix must include a snapshot and end within the recording")
            reference = dict(reference, frames=args.until_frame,
                snapshots={n: v for n, v in reference["snapshots"].items() if int(n) <= args.until_frame})
            manifest["evidence"] = dict(manifest["evidence"], frames=args.until_frame)
            report["comparison_scope"] = {"first_frame": 1, "last_frame": args.until_frame,
                                          "kind": "explicit-prefix"}
        if gl_experiment:
            if manifest["settings"].get("MIDV_GL") != "1":
                raise ValueError("live V-Unit GL diagnostics require a recording made with MIDV_GL=1")
            overrides = {}
            if args.gl_capture:
                first, last = map(int, args.gl_capture.split(":"))
                if not 0 <= first < last <= reference["frames"]:
                    raise ValueError("GL interval must be within the recorded frames")
                overrides.update(MIDV_GL_SNAP="redirect-at-launch", MIDV_GL_SNAP_FIRST=str(first),
                    MIDV_GL_SNAP_LAST=str(last), MIDV_GL_SNAP_EVERY=str(args.gl_every),
                    MIDV_GL_SNAP_MAX=str(args.gl_max))
            if args.gl_log:
                overrides["MIDV_GL_LOG"] = "1"
            if args.gl_scale is not None:
                overrides["MIDV_GL_SCALE"] = str(args.gl_scale)
            if args.no_crackfill:
                overrides["MIDV_GL_CRACKFILL"] = "0"
            manifest["settings"].update(overrides)
            report["presentation_overrides"] = overrides
            report["presentation"] = "explicit-gl-experiment"
        if args.candidate:
            manifest["command"][0] = str(args.candidate.resolve())
        if args.snapshot_mode:
            manifest["snapshot_mode"] = args.snapshot_mode
            report["snapshot_mode_override"] = args.snapshot_mode
        runtime = work / "run"
        command, env = prepare_run(case, manifest, runtime, playback=True, headless=args.headless)
        if args.snapshot_mode:
            shutil.copy2(ROOT / "lua" / "session.lua", runtime / "session.lua")
            report["diagnostic_script_sha256"] = sha256_file(runtime / "session.lua")
        if args.video:
            command = set_option(command, "-video", args.video)
            report["video_override"] = args.video
        if args.native_renderer:
            for key in ("MIDV_GL", "MIDV_LIVE", "MIDZ_GL"):
                env.pop(key, None)
            report["presentation"] = "native-window-control"
            command += ["-keepaspect"]
        if args.capture_state:
            capture = runtime / "capture"
            capture.mkdir()
            env.update(MIDV_QUADLOG=str(capture / "quads.bin"),
                       MIDV_STATEDUMP_FRAME=str(args.until_frame - 2), MIDV_STATEDUMP_DIR=str(capture))
        invocation = execute(command, runtime, env, args.timeout)
        # Recording uses the product launch log; normalize the replay's stdout
        # path so the same strict evidence validator serves both paths.
        if (runtime / "stdout.log").exists():
            (runtime / "launch.log").write_bytes((runtime / "stdout.log").read_bytes())
        if invocation["error"]:
            raise ValueError(invocation["error"])
        convert_raw_snapshots(runtime)
        report["evidence"] = session_evidence(runtime, manifest["every"], invocation["returncode"],
            require_gl=not (args.headless or args.native_renderer) and bool(manifest["settings"].get("MIDV_GL_SNAP")))
        report["comparison"] = compare_evidence(case / "record", runtime, reference, report["evidence"])
        report["passed"] = report["comparison"]["passed"]
        if args.capture_state:
            required_files(capture, ARTIFACTS)
            report["capture"] = {"directory": str(capture), "requested_dump_frame": args.until_frame - 2,
                                 "sha256": {n: sha256_file(capture / n) for n in ARTIFACTS}}
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        report["passed"] = False
        report["error"] = str(exc)
    write_json(work / "report.json", report)
    print(("PASS" if report["passed"] else "FAIL") + f": {work / 'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
