"""Attribute selected indexed V-Unit pixels using a saved original mirror.

Direct coordinates are bottom-up fine pixels in the indexed mirror. An optional
calibrated 1440p CRT screenshot point maps to its center indexed sample after a
full-image reconstruction check. Source DMA is reported only when its
isolated raster matches the captured original-only pixel. It does not validate
the complete host packet stream, surrounding image or temporal behavior.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from offroad_gap_loaded_screen import render_quads, resolve
from vunit_display_scene import load as original_scene


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def screen_to_indexed(x, y):
    """Center sample for the empirically qualified 2544x1353 V-Unit CRT view."""
    if not (67 <= x < 2477 and 0 <= y < 1353):
        raise ValueError('screen point outside calibrated 1440p V-Unit viewport')
    u = (x + .5 - 67) / 2410
    v = (1353 - y - .5) / 1353
    cx, cy = 2 * u - 1, 2 * v - 1
    wx = .5 * cx * (1 + .041 * cy * cy) + .5
    wy = .5 * cy * (1 + .052 * cx * cx) + .5
    if not (0 <= wx < 1 and 0 <= wy < 1):
        raise ValueError('screen point outside the CRT glass')
    return int(wx * 2736), int(wy * 1600)


def screen_capture(run, frame, page, planes, screen_points):
    mapped = [screen_to_indexed(x, y) for x, y in screen_points]
    captures = run / 'gl-snap/captures.csv'
    with captures.open(newline='', encoding='utf-8') as stream:
        rows = [row for row in csv.DictReader(stream)
                if int(row['completed_frame']) == frame and int(row['visible_page']) == page]
    if len(rows) != 1 or (int(rows[0]['width']), int(rows[0]['height'])) != (2544, 1353):
        raise ValueError('no unique calibrated 1440p completed image for mirror frame/page')
    screenshot = run / 'gl-snap' / rows[0]['file']
    with Image.open(screenshot) as source:
        reference = np.asarray(source.convert('RGB'))
    palette = run / 'capture/paletteram.bin'
    reconstructed = resolve(planes[0], planes[1], palette.read_bytes())
    delta = np.max(np.abs(reconstructed.astype('i2') - reference.astype('i2')), axis=2)
    over_one = int(np.count_nonzero(delta > 1))
    if over_one > 1000:
        raise ValueError('saved CRT screenshot does not match indexed/palette reconstruction')
    return mapped, dict(completed_frame=frame, visible_page=page,
                        screenshot=rows[0]['file'], size=[2544, 1353],
                        viewport=[67, 0, 2410, 1353],
                        pixels_differing_over_one_channel_unit=over_one,
                        maximum_channel_difference=int(delta.max()),
                        center_samples=[{'screen': list(point), 'indexed': list(indexed)}
                                        for point, indexed in zip(screen_points, mapped)],
                        scope='CRT center samples; beam blur and dither may also use '
                              'neighboring indexed pixels. Only calibrated 1440p geometry.',
                        sha256={'captures': sha(captures), 'screenshot': sha(screenshot),
                                'palette': sha(palette)})


def probe(run, points, screen_points=()):
    run = Path(run)
    receipt_path = run / 'vunit-mirror.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    frame, page = int(receipt['frame']), int(receipt['visible_page'])
    width, height = int(receipt['width']), int(receipt['height'])
    if page not in (0, 1) or (width, height) != (2736, 1600):
        raise ValueError('unsupported V-Unit mirror geometry or page')
    if (not points and not screen_points or
            any(not (0 <= x < width and 0 <= y < height) for x, y in points)):
        raise ValueError('empty or out-of-bounds indexed point selection')
    prefix = f'vunit-mirror-{frame}-page{page}-plane'
    paths = [run / (prefix + str(i) + '.bin') for i in range(4)]
    planes = []
    for i, path in enumerate(paths):
        dtype = '<u2' if i % 2 == 0 else 'u1'
        value = np.fromfile(path, dtype=dtype)
        if value.size != width * height:
            raise ValueError(f'incomplete indexed mirror plane {i}')
        planes.append(value.reshape(height, width))
    display = None
    if screen_points:
        mapped, display = screen_capture(run, frame, page, planes, screen_points)
        points = [*points, *mapped]
    if not points or any(not (0 <= x < width and 0 <= y < height) for x, y in points):
        raise ValueError('empty or out-of-bounds indexed point selection')
    source = original_scene(run)
    raw_report = run.parent / 'report.json'
    replay = json.loads(raw_report.read_text(encoding='utf-8')) if raw_report.is_file() else None
    texture = run / 'capture/textureram.bin'
    dma_index, dma_tag = render_quads(source.current, texture.read_bytes())
    dma_id, id_tag = render_quads(source.current, texture.read_bytes(), debug_quad_id=True)
    if dma_index.shape != (height, width) or dma_tag.shape != (height, width):
        raise ValueError('original DMA raster differs from mirror geometry')
    rows = []
    for x, y in points:
        combined = [int(planes[0][y, x]), int(planes[1][y, x])]
        original = [int(planes[2][y, x]), int(planes[3][y, x])]
        sampled = [int(dma_index[y, x]), int(dma_tag[y, x]) & 3]
        match = bool(id_tag[y, x] and original == sampled)
        owner = ('auxiliary' if combined[1] & 4 else
                 'original_or_prior_page' if combined[1] else 'unowned')
        row = dict(indexed=[x, y], combined=combined, original_only=original,
                   combined_owner=owner, current_original_dma=sampled,
                   current_original_dma_matches_original_only=match)
        if match:
            ordinal = int(dma_id[y, x])
            quad = np.asarray(source.current[ordinal], dtype='<u2')
            row['current_original_dma_ordinal'] = ordinal
            row['current_original_dma_quad'] = [int(v) for v in quad]
            row['current_original_dma_quad_sha256'] = hashlib.sha256(quad.tobytes()).hexdigest()
        rows.append(row)
    return dict(schema=1, scope='Selected bottom-up indexed pixels only; original DMA '
                'attribution requires a matching isolated raster. Host source and '
                'complete CRT color provenance are not inferred.', frame=frame,
                visible_page=page, geometry=[width, height],
                replay_report={'passed': replay.get('passed'), 'error': replay.get('error')}
                if replay is not None else None,
                original_scene=source.report, completed_screen=display, points=rows,
                sha256={'mirror_receipt': sha(receipt_path),
                        'replay_report': sha(raw_report) if replay is not None else None,
                        'original_dma': sha(run / 'capture/quads.bin'),
                        'texture': sha(texture),
                        **{f'plane{i}': sha(path) for i, path in enumerate(paths)}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--point', action='append', default=[],
                        help='bottom-up fine indexed X,Y; repeat for more points')
    parser.add_argument('--screen-point', action='append', default=[],
                        help='calibrated 2544x1353 CRT screenshot X,Y; center sample only')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite indexed pixel probe')
    points = [tuple(map(int, value.split(','))) for value in args.point]
    screen_points = [tuple(map(int, value.split(','))) for value in args.screen_point]
    if any(len(point) != 2 for point in (*points, *screen_points)):
        raise ValueError('each point must be X,Y')
    result = probe(args.run, points, screen_points)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', result['frame'], len(result['points']))


if __name__ == '__main__':
    main()
