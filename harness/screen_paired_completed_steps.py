"""Measure adjacent completed-image changes in an already qualified paired replay.

Counts locate a transition for review; they do not identify geometry or judge
whether a motion step looks good. Capture bytes and the paired report are
verified before analysis.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from gl_frames import capture_paths
from verification import image_signature


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def step_counts(control_before, control_after, trial_before, trial_after):
    if not all(image.shape == control_before.shape for image in
               (control_after, trial_before, trial_after)):
        raise ValueError('completed image dimensions differ')
    control_motion = np.any(control_before != control_after, axis=2)
    trial_motion = np.any(trial_before != trial_after, axis=2)
    paired_before = np.any(control_before != trial_before, axis=2)
    paired_after = np.any(control_after != trial_after, axis=2)
    return dict(control_changed_pixels=int(control_motion.sum()),
                trial_changed_pixels=int(trial_motion.sum()),
                trial_only_changed_locations=int((trial_motion & ~control_motion).sum()),
                control_only_changed_locations=int((control_motion & ~trial_motion).sum()),
                both_changed_locations=int((control_motion & trial_motion).sum()),
                paired_difference_before=int(paired_before.sum()),
                paired_difference_after=int(paired_after.sum()),
                paired_difference_gained_locations=int((paired_after & ~paired_before).sum()),
                paired_difference_lost_locations=int((paired_before & ~paired_after).sum()),
                paired_difference_shared_locations=int((paired_before & paired_after).sum()))


def screen(paired_path):
    paired_path = Path(paired_path)
    paired = json.loads(paired_path.read_text(encoding='utf-8'))
    if not paired.get('passed') or paired.get('completed_center_third_changed_pixels') != 0:
        raise ValueError('paired motion/preservation qualification did not pass')
    roots = [Path(paired['completed'][name]).parent.parent for name in
             ('reference', 'candidate')]
    reports = [json.loads((root / 'report.json').read_text(encoding='utf-8'))
               for root in roots]
    paths = [capture_paths(root / 'run/gl-snap') for root in roots]
    expected = sorted(paths[0])
    if (expected != sorted(paths[1]) or len(expected) != paired['completed']['frames']
            or any(not report['passed'] for report in reports)):
        raise ValueError('completed frame/route receipt differs')
    for i, label in enumerate(('control', 'trial')):
        if (sha(roots[i] / 'report.json') != paired['sha256'][label + '_report'] or
                sha(roots[i] / 'run/gl-snap/captures.csv') !=
                paired['sha256'][label + '_capture_index']):
            raise ValueError(f'{label} report/capture index differs')
        receipts = reports[i]['evidence']['gl_captures']['files']
        for path in paths[i].values():
            if image_signature(path) != receipts[path.name]:
                raise ValueError(f'{label} completed image changed: {path}')
    def pixels(path):
        with Image.open(path) as image:
            return np.asarray(image.convert('RGB')).copy()

    before = [pixels(files[expected[0]]) for files in paths]
    steps = []
    for previous, current in zip(expected, expected[1:]):
        after = [pixels(files[current]) for files in paths]
        counts = step_counts(before[0], after[0], before[1], after[1])
        steps.append(dict(from_frame=previous, to_frame=current, **counts))
        before = after
    return dict(schema=1, passed=True,
                scope='Adjacent completed RGB frame-pixel changes and paired-mode '
                      'difference-footprint turnover for one matched recorded interval. '
                      'Raw adjacent motion includes CRT temporal changes over much of the '
                      'screen; paired turnover is a better locator, not object identity, '
                      'a quality verdict, or continuous-frame acceptance.',
                frames=expected, steps=steps,
                sha256={'paired_report': sha(paired_path),
                        'control_report': sha(roots[0] / 'report.json'),
                        'trial_report': sha(roots[1] / 'report.json')} )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paired-report', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite completed-step evidence')
    result = screen(args.paired_report)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', len(result['steps']), 'adjacent completed steps')


if __name__ == '__main__':
    main()
