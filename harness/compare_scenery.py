"""Compare same-frame object-attributed DMA traces, preserving duplicates/order.

This checks submitted geometry, not visible pixels or route equivalence. Use on
matched-state intervals and pair with completed GL captures and motion traces.
"""
import argparse
from collections import Counter, defaultdict
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


def compare(control, candidate, allowed, max_added_extent=None):
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
    args = ap.parse_args()
    try:
        if args.max_added_extent is not None and args.max_added_extent < 1:
            raise ValueError('added extent must be positive')
        report = compare(load(args.control), load(args.candidate), set(args.allow_added_model), args.max_added_extent)
    except (OSError, ValueError) as error:
        report = {'schema': 1, 'passed': False, 'error': str(error)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('PASS' if report['passed'] else 'FAIL', args.report)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
