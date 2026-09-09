"""Check USA future section sources/frontiers against later guest allocations.

Raw ROM/RAM and allocation operands remain local. No GPU visibility claim.
"""
import argparse
import csv
import json
from pathlib import Path
import struct
import subprocess

from usa_sections import future, section_definitions, material_operands, placement, final_flags
from verification import sha256_file, write_json


class Memory:
    def __init__(self, rom, ram=None, fast=None, overlay=None):
        if len(rom) != 0x1000000 or ram is not None and len(ram) != 0x80000 or fast is not None and len(fast) != 0x2000:
            raise ValueError('incomplete USA memory snapshot')
        self.rom, self.ram, self.fast, self.overlay = rom, ram, fast, overlay or {}

    def __call__(self, p):
        if p in self.overlay:
            return self.overlay[p]
        for start, data in ((0, self.ram), (0x809800, self.fast), (0xc00000, self.rom)):
            if data is not None and start <= p < start+len(data)//4:
                return struct.unpack_from('<I', data, 4*(p-start))[0]
        raise ValueError(f'uncaptured USA operand {p:x}')

    __getitem__ = __call__


def native_check(binary, run, frame, memory, decoded):
    command = [str(binary.resolve()), '--future', str(run/f'usa-future-ram-{frame}.bin'),
               str(run/f'usa-future-fast-{frame}.bin'), str(run/'usa-future-rom.bin')]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise ValueError('native USA future failed: '+result.stderr.strip())
    lines = [list(map(int, line.split())) for line in result.stdout.splitlines()]
    rows = decoded['definitions']
    expected_header = [decoded['start'], decoded['loading'], decoded['number'], int(decoded['partial']),
                       int(decoded['stop'] == 'track not initialized'), int(decoded['stop'] == 'end marker'), len(rows)]
    if not lines or lines[0] != expected_header or len(lines) != len(rows)+1:
        raise ValueError('native USA frontier/count mismatch')
    count = custom = 0
    for row, actual in zip(rows, lines[1:]):
        if len(actual) != 42:
            raise ValueError('incomplete native USA future descriptor')
        expected = [row['section_pointer'], row['source'], row['stage'], row['section_number']]
        meta = row['definition'][5]
        if meta & 0x2000:
            expected += [0]*38
            custom += 1
        else:
            operands = dict(row, trig_constants=[memory(0xc8ed+i) for i in range(7)],
                            **material_operands(memory, row['definition'][0]))
            xyz, heading, matrix = placement(operands)
            flags = final_flags(operands['model_prefix'], meta)
            expected += [int(not flags & 0x8e3), int(operands['palette_binding'] != 0),
                         operands['model_prefix'], operands['palette_binding']]
            obj = [0]*34
            obj[1:4], obj[4:13], obj[21] = xyz, matrix, heading
            obj[13], obj[14] = row['definition'][0], flags | 0x2000
            obj[15] = 0x300 if (meta >> 8) & 15 == 11 else meta & 0xfff
            obj[16] = (operands['palette_binding'] >> 16) << 8
            obj[31] = row['section_number'] << 8 | 0xaa
            if (meta >> 8) & 15 == 11:
                obj[30] = row['section_number'] << 8 | (255-(meta & 255) if row['section_flags'] & 8 else meta & 255)
            expected += obj
            count += 1
        if actual != expected:
            raise ValueError(f'native USA descriptor mismatch at snapshot {frame}, source {row["source"]}, stage {row["stage"]}')
    return dict(passed=True, compared=count, custom=custom, binary_sha256=sha256_file(binary))


def check(run, native=None):
    receipt = json.loads((run/'usa-future-capture.json').read_text())
    if receipt.get('schema') != 1 or receipt.get('complete') is not True:
        raise ValueError('incomplete USA future capture')
    rom = (run/'usa-future-rom.bin').read_bytes()
    base = Memory(rom)
    allocation = [json.loads(line) for line in (run/'usa-sections.jsonl').read_text().splitlines()]
    if not allocation or [r['serial'] for r in allocation] != list(range(1, len(allocation)+1)):
        raise ValueError('incomplete allocation trace')
    failures, source_checks, section_cache = [], 0, {}
    for row in allocation:
        p = row['section_pointer']
        if p not in section_cache:
            section_cache[p] = section_definitions(base, p)[0]
        expected = [r for r in section_cache[p] if r['source'] == row['source'] and r['stage'] == row['stage']]
        fields = ('definition', 'section_words', 'section_flags', 'heading')
        passed = len(expected) == 1 and all(row[k] == expected[0][k] for k in fields)
        source_checks += 1
        if not passed:
            failures.append(dict(kind='section source', serial=row['serial']))
    progress = list(csv.DictReader((run/'usa-future-progress.csv').open()))
    if len(progress) != receipt['scenes'] or not progress:
        raise ValueError('incomplete USA scene frontiers')
    last_time, keys, partial, initialized = -1, set(), 0, 0
    for entry in progress:
        clock = float(entry['time'])
        key = (entry['native_frame'], entry['time'], entry['page'])
        if key in keys or not clock > last_time or not receipt['first'] <= int(entry['frame']) <= receipt['last']:
            raise ValueError('duplicate, unordered or unbounded scene frontier')
        keys.add(key); last_time = clock
        overlay = {p: int(entry[k]) for p, k in ((0xa12e, 'track'), (0xe49d, 'loading'),
                                                (0xe4a5, 'next_section'), (0xe4a4, 'section_number'))}
        try:
            decoded = future(Memory(rom, overlay=overlay), sections=1)
            partial += decoded['partial']; initialized += decoded['stop'] != 'track not initialized'
        except ValueError as error:
            failures.append(dict(kind='frontier', frame=int(entry['frame']), error=str(error)))
    snapshots = []
    paths = sorted(run.glob('usa-future-scene-*.json'))
    if len(paths) != receipt['snapshots'] or not paths:
        raise ValueError('missing USA future snapshots')
    for path in paths:
        scene = json.loads(path.read_text()); frame = scene['frame']
        if (str(scene['native_frame']), scene['time'], str(scene['page'])) not in keys:
            raise ValueError('snapshot missing its exact native scene clock')
        ram_path, fast_path = run/f'usa-future-ram-{frame}.bin', run/f'usa-future-fast-{frame}.bin'
        memory = Memory(rom, ram_path.read_bytes(), fast_path.read_bytes())
        decoded = future(memory)
        predicted = {(r['section_pointer'], r['source'], r['stage']): r for r in decoded['definitions']}
        later = [r for r in allocation if r['frame'] > frame and
                 (r['section_pointer'], r['source'], r['stage']) in predicted]
        compared = bound = custom = supported = 0
        for row in later:
            expected = dict(predicted[row['section_pointer'], row['source'], row['stage']],
                            trig_constants=[memory(0xc8ed+i) for i in range(7)])
            expected.update(material_operands(memory, expected['definition'][0]))
            meta = expected['definition'][5]
            if meta & 0x2000:
                custom += 1
                continue
            xyz, heading, matrix = placement(expected)
            flags = final_flags(expected['model_prefix'], meta)
            obj = row['actual']; compared += 1
            checks = dict(position=xyz == obj[1:4], heading=heading == obj[21], matrix=matrix == obj[4:13],
                          flags=flags == obj[14] & ~0x3000, model=expected['definition'][0] == obj[13],
                          tag=(expected['section_number'] << 8 | 0xaa) == obj[31],
                          kind=(0x300 if (meta >> 8) & 15 == 11 else meta & 0xfff) == obj[15])
            if expected['model_prefix'] & 0x2000 and expected['palette_binding']:
                checks['resident_palette'] = (expected['palette_binding'] >> 16) << 8 == obj[16]
                bound += 1
            supported += not bool(flags & 0x8e3)
            if not all(checks.values()):
                failures.append(dict(kind='future descriptor', snapshot=frame, serial=row['serial'], checks=checks))
        snapshot = dict(frame=frame, definitions=len(predicted), later=len(later), compared=compared,
                              custom=custom, supported=supported, bound_palettes=bound, partial=decoded['partial'],
                              sources={p.name: sha256_file(p) for p in (path, ram_path, fast_path)})
        if native is not None:
            snapshot['native'] = native_check(native, run, frame, memory, decoded)
        snapshots.append(snapshot)
    return dict(schema=1, passed=source_checks > 0 and sum(s['compared'] for s in snapshots) > 0 and not failures,
                allocation_sources=source_checks, frontiers=len(progress), initialized=initialized, partial=partial,
                snapshots=snapshots, failures=failures,
                sources={p.name: sha256_file(p) for p in (run/'usa-future-rom.bin', run/'usa-future-progress.csv',
                                                        run/'usa-future-capture.json', run/'usa-sections.jsonl')},
                scope='USA list/stage/heading and bounded loader frontiers; upcoming render descriptors compared '
                      'with later allocations. Current partial list, custom handlers, material lifetime, '
                      'texture residency, clipping/occlusion/handover and GPU visibility remain unverified.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path); ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--native', type=Path)
    args = ap.parse_args()
    try:
        result = check(args.run, args.native)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = dict(schema=1, passed=False, error=str(error))
    write_json(args.report, result)
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
