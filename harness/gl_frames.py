"""Compare completed GL frames; asynchronous legacy captures are not frame oracles."""
import argparse
import csv
from pathlib import Path
import sys

from verification import image_signature, write_json


def read_completed_frames(directory, expected=None):
    directory = Path(directory)
    with (directory / "captures.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows or "completed_frame" not in rows[0]:
        raise ValueError("completed-frame GL captures required; legacy asynchronous images are insufficient")
    frames, previous = {}, -1
    for row in rows:
        frame = int(row["completed_frame"])
        if frame <= previous or frame != int(row["last_received_frame"]):
            raise ValueError("GL frame fences are duplicated, unordered or inconsistent")
        if int(row["dropped_messages"]) != 0:
            raise ValueError("GL stream lost persistent rendering state")
        name = row["file"]
        if Path(name).name != name or name in ("", ".", ".."):
            raise ValueError("GL capture filename must be local to its directory")
        signature = image_signature(directory / name)
        if signature["size"] != [int(row["width"]), int(row["height"])]:
            raise ValueError("GL image dimensions differ from the capture receipt")
        frames[frame] = signature
        previous = frame
    if expected is not None and list(frames) != list(expected):
        raise ValueError("completed GL capture interval is incomplete")
    return frames


def compare_completed_frames(reference, candidate, expected=None):
    a, b = read_completed_frames(reference, expected), read_completed_frames(candidate, expected)
    if a.keys() != b.keys():
        raise ValueError("GL recordings cover different completed frames")
    different = [n for n in a if a[n] != b[n]]
    return {"scope": "completed GL frame pixels", "passed": not different,
            "frames": len(a), "different_frames": different}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("reference", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--frames", help="required inclusive FIRST:LAST consecutive interval")
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args(argv)
    result = {"passed": False}
    try:
        expected = None
        if args.frames:
            first, last = map(int, args.frames.split(":"))
            if not 0 <= first <= last:
                raise ValueError("invalid frame interval")
            expected = range(first, last + 1)
        result = compare_completed_frames(args.reference, args.candidate, expected)
    except (ValueError, OSError, KeyError) as exc:
        result["error"] = str(exc)
    write_json(args.report, result)
    print(("PASS" if result["passed"] else "FAIL") + f": {args.report}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
