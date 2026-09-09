"""Compare captured USA pending scenes against independent Python and native.

Snapshots contain raw ROM/model operands and must remain local. Scene agreement
does not certify residency, occlusion, handover or earlier visible scenery.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from scenery_c31 import F
from usa_model import prepare, project, quads
from world_host_scenery import reciprocal_table
from verification import sha256_file, write_json
from analyze_usa_host import COUNTERS, evidence, key


def reference(memory, far):
    def words(address, count):
        return [memory[address+i] for i in range(count)]
    counts = [0]*6
    objects = []
    seen = set()
    assert memory[0x41] == 0xc9b4 and memory[0x52] == 0xb2b3
    reciprocal = reciprocal_table({i: memory[0xb2b3+i] for i in range(-80, 5000)}, far)
    owner = memory[0xc9b4]
    while owner:
        if owner in seen or len(seen) >= 2048 or not 0x1000 <= owner <= 0x20000-32:
            raise ValueError('invalid pending chain')
        seen.add(owner)
        obj = words(owner, 32)
        counts[0] += 1
        if obj[14] & 0x3000 != 0x2000:
            raise ValueError('invalid pending flags')
        if obj[14] & 0x8e3:
            counts[1] += 1
            owner = obj[0]
            continue
        compact = int(not obj[14] & 0x08000840 and memory[0xc8f5] & 15 == 4 and memory[0xe8a1] != 0)
        record = dict(object_words=obj, compact=compact, camera=words(memory[0x45], 3),
                      view=words(memory[0x47], 9), billboard_full=words(memory[0x4d], 9),
                      billboard_compact=words(memory[0x4e], 4), palette_kind=int(bool(obj[14] & 0x400)), fast=1,
                      origin_y=memory[0x54] if compact else F.integer(200).store())
        record['camera_space'], record['matrix'] = prepare(record)
        depth = F.load(record['camera_space'][2]).fix()
        model = obj[13]
        if obj[14] & 0x200 and depth > 8000:
            model = obj[25 if obj[14] & 4 and depth > 15000 else 24]
        if not 0xc00000 <= model <= 0xfffffe:
            raise ValueError('invalid model address')
        radius = memory[model]
        if depth-radius < 1000:
            counts[2] += 1
        elif depth-radius > far:
            counts[3] += 1
        else:
            header = memory[model+1]
            vertices, polygons = (header & 255)+1, (header >> 16)+1
            if polygons > 1024 or model+2+2*vertices+5*polygons > 0x1000000:
                raise ValueError('invalid model bounds')
            model_words = words(model, 2+2*vertices+5*polygons)
            palettes = [obj[16] if record['palette_kind'] else memory[memory[0x62]+(model_words[2+2*vertices+5*i] >> 16)]
                        for i in range(polygons)]
            record.update(model_words=model_words, vertices=vertices, polygons=polygons,
                          projected=[0]*(3*vertices), palette_words=palettes)
            try:
                buffer = project(record, reciprocal, host_far=far)
            except ValueError as error:
                if not str(error).startswith('host '):
                    raise
                counts[4] += 1
            else:
                counts[5] += 1
                objects.append((owner, model, depth, quads(record, buffer)))
        owner = obj[0]
    objects.sort(key=lambda item: (-item[2], item[0]))
    return counts, [[owner, model, depth, *q] for owner, model, depth, output in objects for q in output]


def check(path, binary, runtime=None):
    snapshot = json.loads(path.read_text())
    memory = dict(snapshot['memory'])
    if not memory or len(memory) != len(snapshot['memory']):
        raise ValueError('empty or duplicate snapshot memory')
    wire = ''.join(f'{p} {value}\n' for p, value in sorted(memory.items()))
    env = dict(os.environ)
    if os.name == 'nt':
        env['PATH'] = 'E:/msys64/mingw64/bin;'+env.get('PATH', '')
    trials = []
    for far in (80000, 160000, 240000):
        expected_counts, expected = reference(memory, far)
        result = subprocess.run([str(binary), '--scene', str(far)], input=wire, capture_output=True,
                                text=True, env=env, timeout=30)
        if result.returncode:
            trials.append(dict(far=far, passed=False, error=result.stderr[:300]))
            continue
        actual = [list(map(int, line.split())) for line in result.stdout.splitlines()]
        trials.append(dict(far=far, passed=actual == [expected_counts, *expected],
                           counts=expected_counts, quads=len(expected)))
        if runtime:
            scenes, geometry = runtime
            # Lua's replay frame is latched by a different notifier. Capture
            # screen.frame_number() explicitly; never align by nearby frames.
            clock = (int(snapshot['native_frame']), snapshot['time'], int(snapshot['page']))
            if clock not in scenes or geometry is None:
                raise ValueError('snapshot lacks unique native scene and detailed geometry')
            scene = scenes[clock]
            if int(scene['host_far']) == far:
                trials[-1]['runtime_passed'] = (geometry[clock] == expected and
                    [int(scene[n]) for n in COUNTERS[:6]] == expected_counts)
                trials[-1]['passed'] &= trials[-1]['runtime_passed']
    if runtime and sum('runtime_passed' in t for t in trials) != 1:
        raise ValueError('no runtime far plane matched the snapshot oracle')
    return dict(passed=all(t['passed'] for t in trials), frame=snapshot['frame'], trials=trials,
                snapshot_sha256=sha256_file(path))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path)
    ap.add_argument('--native', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--runtime', action='store_true', help='also compare unique live scene/quad logs at exact snapshot clocks')
    args = ap.parse_args()
    try:
        snapshots = sorted(args.run.glob('usa-scene-*.json'))
        if not snapshots:
            raise ValueError('empty USA scene evidence')
        runtime = None
        if args.runtime:
            scenes, geometry, summary = evidence(args.run)
            runtime = ({key(r): r for r in scenes}, geometry)
        results = [check(p, args.native, runtime) for p in snapshots]
        report = dict(schema=1, passed=all(r['passed'] for r in results), snapshots=results,
                      native_sha256=sha256_file(args.native))
        if args.runtime:
            report['runtime'] = summary
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        report = dict(schema=1, passed=False, error=str(error))
    write_json(args.report, report)
    print(json.dumps(report))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
