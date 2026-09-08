"""Compare independently reconstructed World projections with read-only captures."""
import argparse
import collections
import csv
import json
from pathlib import Path
import struct

from scenery_c31 import F
from world_host_scenery import camera_center, rotation_matrix, project, fast_quads
from verification import sha256_file, write_json

DMA_KEYS = ('flags', 'palette', 'x0', 'y0', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3',
            'uv0', 'uv1', 'uv2', 'uv3', 'texture')


def verify(run):
    run = Path(run)
    names = ['world-transform.jsonl', 'world-transform-draws.csv',
             'world-transform-reciprocals.bin', 'world-transform-summary.json']
    hashes = {name: sha256_file(run/name) for name in names}
    summary = json.loads((run/names[-1]).read_text())
    records = [json.loads(line) for line in (run/names[0]).read_text().splitlines()]
    recip = dict(zip(range(-80, 5000), struct.unpack('<5080I', (run/names[2]).read_bytes())))
    draws = collections.defaultdict(list)
    for row in csv.DictReader((run/names[1]).open()):
        draws[int(row['call'])].append([int(row[k]) for k in DMA_KEYS])
    counts = collections.Counter()
    failures = []
    seen = set()
    comparisons = []

    def check(kind, actual, expected, call):
        counts[kind+'_checked'] += 1
        counts[kind+'_passed'] += actual == expected
        if actual != expected:
            failures.append({'call': call, 'kind': kind})

    for r in records:
        call = r['call']
        if call in seen:
            raise ValueError('duplicate transform call')
        seen.add(call)
        counts['vertices'] += r['vertices']
        center = camera_center(r['object_words'], r['camera'], r['view'])
        check('center', [x.store() for x in center], r['camera_space'][:3], call)
        if r['object_words'][14] & 8:
            # Shared billboard camera basis is an adapter input, not per-object
            # projected geometry. Capturing it is analogous to capturing view.
            matrix = list(map(F.load, r['matrix']))
            counts['billboard_basis_inputs'] += 1
        else:
            matrix = rotation_matrix(r['object_words'], r['view'])
            check('rotation', [x.store() for x in matrix], r['matrix'], call)
        projected = project(r, recip, center=center, matrix=matrix)
        check('projection', projected, r['projected'], call)
        if r['end_pc'] == 0x242:
            quads = fast_quads(r, projected)
            check('ordered_dma', quads, draws[call], call)
            counts['quads'] += len(quads)
        else:
            counts['clipped_calls_excluded'] += 1
            counts['clipped_quads_excluded'] += len(draws[call])
        comparisons.append({'call': call, 'frame': r['frame'], 'object': r['object'],
            'model': r['model'], 'vertices': r['vertices'], 'quads': len(draws[call]),
            'projection_passed': projected == r['projected']})
    if (not records or len(records) != summary['projected'] or summary['starts'] != len(records)
            or sum(map(len, draws.values())) != summary['draws']
            or len(draws[0]) != summary['unmatched_draws']
            or set(draws)-seen-{0}):
        raise ValueError('incomplete or inconsistent capture')
    counts['unmatched_quads_excluded'] = len(draws[0])
    return dict(schema=1, scope='World 2.4 main-model projection and unclipped DMA',
                passed=not failures, hashes=hashes, counts=dict(counts),
                failures=failures, comparisons=comparisons,
                limitations=['No clipped-polygon or alternate road/car reconstruction',
                             'No new scenery is drawn by this verifier',
                             'Billboard camera basis and resource words are captured adapter inputs'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(args.run)
    except (ValueError, OSError, KeyError, struct.error) as exc:
        result = dict(schema=1, passed=False, error=str(exc))
    write_json(args.report, result)
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
