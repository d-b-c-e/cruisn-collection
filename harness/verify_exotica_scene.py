"""Verify private Exotica future-scene assembly from local original captures.

Reconstruct the camera/context join and all section sources independently in
Python, then compare every native instance and projected quad at 1/2/3x, with
original and completed fade flags, plus a repeat. This is generated geometry,
NOT an original-hardware submission, material-residency or live-render verdict.
Raw input resources and generated geometry must remain local.
"""
import argparse
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import struct
import subprocess

import numpy as np
from exotica_sections import sections
from exotica_state import setup
from exotica_transform import prepare, packet, select_model
from scenery_c31 import signed
from verify_exotica_future import Memory, words
from verify_exotica_transforms import read_rows
from verify_zeus_state import floats, verify as verify_original_state
from verify_zeus_models import verify as verify_original_geometry
from verification import sha256_file, write_json
from zeus_model import decode
from zeus_models import parse
from zeus_state import SCALARS, FLOATS, transition, validate
from zeus_capture import ARTIFACTS, validate as validate_resources


def csv_rows(path):
    if path.stat().st_size > 16*1024*1024:
        raise ValueError('scene CSV budget')
    with path.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) > 20001:
        raise ValueError('scene row budget')
    return rows


def unique_frame(rows, frame):
    selected = [r for r in rows if int(r['frame']) == frame]
    if len(selected) != 1:
        raise ValueError('missing or duplicate scene frame')
    return selected[0]


def join_context(calls, models, position, view):
    by_key = defaultdict(list)
    for row in calls:
        if not row['flags'] & 0x80:
            _, translation = floats(row)
            by_key[row['metadata'][3], row['metadata'][4], *translation].append(row)
    matching = []
    for model in models:
        key = (model['base'], model['count'], *model['translation'][:3])
        candidates = [r for r in by_key[key] if r['native_frame'] in (model['frame'], model['frame']-1)
                      and 0 <= model['time']-r['time'] < .0176]
        if len(candidates) > 1:
            raise ValueError('ambiguous scene CPU/device join')
        if candidates and candidates[0]['camera'] == position and candidates[0]['view'] == view:
            matching.append((model, candidates[0]))
    if not matching:
        raise ValueError('no original context with the snapshot camera')
    alternate = {tuple(call['alternate']) for _, call in matching}
    if len(alternate) != 1:
        raise ValueError('ambiguous scene billboard rotation')
    ordinary = [(model, call) for model, call in matching if call['flags'] & 3 in (0, 3)]
    if not ordinary:
        raise ValueError('no ordinary scene context')
    model, call = ordinary[0]
    if any(m['render_policy'] for m, _ in matching):
        raise ValueError('scene assembler supports legacy render policy only')
    validate(model)
    return model, call, list(next(iter(alternate))), dict(
        matching=len(matching), chosen_model=model['id'], chosen_call=call['id'],
        cpu_time=[min(c['time'] for _, c in matching), max(c['time'] for _, c in matching)],
        device_time=[min(m['time'] for m, _ in matching), max(m['time'] for m, _ in matching)])


def verify_operands(read, call, position):
    if position != read.words(0xfeb, 3):
        raise ValueError('scene snapshot camera mismatch')
    programs = [read(a) for a in (0xe7c1, 0xe7c7, 0xe7d3, 0xe7d9)]
    default = read(0xe4)
    size = read(default)+1
    if not 1 <= size <= 16:
        raise ValueError('scene default-state budget')
    if (read.words(0x67d0, 12) != call['state_constants'] or
            read.words(0xb479, 46) != call['state_commands'] or programs != call['programs'] or
            any(read.words(p, 4) != call['program'+str(i)] for i, p in enumerate(programs)) or
            read.words(default+1, size) != call['default_state'] or
            read(0x15f2) != call['palette_setup'] or read(0x67db) != call['scale'] or
            read(0x67da) != 204800):
        raise ValueError('scene snapshot/setup operand mismatch')


def context_bytes(frame, multiplier, margin, fade, progress, call, context, position, view, alternate):
    if (not 1800 <= frame <= 16000 or multiplier not in (1, 2, 3) or
            not math.isfinite(margin) or not 0 <= margin <= 256 or fade not in (0, 1) or
            context.get('render_policy', 0)):
        raise ValueError('scene context bounds/policy')
    bits = lambda f: struct.unpack('<I', struct.pack('<f', f))[0]
    values = [0x31534358, frame, multiplier, bits(margin), fade,
              int(progress['bank']), int(progress['loading']), call['scale'], call['palette_setup'],
              *position, *view, *alternate, *call['state_constants'], *call['state_commands'],
              *call['programs'], *[w for i in range(4) for w in call['program'+str(i)]],
              len(call['default_state']), *call['default_state'], *[context[k] for k in SCALARS],
              *[bits(f) for k, _ in FLOATS for f in context[k]], *context['regs'], *context['render']]
    return struct.pack('<'+str(len(values))+'I', *values)


def explicit_texture(model, quad_size):
    index = 0; texture = format_seen = False
    while index < len(model):
        op = model[index] >> 24
        size = quad_size if op == 0x38 else 2
        if size > len(model)-index:
            raise ValueError('scene incomplete model')
        d = model[index:index+size];index += size
        if op in (0, 0x22):
            format_seen = True
        if op == 0x36 and (d[0] >> 16) & 127 == 0x20 and d[1] >> 24 == 5:
            texture = True
        if op == 0x38 and not (texture and format_seen):
            raise ValueError('scene inherited model texture')


def reference(sources, read, wave, frame, margin, fade, call, context, position, view, alternate):
    """Build at 3x once; band filtering preserves original source/quad order."""
    instances = []; identities = set();selected = unsupported = culled = 0
    for source in sources:
        if not source['supported'] or not source['future']:
            continue
        key = (source['entry'], source['source'])
        if key in identities:
            raise ValueError('duplicate scene source')
        identities.add(key);selected += 1
        obj = source['words'];flags = obj[15]
        if flags & 3 not in (0, 3) or flags & 0x80:
            unsupported += 1;continue
        transform = prepare(obj[1:4], position, view, obj[5:14], alternate, flags)
        radius = signed(obj[21]);distance = transform['depth']+radius
        if not 0 <= radius < 10000000:
            raise ValueError('scene radius')
        if transform['depth'] <= 0 or distance > 614400:
            culled += 1;continue
        descriptor = select_model(obj[17], read(obj[17]), transform['depth'])
        base, count = read.words(descriptor+3, 2)
        block = base % 1024+((base >> 16) % 2048)*1024
        if not base or count > 0xc800 or 8*(block+count+1) > len(wave):
            raise ValueError('scene model bounds')
        model = list(struct.unpack_from('<'+str(2*(count+1))+'I', wave, block*8))
        if fade:
            flags &= ~0x04000100
        state = setup(obj, flags, [0xffffffff]*3, call['state_constants'], call['state_commands'],
                      call['programs'], [call['program'+str(i)] for i in range(4)],
                      call['default_state'], call['palette_setup'])
        private, _ = transition(context, [], state['packet']+packet(transform, call['scale'], 1), base)
        if private['regs'][0x40] != 0x0084003f:
            raise ValueError('scene unsupported palette request')
        explicit_texture(model, private['quad_size'])
        private['frame'] = frame;private['words'] = model
        quads, _ = decode(private);raw = bytearray();viewport = 0
        for fields, vertices in quads:
            x, y = vertices[:, 0], vertices[:, 1]
            viewport += max(x) >= -margin and min(x) <= 512+margin and max(y) >= 0 and min(y) <= 400
            padded = np.zeros((8, 6), dtype='<f4');padded[:len(vertices)] = vertices
            raw.extend(struct.pack('<17I', *fields)+padded.tobytes())
        band = (distance-1)//204800+1
        header = [*key, descriptor, base, count, band, private['palette'], private['regs'][0x40],
                  transform['depth'] & 0xffffffff]
        instances.append(dict(header=header, band=band, raw=raw, viewport=int(viewport)))
    return instances, dict(selected=selected, unsupported_transform=unsupported, culled_distance=culled)


def expected_bytes(instances, multiplier):
    quads = bytearray();headers = bytearray();viewport = 0;included = 0
    for row in instances:
        if row['band'] > multiplier:
            continue
        headers.extend(struct.pack('<11I', *row['header'], len(quads)//260, len(row['raw'])//260))
        quads.extend(row['raw']);viewport += row['viewport'];included += 1
    return quads, headers, dict(instances=included, quads=len(quads)//260, viewport_quads=viewport)


def check(directory, frame, margin, native, output):
    directory = directory.resolve();native = native.resolve();output = output.resolve()
    if not 1800 <= frame <= 16000 or not math.isfinite(margin) or not 0 <= margin <= 256:
        raise ValueError('scene frame/margin bounds')
    output.mkdir(parents=True, exist_ok=False)
    capture = directory/'zeus-capture'
    paths = [directory/name for name in ('exotica-section-capture.json', 'exotica-section-progress.csv',
             'exotica-camera.csv', 'exotica-model-capture.json', 'exotica-models.jsonl', 'exotica-emissions.jsonl',
             'exotica-main-rom.bin', 'exotica-banked-rom.bin', f'exotica-section-{frame}.bin')]
    paths += [capture/name for name in ('models.json', 'models.bin', *ARTIFACTS)]
    before = {p.relative_to(directory).as_posix(): sha256_file(p) for p in paths}
    native_hash = sha256_file(native)
    receipt = json.loads((directory/'exotica-section-capture.json').read_text(encoding='utf-8'))
    if (receipt.get('schema') != 1 or receipt.get('complete') is not True or
            not receipt['first'] <= frame <= receipt['last'] or receipt['last']-receipt['first'] > 20000):
        raise ValueError('incomplete scene section capture')
    validate_resources(capture, frame)
    original = verify_original_state(directory)
    geometry = verify_original_geometry(capture)
    progress = unique_frame(csv_rows(directory/'exotica-section-progress.csv'), frame)
    camera = unique_frame(csv_rows(directory/'exotica-camera.csv'), frame)
    position = [int(camera[k], 16) for k in ('x', 'y', 'z')]
    view = [int(camera['m'+str(i)], 16) for i in range(9)]
    ram = directory/f'exotica-section-{frame}.bin'
    read = Memory(words(ram, 0x100000), words(directory/'exotica-main-rom.bin', 0x800000),
                  words(directory/'exotica-banked-rom.bin', 0x3000000), int(progress['bank']))
    context, call, alternate, joins = join_context(read_rows(directory/'exotica-models.jsonl'),
                                                  parse(capture/'models.bin'), position, view)
    verify_operands(read, call, position)
    if (capture/'waveram.bin').stat().st_size != 0x1000000:
        raise ValueError('scene WaveRAM snapshot size')
    wave = (capture/'waveram.bin').read_bytes()
    source_result = sections(read, bool(int(progress['loading'])))
    results = []
    for fade in (0, 1):
        instances, counts = reference(source_result['sources'], read, wave, frame, margin, fade,
                                      call, context, position, view, alternate)
        repeat = None
        for ordinal, multiplier in enumerate((1, 2, 3, 3)):
            prefix = output/f'fade{fade}-{ordinal}-{multiplier}x'
            binary_context = prefix.with_suffix('.context')
            binary_context.write_bytes(context_bytes(frame, multiplier, margin, fade, progress, call,
                                                      context, position, view, alternate))
            command = [str(native), str(ram), str(directory/'exotica-main-rom.bin'),
                       str(directory/'exotica-banked-rom.bin'), str(capture/'waveram.bin'),
                       str(binary_context), str(prefix)]
            run = subprocess.run(command, capture_output=True, text=True, timeout=60)
            prefix.with_suffix('.stdout.txt').write_text(run.stdout, encoding='utf-8')
            prefix.with_suffix('.stderr.txt').write_text(run.stderr, encoding='utf-8')
            if run.returncode:
                raise ValueError(f'native scene rejected {prefix.name}: {run.stderr[:1000]}')
            actual = json.loads(run.stdout)
            raw = Path(str(prefix)+'-quads.bin').read_bytes()
            headers = Path(str(prefix)+'-instances.bin').read_bytes()
            expected, expected_headers, summary = expected_bytes(instances, multiplier)
            if raw != expected or headers != expected_headers:
                raise ValueError(f'native scene geometry mismatch {prefix.name}')
            expected_counts = dict(counts, **summary)
            expected_counts['culled_distance'] += sum(r['band'] > multiplier for r in instances)
            if any(actual[k] != v for k, v in expected_counts.items()):
                raise ValueError(f'native scene counter mismatch {prefix.name}')
            if ordinal == 3 and repeat != (raw, headers):
                raise ValueError('native scene repeat mismatch')
            if ordinal == 2:
                repeat = (raw, headers)
            results.append(dict(fade='completed' if fade else 'original', multiplier=multiplier,
                                repeat=ordinal == 3, passed=True, native=actual,
                                quad_sha256=sha256_file(Path(str(prefix)+'-quads.bin')),
                                instance_sha256=sha256_file(Path(str(prefix)+'-instances.bin'))))
    after = {p.relative_to(directory).as_posix(): sha256_file(p) for p in paths}
    if before != after or native_hash != sha256_file(native):
        raise ValueError('scene inputs/native changed during verification')
    return dict(schema=1, passed=True, scope=__doc__, frame=frame, margin=margin, joins=joins,
                original_context_pairs=original['consecutive_contexts'],
                original_ordered_quads=geometry['covered_quads'], cases=results,
                native_sha256=native_hash, sources=before, immutable_inputs=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path);p.add_argument('--frame', type=int, required=True)
    p.add_argument('--margin', type=float, required=True);p.add_argument('--native', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True);p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    try:
        result = check(a.directory, a.frame, a.margin, a.native, a.output)
    except (ValueError, OSError, KeyError, TypeError, OverflowError, subprocess.SubprocessError) as error:
        result = dict(schema=1, passed=False, scope=__doc__, error=str(error))
    write_json(a.report, result);print('PASS' if result['passed'] else 'FAIL', a.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
