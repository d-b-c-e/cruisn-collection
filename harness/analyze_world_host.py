"""Check host scenery repeatability without mistaking changed pixels for quality.

The guest-input, camera and actual ADC comparisons remain strict, including ADC
timestamps. GL equality is reported separately: visible changes are not a visual
acceptance verdict. All original runs and failed equality reports remain intact.
"""
import argparse
import csv
import json
from pathlib import Path

from gl_frames import compare_completed_frames
from verification import sha256_file, write_json


def rows(path):
    with path.open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        result = list(reader)
        if not result or any(None in r or any(v is None for v in r.values()) for r in result):
            raise ValueError(f'empty or malformed evidence: {path}')
        return reader.fieldnames, result


def scene_summary(run):
    _, scenes = rows(run/'world-host-scenes.csv')
    keys = [(int(r['frame']), int(r['page'])) for r in scenes]
    if keys != sorted(set(keys)):
        raise ValueError('duplicate or unordered host scene clocks')
    totals = {key: sum(int(r[key]) for r in scenes)
              for key in ('pending', 'unsupported', 'distance', 'decoded', 'quads')}
    _, quads = rows(run/'world-host-quads.csv')
    counts = {}
    for q in quads:
        key = (int(q['frame']), int(q['page']))
        counts[key] = counts.get(key, 0)+1
    if set(counts)-set(keys) or any(counts.get(k, 0) != int(r['quads']) for k, r in zip(keys, scenes)):
        raise ValueError('host scene counts do not match actual submitted geometry log')
    costs = sorted(float(r['microseconds']) for r in scenes)
    return dict(scenes=len(scenes), first=keys[0][0], last=keys[-1][0], totals=totals,
                modes=sorted({int(r['mode']) for r in scenes}),
                far=sorted({int(r.get('host_far', 80000)) for r in scenes}),
                maximum_pending=max(int(r['pending']) for r in scenes),
                maximum_quads=max(int(r['quads']) for r in scenes),
                host_microseconds=dict(maximum=costs[-1], p99=costs[min(len(costs)-1, int(len(costs)*.99))]),
                quads_sha256=sha256_file(run/'world-host-quads.csv'))


def compare(reference, candidate, *, expect_gl='changed'):
    result = dict(schema=1, passed=False, scope='guest invariance and host visibility/repeatability; not visual quality',
                  reference=str(reference.resolve()), candidate=str(candidate.resolve()), expect_gl=expect_gl)
    reports = [json.loads((p/'report.json').read_text()) for p in (reference, candidate)]
    result['original_replays_passed'] = all(r['passed'] and r['comparison']['passed'] for r in reports)
    a, b = reference/'run', candidate/'run'
    result['scenes'] = [scene_summary(p) for p in (a, b)]
    result['guest_files'] = {}
    for name in ('world-camera.csv', 'world-adc.csv'):
        hashes = [sha256_file(p/name) for p in (a, b)]
        result['guest_files'][name] = dict(sha256=hashes, equal=hashes[0] == hashes[1])
    inputs = []
    for p in (a, b):
        fields, data = rows(p/'frames.csv')
        fields = [k for k in fields if k not in ('host_seconds', 'speed_percent')]
        if [int(r['frame']) for r in data] != list(range(1, len(data)+1)):
            raise ValueError('incomplete input frame sequence')
        inputs.append((fields, [tuple(r[k] for k in fields) for r in data]))
    result['inputs_equal'] = inputs[0] == inputs[1]
    result['input_frames'] = [len(i[1]) for i in inputs]
    result['gl'] = compare_completed_frames(a/'gl-snap', b/'gl-snap', details=True)
    result['gl_expectation_passed'] = (not result['gl']['size_mismatches'] and
        result['gl']['passed'] == (expect_gl == 'equal'))
    result['passed'] = (result['original_replays_passed'] and result['inputs_equal'] and
        all(r['equal'] for r in result['guest_files'].values()) and result['gl_expectation_passed'])
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('reference', type=Path); ap.add_argument('candidate', type=Path)
    ap.add_argument('--expect-gl', choices=('equal', 'changed'), required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    try:
        report = compare(args.reference, args.candidate, expect_gl=args.expect_gl)
    except (OSError, ValueError, KeyError) as error:
        report = dict(passed=False, error=str(error))
    write_json(args.report, report)
    print('PASS' if report['passed'] else 'FAIL', args.report)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
