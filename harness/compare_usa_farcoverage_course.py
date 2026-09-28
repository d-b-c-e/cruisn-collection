"""Qualify a matched USA partial-far-coverage completed-image interval.

The candidate may change only the left widescreen third. This is an image
preservation gate, not a claim of complete scenery or smooth activation.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from gl_frames import compare_completed_frames


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def frame_rows(path):
    with Path(path).open(newline='', encoding='utf-8') as stream:
        rows = csv.DictReader(stream)
        fields = [name for name in rows.fieldnames if name not in ('host_seconds', 'speed_percent')]
        return [tuple(row[name] for name in fields) for row in rows]


def compare(control, trial):
    roots = (Path(control), Path(trial))
    reports = [json.loads((root / 'report.json').read_text(encoding='utf-8'))
               for root in roots]
    a, b = reports
    options = [dict(r['usa_host_scenery']) for r in reports]
    modes = [item.pop('far_coverage', None) for item in options]
    if (modes != ['off', 'on'] or options[0] != options[1] or
            options[0].get('mode') != 'draw' or options[0].get('far') != 240000):
        raise ValueError('replays differ in more than USA partial far coverage')
    if any(not r['passed'] or not r['comparison']['passed'] or
           not r['display_watch']['passed'] or
           r['vunit_runtime']['result']['completion'] != 'owned-worker-stop'
           for r in reports):
        raise ValueError('input/native/display/shutdown replay gate failed')
    if (a['case'] != b['case'] or a['emulator_source'] != b['emulator_source'] or
            a['display_target'] != b['display_target'] or
            a['presentation_overrides'] != b['presentation_overrides'] or
            a['comparison_scope'] != b['comparison_scope']):
        raise ValueError('case, binary, display, presentation or prefix differs')
    invocations = [json.loads((root / 'run/invocation.json').read_text(encoding='utf-8'))
                   for root in roots]
    if any(i['returncode'] != 0 or i['environment'].get('MIDV_FFB') != '0'
           for i in invocations):
        raise ValueError('physical force was not off or process failed')
    clocks = [frame_rows(root / 'run/frames.csv') for root in roots]
    if clocks[0] != clocks[1] or len(clocks[0]) != a['comparison_scope']['last_frame']:
        raise ValueError('recorded frame clocks/input differ')
    images = compare_completed_frames(roots[0] / 'run/gl-snap',
                                      roots[1] / 'run/gl-snap', details=True)
    right_or_center = sum(sum(row[1:]) for frame in images['pixel_changes']
                          for row in frame['changed_pixels_by_thirds'])
    if right_or_center:
        raise ValueError(f'USA partial coverage changed {right_or_center} center/right pixels')
    runtime = [r['vunit_runtime']['result'] for r in reports]
    if runtime[0]['scenes'] != runtime[1]['scenes']:
        raise ValueError('host scene count differs')
    return dict(schema=1, passed=True,
                scope='One matched USA route prefix at physical display/FFB0. '
                      'Intentional completed changes are left-third only; no '
                      'complete bridge, continuous transition, 4K or release claim.',
                rom=json.loads((Path(a['case']) / 'case.json').read_text(encoding='utf-8'))['rom'],
                input_frames=len(clocks[0]), host_scenes=runtime[0]['scenes'],
                host_quads_control=runtime[0]['quads'],
                host_quads_trial=runtime[1]['quads'],
                additional_submitted_quads=runtime[1]['quads'] - runtime[0]['quads'],
                completed_center_third_changed_pixels=0,
                completed_center_and_right_changed_pixels=right_or_center,
                completed=images,
                sha256={'control_report': sha(roots[0] / 'report.json'),
                        'trial_report': sha(roots[1] / 'report.json'),
                        'control_capture_index': sha(roots[0] / 'run/gl-snap/captures.csv'),
                        'trial_capture_index': sha(roots[1] / 'run/gl-snap/captures.csv'),
                        'control_frames': sha(roots[0] / 'run/frames.csv'),
                        'trial_frames': sha(roots[1] / 'run/frames.csv')})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--trial', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite USA paired evidence')
    result = compare(args.control, args.trial)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', result['rom'], result['completed']['frames'], 'completed images',
          len(result['completed']['different_frames']), 'different')


if __name__ == '__main__':
    main()
