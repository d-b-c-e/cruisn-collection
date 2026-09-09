"""Validate USA host logs and compare visibility without certifying visual quality."""
import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path

from analyze_world_host import HASH_SEED, QUAD_FIELDS, cost_summary, hash_quad, rows
from compare_world_motion import compare as compare_motion
from gl_frames import compare_completed_frames
from verification import sha256_file, write_json

COUNTERS = ('pending', 'unsupported', 'near', 'far', 'projection', 'decoded', 'quads')
PHASES = ('guard_us', 'prepare_us', 'pack_us', 'log_us', 'submit_us')


def key(row):
    return int(row['frame']), row['time'], int(row['page'])


def evidence(run):
    _, scenes = rows(run/'usa-host-scenes.csv')
    keys = [key(r) for r in scenes]
    if len(set(keys)) != len(keys) or any(a[0] >= b[0] for a, b in zip(keys, keys[1:])):
        raise ValueError('duplicate or unordered USA host scenes')
    times = [Decimal(k[1]) for k in keys]
    if any(not t.is_finite() or t < 0 for t in times) or any(a >= b for a, b in zip(times, times[1:])):
        raise ValueError('invalid USA emulated scene times')
    for r in scenes:
        if (any(int(r[n]) < 0 for n in COUNTERS) or int(r['mode']) not in (1, 2)
                or int(r['host_far']) not in (80000, 160000, 240000)
                or len(r['quads_hash']) != 16 or any(c not in '0123456789abcdef' for c in r['quads_hash'])):
            raise ValueError('invalid USA scene mode/count/fingerprint')
    if any(int(r['pending']) != sum(int(r[k]) for k in COUNTERS[1:6]) for r in scenes):
        raise ValueError('USA object decisions do not partition the pending list')
    if any(abs(sum(float(r[p]) for p in PHASES)-float(r['microseconds'])) > .01 for r in scenes):
        raise ValueError('USA host phase costs do not sum to total')
    geometry = None
    quad_path = run/'usa-host-quads.csv'
    if quad_path.exists():
        # Empty geometry is valid only when every scene independently reports zero.
        import csv
        with quad_path.open(newline='') as stream:
            reader = csv.DictReader(stream)
            if not {'frame', 'time', 'page', 'object', 'model', 'depth', *QUAD_FIELDS} <= set(reader.fieldnames or []):
                raise ValueError('incomplete USA quad trace header')
            geometry = {k: [] for k in keys}
            last_index = -1
            indices = {k: i for i, k in enumerate(keys)}
            for row in reader:
                k = key(row)
                if k not in indices or indices[k] < last_index:
                    raise ValueError('orphan or unordered USA geometry')
                last_index = indices[k]
                geometry[k].append([int(row[n]) for n in ('object', 'model', 'depth', *QUAD_FIELDS)])
        for r, k in zip(scenes, keys):
            value = HASH_SEED
            for q in geometry[k]:
                value = hash_quad(value, q[3:])
            if len(geometry[k]) != int(r['quads']) or f'{value:016x}' != r['quads_hash']:
                raise ValueError('USA detailed geometry count/fingerprint mismatch')
    signature = [[*k, *(int(r[n]) for n in COUNTERS), r['quads_hash']] for k, r in zip(keys, scenes)]
    summary = dict(scenes=len(scenes), first=keys[0][0], last=keys[-1][0],
                   totals={n: sum(int(r[n]) for r in scenes) for n in COUNTERS},
                   far=sorted({int(r['host_far']) for r in scenes}),
                   modes=sorted({int(r['mode']) for r in scenes}),
                   phases={p: cost_summary(r[p] for r in scenes) for p in (*PHASES, 'microseconds')},
                   scene_signature_sha256=hashlib.sha256(json.dumps(signature).encode()).hexdigest(),
                   geometry_evidence='detailed' if geometry is not None else 'ordered fingerprints only',
                   sources={'scenes': sha256_file(run/'usa-host-scenes.csv'),
                            'quads': sha256_file(quad_path) if geometry is not None else None})
    return scenes, geometry, summary


def compare(reference, candidate, expect_gl, require_host_equal=False):
    reports = [json.loads((p/'report.json').read_text()) for p in (reference, candidate)]
    result = dict(schema=1, scope='USA original route, host repeatability and visible changes; NOT visual acceptance',
                  reference=str(reference.resolve()), candidate=str(candidate.resolve()),
                  replays_passed=all(r['passed'] and r['comparison']['passed'] for r in reports))
    a, b = reference/'run', candidate/'run'
    result['motion'] = compare_motion(a, b, 'usa')
    inputs = []
    for p in (a, b):
        fields, data = rows(p/'frames.csv')
        fields = [k for k in fields if k not in ('host_seconds', 'speed_percent')]
        if [int(r['frame']) for r in data] != list(range(1, len(data)+1)):
            raise ValueError('incomplete input frame sequence')
        inputs.append((fields, [tuple(r[k] for k in fields) for r in data]))
    result['inputs_equal'] = inputs[0] == inputs[1]
    result['input_frames'] = [len(i[1]) for i in inputs]
    result['scenes'] = [evidence(p)[2] if (p/'usa-host-scenes.csv').exists() else None for p in (a, b)]
    signatures = [s['scene_signature_sha256'] if s else None for s in result['scenes']]
    result['host_equal'] = signatures[0] == signatures[1] if all(signatures) else None
    result['gl'] = compare_completed_frames(a/'gl-snap', b/'gl-snap', details=True)
    result['expect_gl'] = expect_gl
    result['gl_expectation_passed'] = not result['gl']['size_mismatches'] and result['gl']['passed'] == (expect_gl == 'equal')
    result['passed'] = (result['replays_passed'] and result['motion']['passed'] and result['inputs_equal']
                        and result['gl_expectation_passed'] and (not require_host_equal or result['host_equal'] is True))
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('reference', type=Path); ap.add_argument('candidate', type=Path)
    ap.add_argument('--expect-gl', choices=('equal', 'changed'), required=True)
    ap.add_argument('--require-host-equal', action='store_true')
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    try:
        result = compare(args.reference, args.candidate, args.expect_gl, args.require_host_equal)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = dict(passed=False, error=str(error))
    write_json(args.report, result)
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
