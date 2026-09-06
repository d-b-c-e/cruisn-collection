"""Map emulated-time force candidates to the first completed game frame."""
import bisect
import csv
import math


def event_frames(events_ms, frames_path):
    with open(frames_path, newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if not {"frame", "emulated_seconds"}.issubset(reader.fieldnames or []):
            raise ValueError("frames.csv requires frame and emulated_seconds columns")
        rows = list(reader)
    frames = [int(row["frame"]) for row in rows]
    times = [float(row["emulated_seconds"]) * 1000 for row in rows]
    if not times or any(not math.isfinite(t) or t < 0 for t in times):
        raise ValueError("invalid emulated frame clock")
    if frames != list(range(1, len(frames) + 1)) or any(a >= b for a, b in zip(times, times[1:])):
        raise ValueError("frame trace must be contiguous with increasing emulated time")
    result = []
    for event in events_ms:
        if not math.isfinite(event) or event < 0:
            raise ValueError("invalid candidate time")
        index = bisect.bisect_left(times, event)
        result.append({"emulated_ms": event,
                       "first_completed_frame": frames[index] if index < len(frames) else None,
                       "classification": "unlabelled force-rise candidate"})
    return result
