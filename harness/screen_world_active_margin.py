"""Census World active lists at a matched black-margin source frame.

This is source membership evidence only. It does not project models, establish
texture residency, or qualify a renderer policy.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import struct

from world_future_sections import future, layout, section_definitions


HEADS = {24: (0x61ee, 0x61eb, 0x61ed, 0x61ef),
         25: (0x658f, 0x658c, 0x658e, 0x6590)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(run, rom_path, revision):
    if revision not in HEADS:
        raise ValueError('unsupported World revision')
    report_path = run / 'report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if report.get('passed') is not True or report['vunit_original_mirror']['result']['host_completion'][
            'captured_preparation_matches_visible'] is not True:
        raise ValueError('source replay or visible-page join is unqualified')
    source = report['vunit_original_mirror']['result']['host_completion']['visible']['frame']
    receipt = report['capture']['source_ram']
    ram_path = run / 'run/capture' / receipt['file']
    if receipt['frame'] != source or receipt['bytes'] != 0x80000 or sha(ram_path) != receipt['sha256']:
        raise ValueError('program RAM does not match visible source')
    ram, rom = ram_path.read_bytes(), rom_path.read_bytes()
    if len(ram) != 0x80000 or len(rom) != 0x1000000:
        raise ValueError('incomplete World RAM or ROM')

    def read(p):
        if 0 <= p < 0x20000:
            return struct.unpack_from('<I', ram, p*4)[0]
        if 0xc00000 <= p < 0x1000000:
            return struct.unpack_from('<I', rom, (p-0xc00000)*4)[0]
        raise ValueError(f'unmapped operand {p:x}')

    # The game's four list walkers must be the known World 2.4/2.5 revision.
    for offset, head in enumerate(HEADS[revision]):
        pc = (0x69, 0x6c, 0x6f, 0x72)[offset]
        if read(pc) != (0x08280000 | head) or read(pc+1) != 0x6200034c:
            raise ValueError('World active-list code does not match revision')
    seen = set()
    lists = []
    for global_addr in HEADS[revision]:
        sentinel = read(global_addr)
        if not 0x1000 <= sentinel < 0x20000:
            raise ValueError('invalid active-list sentinel')
        p = read(sentinel)
        flags = Counter()
        count = roads = 0
        while p:
            if (not 0x1000 <= p <= 0x20000-32 or p in seen or len(seen) >= 2048):
                raise ValueError('invalid or cyclic active-list object')
            seen.add(p)
            word = read(p+14)
            flags[f'{word & 0x3861:#x}'] += 1
            roads += (word & 0x3861) == 0x1001 and read(p+16) <= 65535 and read(p+17) <= 65535
            count += 1
            p = read(p)
        lists.append({'global': hex(global_addr), 'sentinel': hex(sentinel),
                      'objects': count, 'eligible_active_roads': int(roads),
                      'flag_classes': dict(sorted(flags.items()))})
    profile = layout(revision)
    start, stage, cursor = (read(profile[key]) for key in ('section', 'stage', 'cursor'))
    current, _ = section_definitions(read, start)
    future_scene = future(read, revision=revision)
    native_scene_path = run / 'run/world-host-scenes.csv'
    with native_scene_path.open(newline='', encoding='utf-8') as stream:
        native_rows = [row for row in csv.DictReader(stream) if int(row['frame']) == source]
    if len(native_rows) != 1:
        raise ValueError('missing or duplicated native source scene')
    native = native_rows[0]
    expected = {'future_definitions': len(future_scene['definitions']),
                'future_skipped': future_scene['skipped_allocated'],
                'future_stage': stage, 'future_cursor': cursor,
                'future_start': start}
    if any(int(native[key]) != value for key, value in expected.items()):
        raise ValueError('offline section frontier differs from native source scene')
    return {
        'passed': True, 'revision': revision, 'source_frame': source,
        'active_lists': lists, 'active_total': sum(item['objects'] for item in lists),
        'eligible_active_roads': sum(item['eligible_active_roads'] for item in lists),
        'frontier': {'start': hex(start), 'stage': stage, 'cursor': hex(cursor),
                     'current_section_definitions': len(current),
                     'future_definitions': len(future_scene['definitions']),
                     'skipped_allocated': future_scene['skipped_allocated']},
        'native_scene': {'future_definitions': int(native['future_definitions']),
                         'future_skipped': int(native['future_skipped']),
                         'road_objects': int(native['road_objects']),
                         'road_quads': int(native['road_quads'])},
        'source_sha256': {'report': sha(report_path), 'program_ram': sha(ram_path),
                          'program_rom': sha(rom_path),
                          'native_scene': sha(native_scene_path)},
        'scope': 'Exact RAM/list membership at one source frame; no model projection, material lifetime, '
                 'gap coverage, completed-image change, or cross-course claim.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--revision', type=int, choices=(24,25), required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite source census')
    result = analyze(args.run, args.rom, args.revision)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', result['source_frame'], result['active_total'], result['eligible_active_roads'])


if __name__ == '__main__':
    main()
