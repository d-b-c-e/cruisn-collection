"""Compare the bounded Off-Road resident-margin trial with its saved 3x control."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'results/diagnostics/offroad-full-20260910'
CONTROL = HERE / 'left-gap-temporal-run'
TRIAL = HERE / 'left-gap-resident-temporal-run'
FRAMES = list(range(3100, 3141, 4))


def captures(path):
    with (path / 'run/gl-snap/captures.csv').open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    result = {int(row['completed_frame']): row for row in rows}
    if list(result) != FRAMES or len(rows) != len(FRAMES):
        raise ValueError('missing, duplicate or unordered completed frames')
    if any((int(row['width']), int(row['height']), int(row['visible_page'])) != (2544, 1353, 1)
           for row in rows):
        raise ValueError('completed dimensions or page changed')
    return result


def screen(contact=None):
    reports = [json.loads((path / 'report.json').read_text(encoding='utf-8'))
               for path in (CONTROL, TRIAL)]
    if any(not report['passed'] or not report['comparison']['passed']
           or report['display_watch']['changes'] for report in reports):
        raise ValueError('control or trial replay failed input/display qualification')
    if reports[0]['case'] != reports[1]['case'] or reports[1]['offroad_host_scenery'].get('resident_margins') is not True:
        raise ValueError('candidate does not match recorded control case/policy')
    invocations = [json.loads((path / 'run/invocation.json').read_text(encoding='utf-8'))
                   for path in (CONTROL, TRIAL)]
    if any(inv['environment'].get('MIDV_FFB') != '0' for inv in invocations):
        raise ValueError('physical force must be disabled')
    rows = [captures(path) for path in (CONTROL, TRIAL)]
    output = []
    contact_images = []
    # The hardware 4:3 left edge maps to about x370 in the completed client.
    # Allow only pixels to its left to differ; exact center/right acceptance.
    cutoff = 370
    for frame in FRAMES:
        paths = [path / 'run/gl-snap' / row[frame]['file'] for path, row in zip((CONTROL, TRIAL), rows)]
        images = [np.asarray(Image.open(path).convert('RGB')) for path in paths]
        different = np.any(images[0] != images[1], axis=2)
        yy, xx = np.where(different)
        if not len(xx) or int(xx.max()) >= cutoff:
            raise ValueError(f'frame {frame} has no margin gain or changes outside the left margin')
        old_dark = np.max(images[0], axis=2) < 40
        new_dark = np.max(images[1], axis=2) < 40
        output.append(dict(frame=frame, changed_pixels=int(different.sum()),
                           box=[int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())],
                           new_near_black=int((different & new_dark & ~old_dark).sum()),
                           removed_near_black=int((different & old_dark & ~new_dark).sum()),
                           control_sha256=hashlib.sha256(paths[0].read_bytes()).hexdigest(),
                           trial_sha256=hashlib.sha256(paths[1].read_bytes()).hexdigest()))
        if frame in (3100, 3120, 3136, 3140):
            contact_images.append((frame, images))
    if contact is not None:
        contact.parent.mkdir(parents=True, exist_ok=True)
        canvas = Image.new('RGB', (960, 4 * 420), 'black')
        draw = ImageDraw.Draw(canvas)
        for row, (frame, images) in enumerate(contact_images):
            for col, (label, rgb) in enumerate(zip(('control', 'resident'), images)):
                canvas.paste(Image.fromarray(rgb).crop((40, 250, 520, 650)), (col*480, row*420+20))
                draw.text((col*480+8, row*420+4), f'{frame} {label}', fill='white')
        canvas.save(contact)
    return dict(frames=output, changed_range=[min(r['changed_pixels'] for r in output),
                                               max(r['changed_pixels'] for r in output)],
                new_near_black_total=sum(r['new_near_black'] for r in output),
                changed_outside_left_margin=0, cutoff_completed_x=cutoff,
                control_binary_sha256=invocations[0]['executable_sha256'],
                trial_binary_sha256=invocations[1]['executable_sha256'],
                scope='11 exact completed-frame pairs at physical 1440p; dark threshold is heuristic, not full visual acceptance')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--contact', type=Path)
    args = parser.parse_args()
    if args.report.exists() or args.contact and args.contact.exists():
        raise ValueError('refusing to overwrite saved analysis')
    result = screen(args.contact)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('changed_range', 'new_near_black_total', 'changed_outside_left_margin')}))


if __name__ == '__main__':
    main()
