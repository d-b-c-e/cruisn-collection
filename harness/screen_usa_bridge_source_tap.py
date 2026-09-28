"""Qualify one exact-hook USA bridge projection against a saved native scene.

The read-only Lua tap captures RAM/resources at the actual C31 host scene. An
independent reconstruction must reproduce the entire ordinary ordered scene
before its partial-far-coverage counterfactual is considered. No candidate
pixels or temporal appearance are inferred from this source-only screen.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

from analyze_vunit_margin_gap import projected_box
from analyze_world_host import HASH_SEED, hash_quad
from screen_vunit_panorama_strips import sha
from usa_future_scene import collect
from verify_usa_future import Memory
from verify_usa_host import reference

FRAME = 10473
TARGET = 0x800a0040
COUNTERS = ('candidates', 'unsupported', 'near', 'far', 'projection', 'decoded')


def scene(path):
    with path.open(newline='', encoding='utf-8') as stream:
        rows = [row for row in csv.DictReader(stream) if int(row['frame']) == FRAME]
    if len(rows) != 1:
        raise ValueError('source scene is absent or ambiguous')
    return rows[0]


def screen(source, traced, activation_path, rom_path, lua_path):
    src_report = json.loads((source / 'report.json').read_text(encoding='utf-8'))
    trace_report = json.loads((traced / 'report.json').read_text(encoding='utf-8'))
    invocation = json.loads((source / 'run/invocation.json').read_text(encoding='utf-8'))
    activation = json.loads(activation_path.read_text(encoding='utf-8'))
    if (not src_report['passed'] or not src_report['comparison']['passed'] or
            not src_report['display_watch']['passed'] or
            src_report['vunit_runtime']['result']['completion'] != 'owned-worker-stop' or
            not trace_report['passed'] or not trace_report['comparison']['passed'] or
            src_report['case'] != trace_report['case'] or
            src_report['emulator_source']['executable_sha256'] !=
            trace_report['emulator_source']['executable_sha256'] or
            invocation['environment'].get('MIDV_FFB') != '0' or
            invocation['environment'].get('MIDV_RAMDUMP_EVERY') != str(FRAME) or
            sha(source / 'run/probe.lua') != sha(lua_path) or
            not activation['passed'] or
            activation['sha256']['detailed_replay_report'] != sha(traced / 'report.json') or
            activation['sha256']['program_rom'] != sha(rom_path)):
        raise ValueError('source tap/recording/native/activation provenance differs')
    receipt_path = source / f'run/usa-source-{FRAME}-receipt.csv'
    with receipt_path.open(newline='', encoding='utf-8') as stream:
        receipt = list(csv.DictReader(stream))
    if receipt != [dict(frame=str(FRAME), pc='81', scene_address='40', rom='crusnusa')]:
        raise ValueError('tap missed the requested C31 source read')
    live = scene(source / 'run/usa-host-scenes.csv')
    old_trace = scene(traced / 'run/usa-host-scenes.csv')
    for key in ('frame', 'time', 'page', 'quads', 'quads_hash'):
        if live[key] != old_trace[key]:
            raise ValueError('read tap changed the source scene')
    ram = source / f'run/usa-source-{FRAME}-ram.bin'
    fast = source / f'run/usa-source-{FRAME}-fast.bin'
    texture = source / f'run/usa-source-{FRAME}-textures.bin'
    palette = source / f'run/usa-source-{FRAME}-palettes.bin'
    for path, size in ((ram, 0x80000), (fast, 0x2000),
                       (texture, 0x800000), (palette, 0x20000)):
        if path.stat().st_size != size:
            raise ValueError('source-time resource has wrong extent')
    memory = Memory(rom_path.read_bytes(), ram.read_bytes(), fast.read_bytes())
    future, stats, objects = collect(memory)
    target = [(owner, words) for owner, words in objects if owner == TARGET]
    match = [item for item in activation['objects'] if item['object'] == hex(TARGET)]
    if (len(target) != 1 or len(match) != 1 or
            match[0]['first_scene']['frame'] != 10475 or stats['unbound'] or stats['deferred']):
        raise ValueError('pre-activation target is not uniquely material-ready')
    old_counts, old_quads = reference(memory, 240000, future=objects)
    fingerprint = HASH_SEED
    for row in old_quads:
        fingerprint = hash_quad(fingerprint, tuple(row[3:19]))
    native_counts = [int(live['pending']) + int(live['future_ready'])] + \
        [int(live[key]) for key in COUNTERS[1:]]
    if (old_counts != native_counts or
            len(old_quads) != int(live['quads']) or
            f'{fingerprint:016x}' != live['quads_hash'] or
            any(row[0] == TARGET for row in old_quads)):
        raise ValueError('independent ordinary scene does not match native')
    new_counts, new_quads = reference(memory, 240000, future=objects,
                                      far_coverage=True)
    old16 = Counter(tuple(row[:19]) for row in old_quads)
    new16 = Counter(tuple(row[:19]) for row in new_quads)
    added = new16 - old16
    old_sequence = iter(tuple(row[:19]) for row in old_quads)
    next_old = next(old_sequence, None)
    for row in new_quads:
        if tuple(row[:19]) == next_old:
            next_old = next(old_sequence, None)
    target_quads = [row for row in new_quads if row[0] == TARGET]
    if (old16 - new16 or next_old is not None or len(new_quads) != 3782 or
            sum(added.values()) != 76 or
            len(target_quads) != 3 or new_counts[:4] != old_counts[:4] or
            new_counts[4:] != [0, 987]):
        raise ValueError('partial-coverage projection is not the qualified addition')
    return dict(schema=1, passed=True,
                scope='Exact C31 source frame 10473 on one USA Golden Gate drive. '
                      'The existing opt-in partial coverage is reconstructed offline; '
                      'no live candidate source packet or completed-pixel attribution.',
                source_clock=dict(frame=FRAME, time=live['time'], page=int(live['page']),
                                  pc='81', scene_address='40'),
                original=dict(counters=dict(zip(COUNTERS, old_counts)),
                              quads=len(old_quads), fingerprint=live['quads_hash'],
                              agrees_with_prior_detailed_trace=True),
                partial_coverage=dict(counters=dict(zip(COUNTERS, new_counts)),
                                      quads=len(new_quads), old_ordered_words_preserved=True,
                                      additional_quads=sum(added.values()),
                                      target_quads=len(target_quads),
                                      target_boxes=[projected_box(tuple(row[3:19]))
                                                    for row in target_quads]),
                target=dict(object=hex(TARGET), ready=True,
                            first_logged_submission=match[0]['first_scene']['frame'],
                            future_sections=stats['sections'],
                            future_definitions=stats['definitions'],
                            future_ready=stats['ready'], uploads=stats['uploads']),
                sha256={'source_report': sha(source / 'report.json'),
                        'trace_report': sha(traced / 'report.json'),
                        'activation': sha(activation_path), 'invocation': sha(source / 'run/invocation.json'),
                        'lua': sha(lua_path), 'tap_receipt': sha(receipt_path),
                        'source_scenes': sha(source / 'run/usa-host-scenes.csv'),
                        'trace_scenes': sha(traced / 'run/usa-host-scenes.csv'),
                        'ram': sha(ram), 'fast': sha(fast), 'texture': sha(texture),
                        'palette': sha(palette), 'rom': sha(rom_path)})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'traced', 'activation', 'rom', 'lua', 'report'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite source-tap qualification')
    result = screen(args.source, args.traced, args.activation, args.rom, args.lua)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', result['original']['quads'], result['partial_coverage']['additional_quads'])


if __name__ == '__main__':
    main()
