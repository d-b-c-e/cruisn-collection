"""Compare future material admission and projected quads without guest execution."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from usa_future_scene import collect
from verify_usa_future import Memory
from verify_usa_host import reference
from verification import sha256_file, write_json
from analyze_usa_host import evidence, key, COUNTERS


def check(run, binary, runtime=False):
    rom = (run/'usa-future-rom.bin').read_bytes(); snapshots = sorted(run.glob('usa-future-scene-*.json'))
    if not snapshots: raise ValueError('empty USA future scene evidence')
    env = dict(os.environ)
    if os.name == 'nt': env['PATH'] = 'E:/msys64/mingw64/bin;'+env.get('PATH', '')
    scenes = geometry = None
    if runtime:
        captures = [json.loads(p.read_text()) for p in snapshots]
        clocks = {(int(r['native_frame']), r['time'], int(r['page'])) for r in captures}
        scene_rows, geometry, _ = evidence(run, retain_geometry=clocks); scenes = {key(r): r for r in scene_rows}
    results = []
    for path in snapshots:
        captured = json.loads(path.read_text()); frame = captured['frame']
        ram_path, fast_path = run/f'usa-future-ram-{frame}.bin', run/f'usa-future-fast-{frame}.bin'
        memory = Memory(rom, ram_path.read_bytes(), fast_path.read_bytes())
        frontier, stats, objects = collect(memory)
        header = [frontier['start'], frontier['loading'], frontier['number'], int(frontier['partial']),
                  int(frontier['stop'] == 'track not initialized'), *stats.values()]
        trials = []
        for far in (80000, 160000, 240000):
            counts, expected = reference(memory, far, objects)
            cmd = [str(binary.resolve()), '--scene', str(far), str(ram_path), str(fast_path), str(run/'usa-future-rom.bin')]
            native = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
            if native.returncode: raise ValueError('native future scene failed: '+native.stderr)
            actual = [list(map(int, line.split())) for line in native.stdout.splitlines()]
            trial = dict(far=far, passed=actual == [header, counts, *expected], counts=counts, quads=len(expected),
                         future_quads=sum(bool(q[0] & 0x80000000) for q in expected))
            if runtime:
                clock = (int(captured['native_frame']), captured['time'], int(captured['page']))
                if clock not in scenes or geometry is None: raise ValueError('missing exact runtime future scene')
                row = scenes[clock]
                if int(row['host_far']) == far:
                    live_counts = [int(row['pending'])+int(row['future_ready']), *[int(row[n]) for n in COUNTERS[1:6]]]
                    trial['runtime_passed'] = live_counts == counts and geometry[clock] == expected
                    trial['passed'] &= trial['runtime_passed']
            trials.append(trial)
        if runtime and sum('runtime_passed' in t for t in trials) != 1: raise ValueError('missing runtime far plane')
        results.append(dict(frame=frame, passed=all(t['passed'] for t in trials), stats=stats, trials=trials,
                            source_sha256={p.name: sha256_file(p) for p in (path, ram_path, fast_path)}))
    return dict(schema=1, passed=all(r['passed'] for r in results), snapshots=results, native_sha256=sha256_file(binary),
                rom_sha256=sha256_file(run/'usa-future-rom.bin'),
                scope='Independent future admission/ownership/upload readiness and ordered projection; visual occlusion and lifetime unproven')


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('run', type=Path)
    ap.add_argument('--native', type=Path, required=True); ap.add_argument('--runtime', action='store_true')
    ap.add_argument('--report', type=Path, required=True); args = ap.parse_args()
    try: result = check(args.run, args.native, args.runtime)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error: result = dict(passed=False, error=str(error))
    write_json(args.report, result); print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__': raise SystemExit(main())
