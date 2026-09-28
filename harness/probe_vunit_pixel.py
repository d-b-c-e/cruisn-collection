"""Attribute selected indexed V-Unit pixels using a saved original mirror.

Coordinates are bottom-up fine pixels in the indexed mirror, not CRT screenshot
pixels. This is a point diagnostic: source DMA is reported only when its
isolated raster matches the captured original-only pixel. It does not validate
the complete host packet stream, surrounding image or temporal behavior.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from offroad_gap_loaded_screen import render_quads
from vunit_display_scene import load as original_scene


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(run, points):
    run = Path(run)
    receipt_path = run / 'vunit-mirror.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    frame, page = int(receipt['frame']), int(receipt['visible_page'])
    width, height = int(receipt['width']), int(receipt['height'])
    if page not in (0, 1) or (width, height) != (2736, 1600):
        raise ValueError('unsupported V-Unit mirror geometry or page')
    if not points or any(not (0 <= x < width and 0 <= y < height) for x, y in points):
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
                'completed CRT colors are not reconstructed.', frame=frame,
                visible_page=page, geometry=[width, height],
                replay_report={'passed': replay.get('passed'), 'error': replay.get('error')}
                if replay is not None else None,
                original_scene=source.report, points=rows,
                sha256={'mirror_receipt': sha(receipt_path),
                        'replay_report': sha(raw_report) if replay is not None else None,
                        'original_dma': sha(run / 'capture/quads.bin'),
                        'texture': sha(texture),
                        **{f'plane{i}': sha(path) for i, path in enumerate(paths)}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--point', action='append', required=True,
                        help='bottom-up fine indexed X,Y; repeat for more points')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite indexed pixel probe')
    points = [tuple(map(int, value.split(','))) for value in args.point]
    if any(len(point) != 2 for point in points):
        raise ValueError('each point must be X,Y')
    result = probe(args.run, points)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', result['frame'], len(result['points']))


if __name__ == '__main__':
    main()
