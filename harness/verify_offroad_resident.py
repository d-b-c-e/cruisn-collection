"""Compare independent Python resident scenes with native cold/warm projection.

Saved RAM/ROM operands only. This does not prove a live GPU insertion, packet
ordering, material lifetime, or completed-image quality.
"""
import argparse
import csv
from functools import reduce
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from analyze_world_host import HASH_SEED, hash_quad
from offroad_scene import scene
from verify_offroad_future import Memory
from verification import sha256_file, write_json

HEADER = ('pending', 'future', 'unsupported', 'near', 'far', 'projection',
          'material', 'pretrack', 'partial', 'deferred')
RESIDENT = ('resident_candidates', 'resident_margin', 'resident_pruned')


def check(rom_path, snapshots, native, dll_dir=None, live_journal=None):
    rom = rom_path.read_bytes()
    if len(rom) != 0x1000000 or not snapshots:
        raise ValueError('missing Off Road ROM or snapshots')
    result = []
    live = {}
    if live_journal is not None:
        with live_journal.open(newline='', encoding='utf-8') as stream:
            for row in csv.DictReader(stream):
                frame = int(row['frame'])
                if frame in live:
                    raise ValueError('duplicate live resident scene frame')
                live[frame] = row
    for ram in snapshots:
        memory = Memory(rom, ram.read_bytes())
        counts, objects = scene(memory, 3, True, recover_partial=True,
                                resident_margins=True)
        expected = [[*(counts[k] for k in HEADER), len(objects),
                     *(counts[k] for k in RESIDENT)]]
        expected.extend([o[k] for k in ('id', 'model', 'lod', 'depth', 'order')] + q
                        for o in objects for q in o['quads'])
        command = [str(native.resolve()), '--scene', '3', 'future', str(ram.resolve()),
                   str(rom_path.resolve()), '--recover-partial', '--resident-margins']
        env = os.environ.copy()
        if dll_dir is not None:
            env['PATH'] = str(dll_dir.resolve()) + os.pathsep + env['PATH']
        proc = subprocess.run(command, text=True, capture_output=True, timeout=120, env=env)
        if proc.returncode:
            raise ValueError(f'{ram.stem}: native scene rejected: {proc.returncode} {proc.stderr.strip()}')
        passes = proc.stdout.strip().split('end')
        if len(passes) != 3 or passes[-1].strip():
            raise ValueError(f'{ram.stem}: missing native cold/warm pass')
        for index, output in enumerate(passes[:2]):
            rows = [list(map(int, line.split())) for line in output.strip().splitlines()]
            if rows != expected:
                mismatch = next((i for i, (a, b) in enumerate(zip(rows, expected)) if a != b), None)
                raise ValueError(f'{ram.stem}: native/Python pass{index} mismatch row{mismatch}; '
                                 f'rows {len(rows)}/{len(expected)}; '
                                 f'header {rows[0] if rows else None}/{expected[0]}')
        if not counts['resident_candidates'] or not counts['resident_margin']:
            raise ValueError(f'{ram.stem}: no resident candidate or visible margin work')
        quads = [q for o in objects for q in o['quads']]
        fingerprint = f'{reduce(hash_quad, quads, HASH_SEED):016x}'
        live_match = None
        if live_journal is not None:
            name = re.search(r'-(\d+)-ram$', ram.stem)
            if not name or int(name[1]) not in live:
                raise ValueError(f'{ram.stem}: no matching live scene frame')
            row = live[int(name[1])]
            live_match = (row['quads_hash'] == fingerprint and int(row['quads']) == len(quads)
                          and int(row['decoded']) == len(objects)
                          and all(int(row[k]) == counts[k] for k in (*HEADER, *RESIDENT)))
            if not live_match:
                raise ValueError(f'{ram.stem}: independent scene differs from live ordered receipt')
        encoded = json.dumps(expected, separators=(',', ':')).encode()
        result.append(dict(snapshot=ram.stem, ram_sha256=sha256_file(ram),
                           counters={k: counts[k] for k in (*HEADER, *RESIDENT)},
                           objects=len(objects), quads=len(quads),
                           live_ordered_fingerprint=fingerprint if live_match else None,
                           live_receipt_equal=live_match,
                           ordered_sha256=hashlib.sha256(encoded).hexdigest(),
                           cold_warm_equal=True))
    return dict(passed=True, snapshots=result, native_sha256=sha256_file(native),
                rom_sha256=sha256_file(rom_path),
                live_journal_sha256=sha256_file(live_journal) if live_journal else None,
                scope=__doc__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--snapshot', required=True, action='append', type=Path)
    parser.add_argument('--native', required=True, type=Path)
    parser.add_argument('--dll-dir', type=Path, help='directory containing the native CLI runtime DLLs')
    parser.add_argument('--live-journal', type=Path,
                        help='optional live candidate scene CSV for exact per-frame ordered fingerprint checks')
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite saved analysis')
    try:
        report = check(args.rom, args.snapshot, args.native, args.dll_dir, args.live_journal)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report = dict(passed=False, error=str(error))
    write_json(args.report, report)
    print('PASS' if report['passed'] else 'FAIL', args.report)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
