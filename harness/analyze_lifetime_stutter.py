"""Associate measured Exotica lifetime bursts with nearby recorded callback intervals.

The native phase frame and session callback frame are distinct clocks.  This
reports an observed one-frame adjacency, not an exact causal time join.
"""

import argparse
import csv
import json
import math
from pathlib import Path

from verification import sha256_file


def load_frames(path):
    rows = {}
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "frame" not in reader.fieldnames or "host_seconds" not in reader.fieldnames:
            raise ValueError("missing session frame clock")
        last_frame, last_time = 0, -1.0
        for row in reader:
            frame, when = int(row["frame"]), float(row["host_seconds"])
            if frame != last_frame + 1 or not math.isfinite(when) or when <= last_time:
                raise ValueError("nonconsecutive or nonmonotonic session clock")
            rows[frame] = when
            last_frame, last_time = frame, when
    return rows


def load_lifetime(path):
    phases = {"lifetime_install": {}, "lifetime_complete": {}}
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["frame", "scene", "phase", "microseconds", "units"]:
            raise ValueError("unexpected native timing columns")
        for row in reader:
            phase = row["phase"]
            if phase not in phases:
                continue
            frame, scene, callbacks = int(row["frame"]), int(row["scene"]), int(row["units"])
            us = float(row["microseconds"])
            if frame < 1 or scene < 0 or callbacks < 1 or not math.isfinite(us) or us < 0:
                raise ValueError("invalid lifetime bucket")
            if frame in phases[phase]:
                raise ValueError("duplicate lifetime frame")
            phases[phase][frame] = dict(scene=scene, callbacks=callbacks, microseconds=us)
    if not phases["lifetime_complete"]:
        raise ValueError("no lifetime completion coverage")
    for frame, complete in phases["lifetime_complete"].items():
        install = phases["lifetime_install"].get(frame)
        if not install or (install["scene"], install["callbacks"]) != (complete["scene"], complete["callbacks"]):
            raise ValueError("lifetime install/completion pairing differs")
    if phases["lifetime_install"].keys() != phases["lifetime_complete"].keys():
        raise ValueError("unpaired lifetime install bucket")
    return phases


def analyze(frames, phases, first, last, threshold_ms=25.0, control_frames=None):
    if not 1 < first <= last <= len(frames) or not math.isfinite(threshold_ms) or threshold_ms <= 0:
        raise ValueError("invalid bounded callback interval")
    intervals = {frame: (frames[frame] - frames[frame - 1]) * 1000
                 for frame in range(first, last + 1)}
    event_next = {}
    detail = []
    for frame, complete in sorted(phases["lifetime_complete"].items()):
        if frame < first or frame + 1 > last:
            continue
        install = phases["lifetime_install"][frame]
        event_next[frame + 1] = frame
        detail.append(dict(native_frame=frame, scene=complete["scene"], callbacks=complete["callbacks"],
                           completion_ms=round(complete["microseconds"] / 1000, 4),
                           installation_ms=round(install["microseconds"] / 1000, 4),
                           same_callback_interval_ms=round(intervals[frame], 4),
                           next_callback_interval_ms=round(intervals[frame + 1], 4)))
    if not detail:
        raise ValueError("no complete lifetime event in callback window")
    with_event = [intervals[f] for f in event_next]
    without_event = [ms for f, ms in intervals.items() if f not in event_next]
    result = dict(window=[first, last], threshold_ms=threshold_ms,
                event_buckets=len(detail), callbacks=sum(d["callbacks"] for d in detail),
                completion_total_ms=round(sum(d["completion_ms"] for d in detail), 4),
                installation_total_ms=round(sum(d["installation_ms"] for d in detail), 4),
                next_callback_over_threshold=sum(ms > threshold_ms for ms in with_event),
                other_callback_over_threshold=sum(ms > threshold_ms for ms in without_event),
                next_callback_max_ms=round(max(with_event), 4),
                other_callback_max_ms=round(max(without_event), 4),
                details=detail,
                interpretation="One-frame adjacency across distinct clocks; no per-callback latency or causal attribution")
    if control_frames is not None:
        if last > len(control_frames):
            raise ValueError("control callback window incomplete")
        control_intervals = {frame: (control_frames[frame] - control_frames[frame - 1]) * 1000
                             for frame in range(first, last + 1)}
        result["control_same_ordinal"] = dict(
            next_callback_over_threshold=sum(control_intervals[f] > threshold_ms for f in event_next),
            other_callback_over_threshold=sum(ms > threshold_ms for f, ms in control_intervals.items() if f not in event_next),
            event_next_intervals_ms=[round(control_intervals[f], 4) for f in event_next],
            scope="Same recorded frame ordinals only; display size and host load may differ")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--first", type=int, default=3700)
    parser.add_argument("--last", type=int, default=5690)
    parser.add_argument("--control-frames", type=Path, help="older same-input callback trace for ordinal association only")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    frames = args.run / "frames.csv"
    timing = args.run / "exotica-host-timing.csv"
    if args.output.exists():
        parser.error("output already exists")
    control = load_frames(args.control_frames) if args.control_frames else None
    result = analyze(load_frames(frames), load_lifetime(timing), args.first, args.last, control_frames=control)
    hashes = {name: sha256_file(path) for name, path in (("frames.csv", frames), ("exotica-host-timing.csv", timing))}
    if args.control_frames:
        hashes["control-frames.csv"] = sha256_file(args.control_frames)
    result.update(source_hashes=hashes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "details"}, indent=2))


if __name__ == "__main__":
    main()
