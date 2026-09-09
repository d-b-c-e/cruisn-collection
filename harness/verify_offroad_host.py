"""Compare standalone Off Road host scenes against independent Python projection.

No native MAME integration, GPU visibility or complete material lifetime claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from offroad_scene import scene
from verify_offroad_future import Memory
from verification import sha256_file, write_json


def check(run, rom_path, binary):
    rom = rom_path.read_bytes(); results = []
    for ram in sorted(run.glob('offroad-scene-*.bin')):
        memory = Memory(rom, ram.read_bytes())
        for source in ('pending', 'future'):
            for multiplier in (1, 2, 3):
                counts, objects = scene(memory, multiplier, source == 'future')
                fields = ('pending', 'future', 'unsupported', 'near', 'far', 'projection',
                          'material', 'pretrack', 'partial', 'deferred')
                header = [counts[k] for k in fields]+[len(objects)]
                rows = [[o[k] for k in ('id', 'model', 'lod', 'depth', 'order')]+q
                        for o in objects for q in o['quads']]
                proc = subprocess.run([str(binary.resolve()), '--scene', str(multiplier), source,
                                       str(ram), str(rom_path)], text=True, capture_output=True, timeout=120)
                if proc.returncode:
                    raise ValueError(f'native host rejected {ram.stem}/{source}/{multiplier}: {proc.returncode} {proc.stderr}')
                passes = proc.stdout.strip().split('end')
                if len(passes) != 3 or passes[-1].strip():
                    raise ValueError('incomplete cold/warm native scene')
                for output in passes[:2]:
                    values = [list(map(int, line.split())) for line in output.strip().splitlines()]
                    if values != [header, *rows]:
                        mismatch = next((i for i, (a, b) in enumerate(zip(values, [header, *rows])) if a != b), None)
                        raise ValueError(f'host scene mismatch {ram.stem}/{source}/{multiplier}, row {mismatch}, '
                                         f'rows {len(values)}/{len(rows)+1}; header {values[0] if values else None}/{header}')
                encoded = json.dumps(rows, separators=(',', ':')).encode()
                row = dict(snapshot=ram.stem, source=source, multiplier=multiplier,
                           counters=dict(counts), objects=len(objects), quads=len(rows),
                           ordered_sha256=hashlib.sha256(encoded).hexdigest(),
                           snapshot_sha256=sha256_file(ram), cold_warm_equal=True)
                results.append(row)
                print(ram.stem, source, multiplier, len(objects), len(rows), 'PASS', flush=True)
    if not results or not sum(r['quads'] for r in results):
        raise ValueError('empty Off Road scene coverage')
    return dict(schema=1, passed=True, results=results, native_sha256=sha256_file(binary),
                rom_sha256=sha256_file(rom_path),
                scope='Independent scalar admission, transform/LOD, host projection, material bounds and '
                      'radial ordering; cold/warm immutable model cache parity. Raw operands local. '
                      'Not GPU visibility, material lifetime, full clipping, occlusion, handover or performance acceptance.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path); ap.add_argument('--rom', type=Path, required=True)
    ap.add_argument('--native', type=Path, required=True); ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    try:
        result = check(args.run, args.rom, args.native)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        result = dict(schema=1, passed=False, error=str(exc))
    write_json(args.report, result)
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
