"""Capture V-Unit quads, RAM and a native snapshot without overwriting evidence.

The RAM dump precedes the named snapshot by two frames, as in the original
harness. Renderer acceptance compares to the RAM dump, not that later PNG.
"""
import argparse
import shutil
import sys

from diagnostic_runtime import new_run
from run_oracle import DEFAULT_MAME, DEFAULT_ROMPATH, capture_run
from verification import required_files, sha256_file, write_json

ARTIFACTS = ("quads.bin", "videoram.bin", "textureram.bin", "paletteram.bin", "meta.txt")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mame", nargs="?", default=DEFAULT_MAME)
    ap.add_argument("frame", nargs="?", type=int, default=2400)
    ap.add_argument("rom", nargs="?", default="crusnusa")
    ap.add_argument("--rompath", default=DEFAULT_ROMPATH)
    ap.add_argument("--output", help="new capture directory (must not exist)")
    ap.add_argument("--timeout", type=float, default=900)
    args = ap.parse_args(argv)
    if args.frame < 3 or args.timeout <= 0:
        ap.error("frame must be at least 3 and timeout must be positive")
    try:
        cap = new_run("capture", args.output)
    except OSError as exc:
        ap.error(str(exc))
    args.frames = str(args.frame)
    args.max_seconds = args.frame // 57 + 30
    report = {"schema": 1, "rom": args.rom, "snapshot_frame": args.frame,
              "requested_dump_frame": args.frame - 2, "passed": False}
    print(f"capture evidence: {cap}")
    try:
        report["snapshots"] = capture_run(cap / "run", args, {
            "MIDV_QUADLOG": str(cap / "quads.bin"),
            "MIDV_STATEDUMP_FRAME": str(args.frame - 2),
            "MIDV_STATEDUMP_DIR": str(cap)})
        required_files(cap, ARTIFACTS)
        report["artifacts"] = {n: {"bytes": (cap / n).stat().st_size,
                                     "sha256": sha256_file(cap / n)} for n in ARTIFACTS}
        for shot in (cap / "run" / "snap").glob("*.png"):
            shutil.copy2(shot, cap / f"mame-snapshot-{shot.name}")
        report["passed"] = True
    except (ValueError, OSError) as exc:
        report["error"] = str(exc)
    write_json(cap / "capture-report.json", report)
    print(("PASS" if report["passed"] else "FAIL") + f": {cap / 'capture-report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
