"""Exercise the V-Unit pause menu on recorded inputs, with physical output off.

The explicit emulator diagnostic drives the real menu key handler, captures its
states separately from game frames, resumes, then requests a clean menu exit.
"""
import argparse
import json
from pathlib import Path
import re

import numpy as np
from PIL import Image

from diagnostic_runtime import execute, new_run
from session_case import prepare_run, set_option, tree_hashes
from verification import sha256_file, write_json


def inspect(directory):
    directory = Path(directory)
    log = (directory / "midv_gl.log").read_text(errors="replace")
    pattern = (r"menu snapshot step=(\d+) open=(\d+) selected=(\d+) crt=(\d+) "
               r"completed_frame=(\d+) new_frame=(\d+)")
    rows = [dict(zip(("step", "open", "selected", "crt", "frame", "new_frame"), map(int, m)))
            for m in re.findall(pattern, log)]
    if [r["step"] for r in rows] != list(range(9)):
        raise ValueError("missing menu redraws while emulation is paused")
    states = [(r["open"], r["selected"]) for r in rows]
    if states != [(1, 0), (1, 1), (1, 1), (1, 0), (0, 0), (1, 0), (1, 1), (1, 2), (1, 3)]:
        raise ValueError("menu navigation/resume state mismatch")
    if rows[0]["crt"] != rows[1]["crt"] or rows[2]["crt"] == rows[1]["crt"]:
        raise ValueError("CRT toggle failed while paused")
    if len({r["frame"] for r in rows[1:4]}) != 1 or rows[5]["frame"] <= rows[3]["frame"]:
        raise ValueError("pause/resume did not stop/restart completed game frames")
    for row in rows:
        path = directory / "gl-snap" / f"menu_{row['step']:02d}.bmp"
        pixels = np.array(Image.open(path).convert("RGB"))
        gold = (pixels[:, :, 0] > 220) & (pixels[:, :, 1] > 120) & (pixels[:, :, 1] < 215) & (pixels[:, :, 2] < 90)
        if row["open"] and int(gold.sum()) < 500:
            raise ValueError(f"menu text not visibly rendered at step {row['step']}")
        row["image_sha256"] = sha256_file(path)
    if rows[0]["image_sha256"] == rows[1]["image_sha256"]:
        raise ValueError("selection change did not redraw the menu")
    if "menu test step=9" not in log or "machine exit" not in log:
        raise ValueError("menu exit did not complete cleanly")
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case", type=Path)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--frame", type=int, default=1800)
    ap.add_argument("--output")
    ap.add_argument("--timeout", type=float, default=120)
    args = ap.parse_args(argv)
    work = new_run("menu-check", args.output)
    report = {"passed": False, "physical_force": False, "frame": args.frame}
    try:
        manifest = json.loads((args.case / "case.json").read_text())
        if manifest.get("status") != "recorded" or manifest.get("rom") == "crusnexo":
            raise ValueError("completed V-Unit case required")
        if not 1 <= args.frame < manifest["evidence"]["frames"] - 120:
            raise ValueError("menu test must start within the recording")
        if tree_hashes(args.case / "initial") != manifest["initial_hashes"]:
            raise ValueError("recording initial state changed")
        if sha256_file(args.case / "record/input/session.inp") != manifest["inp_sha256"]:
            raise ValueError("recording inputs changed")
        runtime = work / "run"
        cmd, env = prepare_run(args.case.resolve(), manifest, runtime, playback=True)
        cmd[0] = str(args.candidate.resolve())
        for key, value in (("-sound", "none"), ("-video", "d3d"), ("-resolution", "1280x720")):
            cmd = set_option(cmd, key, value)
        cmd += ["-window", "-nomaximize", "-throttle"]
        (runtime / "gl-snap").mkdir(exist_ok=True)
        env.update(MIDV_GL="1", MIDV_FFB="0", MIDV_GL_LOG="1",
                   MIDV_GL_MENU_TEST_FRAME=str(args.frame), MIDV_GL_SNAP=str(runtime / "gl-snap"),
                   MIDV_GL_SNAP_EVERY="2147483647")
        result = execute(cmd, runtime, env, args.timeout)
        if result["returncode"] != 0 or result["error"]:
            raise ValueError(f"emulator failed: {result}")
        report["states"] = inspect(runtime)
        report["passed"] = True
    except (OSError, ValueError, KeyError) as exc:
        report["error"] = str(exc)
    write_json(work / "report.json", report)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
