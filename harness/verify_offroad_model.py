"""Verify private Off Road model captures against original ordered DMA.

Reject empty, incomplete, duplicated, unowned or mismatched evidence. Report only
counts, verdicts and identities; raw geometry and material operands stay local.
"""
import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

from offroad_model import project, quads, validate
import offroad_transform
from verification import sha256_file, write_json

FIELDS = ('flags', 'palette', 'x0', 'y0', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3',
          'uv0', 'uv1', 'uv2', 'uv3', 'texture', 'word15')


def native_records(binary, records, reciprocals, transform_table=None):
    lines = [' '.join(map(str, reciprocals))]
    if transform_table is not None:
        lines.append(' '.join(map(str, [*offroad_transform.CONSTANTS, *transform_table])))
    for r in records:
        values = [r['call'], r['lod'], r['vertices'], r['polygons'], r['origin_x'], r['path'],
                  r['extra_flags'], r['object_words'][18], r['object_words'][19],
                  *r['lod_words'], *r['matrix'], *r['vertex_words'], *r['polygon_words'], *r['palette_words']]
        if transform_table is not None:
            values += [*r['object_words'], *r['view'], *r['lod_context']]
        lines.append(' '.join(map(str, values)))
    env = dict(os.environ)
    if os.name == 'nt':
        env['PATH'] = 'E:/msys64/mingw64/bin;'+env.get('PATH', '')
    command = [str(binary)]+(['--prepared'] if transform_table is not None else [])
    process = subprocess.run(command, input='\n'.join(lines)+'\n', capture_output=True,
                             text=True, env=env, timeout=120)
    if process.returncode:
        raise ValueError(f'native codec failed ({process.returncode}): '+process.stderr[:300])
    result = {}
    for line in process.stdout.splitlines():
        values = list(map(int, line.split()))
        if len(values) < 3:
            raise ValueError('truncated native record')
        call, vertices, count = values[:3]
        if (call in result or not 1 <= vertices <= 512 or not 0 <= count <= 1024 or
                len(values) != 3+2*vertices+16*count):
            raise ValueError('invalid native record')
        split = 3+2*vertices
        result[call] = (values[3:split], [values[i:i+16] for i in range(split, len(values), 16)])
    if list(result) != [r['call'] for r in records]:
        raise ValueError('native record coverage mismatch')
    return result


def check(run, binary=None):
    paths = [run/name for name in ('offroad-model-transform.jsonl', 'offroad-model-draws.csv',
                                  'offroad-model-reciprocals.bin', 'offroad-model-capture.json')]
    records = [json.loads(line) for line in paths[0].read_text().splitlines()]
    if not records or len(records) > 20000:
        raise ValueError('empty or oversized model capture')
    ids = [r['call'] for r in records]
    if any(type(x) is not int or not 1 <= x <= 20000 for x in ids) or ids != sorted(set(ids)):
        raise ValueError('duplicate or unordered model call')
    for r in records:
        validate(r)
    raw = paths[2].read_bytes()
    if len(raw) != 67776*4:
        raise ValueError('incomplete reciprocal table')
    reciprocals = struct.unpack('<67776I', raw)
    prepared = [r for r in records if 'trig_constants' in r]
    table = None
    eligible = []
    if prepared:
        if len(prepared) != len(records):
            raise ValueError('mixed prepared/captured model schema')
        table_path = run/'offroad-model-trig.bin'
        table_raw = table_path.read_bytes()
        if len(table_raw) != 16386*4:
            raise ValueError('incomplete trigonometry table')
        table = struct.unpack('<16386I', table_raw)
        paths.append(table_path)
        for r in records:
            offroad_transform.validate(r, table)
        eligible = [r for r in records if not r['object_words'][5] & 0x200e]
    receipt = json.loads(paths[3].read_text())
    first, last = receipt['first'], receipt['last']
    if (not receipt.get('complete') or receipt['projected'] != len(records) or
            receipt['started'] != len(records) or
            not 1800 <= first <= last <= first+120 or
            any(not first <= r['frame'] <= r.get('end_frame', r['frame']) <= last for r in records)):
        raise ValueError('incomplete capture receipt')
    by_id = {r['call']: r for r in records}
    draws = {}
    previous_call = 0
    pages = set()
    with paths[1].open(newline='') as stream:
        for row in csv.DictReader(stream):
            call = int(row['call'])
            if call not in by_id:
                raise ValueError('orphan DMA call')
            r = by_id[call]
            if (call < previous_call or int(row['object']) != r['object'] or int(row['model']) != r['model'] or
                    not r['frame'] <= int(row['frame']) <= min(last, r.get('end_frame', r['frame'])+1)):
                raise ValueError('DMA owner/frame/order mismatch')
            previous_call = call
            # The probe records the raw control register (e.g. 0x201/0x204),
            # which has separate visible bit0 and draw bit2 plus other flags.
            if int(row['pc']) not in (0x1fb0, 0x1fed) or not 0 <= int(row['page']) <= 0xffffffff:
                raise ValueError('unsupported DMA path/page')
            pages.add(int(row['page']))
            q = [int(row[k]) for k in FIELDS]
            if any(not 0 <= w <= 65535 for w in q):
                raise ValueError('invalid DMA word')
            draws.setdefault(call, []).append(q)
    count = sum(map(len, draws.values()))
    if not count or receipt['draws'] != count:
        raise ValueError('empty or incomplete DMA coverage')
    native = native_records(binary, records, reciprocals) if binary else None
    prepared_native = native_records(binary, eligible, reciprocals, table) if binary and eligible else None
    failures = []
    for r in records:
        points = project(r, reciprocals)
        expected = quads(r, points)
        captured = [n for i in range(r['vertices']) for n in r['projected'][3*i:3*i+2]]
        if points != captured:
            failures.append(dict(call=r['call'], kind='projection'))
        if expected != draws.get(r['call'], []):
            failures.append(dict(call=r['call'], kind='ordered DMA',
                                 expected=len(expected), actual=len(draws.get(r['call'], []))))
        if native is not None and native[r['call']] != (points, expected):
            failures.append(dict(call=r['call'], kind='native'))
        if table is not None:
            index, relative = offroad_transform.select_lod(r)
            if (r['lod_index'] != index or r['lod'] != r['model']+7+5*index or
                    relative is not None and relative & 0xffffffff != r['object_words'][9]):
                failures.append(dict(call=r['call'], kind='LOD selection'))
            if not r['object_words'][5] & 0x200e:
                if offroad_transform.prepare(r, table) != r['matrix']:
                    failures.append(dict(call=r['call'], kind='object transform'))
                if prepared_native is not None and prepared_native[r['call']] != (points, expected):
                    failures.append(dict(call=r['call'], kind='prepared native'))
    transform_paths = Counter('identity' if r['object_words'][5] & 1 else
                              'yaw' if r['object_words'][5] & 0x10 else 'full' for r in eligible)
    return dict(schema=1, passed=not failures, projected=len(records), quads=count,
                models=len({r['model'] for r in records}), objects=len({r['object'] for r in records}),
                lod_indices=sorted({(r['lod']-r['model']-7)//5 for r in records}),
                projection_paths=sorted({r['path'] for r in records}), first=first, last=last,
                page_controls=sorted(pages),
                prepared_transforms=len(eligible), lod_selections=len(prepared),
                prepared_native_checked=prepared_native is not None,
                transform_paths={kind: transform_paths[kind] for kind in ('identity', 'yaw', 'full')},
                native_checked=native is not None, native_sha256=sha256_file(binary) if binary else None,
                failures=failures, files={p.name: sha256_file(p) for p in paths},
                scope='Ordinary projection and ordered DMA; prepared transforms/LOD only where explicitly counted. '
                      'No scene insertion, residency, clipping or visible-distance acceptance')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path)
    ap.add_argument('--native', type=Path)
    ap.add_argument('--report', required=True, type=Path)
    args = ap.parse_args()
    try:
        result = check(args.run, args.native)
    except (OSError, ValueError, KeyError, TypeError, struct.error, subprocess.SubprocessError) as error:
        result = dict(schema=1, passed=False, error=str(error))
    write_json(args.report, result)
    print(json.dumps(result))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
