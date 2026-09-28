"""Screen paired USA bridge images for a bounded red-color continuity hint.

This is a color predicate over completed CRT pixels, not object segmentation.
It cannot prove smooth motion, source identity, texture quality or a full bridge.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from screen_vunit_panorama_strips import sha


FRAMES = list(range(10460, 10501, 4))
ROI = (70, 450, 290, 710)  # XYXY, contains every changed pixel of the paired interval.


def captures(root):
    path = root / 'run/gl-snap/captures.csv'
    with path.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    if (len(rows) != len(FRAMES) or
            [int(row['completed_frame']) for row in rows] != FRAMES or
            any(row['file'] != f'mvgl_{i:03}.bmp' or
                (int(row['width']), int(row['height'])) != (2544, 1353) or
                int(row['dropped_messages']) for i, row in enumerate(rows))):
        raise ValueError('completed capture schedule or dimensions differ')
    return rows, sha(path)


def red(pixels):
    # Integer arithmetic fixes the exact heuristic across NumPy versions.
    rgb = pixels.astype(np.int32)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    return (r > 110) & (r * 100 > g * 135) & (r * 100 > b * 125)


def screen(off, on, qualification):
    qualified = json.loads(qualification.read_text(encoding='utf-8'))
    if (not qualified.get('passed') or qualified.get('changed_frames') != FRAMES or
            qualified['sha256']['control_report'] != sha(off / 'report.json') or
            qualified['sha256']['candidate_report'] != sha(on / 'report.json')):
        raise ValueError('paired interval qualification differs')
    old_rows, old_schedule = captures(off)
    new_rows, new_schedule = captures(on)
    x0, y0, x1, y1 = ROI
    result = []
    image_hash = hashlib.sha256()
    for frame, old, new in zip(FRAMES, old_rows, new_rows):
        old_path = off / 'run/gl-snap' / old['file']
        new_path = on / 'run/gl-snap' / new['file']
        for path in (old_path, new_path):
            image_hash.update(bytes.fromhex(sha(path)))
        a = np.asarray(Image.open(old_path).convert('RGB'))[y0:y1, x0:x1]
        b = np.asarray(Image.open(new_path).convert('RGB'))[y0:y1, x0:x1]
        ordinary, covered = red(a), red(b)
        result.append(dict(frame=frame, control_red=int(ordinary.sum()),
                           candidate_red=int(covered.sum()),
                           candidate_only_red=int((covered & ~ordinary).sum()),
                           control_only_red=int((ordinary & ~covered).sum())))
    if (not all(row['candidate_only_red'] > row['control_only_red'] for row in result) or
            not result[5]['candidate_only_red'] < result[4]['candidate_only_red']):
        raise ValueError('saved red transition differs from expected interval')
    return dict(schema=1, passed=True,
                scope='Heuristic red CRT pixels in one fixed far-left ROI of 11 matched '
                      'USA Golden Gate images. This is not bridge-object segmentation, '
                      'a frame-continuity proof or a global pop-in result.',
                roi_xyxy=list(ROI), predicate='R>110 and 100R>135G and 100R>125B',
                samples=result,
                sha256={'qualification': sha(qualification),
                        'control_capture_schedule': old_schedule,
                        'candidate_capture_schedule': new_schedule,
                        'ordered_image_digests': image_hash.hexdigest()})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('off', 'on', 'qualification', 'report'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite transition screen')
    result = screen(args.off, args.on, args.qualification)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', len(result['samples']),
          [row['candidate_only_red'] for row in result['samples']])


if __name__ == '__main__':
    main()
