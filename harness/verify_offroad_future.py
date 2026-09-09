"""Compare Off Road static sections with native decoding and actual allocations.

Raw snapshots and object operands stay local. No GPU/material-lifetime claim.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import struct
import subprocess

from offroad_sections import sections, frontier, FIELDS
import csv
from verification import sha256_file, write_json


class Memory:
    def __init__(self, rom, ram):
        if len(rom) != 0x1000000 or len(ram) != 0x80000:
            raise ValueError('incomplete Off Road snapshot')
        self.rom, self.ram = rom, ram

    def __call__(self, p):
        if 0 <= p < 0x20000:
            return struct.unpack_from('<I', self.ram, p*4)[0]
        if 0xc00000 <= p < 0x1000000:
            return struct.unpack_from('<I', self.rom, (p-0xc00000)*4)[0]
        raise ValueError(f'unmapped Off Road operand {p:x}')


def native_check(binary, ram, rom, decoded, loaded):
    proc = subprocess.run([str(binary.resolve()), '--loaded' if loaded else '--future',
                           str(ram), str(rom)], text=True, capture_output=True, timeout=120)
    if proc.returncode:
        raise ValueError(f'native Off Road source failed ({proc.returncode}): '+proc.stderr.strip())
    rows = [list(map(int, line.split())) for line in proc.stdout.splitlines()]
    f = decoded['frontier']
    expected = [[int(f[k]) for k in ('track', 'count', 'current', 'front', 'back', 'pretrack', 'partial')]
                +[len(decoded['sources'])]]
    for s in decoded['sources']:
        expected.append([int(s[k]) for k in ('entry', 'source', 'number', 'ordinal', 'flags', 'supported')]+s['words'])
    if rows != expected:
        raise ValueError('native/Python Off Road frontier/descriptor mismatch')
    return len(decoded['sources'])


def differences(expected, actual, fields=FIELDS):
    if len(expected) != 22 or len(actual) != 22:
        raise ValueError('incomplete Off Road object')
    # The renderer marks an active instance with bit31. All other flags must match.
    return [i for i in fields if (expected[i] & (0x7fffffff if i == 5 else 0xffffffff)) !=
            (actual[i] & (0x7fffffff if i == 5 else 0xffffffff))]


def allocated_pool(read):
    base = read(0x111ee)
    if not 0 <= base <= 0x20000-1200*22:
        raise ValueError('Off Road object pool')
    free, p = set(), read(read(0x111f6))
    while p:
        if p in free or p < base or (p-base) % 22 or p >= base+1200*22:
            raise ValueError('Off Road free-list cycle/owner')
        free.add(p); p = read(p)
    tags = defaultdict(list)
    for p in range(base, base+1200*22, 22):
        if p not in free:
            tags[read(p+6)].append([read(p+i) for i in range(22)])
    return tags


def check(snapshots, rom_path, allocations_path, native=None):
    rom = rom_path.read_bytes()
    allocation = [json.loads(line) for line in allocations_path.read_text().splitlines()]
    if not allocation or [r['id'] for r in allocation] != list(range(1, len(allocation)+1)):
        raise ValueError('incomplete allocation sequence')
    raw = Memory(rom, bytes(0x80000))
    failures, initial, initial_excluded = [], 0, 0
    for r in allocation:
        if r['final_pc'] not in (0x9c5f, 0x9c1a) or r['frame'] != r['final_frame']:
            raise ValueError('unqualified allocation boundary')
        if not 0xc00000 <= r['source'] <= 0x1000000-11 or r['source_words'] != [raw(r['source']+i) for i in range(11)]:
            raise ValueError('allocation definition differs from ROM')
        if r['source_words'][0] & 0x04000000:
            initial_excluded += 1
            continue
        # Initial field qualification also includes objects later affected by
        # custom hooks. Do not confuse it with the ordinary runtime contract.
        w, actual = r['source_words'], r['object_words']
        expected = [0]*22
        expected[5], expected[7], expected[8] = w[0] & ~0x23000000, w[3], w[2]
        expected[11:17], expected[17:21] = w[5:11], [r['palette_table'], r['base_palette'], r['base_texture'], w[1]]
        if w[0] & 0x23000000:
            raise ValueError('unqualified alternate allocation binding')
        bad = differences(expected, actual, [i for i in FIELDS if i != 6])
        if bad:
            failures.append(dict(kind='initial allocation', serial=r['id'], fields=bad))
        initial += 1
    progress_report, clocks, source_paths = None, {}, [rom_path, allocations_path]
    receipt_path = snapshots/'offroad-section-capture.json'
    if receipt_path.is_file():
        receipt = json.loads(receipt_path.read_text())
        progress_path = snapshots/'offroad-section-progress.csv'
        rows = list(csv.DictReader(progress_path.open()))
        if (receipt.get('schema') != 1 or receipt.get('complete') is not True or
                receipt.get('started') != len(allocation) or receipt.get('completed') != len(allocation) or
                receipt.get('scenes') != len(rows) or not rows):
            raise ValueError('incomplete section/progress capture')
        if any(not receipt['first'] <= r['frame'] <= receipt['last'] for r in allocation):
            raise ValueError('allocation outside capture window')
        partial = initialized = 0; previous_time = -1
        columns = ('track', 'current_entry', 'current', 'front_entry', 'front', 'lead',
                   'back_entry', 'back', 'trail', 'mode')
        for serial, row in enumerate(rows, 1):
            now = float(row['time']); frame = int(row['frame'])
            if (int(row['scene']) != serial or now <= previous_time or int(row['pc']) != 0x1bf9 or
                    not receipt['first'] <= frame <= receipt['last'] or int(row['live_allocations']) != 0):
                raise ValueError('duplicate/unordered/unbounded or mid-allocation scene')
            overlay = {0x1b4b4+i: int(row[k]) for i, k in enumerate(columns)}
            overlay[0x1b4cc] = int(row['count'])
            f = frontier(lambda p: overlay[p] if p in overlay else raw(p))
            partial += f['partial']; initialized += not f['pretrack']
            clocks[serial] = (frame, now, f)
            previous_time = now
        progress_report = dict(scenes=len(rows), partial=partial, initialized=initialized,
                               snapshots=receipt['snapshots'], live_allocations=0)
        source_paths += [receipt_path, progress_path]
    output = []
    for path in sorted(snapshots.glob('offroad-scene-*.bin')):
        meta_path = path.with_suffix('.json')
        meta = json.loads(meta_path.read_text()); frame = meta['frame']
        if meta['pc'] != 0x1bf9 or path.stem != f'offroad-scene-{frame}':
            raise ValueError('unexpected Off Road scene boundary')
        read = Memory(rom, path.read_bytes())
        loaded, future = sections(read, True), sections(read)
        if clocks:
            clock = clocks.get(meta.get('scene'))
            if (not clock or clock[0] != frame or abs(clock[1]-meta['time']) > 1e-8 or
                    clock[2] != future['frontier'] or meta.get('live_allocations') != 0):
                raise ValueError('snapshot lacks exact checked scene boundary')
        tags = allocated_pool(read)
        matched = later = later_binding = 0
        for source in loaded['sources']:
            if not source['supported']:
                continue
            actual = tags[source['words'][6]]
            bad = differences(source['words'], actual[0]) if len(actual) == 1 else ['membership']
            if bad:
                failures.append(dict(kind='loaded', frame=frame, source=source['source'], fields=bad))
            matched += 1
        by_source = {s['source']: s for s in future['sources'] if s['supported']}
        for r in allocation:
            if r['frame'] <= frame or r['source'] not in by_source:
                continue
            source = by_source[r['source']]
            if r['final_pc'] != 0x9c5f or r['source_words'] != source['definition']:
                failures.append(dict(kind='future source', frame=frame, serial=r['id']))
                continue
            bad = differences(source['words'], r['object_words'])
            if bad:
                failures.append(dict(kind='future allocation', frame=frame, serial=r['id'], fields=bad))
            later += 1
            later_binding += source['words'][17:20] == r['object_words'][17:20]
        row = dict(frame=frame, frontier=future['frontier'], loaded=len(loaded['sources']),
                   loaded_matched=matched, future=len(future['sources']),
                   future_ordinary=len(by_source), later_matched=later, later_bindings=later_binding,
                   sources={p.name: sha256_file(p) for p in (path, meta_path)})
        if native:
            row['native_loaded'] = native_check(native, path, rom_path, loaded, True)
            row['native_future'] = native_check(native, path, rom_path, future, False)
        output.append(row)
    if not output or not sum(r['loaded_matched'] for r in output) or not sum(r['later_matched'] for r in output):
        raise ValueError('empty loaded/future allocation coverage')
    if progress_report and progress_report['snapshots'] != len(output):
        raise ValueError('missing declared section snapshot')
    return dict(schema=1, passed=not failures, initial=initial, initial_dynamic_excluded=initial_excluded,
                snapshots=output, progress=progress_report, failures=failures,
                sources={str(p): sha256_file(p) for p in source_paths},
                native_sha256=sha256_file(native) if native else None,
                scope='Ordinary static descriptors and later bindings at five scene boundaries. '
                      'No material residency/lifetime, queued uploads, full-track frontier coverage, '
                      'clipping, occlusion, handover, native MAME integration or GPU benefit claim.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('snapshots', type=Path); ap.add_argument('--rom', type=Path, required=True)
    ap.add_argument('--allocations', type=Path, required=True); ap.add_argument('--native', type=Path)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    try:
        result = check(args.snapshots, args.rom, args.allocations, args.native)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        result = dict(schema=1, passed=False, error=str(exc))
    write_json(args.report, result)
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
