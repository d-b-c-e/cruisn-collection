"""Check Off Road host decisions, exact clocks and ordered geometry evidence.

This validates reproducibility, not foreground occlusion or visual acceptance.
"""
import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from analyze_world_host import HASH_SEED, QUAD_FIELDS, cost_summary, hash_quad, rows
from offroad_scene import scene
from compare_world_motion import compare as compare_motion
from gl_frames import compare_completed_frames
from verify_offroad_future import Memory
from verification import sha256_file, write_json

COUNTERS = ('pending', 'future', 'future_definitions', 'unsupported', 'near', 'far',
            'projection', 'material', 'decoded', 'pretrack', 'partial', 'deferred', 'quads')
PHASES = ('guard_us', 'prepare_us', 'pack_us', 'log_us', 'submit_us')
OBJECT_FIELDS = ('object', 'model', 'lod', 'depth', 'order')


def key(row):
    return int(row['frame']), Decimal(str(row['time'])), int(row['page'])


def evidence(run, retain_geometry=False):
    _, records = rows(run/'offroad-host-scenes.csv')
    keys = [key(r) for r in records]
    if (any(not k[1].is_finite() or k[1] < 0 for k in keys)
            or any(a[0] >= b[0] or a[1] >= b[1] for a, b in zip(keys, keys[1:]))):
        raise ValueError('invalid or duplicate Off Road host clocks')
    for r in records:
        if (int(r['mode']) not in (1, 2) or int(r['multiplier']) not in (1, 2, 3)
                or any(int(r[n]) < 0 for n in COUNTERS)
                or any(int(r[n]) not in (0, 1) for n in ('future_enabled', 'pretrack', 'partial', 'deferred'))
                or len(r['quads_hash']) != 16 or any(c not in '0123456789abcdef' for c in r['quads_hash'])):
            raise ValueError('invalid Off Road host mode/count/fingerprint')
        if (int(r['future']) > int(r['future_definitions'])
                or not int(r['future_enabled']) and int(r['future_definitions'])
                or int(r['pending'])+int(r['future_definitions']) !=
                sum(int(r[n]) for n in ('unsupported', 'near', 'far', 'projection', 'material', 'decoded'))):
            raise ValueError('Off Road source decisions do not partition descriptors')
        if (int(r['pretrack']) or int(r['deferred'])) and any(int(r[n]) for n in
                ('pending', 'future', 'future_definitions', 'decoded', 'quads')):
            raise ValueError('Off Road deferred scene contains geometry')
        if abs(sum(float(r[p]) for p in PHASES)-float(r['microseconds'])) > .01:
            raise ValueError('Off Road phase costs do not sum to total')
    geometry = {} if retain_geometry else None
    path = run/'offroad-host-quads.csv'
    if path.exists():
        indices = {k: i for i, k in enumerate(keys)}
        counts, hashes = [0]*len(keys), [HASH_SEED]*len(keys)
        last = -1
        with path.open(newline='') as stream:
            reader = csv.DictReader(stream)
            if not {'frame', 'time', 'page', *OBJECT_FIELDS, *QUAD_FIELDS} <= set(reader.fieldnames or []):
                raise ValueError('incomplete Off Road geometry header')
            for row in reader:
                k = key(row)
                if k not in indices or indices[k] < last:
                    raise ValueError('orphan or unordered Off Road geometry')
                last = indices[k]
                values = [int(row[n]) for n in (*OBJECT_FIELDS, *QUAD_FIELDS)]
                counts[last] += 1; hashes[last] = hash_quad(hashes[last], values[5:])
                if geometry is not None and (retain_geometry is True or k in retain_geometry):
                    geometry.setdefault(k, []).append(values)
        for r, count, fingerprint in zip(records, counts, hashes):
            if count != int(r['quads']) or f'{fingerprint:016x}' != r['quads_hash']:
                raise ValueError('Off Road geometry count/fingerprint mismatch')
    elif retain_geometry:
        raise ValueError('detailed Off Road geometry required')
    signature = [[int(r['frame']), r['time'], int(r['page']), int(r['multiplier']), int(r['future_enabled']),
                  *(int(r[n]) for n in COUNTERS), r['quads_hash']] for r in records]
    summary = dict(scenes=len(records), first=keys[0][0], last=keys[-1][0],
                   totals={n: sum(int(r[n]) for r in records) for n in COUNTERS},
                   phases={p: cost_summary(r[p] for r in records) for p in (*PHASES, 'microseconds')},
                   signature_sha256=hashlib.sha256(json.dumps(signature).encode()).hexdigest(),
                   sources={'scenes': sha256_file(run/'offroad-host-scenes.csv'),
                            'quads': sha256_file(path) if path.exists() else None})
    return records, geometry, summary


def snapshots(run, rom_path):
    captures = [(ram, json.loads(ram.with_suffix('.json').read_text(), parse_float=Decimal))
                for ram in sorted(run.glob('offroad-scene-*.bin'))]
    wanted = {(int(meta['native_frame']), meta['time'], int(meta['page'])) for _, meta in captures}
    if not wanted:
        raise ValueError('empty live Off Road snapshot coverage')
    records, geometry, summary = evidence(run, retain_geometry=wanted)
    by_key = {key(r): r for r in records}; rom = rom_path.read_bytes(); results = []
    for ram, meta in captures:
        k = int(meta['native_frame']), meta['time'], int(meta['page'])
        if k not in by_key:
            raise ValueError(f'no exact native frame/time/page match for {ram.stem}')
        actual = by_key[k]
        counts, objects = scene(Memory(rom, ram.read_bytes()), int(actual['multiplier']), bool(int(actual['future_enabled'])))
        expected = [[o[n] for n in ('id', 'model', 'lod', 'depth', 'order')]+q for o in objects for q in o['quads']]
        if (any(int(actual[n]) != int(v) for n, v in counts.items())
                or int(actual['decoded']) != len(objects) or expected != geometry.get(k, [])):
            raise ValueError(f'live Off Road scalar/ordered geometry mismatch at {ram.stem}')
        results.append(dict(snapshot=ram.stem, native_frame=k[0], time=str(k[1]), page=k[2],
                            objects=len(objects), quads=len(expected), sha256=sha256_file(ram)))
    if not results or not sum(r['quads'] for r in results):
        raise ValueError('empty live Off Road snapshot coverage')
    return dict(passed=True, scenes=summary, snapshots=results, rom_sha256=sha256_file(rom_path))


def compare(reference, candidate, expect_gl, require_host_equal=False):
    reports = [json.loads((p/'report.json').read_text()) for p in (reference, candidate)]
    inputs = []
    for p in (reference, candidate):
        fields, data = rows(p/'run/frames.csv')
        fields = [n for n in fields if n not in ('host_seconds', 'speed_percent')]
        if [int(r['frame']) for r in data] != list(range(1, len(data)+1)):
            raise ValueError('incomplete Off Road input sequence')
        inputs.append((fields, [tuple(r[n] for n in fields) for r in data]))
    result = dict(scope='Complete recorded inputs, camera/ADC times, host decisions and GL; not visual acceptance',
                  replays_passed=all(r['passed'] and r['comparison']['passed'] for r in reports),
                  inputs_equal=inputs[0] == inputs[1], input_frames=[len(i[1]) for i in inputs],
                  motion=compare_motion(reference/'run', candidate/'run', 'offroad'))
    result['host'] = [evidence(p/'run')[2] if (p/'run/offroad-host-scenes.csv').exists() else None
                      for p in (reference, candidate)]
    result['host_equal'] = (result['host'][0]['signature_sha256'] == result['host'][1]['signature_sha256']
                            if all(result['host']) else None)
    result['gl'] = compare_completed_frames(reference/'run/gl-snap', candidate/'run/gl-snap', details=True)
    result['expect_gl'] = expect_gl
    result['passed'] = (result['replays_passed'] and result['inputs_equal'] and result['motion']['passed']
                        and not result['gl']['size_mismatches'] and result['gl']['passed'] == (expect_gl == 'equal')
                        and (not require_host_equal or result['host_equal'] is True))
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path); ap.add_argument('--rom', type=Path)
    ap.add_argument('--reference', type=Path)
    ap.add_argument('--expect-gl', choices=('equal', 'changed'))
    ap.add_argument('--require-host-equal', action='store_true')
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    try:
        if args.reference:
            if not args.expect_gl or args.rom:
                raise ValueError('comparison requires --expect-gl and cannot take --rom')
            result = compare(args.reference, args.run, args.expect_gl, args.require_host_equal)
        else:
            if args.expect_gl or args.require_host_equal:
                raise ValueError('comparison options require --reference')
            result = snapshots(args.run, args.rom) if args.rom else dict(passed=True, scenes=evidence(args.run)[2])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = dict(passed=False, error=str(exc))
    write_json(args.report, result); print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
