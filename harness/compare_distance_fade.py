"""Recheck a same-candidate World fade off/on pair without replaying the game."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

from gl_frames import requested_frames, read_completed_frames, capture_paths
from verification import write_json
from vunit_original_mirror import verify, compare_originals

TIMINGS = {'microseconds', 'guard_us', 'prepare_us', 'pack_us', 'quad_log_us',
           'submit_us', 'previous_scene_log_us', 'future_us'}


def same_invocation(control, candidate, left_run, right_run):
    if (control.get('returncode') != 0 or candidate.get('returncode') != 0
            or control.get('error') or candidate.get('error')
            or not control.get('executable_sha256')
            or control['executable_sha256'] != candidate.get('executable_sha256')):
        raise ValueError('fade policy comparison requires successful runs of the same binary')
    normalized = []
    for invocation, root in ((control, left_run), (candidate, right_run)):
        def normalize(value):
            return value.replace('\\', '/').replace(str(root.resolve()).replace('\\', '/'), '@RUN')
        environment = {k:normalize(v) for k,v in invocation['environment'].items()}
        if environment.get('MIDV_FFB') != '0':
            raise ValueError('physical force was not disabled')
        normalized.append((list(map(normalize, invocation['command'])), environment))
    if normalized[0][1].pop('MIDV_WORLD_HOST_DISTANCE_FADE', '0') != '0':
        raise ValueError('control already enabled distance fade')
    if normalized[1][1].pop('MIDV_WORLD_HOST_DISTANCE_FADE', '0') != '1':
        raise ValueError('candidate did not enable distance fade')
    if normalized[0] != normalized[1]:
        raise ValueError('settings or command differ beyond the distance-fade toggle')
    return control['executable_sha256']


def compare(control, candidate, frames, *, report, control_report='report.json', candidate_report='report.json'):
    control, candidate = Path(control), Path(candidate)
    roots = [control/'run', candidate/'run']
    names = (control_report, candidate_report)
    if any(Path(n).name != n for n in names):
        raise ValueError('comparison report names must be local filenames')
    saved = [json.loads((p/n).read_text(encoding='utf-8')) for p,n in zip((control,candidate),names)]
    report['input_reports'] = [str((p/n).resolve()) for p,n in zip((control,candidate),names)]
    if any(not r.get('passed') or not r.get('comparison', {}).get('passed') for r in saved):
        raise ValueError('both input/native replay comparisons must pass')
    for field in ('case', 'comparison_scope'):
        if saved[0].get(field) != saved[1].get(field):
            raise ValueError('replays cover different recordings or prefixes')
    invocations = [json.loads((p/'invocation.json').read_text(encoding='utf-8')) for p in roots]
    report['binary_sha256'] = same_invocation(*invocations, *roots)
    actual = [verify(r['vunit_original_mirror'], p) for r,p in zip(saved, roots)]
    report['original_mirror'] = compare_originals(*actual)
    if any(actual[1]['sha256'][k] != v for k,v in actual[0]['sha256'].items()):
        raise ValueError('extended indexed rendering changed')
    if actual[0]['fade_metadata'] != actual[1]['fade_metadata']:
        raise ValueError('metadata stream changed')
    report.update(all_eight_index_mask_planes_exact=True, metadata=actual[1]['fade_metadata'],
                  opacity=actual[1]['opacity'])
    scenes = []
    for root in roots:
        with (root/'world-host-scenes.csv').open(encoding='utf-8', newline='') as stream:
            scenes.append(list(csv.DictReader(stream)))
    if len(scenes[0]) != len(scenes[1]) or any(
            {k:v for k,v in a.items() if k not in TIMINGS} !=
            {k:v for k,v in b.items() if k not in TIMINGS} for a,b in zip(*scenes)):
        raise ValueError('host scene selection or geometry changed')
    report['host_scene_rows_exact'] = len(scenes[0])
    report['excluded_timing_fields'] = sorted(TIMINGS)
    for root in roots:
        read_completed_frames(root/'gl-snap', frames)
    paths = [capture_paths(root/'gl-snap') for root in roots]
    report['frames'] = []
    for frame in frames:
        images = []
        for files in paths:
            with Image.open(files[frame]) as image:
                images.append(np.asarray(image.convert('RGB')))
        a,b = images
        if a.shape != b.shape:
            raise ValueError('completed presentation sizes differ')
        changed = np.any(a != b, axis=2)
        delta = np.abs(a.astype('i2')-b.astype('i2'))
        report['frames'].append(dict(frame=frame, width=a.shape[1], height=a.shape[0],
            changed_pixels=int(changed.sum()), l1=int(delta.sum()),
            new_black=int((np.all(b==0,axis=2) & ~np.all(a==0,axis=2)).sum()),
            foreground_bottom_third_exact=bool(np.array_equal(a[2*a.shape[0]//3:], b[2*b.shape[0]//3:]))))
    report['geometry_passed'] = True
    if not any(r['changed_pixels'] for r in report['frames']):
        raise ValueError('no visible fade effect in the requested window')
    if any(r['new_black'] or not r['foreground_bottom_third_exact'] for r in report['frames']):
        raise ValueError('new black pixels or foreground changes require review')
    report['passed'] = True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('control', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--frames', required=True, help='FIRST:LAST:EVERY completed frames')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--control-report', default='report.json', help='explicit saved recheck report filename')
    parser.add_argument('--candidate-report', default='report.json', help='explicit saved recheck report filename')
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error('output exists; preserve previous comparisons')
    report = dict(passed=False, scope='Same-candidate fade off/on: saved packet/index integrity and bounded '
                  'completed-image appearance. Lower-third foreground and fully-black-pixel checks are '
                  'limited gates, not all-scene correctness, perceived smoothness, or performance acceptance.')
    try:
        first,last,every = map(int,args.frames.split(':'))
        frames = requested_frames(first,last,every)
        if not frames:
            raise ValueError('empty comparison window')
        compare(args.control,args.candidate,frames,report=report,
                control_report=args.control_report,candidate_report=args.candidate_report)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report['error'] = str(exc)
    write_json(args.output,report)
    print('PASS' if report['passed'] else 'FAIL', args.output)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
