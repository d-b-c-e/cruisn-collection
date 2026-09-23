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
NO_HOST = ROOT / 'left-gap-temporal-control-run'
EXPECTED = list(range(3100, 3141, 4))
ROI = (40, 475, 400, 625)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(contact=None, pair_contact=None):
    report_path = RUN / 'report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    control = json.loads((CONTROL / 'report.json').read_text(encoding='utf-8'))
    if (report.get('passed') is not True or control.get('passed') is not True or
            report['case'] != control['case'] or
            report['comparison']['input_or_time_mismatches'] or
            report['comparison']['pixel_mismatches'] or
            not report['display_watch']['passed']):
        raise ValueError('temporal and control replays are not qualified')
    no_host_report = json.loads((NO_HOST / 'report.json').read_text(encoding='utf-8'))
    if (no_host_report.get('passed') is not True or
            no_host_report['case'] != report['case'] or
            no_host_report['comparison']['input_or_time_mismatches'] or
            no_host_report['comparison']['pixel_mismatches'] or
            not no_host_report['display_watch']['passed']):
        raise ValueError('matched no-host replay is not qualified')
    for name in ('run/invocation.json',):
        first = json.loads((RUN / name).read_text(encoding='utf-8'))
        prior = json.loads((CONTROL / name).read_text(encoding='utf-8'))
        if first['executable_sha256'] != prior['executable_sha256']:
            raise ValueError('temporal/control emulator differs')
        if first['environment']['MIDV_FFB'] != '0':
            raise ValueError('temporal replay must be actuator-free')
        plain = json.loads((NO_HOST / name).read_text(encoding='utf-8'))
        if (plain['executable_sha256'] != first['executable_sha256'] or
                plain['environment']['MIDV_FFB'] != '0' or
                plain['environment'].get('MIDV_OFFROAD_HOST_SCENERY') not in (None, '0')):
            raise ValueError('no-host executable or policy differs')

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
    plain_snap = NO_HOST / 'run/gl-snap'
    plain_index = plain_snap / 'captures.csv'
    with plain_index.open(encoding='utf-8', newline='') as stream:
        plain_rows = list(csv.DictReader(stream))
    plain_receipt = no_host_report['evidence']['gl_captures']
    if (plain_receipt['count'] != len(EXPECTED) or
            plain_receipt['completed_frames'] != EXPECTED or
            plain_receipt['index_sha256'] != sha256(plain_index) or
            [int(row['completed_frame']) for row in plain_rows] != EXPECTED or
            any((int(row['width']), int(row['height']), int(row['visible_page']))
                != (2544, 1353, 1)
                or int(row['dropped_messages']) != 0 for row in plain_rows)):
        raise ValueError('no-host completed capture schedule or receipt differs')
    captured_3120 = snap / rows[EXPECTED.index(3120)]['file']
    prior_3120 = CONTROL / 'run/gl-snap/mvgl_000.bmp'
    if sha256(captured_3120) != sha256(prior_3120):
        raise ValueError('source-joined frame 3120 is not byte-exact')

    samples = []
    tiles = []
    pair_tiles = {}
    for row, plain_row in zip(rows, plain_rows):
        path = snap / row['file']
        plain_path = plain_snap / plain_row['file']
        if image_signature(path) != receipt['files'][row['file']]:
            raise ValueError('completed pixels differ from replay receipt')
        if image_signature(plain_path) != plain_receipt['files'][plain_row['file']]:
            raise ValueError('no-host pixels differ from replay receipt')
        with Image.open(path) as image, Image.open(plain_path) as plain_image:
            if image.size != (2544, 1353) or plain_image.size != image.size:
                raise ValueError('completed BMP dimensions differ')
            rgb = image.convert('RGB')
            plain_rgb = plain_image.convert('RGB')
            patch = np.asarray(rgb.crop(ROI), dtype='i2')
            plain_patch = np.asarray(plain_rgb.crop(ROI), dtype='i2')
            changed = int(np.any(np.asarray(rgb) != np.asarray(plain_rgb), axis=2).sum())
            panel = rgb.crop((40, 450, 500, 650))
            if int(row['completed_frame']) in (3108, 3120, 3124, 3136):
                pair_tiles[int(row['completed_frame'])] = (
                    plain_rgb.crop((40, 450, 500, 650)), panel)
        # Pair neighboring CRT-mask columns before testing the source-sky hue.
        def count_blue(values):
            pair = (values[:, ::2, :] + values[:, 1::2, :]) / 2
            return int(((pair[:, :, 2] > pair[:, :, 0] + 10) &
                        (pair[:, :, 1] > pair[:, :, 0] + 5) &
                        (pair[:, :, 2] > pair[:, :, 1] + 3) &
                        (pair[:, :, 0] > 35)).sum())
        blue = count_blue(patch)
        plain_blue = count_blue(plain_patch)
        samples.append(dict(frame=int(row['completed_frame']),
                            heuristic_blue_pair_pixels=blue,
                            no_host_blue_pair_pixels=plain_blue,
                            host_minus_no_host_blue_pairs=blue - plain_blue,
                            changed_completed_pixels=changed,
                            image_sha256=sha256(path),
                            no_host_image_sha256=sha256(plain_path)))
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

    if pair_contact is not None:
        if pair_contact.exists():
            raise ValueError('refusing to overwrite existing comparison sheet')
        pair_contact.parent.mkdir(parents=True, exist_ok=True)
        canvas = Image.new('RGB', (920, 920), 'black')
        draw = ImageDraw.Draw(canvas)
        for i, (frame, pair) in enumerate(pair_tiles.items()):
            for column, (label, tile) in enumerate(zip(('no host', '3x host'), pair)):
                x, y = column * 460, i * 230
                canvas.paste(tile, (x, y + 25))
                draw.text((x + 8, y + 5), f'{frame} {label}', fill='white')
        canvas.save(pair_contact)

    return dict(passed=True, replay=str(RUN.resolve()), control=str(CONTROL.resolve()),
                no_host_control=str(NO_HOST.resolve()),
                completed_frames=EXPECTED, completed_size=[2544, 1353],
                same_3120_bmp_sha256=sha256(captured_3120),
                roi_xyxy=list(ROI), heuristic='Pair adjacent CRT columns; B>R+10, '
                'G>R+5, B>G+3, R>35 in client ROI. Counts are not a sky-area proof.',
                samples=samples,
                source_sha256={label: sha256(path) for label, path in
                               (('host_report', report_path),
                                ('source_joined_report', CONTROL / 'report.json'),
                                ('no_host_report', NO_HOST / 'report.json'),
                                ('host_captures_csv', capture_path),
                                ('no_host_captures_csv', plain_index))},
                scope='One recorded El Paso turn, 11 completed 1440p-client captures. '
                      'No 4K or cross-course acceptance, no renderer repair or FFB test.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--contact', type=Path)
    parser.add_argument('--pair-contact', type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite temporal gap report')
    result = analyze(args.contact, args.pair_contact)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', [(row['frame'], row['heuristic_blue_pair_pixels']) for row in result['samples']])


if __name__ == '__main__':
    main()
