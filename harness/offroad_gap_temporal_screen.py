"""Screen the saved El Paso turn for a persistent left-margin blue opening.

Uses a deliberately narrow CRT-color heuristic plus the completed image sequence.
The count is a review aid, not an indexed sky or exact missing-geometry mask.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from verification import image_signature


ROOT = Path(__file__).resolve().parents[1] / 'results/diagnostics/offroad-full-20260910'
RUN = ROOT / 'left-gap-temporal-run'
CONTROL = ROOT / 'left-gap-original-run'
EXPECTED = list(range(3100, 3141, 4))
ROI = (40, 475, 400, 625)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(contact=None):
    report_path = RUN / 'report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    control = json.loads((CONTROL / 'report.json').read_text(encoding='utf-8'))
    if (report.get('passed') is not True or control.get('passed') is not True or
            report['case'] != control['case'] or
            report['comparison']['input_or_time_mismatches'] or
            report['comparison']['pixel_mismatches'] or
            not report['display_watch']['passed']):
        raise ValueError('temporal and control replays are not qualified')
    for name in ('run/invocation.json',):
        first = json.loads((RUN / name).read_text(encoding='utf-8'))
        prior = json.loads((CONTROL / name).read_text(encoding='utf-8'))
        if first['executable_sha256'] != prior['executable_sha256']:
            raise ValueError('temporal/control emulator differs')
        if first['environment']['MIDV_FFB'] != '0':
            raise ValueError('temporal replay must be actuator-free')

    snap = RUN / 'run/gl-snap'
    capture_path = snap / 'captures.csv'
    receipt = report['evidence']['gl_captures']
    if (receipt['count'] != len(EXPECTED) or
            receipt['completed_frames'] != EXPECTED or
            receipt['index_sha256'] != sha256(capture_path)):
        raise ValueError('completed capture receipt differs')
    with capture_path.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if ([int(row['completed_frame']) for row in rows] != EXPECTED or
            len({row['file'] for row in rows}) != len(rows) or
            any((int(row['width']), int(row['height']), int(row['visible_page']))
                != (2544, 1353, 1) or int(row['dropped_messages']) != 0 for row in rows)):
        raise ValueError('completed capture schedule, size, page or queue differs')
    captured_3120 = snap / rows[EXPECTED.index(3120)]['file']
    prior_3120 = CONTROL / 'run/gl-snap/mvgl_000.bmp'
    if sha256(captured_3120) != sha256(prior_3120):
        raise ValueError('source-joined frame 3120 is not byte-exact')

    samples = []
    tiles = []
    for row in rows:
        path = snap / row['file']
        if image_signature(path) != receipt['files'][row['file']]:
            raise ValueError('completed pixels differ from replay receipt')
        with Image.open(path) as image:
            if image.size != (2544, 1353):
                raise ValueError('completed BMP dimensions differ')
            rgb = image.convert('RGB')
            patch = np.asarray(rgb.crop(ROI), dtype='i2')
            panel = rgb.crop((40, 450, 500, 650))
        # Pair neighboring CRT-mask columns before testing the source-sky hue.
        pair = (patch[:, ::2, :] + patch[:, 1::2, :]) / 2
        blue = ((pair[:, :, 2] > pair[:, :, 0] + 10) &
                (pair[:, :, 1] > pair[:, :, 0] + 5) &
                (pair[:, :, 2] > pair[:, :, 1] + 3) &
                (pair[:, :, 0] > 35))
        samples.append(dict(frame=int(row['completed_frame']),
                            heuristic_blue_pair_pixels=int(blue.sum()),
                            image_sha256=sha256(path)))
        tiles.append(panel)

    if contact is not None:
        if contact.exists():
            raise ValueError('refusing to overwrite existing contact sheet')
        contact.parent.mkdir(parents=True, exist_ok=True)
        canvas = Image.new('RGB', (1840, 690), 'black')
        draw = ImageDraw.Draw(canvas)
        for i, (sample, tile) in enumerate(zip(samples, tiles)):
            x, y = (i % 4) * 460, (i // 4) * 230
            canvas.paste(tile, (x, y + 25))
            draw.text((x + 8, y + 5), str(sample['frame']), fill='white')
        canvas.save(contact)

    return dict(passed=True, replay=str(RUN.resolve()), control=str(CONTROL.resolve()),
                completed_frames=EXPECTED, completed_size=[2544, 1353],
                same_3120_bmp_sha256=sha256(captured_3120),
                roi_xyxy=list(ROI), heuristic='Pair adjacent CRT columns; B>R+10, '
                'G>R+5, B>G+3, R>35 in client ROI. Counts are not a sky-area proof.',
                samples=samples,
                source_sha256={path.name: sha256(path) for path in
                               (report_path, CONTROL / 'report.json', capture_path)},
                scope='One recorded El Paso turn, 11 completed 1440p-client captures. '
                      'No 4K or cross-course acceptance, no renderer repair or FFB test.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--contact', type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite temporal gap report')
    result = analyze(args.contact)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', [(row['frame'], row['heuristic_blue_pair_pixels']) for row in result['samples']])


if __name__ == '__main__':
    main()
