"""Analyze saved callback intervals without launching a game or joining clocks."""
import argparse
import csv
import json
import math
from pathlib import Path
import re
import statistics

from verification import sha256_file


def analyze(directory, first, last, threshold_ms=25.0):
    directory = Path(directory)
    if not 2 <= first <= last or not math.isfinite(threshold_ms) or threshold_ms <= 0:
        raise ValueError('invalid callback window or threshold')
    paths = [directory / name for name in ('frames.csv', 'stdout.log', 'invocation.json')]
    for path, limit in zip(paths, (256 << 20, 16 << 20, 1 << 20)):
        if not path.is_file() or path.stat().st_size > limit:
            raise ValueError('missing or oversized evidence: ' + path.name)
    invocation = json.loads(paths[2].read_text(encoding='utf-8'))
    every = int(invocation['environment']['SNAP_EVERY'])
    if every <= 0:
        raise ValueError('invalid snapshot cadence')
    acknowledged = [int(n) for n in re.findall(
        r'^session.lua: snapshot at frame (\d+)\s*$',
        paths[1].read_text(encoding='utf-8'), re.M)]
    samples = []
    previous = None
    count = 0
    with paths[0].open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        if not {'frame', 'emulated_seconds', 'host_seconds'} <= set(reader.fieldnames or ()):
            raise ValueError('missing callback columns')
        for count, row in enumerate(reader, 1):
            if None in row or any(row.get(k) is None for k in ('frame', 'host_seconds', 'emulated_seconds')):
                raise ValueError('incomplete callback row')
            frame = int(row['frame'])
            host, emulated = (float(row[k]) for k in ('host_seconds', 'emulated_seconds'))
            if (count > 500000 or None in row or frame != count or
                    not all(math.isfinite(v) for v in (host, emulated)) or host < 0):
                raise ValueError('invalid or nonconsecutive callback data')
            if previous:
                delta = (host - previous[0]) * 1000
                if delta < 0:
                    raise ValueError('host clock moved backwards')
                if first <= frame <= last:
                    emulated_delta = (emulated - previous[1]) * 1000
                    if emulated_delta <= 0:
                        raise ValueError('window crosses an emulated clock discontinuity')
                    samples.append(dict(frame=frame, host_ms=delta, emulated_ms=emulated_delta))
            previous = (host, emulated)
    if len(samples) != last - first + 1:
        raise ValueError('requested window not fully recorded')
    if acknowledged != list(range(every, count + 1, every)):
        raise ValueError('snapshot acknowledgments disagree with recorded cadence')
    captured = set(acknowledged)

    def summary(rows):
        values = [r['host_ms'] for r in rows]
        return dict(intervals=len(values), over_threshold=sum(v > threshold_ms for v in values),
                    median_ms=statistics.median(values) if values else None,
                    maximum_ms=max(values) if values else None,
                    total_ms=sum(values))

    following = [r for r in samples if r['frame'] - 1 in captured]
    other = [r for r in samples if r['frame'] - 1 not in captured]
    spikes = [dict(r, follows_snapshot=r['frame'] - 1 in captured) for r in samples
              if r['host_ms'] > threshold_ms]
    return dict(passed=True, directory=str(directory.resolve()), first=first, last=last,
                threshold_ms=threshold_ms, snapshot_every=every,
                all_callbacks=summary(samples), after_snapshot=summary(following),
                other_callbacks=summary(other), spikes=spikes[:200],
                omitted_spikes=max(0, len(spikes)-200),
                hashes={p.name: sha256_file(p) for p in paths},
                scope='Callback wall intervals only, not GPU presentation or wheel latency. '
                      'session.lua timestamps before taking a snapshot, so its immediate cost '
                      'falls in the following interval. Association does not establish cause '
                      'or exclude delayed I/O. No native scene-clock join is assumed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--first', required=True, type=int)
    parser.add_argument('--last', required=True, type=int)
    parser.add_argument('--threshold-ms', type=float, default=25.0)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite prior evidence')
    try:
        result = analyze(args.directory, args.first, args.last, args.threshold_ms)
    except (ValueError, OSError, KeyError) as error:
        result = dict(passed=False, error=str(error))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: result[k] for k in ('passed', 'all_callbacks', 'after_snapshot', 'error') if k in result}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
