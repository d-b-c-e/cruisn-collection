"""Compare saved USA host-scene work in a capture-free bridge approach window.

This is instrumented CPU preparation, not a throughput or GPU frame-pacing
benchmark. Both replays can remain synchronized at 100% with different costs.
"""
import argparse
import csv
import json
from pathlib import Path
from statistics import mean, median

from qualify_usa_farcoverage_interval import frames
from screen_vunit_panorama_strips import sha

FIRST, LAST = 10000, 10469


def rows(path):
    with path.open(newline='', encoding='utf-8') as stream:
        return [r for r in csv.DictReader(stream)
                if FIRST <= int(r['frame']) <= LAST]


def stats(values):
    ordered = sorted(values)
    return dict(mean=mean(ordered), median=median(ordered),
                p95=ordered[int(.95*(len(ordered)-1))],
                maximum=ordered[-1], total=sum(ordered))


def screen(off, on, scene_screen):
    qualified = json.loads(scene_screen.read_text(encoding='utf-8'))
    a = json.loads((off / 'report.json').read_text(encoding='utf-8'))
    b = json.loads((on / 'report.json').read_text(encoding='utf-8'))
    if (not qualified['passed'] or
            qualified['sha256']['control_report'] != sha(off / 'report.json') or
            qualified['sha256']['candidate_report'] != sha(on / 'report.json') or
            not a['passed'] or not b['passed'] or
            a['display_target'] != b['display_target'] or
            a['comparison_scope'] != b['comparison_scope'] or
            a['case'] != b['case'] or
            a['emulator_source']['executable_sha256'] !=
            b['emulator_source']['executable_sha256'] or
            not a['display_watch']['passed'] or not b['display_watch']['passed']):
        raise ValueError('paired USA source/recording/display qualification differs')
    for root in (off, on):
        env = json.loads((root / 'run/invocation.json').read_text(encoding='utf-8'))['environment']
        if env.get('MIDV_FFB') != '0' or (root / 'run/gl-snap/captures.csv').exists():
            raise ValueError('physical force or completed capture contaminates cost window')
    old = rows(off / 'run/usa-host-scenes.csv')
    new = rows(on / 'run/usa-host-scenes.csv')
    clocks = lambda seq: [(r['frame'], r['time'], r['page']) for r in seq]
    if len(old) < 100 or clocks(old) != clocks(new):
        raise ValueError('host scene sequence differs')
    old_frames = frames(off / 'run/frames.csv')
    new_frames = frames(on / 'run/frames.csv')
    if old_frames != new_frames:
        raise ValueError('recorded inputs or emulated clocks differ')
    def timing(root):
        with (root / 'run/frames.csv').open(newline='', encoding='utf-8') as stream:
            records = {int(r['frame']): r for r in csv.DictReader(stream)
                       if int(r['frame']) in (FIRST, LAST)}
        if set(records) != {FIRST, LAST}:
            raise ValueError('host-time interval missing endpoint')
        return float(records[LAST]['host_seconds']) - float(records[FIRST]['host_seconds'])
    a_us = stats([float(r['microseconds']) for r in old])
    b_us = stats([float(r['microseconds']) for r in new])
    total_quads = [sum(int(r['quads']) for r in seq) for seq in (old, new)]
    host = [timing(root) for root in (off, on)]
    return dict(schema=1, passed=True,
                scope='Matched USA source10000..10469, physical1440/FFB0, no GL captures. '
                      'Native host-scene timer only; replay is synchronized near100%, '
                      'so this is not a throughput/GPU/stutter or release cost pass.',
                source_window=[FIRST, LAST], matched_scenes=len(old),
                auxiliary_quads=total_quads, additional_quads=total_quads[1]-total_quads[0],
                host_scene_microseconds=dict(control=a_us,candidate=b_us,
                                             mean_delta=b_us['mean']-a_us['mean']),
                host_elapsed_seconds=dict(control=host[0],candidate=host[1],
                                          difference=host[1]-host[0]),
                sha256={'source_scene_screen': sha(scene_screen),
                        'control_report': sha(off / 'report.json'),
                        'candidate_report': sha(on / 'report.json'),
                        'control_scenes': sha(off / 'run/usa-host-scenes.csv'),
                        'candidate_scenes': sha(on / 'run/usa-host-scenes.csv'),
                        'control_frames': sha(off / 'run/frames.csv'),
                        'candidate_frames': sha(on / 'run/frames.csv')})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('off', 'on', 'scene_screen', 'report'):
        ap.add_argument('--' + name.replace('_', '-'), dest=name, type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite USA cost screen')
    result = screen(args.off, args.on, args.scene_screen)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', result['matched_scenes'],
          round(result['host_scene_microseconds']['mean_delta'], 3))


if __name__ == '__main__':
    main()
