"""Compare same-frame object-attributed DMA traces, preserving duplicates/order.

This checks submitted geometry, not visible pixels or route equivalence. Use on
matched-state intervals and pair with completed GL captures and motion traces.
"""
import argparse
from collections import Counter, defaultdict, deque
from bisect import bisect_left, insort
import csv
import json
from pathlib import Path

FIELDS = ('pc', 'page', 'object', 'model', 'matched', 'flags', 'palette',
          'x0', 'y0', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3',
          'uv0', 'uv1', 'uv2', 'uv3', 'texture', 'word15')
HEX = {'pc', 'object', 'model'}


def load(path):
    frames = defaultdict(list)
    previous = -1
    with open(path, newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['frame', *FIELDS]:
            raise ValueError(f'{path}: unexpected scenery trace columns')
        for line, row in enumerate(reader, 2):
            try:
                if None in row:
                    raise ValueError('extra columns')
                frame = int(row['frame'])
                values = tuple(int(row[k], 16 if k in HEX else 10) for k in FIELDS)
                if frame < previous or frame < 0 or min(values) < 0:
                    raise ValueError('negative value or frame order')
                if values[4] not in (0, 1) or bool(values[3]) != bool(values[4]):
                    raise ValueError('invalid matched/model attribution')
                if any(v > 65535 for v in values[5:]):
                    raise ValueError('DMA words must be unsigned 16-bit')
            except (ValueError, TypeError) as error:
                raise ValueError(f'{path}:{line}: malformed scenery row: {error}') from error
            frames[frame].append(values)
            previous = frame
    if not frames:
        raise ValueError(f'{path}: empty scenery trace')
    return frames


def additions(rows):
    groups = defaultdict(list)
    for row, count in rows.items():
        groups[row[3]].extend([row] * count)
    result = []
    for model, group in sorted(groups.items()):
        xs = [r[k]-65536 if r[k] >= 32768 else r[k] for r in group for k in (7, 9, 11, 13)]
        ys = [r[k]-65536 if r[k] >= 32768 else r[k] for r in group for k in (8, 10, 12, 14)]
        result.append({'model': f'{model:x}', 'quads': len(group),
                       'objects': sorted({f'{r[2]:x}' for r in group}),
                       'bounds': [min(xs), min(ys), max(xs), max(ys)]})
    return result


def completed_scenes(frames):
    """Nonempty consecutive page-control runs; discard both partial edges."""
    runs = []
    for frame, rows in sorted(frames.items()):
        for row in rows:
            if not runs or runs[-1]['page'] != row[1]:
                runs.append({'page': row[1], 'first_frame': frame,
                             'last_frame': frame, 'rows': []})
            runs[-1]['rows'].append(row)
            runs[-1]['last_frame'] = frame
    if len(runs) < 3:
        raise ValueError('need at least one completed page-control run between partial edges')
    return runs[1:-1]


def compare_scenes(control, candidate, allowed, max_added_extent=None, order_details=False):
    a, b = completed_scenes(control), completed_scenes(candidate)
    if len(a) != len(b) or [r['page'] for r in a] != [r['page'] for r in b]:
        raise ValueError('completed page-control run sequences differ; cannot align scenes')
    report = compare({i: r['rows'] for i, r in enumerate(a)},
                     {i: r['rows'] for i, r in enumerate(b)}, allowed, max_added_extent, order_details)
    report['scope'] = ('completed page-control run geometry; frame timing differences retained; '
                       'not visible-pixel, presentation-timing or route acceptance')
    report['alignment'] = 'scene'
    report['discarded_edge_runs_per_trace'] = 2
    report['scenes'] = report.pop('frames')
    for row, original, revised in zip(report['scenes'], a, b):
        row['scene'] = row.pop('frame')
        row['page'] = original['page']
        row['control_frames'] = [original['first_frame'], original['last_frame']]
        row['candidate_frames'] = [revised['first_frame'], revised['last_frame']]
    return report


def reordering_bounds(original, candidate, padding=2):
    """Describe inversions without relaxing the strict order acceptance gate.

    Bounds cannot establish texture/palette write ordering or visible correctness.
    Duplicate draws use a stable occurrence matching, not inferred object lifetime.
    """
    occurrences = defaultdict(deque)
    for i, row in enumerate(original):
        occurrences[row].append(i)
    indices = []
    for row in candidate:
        if occurrences[row]:
            indices.append(occurrences[row].popleft())
    if len(indices) != len(original):
        return {'checked': False, 'reason': 'original geometry is missing or changed'}
    bounds = [additions(Counter({row: 1}))[0]['bounds'] for row in original]
    seen, count, overlapping, examples = [], 0, 0, []
    for i in indices:
        for j in seen[bisect_left(seen, i):]:
            count += 1
            a, b = bounds[i], bounds[j]
            same_page = (original[i][1] & 4) == (original[j][1] & 4)
            overlaps = same_page and not (a[2]+padding < b[0]-padding
                or b[2]+padding < a[0]-padding or a[3]+padding < b[1]-padding
                or b[3]+padding < a[1]-padding)
            overlapping += int(overlaps)
            if len(examples) < 12:
                examples.append({'original_indices': [i, j], 'bounds': [a, b],
                    'models': [f'{original[k][3]:x}' for k in (i, j)],
                    'possibly_overlapping': bool(overlaps)})
        insort(seen, i)
    return {'checked': True, 'inverted_pairs': count, 'possibly_overlapping_pairs': overlapping,
            'padding_native_pixels': padding, 'examples': examples,
            'scope': 'stable occurrence matching and padded bounds only; strict order failure remains'}


def compare(control, candidate, allowed, max_added_extent=None, order_details=False):
    if set(control) != set(candidate):
        raise ValueError('trace frame sets differ; use matched intervals')
    rows = []
    for frame in sorted(control):
        a, b = control[frame], candidate[frame]
        removed, added = Counter(a)-Counter(b), Counter(b)-Counter(a)
        cursor = iter(b)
        ordered = all(any(original == item for item in cursor) for original in a)
        unexpected = sum(n for r, n in added.items() if not r[4] or r[3] not in allowed)
        oversized = 0
        if max_added_extent is not None:
            for row, count in added.items():
                x0,y0,x1,y1=additions(Counter({row:1}))[0]['bounds']
                if max(x1-x0,y1-y0)>max_added_extent:
                    oversized += count
        rows.append({'frame': frame, 'control_quads': len(a), 'candidate_quads': len(b),
                     'removed_or_changed': sum(removed.values()), 'added': sum(added.values()),
                     'originals_in_order': ordered, 'unexpected_additions': unexpected,
                     'oversized_additions': oversized,
                     'added_models': additions(added)})
        if order_details and not ordered:
            rows[-1]['reordering_bounds'] = reordering_bounds(a, b)
    return {'schema': 1, 'scope': 'matched-frame submitted geometry; not visible-pixel or route acceptance',
            'passed': all(not r['removed_or_changed'] and r['originals_in_order']
                          and not r['unexpected_additions'] and not r['oversized_additions'] for r in rows),
            'maximum_added_quad_extent': max_added_extent,
            'allowed_added_models': sorted(f'{m:x}' for m in allowed),
            'frames': rows, 'total_added': sum(r['added'] for r in rows),
            'total_removed_or_changed': sum(r['removed_or_changed'] for r in rows)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('control', type=Path)
    ap.add_argument('candidate', type=Path)
    ap.add_argument('--allow-added-model', action='append', default=[], type=lambda s: int(s, 16))
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--max-added-extent', type=int, help='optional native-pixel width/height bound for each new quad')
    ap.add_argument('--alignment', choices=('frame', 'scene'), default='frame',
                    help='scene compares complete nonempty page-control runs and reports their frame ranges')
    ap.add_argument('--order-details', action='store_true',
                    help='locate reordered polygon pairs; does not relax the strict order gate')
    args = ap.parse_args()
    try:
        if args.max_added_extent is not None and args.max_added_extent < 1:
            raise ValueError('added extent must be positive')
        comparer = compare_scenes if args.alignment == 'scene' else compare
        report = comparer(load(args.control), load(args.candidate), set(args.allow_added_model),
                          args.max_added_extent, args.order_details)
    except (OSError, ValueError) as error:
        report = {'schema': 1, 'passed': False, 'error': str(error)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('PASS' if report['passed'] else 'FAIL', args.report)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
