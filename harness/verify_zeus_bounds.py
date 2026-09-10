"""Compare native model bounds with Python and full independent polygon projection.

JSON contexts and binary work files contain raw game operands: keep them local.
The synthetic suite covers random transforms, viewport edges and near clipping.
No drawing, live material acceptance or performance claim is made.
"""
import argparse
import json
import math
import random
import struct
import subprocess
from pathlib import Path

from zeus_model import decode, F
from zeus_models import parse
from zeus_model_bounds import model_bounds, outside
from verification import sha256_file, write_json


def word(f):
    return struct.unpack('<I', struct.pack('<f', f))[0]


def pair(a, b):
    return (a & 65535) | ((b & 65535) << 16)


def polygon(v):
    return [0x38000000, 0, pair(v[0][0], v[1][0]), pair(v[0][1], v[1][1]), 0, 0,
            pair(v[0][2], v[1][2]), pair(v[2][2], v[3][2]), pair(v[2][0], v[3][0]), pair(v[2][1], v[3][1])]


def synthetic(count=5000, seed=0x5ce9e):
    rng = random.Random(seed)
    for i in range(count):
        regs = [0]*128
        regs[0x66] = 0x8e;regs[0x68] = 0x9d;regs[0x6c] = 9
        regs[0x6a] = word(256);regs[0x6b] = word(200);regs[0x78] = word(1.)
        matrix = [1., 0., 0., 0., 1., 0., 0., 0., 1.]
        if i < count//5:
            vertices = [[rng.randint(-32768, 32767) for _ in range(3)] for _ in range(4)]
            matrix = [rng.uniform(-2, 2) for _ in range(9)]
            translation = [rng.uniform(-1e5, 1e5), rng.uniform(-1e5, 1e5), rng.uniform(-1e4, 1e6)]
            regs[0x66] += rng.randrange(-4, 5)
        else:
            vertices = [[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]]
            z = 2.**rng.randrange(-4, 18);translation = [0., 0., z]
            side = i % 4;axis = side//2;edge = (-86, 598, 0, 400)[side]
            origin = 256 if axis == 0 else 200
            translation[axis] = (edge-origin)*(z+2)/512 + rng.choice([-1., 1.])*2.**rng.randrange(-20, 3)
            if i % 7 == 0:
                vertices = [v[:2]+[rng.choice([-2, 2])] for v in vertices]
                translation[2] = 1.;regs[0x78] = word(rng.choice([-.5, 0., .5, 1., 2.]))
        yield dict(frame=1, quad_size=10, words=polygon(vertices), regs=regs, render=[0]*80,
                   matrix=[float(F(x)) for x in matrix], translation=[float(F(x)) for x in translation],
                   texture=0, yscale=0, render_policy=0)


def intersects(points, margin):
    x, y = points[:, 0], points[:, 1]
    return bool(max(x) >= -margin and min(x) <= 512+margin and max(y) >= 0 and min(y) <= 400)


def encode(context, margin):
    words = context['words']
    return (struct.pack('<2I128I13f', len(words), context['quad_size'], *context['regs'],
                        *context['matrix'], *context['translation'][:3], margin) +
            struct.pack('<'+str(len(words))+'I', *words))


def verify(contexts, native, work, margin=86):
    if not 1 <= len(contexts) <= 65536 or not math.isfinite(margin) or not 0 <= margin <= 256:
        raise ValueError('bounds case count or margin')
    work.mkdir(parents=True, exist_ok=False)
    native_hash = sha256_file(native)
    expected = [];pieces = [];byte_count = 8;visible = avoided = total = 0
    for i, context in enumerate(contexts):
        # Full projection is independent of the interval-based rejection.
        quads, _ = decode(context)
        rejected = outside(model_bounds(context['words'], context['quad_size']), context, margin)
        onscreen = sum(intersects(points, margin) for fields, points in quads)
        if rejected and onscreen:
            raise ValueError(f'model bounds dropped visible polygons in case {i}')
        visible += onscreen;total += len(quads);avoided += len(quads) if rejected else 0
        expected.append(int(rejected))
        piece = encode(context, margin);byte_count += len(piece)
        if byte_count > 128*1024*1024:
            raise ValueError('bounds encoded byte budget')
        pieces.append(piece)
    source, output = work/'bounds-input.bin', work/'bounds-output.bin'
    source.write_bytes(struct.pack('<II', 0x3142535a, len(contexts))+b''.join(pieces))
    run = subprocess.run([str(native.resolve()), str(source.resolve()), str(output.resolve())],
                         capture_output=True, text=True, timeout=60)
    (work/'stdout.txt').write_text(run.stdout, encoding='utf-8')
    (work/'stderr.txt').write_text(run.stderr, encoding='utf-8')
    if run.returncode:
        raise ValueError(f'native bounds rejected batch: {run.stderr[:500]}')
    raw = output.read_bytes()
    if len(raw) != len(expected)*4:
        raise ValueError('native bounds output size')
    actual = list(struct.unpack('<'+str(len(expected))+'I', raw))
    receipt = json.loads(run.stdout)
    if actual != expected or receipt != dict(passed=True, cases=len(expected), rejected=sum(expected)):
        raise ValueError('native bounds differ from independent reference')
    malformed = (struct.pack('<II', 0, 1), struct.pack('<II', 0x3142535a, 65537),
                 struct.pack('<II', 0x3142535a, 1), source.read_bytes()+b'bad!')
    for i, payload in enumerate(malformed):
        bad, result = work/f'invalid-{i}.bin', work/f'invalid-{i}-output.bin'
        bad.write_bytes(payload)
        rejected = subprocess.run([str(native.resolve()), str(bad.resolve()), str(result.resolve())],
                                  capture_output=True, text=True, timeout=60)
        (work/f'invalid-{i}.txt').write_text(rejected.stderr, encoding='utf-8')
        if rejected.returncode == 0 or result.exists():
            raise ValueError('native bounds accepted malformed input or published partial output')
    if native_hash != sha256_file(native):
        raise ValueError('native bounds binary changed during verification')
    return dict(passed=True, cases=len(expected), rejected=sum(expected), visible_polygons=visible,
                decoded_polygons=total, avoided_polygons=avoided, false_rejections=0,
                native_python_exact=True, malformed_batches_rejected=len(malformed), native_sha256=native_hash,
                input_sha256=sha256_file(source), output_sha256=sha256_file(output))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--work-dir', type=Path, required=True, help='new local directory for raw binary batches')
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--models', type=Path, action='append', default=[])
    p.add_argument('--contexts-json', type=Path, action='append', default=[], help='local list of contexts or records containing context')
    p.add_argument('--margin', type=float, default=86)
    args = p.parse_args()
    sources = args.models+args.contexts_json
    try:
        before = {str(path.resolve()): sha256_file(path) for path in sources}
        contexts = []
        for path in args.models:
            contexts.extend(parse(path))
        for path in args.contexts_json:
            if path.stat().st_size > 64*1024*1024:
                raise ValueError('bounds context JSON budget')
            rows = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(rows, list) or len(rows) > 65536:
                raise ValueError('bounds context JSON shape')
            contexts.extend(row.get('context', row) for row in rows)
        if not sources:
            contexts = list(synthetic())
        result = verify(contexts, args.native, args.work_dir, args.margin)
        if before != {str(path.resolve()): sha256_file(path) for path in sources}:
            raise ValueError('bounds source changed during verification')
        result.update(scope=__doc__, sources=before, synthetic=not sources)
    except (OSError, ValueError, KeyError, TypeError, OverflowError, subprocess.SubprocessError) as error:
        result = dict(passed=False, scope=__doc__, error=str(error))
    write_json(args.report, result)
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
