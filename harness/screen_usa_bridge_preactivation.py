"""Screen a saved USA pre-activation RAM state against host projection modes.

End-of-frame RAM proves descriptor/material state at that time, not exact C31
scene operands at an earlier source hook. Use matched live images separately.
"""
import argparse
import json
from pathlib import Path

from analyze_vunit_margin_gap import projected_box
from screen_vunit_panorama_strips import sha
from usa_future_scene import collect
from verify_usa_future import Memory
from verify_usa_host import reference


def screen(run, rom_path, activation_path, target):
    report = json.loads((run / 'report.json').read_text(encoding='utf-8'))
    invocation = json.loads((run / 'run/invocation.json').read_text(encoding='utf-8'))
    if (not report['passed'] or not report['comparison']['passed'] or
            not report['display_watch']['passed'] or
            report['vunit_runtime']['result']['completion'] != 'owned-worker-stop' or
            invocation['environment'].get('MIDV_FFB') != '0'):
        raise ValueError('pre-activation replay not qualified')
    capture = run / 'run/capture'
    meta = (capture / 'meta.txt').read_text(encoding='utf-8').splitlines()
    if not meta or meta[0] != 'frame 10470':
        raise ValueError('expected saved end-of-frame 10470 state')
    ram = capture / 'ram_010470.bin'
    fast = capture / 'ram3_010470.bin'
    memory = Memory(rom_path.read_bytes(), ram.read_bytes(), fast.read_bytes())
    future, counts, objects = collect(memory)
    selected = [(obj, words) for obj, words in objects if obj == target]
    if len(selected) != 1 or counts['unbound'] or counts['deferred']:
        raise ValueError('target not uniquely ready in saved future sources')
    activation = json.loads(activation_path.read_text(encoding='utf-8'))
    matches = [row for row in activation['objects'] if row['object'] == hex(target)]
    if not activation['passed'] or len(matches) != 1 or matches[0]['first_scene']['frame'] <= 10470:
        raise ValueError('target was already submitted at capture time')
    base, _ = reference(memory, 240000)
    ordinary, ordinary_quads = reference(memory, 240000, future=selected)
    coverage, coverage_quads = reference(memory, 240000, future=selected,
                                         far_coverage=True)
    old_target = [quad for quad in ordinary_quads if quad[0] == target]
    new_target = [quad for quad in coverage_quads if quad[0] == target]
    if ([b - a for a, b in zip(base, ordinary)] != [1, 0, 0, 0, 1, 0] or
            old_target or [b - a for a, b in zip(base, coverage)] != [1, 0, 0, 0, 0, 1] or
            not new_target):
        raise ValueError('saved target did not exhibit projection-only recovery')
    boxes = [projected_box(tuple(quad[3:19])) for quad in new_target]
    return dict(schema=1, passed=True,
                scope='One USA end-of-frame RAM/material snapshot at 10470. It is not '
                      'a source-time projection oracle or a completed-image result.',
                target=hex(target), snapshot_frame=10470,
                first_submitted_frame=matches[0]['first_scene']['frame'],
                future=dict(sections=counts['sections'], definitions=counts['definitions'],
                            ready=counts['ready'], uploads=counts['uploads'],
                            target_ready=True, target_model=hex(selected[0][1][13]),
                            target_flags=selected[0][1][14]),
                ordinary=dict(counter_delta=[b - a for a, b in zip(base, ordinary)],
                              target_quads=len(old_target)),
                partial_coverage=dict(counter_delta=[b - a for a, b in zip(base, coverage)],
                                      target_quads=len(new_target), native_boxes=boxes),
                sha256={'replay_report': sha(run / 'report.json'),
                        'invocation': sha(run / 'run/invocation.json'),
                        'meta': sha(capture / 'meta.txt'), 'program_ram': sha(ram),
                        'c31_fast_ram': sha(fast), 'program_rom': sha(rom_path),
                        'activation_report': sha(activation_path)})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--program-rom', type=Path, required=True)
    ap.add_argument('--activation', type=Path, required=True)
    ap.add_argument('--target', required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite pre-activation screen')
    result = screen(args.run, args.program_rom, args.activation, int(args.target, 0))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', result['target'], result['partial_coverage']['target_quads'])


if __name__ == '__main__':
    main()
