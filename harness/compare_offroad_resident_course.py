"""Compare matched Off-Road course captures with resident margins on and off.

This is a sparse completed-frame safety screen, not a whole-course texture or
4K acceptance test. The hardware center must remain byte-exact.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from verification import image_signature


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_run(path):
    report_path = path / 'report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    invocation_path = path / 'run/invocation.json'
    invocation = json.loads(invocation_path.read_text(encoding='utf-8'))
    index = path / 'run/gl-snap/captures.csv'
    with index.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    receipt = report['evidence']['gl_captures']
    frames = [int(row['completed_frame']) for row in rows]
    if (report.get('passed') is not True or report['comparison']['passed'] is not True or
            report['display_watch']['passed'] is not True or
            invocation['environment'].get('MIDV_FFB') != '0' or
            len(rows) != receipt['count'] or frames != receipt['completed_frames'] or
            len(set(frames)) != len(frames) or receipt['dropped_messages'] != 0 or
            sha256(index) != receipt['index_sha256']):
        raise ValueError(f'unqualified replay or capture receipt: {path}')
    for row in rows:
        image = path / 'run/gl-snap' / row['file']
        if row['file'] not in receipt['files'] or image_signature(image) != receipt['files'][row['file']]:
            raise ValueError(f'completed image receipt differs: {image}')
    return report, invocation, rows, {'report': sha256(report_path),
                                      'invocation': sha256(invocation_path),
                                      'captures': sha256(index)}


def compare(control, trial, margin_cutoff):
    (a, ai, ar, ah), (b, bi, br, bh) = load_run(control), load_run(trial)
    if (a['case'] != b['case'] or
            ai['executable_sha256'] != bi['executable_sha256'] or
            a['offroad_host_scenery'].get('resident_margins') is True or
            b['offroad_host_scenery'].get('resident_margins') is not True or
            len(ar) != len(br) or not ar):
        raise ValueError('control and trial do not share the case, binary, or intended policy')
    output = []
    for old, new in zip(ar, br):
        old_descriptor = tuple(old[key] for key in ('completed_frame', 'width', 'height', 'visible_page'))
        new_descriptor = tuple(new[key] for key in ('completed_frame', 'width', 'height', 'visible_page'))
        if old_descriptor != new_descriptor or int(old['dropped_messages']) or int(new['dropped_messages']):
            raise ValueError('capture schedule, dimensions, page or queue differs')
        paths = [run / 'run/gl-snap' / row['file'] for run, row in ((control, old), (trial, new))]
        with Image.open(paths[0]) as old_image, Image.open(paths[1]) as new_image:
            before = np.asarray(old_image.convert('RGB'))
            after = np.asarray(new_image.convert('RGB'))
        if before.shape != after.shape or before.shape[1] <= margin_cutoff * 2:
            raise ValueError('completed sizes or center cutoff differ')
        changed = np.any(before != after, axis=2)
        yy, xx = np.where(changed)
        center = changed[:, margin_cutoff:before.shape[1] - margin_cutoff]
        new_black = changed & np.all(after <= 8, axis=2) & np.any(before >= 32, axis=2)
        output.append({
            'frame': int(old['completed_frame']),
            'visible_page': int(old['visible_page']),
            'changed_pixels': int(changed.sum()),
            'left_changed': int(changed[:, :margin_cutoff].sum()),
            'center_changed': int(center.sum()),
            'right_changed': int(changed[:, before.shape[1] - margin_cutoff:].sum()),
            'change_box': [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())] if len(xx) else None,
            'new_near_black_hint': int(new_black.sum()),
            'control_sha256': sha256(paths[0]),
            'trial_sha256': sha256(paths[1]),
        })
    return {
        'passed': all(row['center_changed'] == 0 for row in output),
        'case': a['case'],
        'binary_sha256': ai['executable_sha256'],
        'prepared_scenes': [a['vunit_runtime']['result']['scenes'],
                            b['vunit_runtime']['result']['scenes']],
        'submitted_quads': [a['vunit_runtime']['result']['quads'],
                            b['vunit_runtime']['result']['quads']],
        'trial_minus_control_submitted_quads': (b['vunit_runtime']['result']['quads'] -
                                                a['vunit_runtime']['result']['quads']),
        'margin_cutoff_completed_x': margin_cutoff,
        'completed_size': [int(ar[0]['width']), int(ar[0]['height'])],
        'samples': output,
        'source_sha256': {'control': ah, 'trial': bh},
        'scope': 'Matched sparse 1440p completed frames, original input/native replay and owned shutdown. '
                 'Near-black counts are review hints, not texture-defect proof; no 4K or full-course visual claim.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--trial', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--margin-cutoff', type=int, default=370)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite report')
    result = compare(args.control, args.trial, args.margin_cutoff)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS' if result['passed'] else 'FAIL', [(x['frame'], x['changed_pixels'], x['center_changed'])
                                                for x in result['samples']])
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
