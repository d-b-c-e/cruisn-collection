"""Check bounded Exotica loader captures with independent descriptors and C++.

Raw ROM, RAM, model and material operands stay local. No host drawing or GPU
material lifetime is implied by this descriptor/initial-binding verification.
"""
import argparse
import array
import csv
import json
from pathlib import Path
import subprocess
import sys
from exotica_sections import FIELDS, binding, descriptor, sections, yaw_matrix
from scenery_c31 import F
from verification import sha256_file, write_json


def words(path, size):
    if path.stat().st_size != size:
        raise ValueError('incomplete Exotica memory snapshot')
    result = array.array('I', path.read_bytes())
    if sys.byteorder != 'little':
        result.byteswap()
    return result


class Memory:
    def __init__(self, ram, main, banks, bank):
        if bank not in (0, 1, 2):
            raise ValueError('Exotica ROM bank')
        self.ram, self.main, self.banks, self.bank = ram, main, banks, bank

    def __call__(self, address):
        if 0 <= address < 0x40000:
            return self.ram[address]
        if 0xa00000 <= address < 0xc00000:
            return self.main[address-0xa00000]
        if 0xc00000 <= address < 0x1000000:
            return self.banks[self.bank*0x400000+address-0xc00000]
        raise ValueError('unmapped Exotica operand')

    def words(self, address, count):
        return [self(address+i) for i in range(count)]


def check_section_matrix(row, read):
    """Verify the unrounded section-angle expression and its stored result.

    The CPU computes the matrix before rounding the angle into RAM. Third-list
    object placement may clear direction bit0 in row.flags; the section's ROM
    flags still own the matrix direction.
    """
    flags = read(row['section']+3)
    if row['flags'] not in (flags, flags & ~1):
        raise ValueError('Exotica captured section direction mismatch')
    angle = F.load(row['scalars'][14])
    if flags & 1:
        angle = angle-F.load(row['list_header'][3])+F.load(0x01491000)
    if angle.store() != row['scalars'][15]:
        raise ValueError('Exotica stored section angle mismatch')
    if yaw_matrix(angle, row['trig']) != row['matrix']:
        raise ValueError('Exotica unrounded section matrix mismatch')


def check(directory, native=None):
    directory = Path(directory)
    receipt = json.loads((directory/'exotica-section-capture.json').read_text(encoding='utf-8'))
    if receipt.get('schema') != 1 or receipt.get('complete') is not True:
        raise ValueError('incomplete Exotica loader capture')
    if (not 1800 <= receipt['first'] <= receipt['last'] or receipt['last']-receipt['first'] > 20000 or
            not 1 <= receipt['allocations'] <= 10000 or not 1 <= receipt['sections'] <= 128 or
            not 1 <= receipt['snapshots'] <= 16):
        raise ValueError('Exotica loader capture budget')
    rows = [json.loads(line) for line in (directory/'exotica-section-allocations.jsonl').read_text(encoding='utf-8').splitlines()]
    with (directory/'exotica-section-progress.csv').open(encoding='utf-8', newline='') as stream:
        progress = list(csv.DictReader(stream))
    if not rows or len(rows) != receipt['allocations'] or [r['id'] for r in rows] != list(range(1, len(rows)+1)):
        raise ValueError('Exotica allocation sequence')
    if [int(r['frame']) for r in progress] != list(range(receipt['first'], receipt['last']+1)):
        raise ValueError('Exotica progress coverage')
    by_frame = {int(r['frame']): r for r in progress}
    for r in progress:
        if (int(r['starts'])-int(r['ends']) != bool(int(r['loading'])) or
                int(r['allocating']) > bool(int(r['loading'])) or int(r['bank']) not in (0, 1, 2)):
            raise ValueError('Exotica loader transaction')
    if int(progress[-1]['ends']) != receipt['sections'] or int(progress[-1]['loading']):
        raise ValueError('unfinished Exotica section')
    main = words(directory/'exotica-main-rom.bin', 0x800000)
    banks = words(directory/'exotica-banked-rom.bin', 0x3000000)
    snapshots = sorted(directory.glob('exotica-section-[0-9]*.bin'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))
    if len(snapshots) != receipt['snapshots'] or not snapshots:
        raise ValueError('Exotica snapshot coverage')
    results = []
    initial = None
    for path in snapshots:
        frame = int(path.stem.rsplit('-', 1)[1]);p = by_frame[frame]
        read = Memory(words(path, 0x100000), main, banks, int(p['bank']))
        if initial is None:
            initial = read
        reference = sections(read, bool(int(p['loading'])))
        sources = reference['sources'];lookup = {(r['entry'], r['source']): r for r in sources}
        if len(lookup) != len(sources):
            raise ValueError('duplicate Exotica section source')
        checked = later = 0
        for row in rows:
            if row['definition'][0] >> 24 or row['definition'][5] & 0xf00 in (0xa00, 0xf00):
                continue
            result = lookup[row['section'], row['source']]
            if not result['supported'] or any(result['words'][i] != row['actual'][i] for i in FIELDS):
                raise ValueError(f'Exotica allocation descriptor mismatch: frame {frame}, id {row["id"]}')
            checked += 1;later += row['frame'] > frame
        if native:
            command = [str(native), str(path), str(directory/'exotica-main-rom.bin'),
                       str(directory/'exotica-banked-rom.bin'), p['bank'], str(int(bool(int(p['loading']))))]
            run = subprocess.run(command, capture_output=True, text=True, timeout=60)
            if run.returncode:
                raise ValueError(f'native Exotica source rejected: {run.returncode}: {run.stderr[:1000]}')
            output = [[int(w) for w in line.split()] for line in run.stdout.splitlines()]
            expected_header = [int(reference['pretrack']), int(reference['partial']), reference['frontier'], len(reference['sections']), len(sources)]
            if not output or output[0] != expected_header or len(output)-1 != len(sources):
                raise ValueError('native Exotica source cardinality')
            for actual, source in zip(output[1:], sources):
                if actual != [source[k] for k in ('entry', 'source', 'index', 'ordinal', 'supported', 'future')]+source['words']:
                    raise ValueError('native Exotica descriptor mismatch')
        results.append(dict(frame=frame, sections=len(reference['sections']), descriptors=len(sources),
                            ordinary=sum(s['supported'] for s in sources), actual_allocations=checked,
                            later_allocations=later, partial=reference['partial'],
                            future=sum(s['supported'] and s['future'] for s in sources), native_verified=bool(native)))
    ordinary = overrides = bindings = 0
    for row in rows:
        d = row['definition']
        read = Memory(initial.ram, main, banks, row['bank'])
        if read.words(row['source'], 6) != d or read.words(row['first_list']-4, 5) != row['list_header']:
            raise ValueError('Exotica source/header operand mismatch')
        if d[0] >> 24 or d[5] & 0xf00 in (0xa00, 0xf00):
            continue
        ordinary += 1
        model = read.words(d[0], 6)
        if model != row['model_words'] or row['initial'][15] != model[5] or row['initial'][21] != model[1]:
            raise ValueError('Exotica base descriptor mismatch')
        material = model[2]
        for name, token, table, field in (
                ('texture', material & 0xf0003fff, row['material_tables'][0], 19),
                ('palette', (material & 0xf0000000) | ((material & 0x0fffc000) >> 14), row['material_tables'][1], 18)):
            actual = row[name+'_binding'];base = read(table+(token >> 28));slot = base+(token & 0x3fff)
            if actual != [token, base, slot, read(slot)] or binding(read, token, table) != row['initial'][field]:
                raise ValueError('Exotica initial material binding mismatch')
            bindings += 1
        overrides += bool(row['override_binding'])
        s = row['scalars']
        context = dict(flags=row['flags'], header=row['list_header'], position=s[11:14], heading=s[14],
                       section_heading=s[15], gap=row['gap'], cursor=s[10], index=s[2] >> 8, initial=bool(s[8]))
        pal = row['override_binding'][3] if row['override_binding'] else row['palette_binding'][3]
        target = descriptor(d, model, context, row['matrix'], row['constants'], row['trig'], (pal, row['texture_binding'][3]))
        if any(target[i] != row['actual'][i] for i in FIELDS):
            raise ValueError('Exotica captured section placement mismatch')
        check_section_matrix(row, read)
    paths = [directory/name for name in ('exotica-section-capture.json', 'exotica-section-allocations.jsonl',
             'exotica-section-progress.csv', 'exotica-main-rom.bin', 'exotica-banked-rom.bin')]+snapshots
    return dict(schema=1, passed=True, allocations=len(rows), ordinary=ordinary, custom_excluded=len(rows)-ordinary,
                initial_bindings=bindings, overrides=overrides, loader_samples=len(progress),
                live_partial_samples=sum(bool(int(r['loading'])) for r in progress), snapshots=results,
                section_matrices=ordinary, section_angle_source='unrounded original arithmetic before RAM storage',
                native_sha256=sha256_file(native) if native else None,
                sources={p.name: sha256_file(p) for p in paths}, scope=__doc__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path);parser.add_argument('--native', type=Path)
    parser.add_argument('--report', type=Path, required=True);args=parser.parse_args()
    try:
        result = check(args.directory, args.native)
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        result = dict(passed=False, error=str(error), scope=__doc__)
    write_json(args.report, result);print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
