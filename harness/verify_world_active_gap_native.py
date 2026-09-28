"""Verify an opt-in World active-margin scene against a source-matched control.

This compares standalone ordered scene words, not MAME completed pixels.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    lines = path.read_text(encoding='utf-8').splitlines()
    if not lines:
        raise ValueError('empty native scene')
    stats = tuple(int(v) for v in lines[0].split())
    if len(stats) != 7:
        raise ValueError('invalid future scene header')
    rows = [tuple(int(v) for v in line.split()) for line in lines[1:]]
    if any(len(row) != 24 for row in rows):
        raise ValueError('expected far-coverage scene rows')
    return stats, rows


def verify(control_path, trial_path, projection_path):
    projection = json.loads(projection_path.read_text(encoding='utf-8'))
    if (not projection['baseline_qualified'] or projection['source_kind'] !=
            'scene-boundary Lua read tap'):
        raise ValueError('source-time projection is not qualified')
    control_header, control = load(control_path)
    trial_header, trial = load(trial_path)
    if control_header != trial_header:
        raise ValueError('future source collection changed between trials')
    remaining = Counter(control)
    extra = []
    retained = []
    for row in trial:
        if remaining[row]:
            remaining[row] -= 1
            retained.append(row)
        else:
            extra.append(row)
    if any(remaining.values()) or retained != control:
        raise ValueError('previous native scene words or order changed')
    if any(row[0] & 0xc0000000 != 0xc0000000 for row in extra):
        raise ValueError('new native quads lack active-list ownership')
    expected = {(0xc0000000 | int(hit['object'], 16), tuple(hit['quad_words']))
                for probe in projection['probes'] for hit in probe['projected_box_hits']
                if not hit['exact_original_dma'] and not hit['exact_host_packet']
                and hit['stock_horizontal_rejected']}
    added = {(row[0], tuple(row[4:20])) for row in extra}
    if not expected or not expected <= added:
        raise ValueError('source-qualified absent quads are missing in native trial')
    return {'passed': True,
            'scope': 'Offline native scene output preserves every prior quad/order and includes '
                     'source-qualified horizontally culled candidates. No completed pixels or '
                     'cross-frame renderer acceptance.',
            'source_frame': projection['source_frame'],
            'future_header': list(control_header),
            'control_quads': len(control), 'trial_quads': len(trial),
            'added_active_quads': len(extra),
            'added_active_objects': len({row[0] for row in extra}),
            'source_qualified_gap_quads': len(expected),
            'source_qualified_gap_quads_recovered': len(expected & added),
            'sha256': {'control': sha(control_path), 'trial': sha(trial_path),
                       'projection': sha(projection_path)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--trial', type=Path, required=True)
    parser.add_argument('--projection', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite native comparison evidence')
    result = verify(args.control, args.trial, args.projection)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('PASS', result['control_quads'], result['trial_quads'],
          result['source_qualified_gap_quads_recovered'])


if __name__ == '__main__':
    main()
