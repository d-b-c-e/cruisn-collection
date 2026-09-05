"""Summarize input coverage and emulation timing over a selected frame interval."""
import argparse
from pathlib import Path
import sys

import numpy as np
from session_case import read_trace
from verification import write_json


def summarize(directory, first=1, last=None):
    fields, all_rows = read_trace(Path(directory) / "frames.csv")
    last = len(all_rows) if last is None else last
    if not 1 <= first < last <= len(all_rows):
        raise ValueError("interval must contain at least two recorded frames")
    rows = all_rows[first - 1:last]
    host = np.array([float(r["host_seconds"]) for r in rows])
    emu = np.array([float(r["emulated_seconds"]) for r in rows])
    if not np.isfinite(host).all() or np.any(np.diff(host) <= 0):
        raise ValueError("host timestamps must be finite and strictly increasing")
    dt = np.diff(host) * 1000
    return {"schema": 1, "first_frame": first, "last_frame": last,
            "scope": "MAME frame callback timing; not GPU present latency or physical FFB latency",
            "emulated_seconds": float(emu[-1] - emu[0]),
            "host_seconds": float(host[-1] - host[0]),
            "emulation_ratio": float((emu[-1] - emu[0]) / (host[-1] - host[0])),
            "host_frame_ms": {"p50": float(np.percentile(dt, 50)), "p95": float(np.percentile(dt, 95)),
                              "p99": float(np.percentile(dt, 99)), "worst": float(dt.max())},
            "inputs": {f: {"minimum": min(int(r[f]) for r in rows),
                           "maximum": max(int(r[f]) for r in rows),
                           "distinct": len({r[f] for r in rows})} for f in fields[4:]}}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run", type=Path)
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    try:
        report = summarize(args.run, args.first, args.last)
    except (ValueError, OSError) as exc:
        ap.error(str(exc))
    write_json(args.report, report)
    print(f"frame interval {args.first}..{report['last_frame']}: "
          f"{report['emulation_ratio'] * 100:.2f}% emulation speed; report {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
