"""Independently reconstruct a bounded native Exotica scene-observer snapshot.

Checks live generated instance/quad bytes against Python, snapshot operands and
the original device context journal when requested. It does not certify live
material ownership or submit/render future geometry. Raw resources stay local.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import struct

from exotica_sections import sections
from verify_exotica_future import Memory, words
from verify_exotica_scene import reference, expected_bytes, verify_operands
from verify_zeus_state import serialized
from verification import sha256_file, write_json
from zeus_models import parse
from zeus_state import SCALARS, FLOATS, validate


def decode_context(raw):
    if not 4 <= len(raw) <= 8192 or len(raw) % 4:
        raise ValueError('live scene context size')
    values = struct.unpack('<'+str(len(raw)//4)+'I', raw);offset = 0

    def take(size):
        nonlocal offset
        if size < 0 or offset+size > len(values):
            raise ValueError('truncated live scene context')
        result = list(values[offset:offset+size]);offset += size
        return result

    def word():
        return take(1)[0]

    def floating(w):
        return struct.unpack('<f', struct.pack('<I', w))[0]

    if word() != 0x31534358:
        raise ValueError('live scene context magic')
    frame, multiplier, margin_word, fade, bank, partial, scale, palette = take(8)
    margin = floating(margin_word)
    if (not 1800 <= frame <= 16000 or multiplier not in (1, 2, 3) or
            not 0 <= margin <= 256 or fade not in (0, 1) or bank not in (0, 1, 2) or partial not in (0, 1)):
        raise ValueError('live scene context bounds')
    position, view, alternate = take(3), take(9), take(9)
    call = dict(scale=scale, palette_setup=palette, state_constants=take(12),
                state_commands=take(46), programs=take(4))
    for i in range(4):
        call['program'+str(i)] = take(4)
    defaults = word()
    if not 1 <= defaults <= 16:
        raise ValueError('live scene default-state bounds')
    call['default_state'] = take(defaults)
    context = dict(zip(SCALARS, take(len(SCALARS))))
    for key, size in FLOATS:
        context[key] = list(map(floating, take(size)))
    context['regs'] = take(128);context['render'] = take(80);context['render_policy'] = 0
    if offset != len(values):
        raise ValueError('live scene context trailing words')
    validate(context)
    return dict(frame=frame, multiplier=multiplier, margin=margin, fade=fade, bank=bank,
                partial=bool(partial), position=position, view=view, alternate=alternate,
                call=call, context=context)


def fnv_bytes(raw):
    value = 14695981039346656037
    for byte in raw:
        value = ((value ^ byte)*1099511628211) & 0xffffffffffffffff
    return f'{value:016x}'


def check_boundary(events, row, position):
    if not events or len(events) > 65536:
        raise ValueError('scene boundary event budget')
    pcs = dict(begin=0x67f6, static=0x6820, end=0x6836, model=0x6964, special=0x6c92)
    previous = -1.
    for event in events:
        if (event['kind'] not in pcs or event['pc'] != pcs[event['kind']] or
                not math.isfinite(event['time']) or event['time'] < previous or
                not 1700 <= event['frame'] <= 16000 or len(event['camera']) != 3):
            raise ValueError('scene boundary event identity')
        previous = event['time']
    beginnings = [i for i, e in enumerate(events) if e['kind'] == 'begin' and
                  abs(e['time']-float(row['scene_time'])) < 1e-11]
    if len(beginnings) != 1:
        raise ValueError('missing or ambiguous game scene boundary')
    first = beginnings[0]
    ends = [i for i in range(first+1, len(events)) if events[i]['kind'] in ('begin', 'end')]
    if not ends or events[ends[0]]['kind'] != 'end':
        raise ValueError('incomplete game scenery lists')
    scene = events[first:ends[0]+1]
    starts = [i for i, e in enumerate(scene) if e['kind'] == 'static']
    if len(starts) != 1 or scene[0]['frame'] != int(row['scene_frame']):
        raise ValueError('game scenery list boundary mismatch')
    eligible = [e for e in scene[starts[0]+1:-1] if e['kind'] == 'model' and
                not (e['flags'] & 0x80) and (e['flags'] & 3) in (0, 3)]
    if (not eligible or abs(eligible[0]['time']-float(row['cpu_time'])) >= 1e-11 or
            eligible[0]['frame'] != int(row['cpu_frame']) or
            eligible[0]['camera'] != position or scene[0]['camera'] != position):
        raise ValueError('observer did not select first supported model of this game scene')
    return dict(passed=True, game_scene=int(row['scene']), cpu_frame=int(row['cpu_frame']),
                scene_frame=int(row['scene_frame']), supported_models=len(eligible),
                initial_special_models=sum(e['kind'] == 'special' for e in scene[:starts[0]]),
                first_supported_model=True, camera_matches=True)


def check(directory, frame, require_original=False, require_boundary=False):
    directory = directory.resolve();prefix = directory/f'exotica-host-{frame}'
    paths = [Path(str(prefix)+suffix) for suffix in ('-context.bin', '-ram.bin', '-wave.bin', '-quads.bin', '-instances.bin')]
    paths += [directory/name for name in ('exotica-host-main-rom.bin', 'exotica-host-banked-rom.bin', 'exotica-host-scenes.csv')]
    if require_boundary:
        paths += [directory/'exotica-scene-events.jsonl', directory/'exotica-scene-events.json']
    before = {p.relative_to(directory).as_posix(): sha256_file(p) for p in paths}
    args = decode_context(paths[0].read_bytes())
    if args['frame'] != frame:
        raise ValueError('live scene snapshot identity')
    read = Memory(words(paths[1], 0x100000), words(paths[5], 0x800000), words(paths[6], 0x3000000), args['bank'])
    verify_operands(read, args['call'], args['position'])
    if paths[2].stat().st_size != 0x1000000:
        raise ValueError('live scene WaveRAM size')
    sources = sections(read, args['partial'])
    instances, counts = reference(sources['sources'], read, paths[2].read_bytes(), frame, args['margin'], args['fade'],
                                  args['call'], args['context'], args['position'], args['view'], args['alternate'])
    expected, expected_headers, summary = expected_bytes(instances, args['multiplier'])
    actual, headers = paths[3].read_bytes(), paths[4].read_bytes()
    if actual != expected or headers != expected_headers:
        raise ValueError('live native scene instance/geometry mismatch')
    if paths[7].stat().st_size > 8*1024*1024:
        raise ValueError('live scene log size')
    with paths[7].open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    fingerprint = fnv_bytes(actual)
    matched = [r for r in rows if int(r['frame']) == frame and r['hash'] == fingerprint]
    if len(matched) != 1:
        raise ValueError('ambiguous or missing live scene fingerprint')
    row = matched[0]
    if (int(row['instances']) != summary['instances'] or int(row['quads']) != summary['quads'] or
            int(row['viewport']) != summary['viewport_quads'] or int(row['sources']) != len(sources['sources']) or
            int(row['guest_cycles']) or int(row['bank']) != args['bank'] or int(row['partial']) != args['partial']):
        raise ValueError('live scene counters/cycles/source state mismatch')
    original = None
    boundary = None
    if require_boundary:
        if paths[8].stat().st_size > 32*1024*1024:
            raise ValueError('scene boundary journal budget')
        events = [json.loads(line) for line in paths[8].read_text(encoding='utf-8').splitlines()]
        receipt = json.loads(paths[9].read_text(encoding='utf-8'))
        if receipt.get('complete') is not True or receipt.get('events') != len(events):
            raise ValueError('incomplete scene boundary journal')
        boundary = check_boundary(events, row, args['position'])
    if require_original:
        model_path = directory/'zeus-capture/models.bin'
        candidates = [m for m in parse(model_path) if m['frame'] == frame and m['base'] == int(row['base']) and
                      m['count'] == int(row['count']) and abs(m['time']-float(row['device_time'])) < 1e-11]
        if len(candidates) != 1 or serialized(candidates[0]) != serialized(args['context']):
            raise ValueError('live scene context differs from original model journal')
        original = dict(model=candidates[0]['id'], frame=frame, exact_context=True, sha256=sha256_file(model_path))
    if before != {p.relative_to(directory).as_posix(): sha256_file(p) for p in paths}:
        raise ValueError('live scene snapshot changed during verification')
    return dict(schema=1, passed=True, scope=__doc__, frame=frame, multiplier=args['multiplier'],
                completed_fade=bool(args['fade']), sources=len(sources['sources']), counts=summary,
                original_context=original, game_scene_boundary=boundary, ordered_hash=fingerprint, immutable_inputs=True, inputs=before)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path);p.add_argument('--frame', type=int, required=True)
    p.add_argument('--require-original-context', action='store_true');p.add_argument('--report', type=Path, required=True)
    p.add_argument('--require-scene-boundary', action='store_true')
    a = p.parse_args()
    try:
        r = check(a.directory, a.frame, a.require_original_context, a.require_scene_boundary)
    except (ValueError, OSError, TypeError, KeyError, OverflowError) as error:
        r = dict(schema=1, passed=False, scope=__doc__, error=str(error))
    write_json(a.report, r);print('PASS' if r['passed'] else 'FAIL', a.report)
    return 0 if r['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
