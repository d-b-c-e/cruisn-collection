"""Verify USA model operands against original DMA and optional native codec.

Fails on empty, duplicate, incomplete or mismatched evidence. Captured operands
must remain local; the report contains scalar verdicts and file identities only.
"""
import argparse
import csv
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

from scenery_c31 import F, signed
from usa_model import prepare, project, quads, validate
from verification import sha256_file, write_json

FIELDS = ('flags', 'palette', 'x0', 'y0', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3',
          'uv0', 'uv1', 'uv2', 'uv3', 'texture', 'word15')


def native_records(binary, records, reciprocals, prepared=False):
    lines = [' '.join(map(str, reciprocals))]
    for r in records:
        values = [r['call'], r['compact'], r['palette_kind'], len(r['model_words']),
            *r['model_words'], *r['matrix'], *r['camera_space'],
            r.get('origin_y', F.integer(200).store())]
        if prepared:
            values += [*r['object_words'], *r['camera'], *r['view'], *r['billboard_full'], *r['billboard_compact']]
            values += [r['dispatch_mode'], r['dispatch_enable'], r['model']]
        values += r['palette_words']
        lines.append(' '.join(map(str, values)))
    env = dict(os.environ)
    if os.name == 'nt':
        env['PATH'] = 'E:/msys64/mingw64/bin;'+env.get('PATH', '')
    process = subprocess.run([str(binary), '--prepared' if prepared else '--captured'], input='\n'.join(lines)+'\n',
                             capture_output=True, text=True, env=env, timeout=120)
    if process.returncode:
        raise ValueError('native codec failed: '+process.stderr[:300])
    result = {}
    for line in process.stdout.splitlines():
        values = list(map(int, line.split()))
        if len(values) < 3:
            raise ValueError('truncated native record')
        call, vertices, count = values[:3]
        if call in result or not 1 <= vertices <= 256 or not 0 <= count <= 1024 or len(values) != 3+3*vertices+16*count:
            raise ValueError('invalid native record')
        split = 3+3*vertices
        result[call] = (values[3:split], [values[i:i+16] for i in range(split, len(values), 16)])
    if set(result) != {r['call'] for r in records}:
        raise ValueError('native record coverage mismatch')
    return result


def check(run, binary=None):
    paths = [run/name for name in ('usa-model-transform.jsonl', 'usa-model-draws.csv', 'usa-model-reciprocals.bin')]
    records = [json.loads(line) for line in paths[0].read_text().splitlines()]
    if not records or len(records) > 100000:
        raise ValueError('empty or oversized model capture')
    ids = [r['call'] for r in records]
    if any(type(x) is not int or x < 1 for x in ids) or ids != sorted(set(ids)):
        raise ValueError('duplicate or unordered model call')
    if len(paths[2].read_bytes()) != 5080*4:
        raise ValueError('incomplete reciprocal table')
    reciprocals = struct.unpack('<5080I', paths[2].read_bytes())
    by_id = {r['call']: r for r in records}
    draws = {}
    with paths[1].open(newline='') as stream:
        for row in csv.DictReader(stream):
            call = int(row['call'])
            if call not in by_id:
                raise ValueError('orphan DMA call')
            r = by_id[call]
            if int(row['object']) != r['object'] or int(row['model']) != r['model'] or not r['frame'] <= int(row['frame']) <= r['end_frame']+1:
                raise ValueError('DMA owner/frame mismatch')
            q = [int(row[k]) for k in FIELDS]
            if any(not 0 <= w <= 65535 for w in q):
                raise ValueError('invalid DMA word')
            draws.setdefault(call, []).append(q)
    native = native_records(binary, records, reciprocals) if binary else None
    eligible = [r for r in records if r.get('schema', 0) >= 2 and not r['object_words'][14] & 0xa3]
    prepared_native = native_records(binary, eligible, reciprocals, prepared=True) if binary and eligible else None
    failures = []
    total_quads = unclipped = 0
    for r in records:
        validate(r)
        buffer = project(r, reciprocals)
        expected = quads(r, buffer)
        if r.get('schema', 0) >= 2 and not r['object_words'][14] & 0xa3:
            if prepare(r) != (r['camera_space'], r['matrix']):
                failures.append({'call': r['call'], 'kind': 'object transform'})
            if prepared_native is not None and prepared_native[r['call']] != (buffer, expected):
                failures.append({'call': r['call'], 'kind': 'prepared native'})
        if r.get('schema', 0) >= 2:
            flags = r['object_words'][14]
            compact = not flags & 0x08000840 and r['dispatch_mode'] & 15 == 4 and r['dispatch_enable'] != 0
            if bool(r['compact']) != compact:
                failures.append({'call': r['call'], 'kind': 'compact dispatch'})
            depth = F.load(r['camera_space'][2]).fix()
            selected = r['object_words'][13]
            if flags & 0x200 and depth > 8000:
                selected = r['object_words'][25 if flags & 4 and depth > 15000 else 24]
            if selected != r['model'] or depth != signed(r['object_words'][28]):
                failures.append({'call': r['call'], 'kind': 'LOD model/depth'})
        if buffer != r['projected']:
            failures.append({'call': r['call'], 'kind': 'projection'})
        if native is not None and native[r['call']] != (buffer, expected):
            failures.append({'call': r['call'], 'kind': 'native'})
        if r['fast']:
            unclipped += 1
            total_quads += len(expected)
            if expected != draws.get(r['call'], []):
                failures.append({'call': r['call'], 'kind': 'ordered DMA',
                                 'expected': len(expected), 'actual': len(draws.get(r['call'], []))})
    if not unclipped or not total_quads:
        raise ValueError('empty unclipped DMA coverage')
    receipt_path = run/'usa-model-capture.json'
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
    if receipt is not None:
        if not receipt.get('complete') or receipt.get('projected') != len(records) or receipt.get('draws') != sum(map(len, draws.values())):
            raise ValueError('incomplete capture receipt')
        if any(not receipt['first'] <= r['frame'] <= r['end_frame'] <= receipt['last'] for r in records):
            raise ValueError('record outside capture interval')
        paths.append(receipt_path)
    elif any(r.get('schema', 0) >= 1 for r in records):
        raise ValueError('missing capture receipt')
    return dict(schema=1, passed=not failures, projected=len(records), unclipped=unclipped,
                excluded_clipped_or_special=len(records)-unclipped, quads=total_quads,
                models=len({r['model'] for r in records}), objects=len({r['object'] for r in records}),
                compact=sum(r['compact'] for r in records), full=sum(not r['compact'] for r in records),
                direct=sum(r['palette_kind'] for r in records), lookup=sum(not r['palette_kind'] for r in records),
                first=min(r['frame'] for r in records), last=max(r['end_frame'] for r in records),
                legacy_origin_assumptions=sum('origin_y' not in r for r in records),
                prepared_transforms=len(eligible), prepared_native_checked=prepared_native is not None,
                native_checked=native is not None, native_sha256=sha256_file(binary) if binary else None,
                failures=failures, files={p.name: sha256_file(p) for p in paths},
                scope='Captured main projection and unclipped DMA; no scene insertion, residency or visible distance acceptance')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path)
    ap.add_argument('--native', type=Path)
    ap.add_argument('--report', required=True, type=Path)
    args = ap.parse_args()
    try:
        report = check(args.run, args.native)
    except (OSError, ValueError, KeyError, struct.error, subprocess.SubprocessError) as error:
        report = dict(schema=1, passed=False, error=str(error))
    write_json(args.report, report)
    print(json.dumps(report))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
