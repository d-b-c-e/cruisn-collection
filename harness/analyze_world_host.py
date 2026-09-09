"""Check host scenery repeatability without mistaking changed pixels for quality.

The guest-input, camera and actual ADC comparisons remain strict, including ADC
timestamps. GL equality is reported separately: visible changes are not a visual
acceptance verdict. All original runs and failed equality reports remain intact.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from gl_frames import compare_completed_frames
from verification import sha256_file, write_json

HASH_SEED = 14695981039346656037
QUAD_FIELDS = ('flags','palette','x0','y0','x1','y1','x2','y2','x3','y3',
               'uv0','uv1','uv2','uv3','texture','word15')
PHASES = ('guard_us','prepare_us','pack_us','quad_log_us','submit_us')


def hash_quad(value, words):
    for word in words:
        if not 0 <= word <= 65535:
            raise ValueError('quad word outside uint16 range')
        for byte in (word & 255, word >> 8):
            value = ((value ^ byte) * 1099511628211) & ((1 << 64)-1)
    return value


def cost_summary(values):
    values = sorted(map(float, values))
    if any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('invalid host phase cost')
    return dict(maximum=values[-1], **{f'p{p}': values[min(len(values)-1, int(len(values)*p/100))]
                                     for p in (50,95,99)})


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
    modern = any('quad_trace' in r for r in scenes)
    trace = True
    if modern:
        required = {'quad_trace','quads_hash','previous_scene_log_us',*PHASES}
        if any(not required <= r.keys() for r in scenes):
            raise ValueError('incomplete host phase/fingerprint schema')
        modes = {r['quad_trace'] for r in scenes}
        if modes not in ({'0'}, {'1'}):
            raise ValueError('invalid/mixed host quad trace modes')
        trace = modes == {'1'}
        for r in scenes:
            digest = r['quads_hash']
            if len(digest) != 16 or any(c not in '0123456789abcdef' for c in digest):
                raise ValueError('invalid ordered quad fingerprint')
            if abs(sum(float(r[p]) for p in PHASES)-float(r['microseconds'])) > .01:
                raise ValueError('host phase costs do not sum to total')
    quad_path = run/'world-host-quads.csv'
    if not trace and quad_path.exists():
        raise ValueError('summary-only run has an unexpected detailed trace')
    quads = rows(quad_path)[1] if trace else []
    counts = {}
    hashes = {}
    for q in quads:
        key = (int(q['frame']), int(q['page']))
        counts[key] = counts.get(key, 0)+1
        if modern:
            hashes[key] = hash_quad(hashes.get(key,HASH_SEED), (int(q[k]) for k in QUAD_FIELDS))
    if trace and (set(counts)-set(keys) or any(counts.get(k, 0) != int(r['quads']) for k, r in zip(keys, scenes))):
        raise ValueError('host scene counts do not match actual submitted geometry log')
    if modern and trace and any(f'{hashes.get(k,HASH_SEED):016x}' != r['quads_hash'] for k,r in zip(keys,scenes)):
        raise ValueError('ordered quad fingerprint does not match detailed geometry')
    # Summary mode keeps a low-cost receipt. It is not equivalent to archiving
    # actual geometry; compare it with a detailed control before accepting it.
    signature = [[*k, *(int(r[t]) for t in totals), r['quads_hash']] for k,r in zip(keys,scenes)] if modern else None
    phases = {p: cost_summary(r[p] for r in scenes) for p in (*PHASES,'previous_scene_log_us')} if modern else {}
    return dict(scenes=len(scenes), first=keys[0][0], last=keys[-1][0], totals=totals,
                modes=sorted({int(r['mode']) for r in scenes}),
                far=sorted({int(r.get('host_far', 80000)) for r in scenes}),
                maximum_pending=max(int(r['pending']) for r in scenes),
                maximum_quads=max(int(r['quads']) for r in scenes),
                host_microseconds=cost_summary(r['microseconds'] for r in scenes), phases=phases,
                geometry_evidence='detailed' if trace else 'ordered fingerprint only',
                scene_signature_sha256=hashlib.sha256(json.dumps(signature).encode()).hexdigest() if modern else None,
                quads_sha256=sha256_file(quad_path) if trace else None)


def compare(reference, candidate, *, expect_gl='changed', require_host_equal=False):
    result = dict(schema=1, passed=False, scope='guest invariance and host visibility/repeatability; not visual quality',
                  reference=str(reference.resolve()), candidate=str(candidate.resolve()), expect_gl=expect_gl,
                  require_host_equal=require_host_equal)
    reports = [json.loads((p/'report.json').read_text()) for p in (reference, candidate)]
    result['original_replays_passed'] = all(r['passed'] and r['comparison']['passed'] for r in reports)
    a, b = reference/'run', candidate/'run'
    result['scenes'] = [scene_summary(p) for p in (a, b)]
    signatures = [s['scene_signature_sha256'] for s in result['scenes']]
    result['host_scene_fingerprints_equal'] = signatures[0] == signatures[1] if all(signatures) else None
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
        all(r['equal'] for r in result['guest_files'].values()) and result['gl_expectation_passed'] and
        (not require_host_equal or result['host_scene_fingerprints_equal'] is True))
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('reference', type=Path); ap.add_argument('candidate', type=Path)
    ap.add_argument('--expect-gl', choices=('equal', 'changed'), required=True)
    ap.add_argument('--require-host-equal',action='store_true',
                    help='also require matching scene counts and ordered quad fingerprints')
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    try:
        report = compare(args.reference, args.candidate, expect_gl=args.expect_gl,
                         require_host_equal=args.require_host_equal)
    except (OSError, ValueError, KeyError) as error:
        report = dict(passed=False, error=str(error))
    write_json(args.report, report)
    print('PASS' if report['passed'] else 'FAIL', args.report)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
