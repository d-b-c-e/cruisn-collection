"""Bind a live USA partial-coverage scene to an exact source reconstruction.

Only source geometry, recorded motion and owned shutdown are checked here.
Completed pixels and visual transitions belong to a separate matched trial.
"""
import argparse
import csv
import json
from pathlib import Path

from analyze_world_host import HASH_SEED, hash_quad
from qualify_usa_farcoverage_interval import frames
from screen_vunit_panorama_strips import sha
from usa_future_scene import collect
from verify_usa_future import Memory
from verify_usa_host import reference

FRAME = 10473
COUNTERS = ('unsupported', 'near', 'far', 'projection', 'decoded')


def at_frame(path):
    with path.open(newline='', encoding='utf-8') as stream:
        rows = [row for row in csv.DictReader(stream) if int(row['frame']) == FRAME]
    if len(rows) != 1:
        raise ValueError('native candidate source scene is absent or ambiguous')
    return rows[0]


def qualify(off, on, source_screen, rom_path):
    source = json.loads(source_screen.read_text(encoding='utf-8'))
    a = json.loads((off / 'report.json').read_text(encoding='utf-8'))
    b = json.loads((on / 'report.json').read_text(encoding='utf-8'))
    if (not source.get('passed') or
            source['sha256']['source_report'] != sha(off / 'report.json') or
            source['sha256']['rom'] != sha(rom_path) or
            not b['passed'] or not b['comparison']['passed'] or
            not b['display_watch']['passed'] or
            b['vunit_runtime']['result']['completion'] != 'owned-worker-stop' or
            a['case'] != b['case'] or
            a['emulator_source']['executable_sha256'] !=
            b['emulator_source']['executable_sha256'] or
            a['comparison_scope'] != b['comparison_scope'] or
            b['comparison_scope']['last_frame'] != 10477 or
            a['display_target'] != b['display_target']):
        raise ValueError('candidate replay/recording/display/source qualification differs')
    for root in (off, on):
        invocation = json.loads((root / 'run/invocation.json').read_text(encoding='utf-8'))
        if invocation['environment'].get('MIDV_FFB') != '0':
            raise ValueError('physical force was not explicitly disabled')
    modes = [dict(r['usa_host_scenery']) for r in (a, b)]
    toggle = [mode.pop('far_coverage') for mode in modes]
    if toggle != ['off', 'on'] or modes[0] != modes[1] or \
            frames(off / 'run/frames.csv') != frames(on / 'run/frames.csv'):
        raise ValueError('replay differs beyond the gated far-coverage toggle')
    original = at_frame(off / 'run/usa-host-scenes.csv')
    candidate = at_frame(on / 'run/usa-host-scenes.csv')
    for key in ('frame', 'time', 'page'):
        if original[key] != candidate[key]:
            raise ValueError('candidate scene clock/page differs')
    if (int(original['quads']) != source['original']['quads'] or
            original['quads_hash'] != source['original']['fingerprint']):
        raise ValueError('source screen no longer names original scene')
    memory = Memory(rom_path.read_bytes(),
                    (off / f'run/usa-source-{FRAME}-ram.bin').read_bytes(),
                    (off / f'run/usa-source-{FRAME}-fast.bin').read_bytes())
    _, _, objects = collect(memory)
    counts, quads = reference(memory, 240000, future=objects, far_coverage=True)
    fingerprint = HASH_SEED
    for row in quads:
        fingerprint = hash_quad(fingerprint, tuple(row[3:19]))
    native_counts = [int(candidate['pending']) + int(candidate['future_ready'])] + \
        [int(candidate[key]) for key in COUNTERS]
    if (counts != native_counts or
            len(quads) != source['partial_coverage']['quads'] or
            len(quads) != int(candidate['quads']) or
            f'{fingerprint:016x}' != candidate['quads_hash']):
        raise ValueError('native partial-coverage scene differs from source oracle')
    return dict(schema=1, passed=True,
                scope='One exact USA source scene at 10473 on physical 1440p/FFB0. '
                      'Live candidate geometry matches independent source projection; '
                      'no completed image, packet-pixel, performance or route-wide acceptance.',
                input_frames=10477, scene_frame=FRAME, page=int(candidate['page']),
                source_time=candidate['time'], original_quads=int(original['quads']),
                candidate_quads=len(quads), additional_quads=len(quads)-int(original['quads']),
                candidate_fingerprint=candidate['quads_hash'],
                counters=dict(zip(('candidates',)+COUNTERS, counts)),
                recorded_frame_clocks_identical=True, original_native_comparisons_passed=True,
                owned_shutdowns=True,
                sha256={'source_screen': sha(source_screen),
                        'control_report': sha(off / 'report.json'),
                        'candidate_report': sha(on / 'report.json'),
                        'control_scenes': sha(off / 'run/usa-host-scenes.csv'),
                        'candidate_scenes': sha(on / 'run/usa-host-scenes.csv'),
                        'control_frames': sha(off / 'run/frames.csv'),
                        'candidate_frames': sha(on / 'run/frames.csv'),
                        'rom': sha(rom_path)})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('off', 'on', 'source_screen', 'rom', 'report'):
        ap.add_argument('--' + name.replace('_', '-'), dest=name, type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite candidate scene qualification')
    result = qualify(args.off, args.on, args.source_screen, args.rom)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', result['candidate_quads'], result['candidate_fingerprint'])


if __name__ == '__main__':
    main()
