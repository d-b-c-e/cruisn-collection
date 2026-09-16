"""Verify original billboard matrices/vertices against independent C31 helpers."""
import argparse
import json
from pathlib import Path
import subprocess

from offroad_billboard import prepare, project
from verification import sha256_file, write_json


def check(run, binary):
    run, binary = Path(run), Path(binary)
    records = run/'offroad-billboards.jsonl'; receipt = run/'offroad-billboard-result.json'
    if records.stat().st_size > 16*1024*1024 or receipt.stat().st_size > 4096:
        raise ValueError('billboard capture extent')
    state = json.loads(receipt.read_text(encoding='utf-8'))
    rows = [json.loads(line) for line in records.read_text(encoding='utf-8').splitlines()]
    if (state.get('complete') is not True or not 1 <= len(rows) <= 4096 or
            state.get('started') != len(rows) or state.get('projected') != len(rows) or
            type(state.get('first')) is not int or type(state.get('last')) is not int or
            not 1800 <= state['first'] <= state['last'] <= state['first']+120):
        raise ValueError('incomplete billboard interval')
    previous = 0; data = []; expected = []
    for index, r in enumerate(rows, 1):
        if (r['id'] != index or not max(previous, state['first']) <= r['frame'] <= state['last'] or
                r['end_frame'] != r['frame'] or r['lod_words'][0] != 3 or r['lod_words'][3] != 0 or
                len(r['projected']) != 12 or len(r['reciprocals']) != 4):
            raise ValueError('billboard record order/extent')
        previous = r['frame']
        matrix = prepare(r['object_words'], r['view'], r['basis'])
        table = {}
        for depth, word in zip(r['projected'][2::3], r['reciprocals']):
            if depth in table and table[depth] != word:
                raise ValueError('inconsistent reciprocal aliases')
            table[depth] = word
        points = project(r['vertices'], matrix, r['origin'], table.__getitem__)
        if matrix != r['matrix'] or points != r['projected']:
            raise ValueError(f'original billboard matrix/XYZ mismatch at record{index}')
        data.append([index, *r['object_words'], *r['view'], *r['basis'], *r['vertices'], r['origin'],
                     *[v for pair in zip(r['projected'][2::3], r['reciprocals']) for v in pair]])
        expected.append([index, *matrix, *points])
    process = subprocess.run([str(binary.resolve())], input='\n'.join(' '.join(map(str, row)) for row in data)+'\n',
                             text=True, capture_output=True, timeout=30)
    if process.returncode or [list(map(int, line.split())) for line in process.stdout.splitlines()] != expected:
        raise ValueError('native billboard output mismatch: '+process.stderr[:1000])
    return dict(passed=True, records=len(rows), vertices=4*len(rows),
                models=len({r['object_words'][20] for r in rows}),
                original_matrix_and_xyz_exact=True,
                sources={str(p): sha256_file(p) for p in (records, receipt, binary)},
                scope='Captured current basis, original bit4 four-vertex projection only. '
                      'No future-source, damage-state, LOD, material, polygon/DMA or GPU acceptance.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('preserve the existing report')
    try:
        result = check(args.run, args.native)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        result = dict(passed=False, error=str(exc))
    write_json(args.report, result)
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
