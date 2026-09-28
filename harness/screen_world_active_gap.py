"""Isolated raster screen of source-time World active quads at a recorded gap.

This is an offline material/coverage trial, not an ordered native draw policy.
Only exact zero-index/zero-tag connected regions may be replaced in previews.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from offroad_gap_loaded_screen import render_quads, resolve


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def component(planes, geometry):
    x0, y0, x1, y1 = geometry['fine_box']
    sx, sy = geometry['unowned_component']['seed']
    region = np.logical_and.reduce([plane[y0:y1+1, x0:x1+1] == 0 for plane in planes])
    if not region[sy-y0, sx-x0]:
        raise ValueError('saved gap seed is now owned')
    seen = np.zeros_like(region, dtype=bool)
    seen[sy-y0, sx-x0] = True
    queue = deque([(sx-x0, sy-y0)])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
            if (0 <= nx < region.shape[1] and 0 <= ny < region.shape[0]
                    and region[ny, nx] and not seen[ny, nx]):
                seen[ny, nx] = True
                queue.append((nx, ny))
    expected = geometry['unowned_component']
    ys, xs = np.where(seen)
    bounds = [int(xs.min()+x0), int(ys.min()+y0),
              int(xs.max()+x0), int(ys.max()+y0)]
    if int(seen.sum()) != expected['pixels'] or bounds != expected['fine_bounds']:
        raise ValueError('connected gap differs from source-hashed geometry report')
    full = np.zeros_like(planes[0], dtype=bool)
    full[y0:y1+1, x0:x1+1] = seen
    return full


def screen(baseline_run, source_tap_run, projection_path, geometry_paths, preview_dir=None):
    baseline_report = json.loads((baseline_run/'report.json').read_text())
    source_report = json.loads((source_tap_run/'report.json').read_text())
    projection = json.loads(projection_path.read_text())
    geometries = {name: json.loads(path.read_text()) for name, path in geometry_paths.items()}
    if (not baseline_report.get('passed') or not source_report.get('passed')
            or baseline_report['case'] != source_report['case']
            or baseline_report['emulator_source']['executable_sha256'] !=
               source_report['emulator_source']['executable_sha256']
            or baseline_report['evidence']['gl_captures']['files'] !=
               source_report['evidence']['gl_captures']['files']
            or baseline_report['vunit_original_mirror']['result']['sha256'] !=
               source_report['vunit_original_mirror']['result']['sha256']
            or not projection['baseline_qualified']
            or projection['source_kind'] != 'scene-boundary Lua read tap'
            or projection['counts']['exact_original_dma_quads'] <
               projection['baseline_minimum_exact_quads']):
        raise ValueError('source-time projection or matched replay is unqualified')
    frame = projection['source_frame']
    source = source_tap_run/'run'
    ram = source/f'world-source-{frame}-ram.bin'
    fast = source/f'world-source-{frame}-fast.bin'
    texture = source/f'world-source-{frame}-textures.bin'
    palette = source/f'world-source-{frame}-palettes.bin'
    receipt = source/f'world-source-{frame}-receipt.csv'
    revision = projection['revision']
    if revision not in (24, 25):
        raise ValueError('unsupported World source revision')
    scene_address = '61ee' if revision == 24 else '658f'
    rom = 'crusnwld24' if revision == 24 else 'crusnwld'
    if ({'program_ram': sha(ram), 'c31_ram': sha(fast)} !=
            {key: projection['source_sha256'][key] for key in ('program_ram', 'c31_ram')}
            or texture.stat().st_size != 0x800000
            or palette.stat().st_size != 0x20000
            or receipt.read_text().splitlines() !=
               ['frame,pc,scene_address,rom', f'{frame},6a,{scene_address},{rom}']):
        raise ValueError('source-time operands or resources differ from projection receipt')
    snap = baseline_run/'run/capture'
    complete_resources_match = (sha(texture) == sha(snap/'textureram.bin') and
                                sha(palette) == sha(snap/'paletteram.bin'))
    visible = baseline_report['vunit_original_mirror']['result']['host_completion']['visible']
    complete = baseline_report['vunit_original_mirror']['result']
    if visible['frame'] != frame:
        raise ValueError('screen is not the qualified source/display/page pair')
    page = complete['visible_page']
    prefix = f'vunit-mirror-{complete["frame"]}-page{page}-plane'
    paths = [baseline_run/'run'/(prefix+str(i)+'.bin') for i in range(4)]
    planes = [np.fromfile(paths[i], dtype='<u2' if i % 2 == 0 else 'u1')
              .reshape(1600, 2736) for i in range(4)]
    quads = []
    candidate_records = []
    seen = set()
    for probe in projection['probes']:
        for hit in probe['projected_box_hits']:
            key = tuple(hit['quad_words'])
            if hit['exact_original_dma'] or hit['exact_host_packet']:
                continue
            if hit.get('stock_horizontal_rejected') is not True:
                raise ValueError('candidate lacks source-time stock horizontal-cull proof')
            if key not in seen:
                seen.add(key)
                quads.append(hit['quad_words'])
                candidate_records.append({key: hit[key] for key in
                                          ('object', 'model', 'depth', 'radius',
                                           'stock_horizontal_rejected', 'bounds')})
    if not quads:
        raise ValueError('no absent source-time quads overlap saved sample')
    added, tags = render_quads(quads, texture.read_bytes())
    if added.shape != planes[0].shape or tags.shape != planes[0].shape:
        raise ValueError('isolated GPU output has wrong dimensions')
    gaps = {}
    replacement = np.zeros_like(tags, dtype=bool)
    for name, geometry in geometries.items():
        if (geometry['source_frame'] != frame or
                geometry['completed_frame'] != complete['frame'] or
                geometry['page'] != page):
            raise ValueError('gap geometry is not the same source/display pair')
        mask = component(planes, geometry)
        covered = mask & (tags != 0)
        x, y = geometry['unowned_component']['seed']
        gaps[name] = {'gap_pixels': int(mask.sum()),
                      'isolated_covered_pixels': int(covered.sum()),
                      'isolated_coverage_fraction': float(covered.sum()/mask.sum()),
                      'seed_index': int(added[y,x]), 'seed_tag': int(tags[y,x]),
                      'seed_covered': bool(tags[y,x] != 0)}
        replacement |= covered
    out = {'passed': all(item['seed_covered'] for item in gaps.values()),
           'scope': 'Source-time resources and isolated GPU raster, masked to exact saved '
                    'unowned connected regions. No ordered native draw, texture-quality, '
                    'temporal, second-course or release acceptance.',
           'source_frame': frame, 'completed_frame': complete['frame'],
           'source_resources_equal_completed': complete_resources_match,
           'exact_original_dma_reconstruction': projection['counts']['exact_original_dma_quads'],
           'original_dma_quads': projection['original_dma_quads'],
           'candidate_quads': len(quads), 'candidates': candidate_records,
           'gap_screens': gaps,
           'all_sampled_gap_pixels_covered': all(item['isolated_covered_pixels'] ==
                                                 item['gap_pixels'] for item in gaps.values()),
           'outside_gap_isolated_pixels': int(((tags != 0) & ~replacement).sum()),
           'source_sha256': {'projection': sha(projection_path), 'tap_receipt': sha(receipt),
                            'texture': sha(texture), 'palette': sha(palette),
                            **{p.name: sha(p) for p in paths}},
           'geometry_sha256': {name: sha(path) for name, path in geometry_paths.items()},
           'preview': None}
    if preview_dir is not None:
        preview_dir.mkdir(parents=True, exist_ok=False)
        source_palette = palette.read_bytes()
        baseline = resolve(planes[0], planes[1], source_palette)
        proposed_indices, proposed_tags = planes[0].copy(), planes[1].copy()
        proposed_indices[replacement] = added[replacement]
        proposed_tags[replacement] = tags[replacement]
        trial = resolve(proposed_indices, proposed_tags, source_palette)
        reference = np.asarray(Image.open(baseline_run/'run/gl-snap/mvgl_000.bmp').convert('RGB'))
        diff = np.max(np.abs(baseline.astype('i2') - reference.astype('i2')), axis=2)
        Image.fromarray(reference).save(preview_dir/'saved-completed.png')
        Image.fromarray(trial).save(preview_dir/'isolated-gap-only.png')
        out['preview'] = {'directory': str(preview_dir),
                          'baseline_pixels_over_one_channel': int((diff > 1).sum()),
                          'baseline_max_channel_error': int(diff.max()),
                          'replacement_indexed_pixels': int(replacement.sum()),
                          'note': 'Hypothetical overwrite of unowned pixels only; not native ordering.'}
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-run', type=Path, required=True)
    parser.add_argument('--source-tap-run', type=Path, required=True)
    parser.add_argument('--projection', type=Path, required=True)
    parser.add_argument('--left-geometry', type=Path, required=True)
    parser.add_argument('--right-geometry', type=Path, required=True)
    parser.add_argument('--preview-dir', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite screen evidence')
    result = screen(args.baseline_run, args.source_tap_run, args.projection,
                    {'left': args.left_geometry, 'right': args.right_geometry},
                    args.preview_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2)+'\n')
    print('PASS' if result['passed'] else 'FAIL', result['gap_screens'])
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
