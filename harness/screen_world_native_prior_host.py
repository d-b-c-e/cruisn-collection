"""Attribute a World margin candidate's prior-host overlap to exact native scenes.

Requires the independent completed-pixel/source check. Object-center depth is
only a diagnostic ordering hint, not a per-fragment depth or safety proof.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np

from offroad_gap_loaded_screen import render_quads
from screen_vunit_prior_host_overlap import added_rows
from screen_world_active_overlap import planes
from screen_world_native_source_pixels import native_scene
from screen_vunit_panorama_strips import sha


def check(overdraw_path, pixels_path, control, trial, source, tap, native_control,
          native_trial):
    overdraw = json.loads(overdraw_path.read_text(encoding='utf-8'))
    pixels = json.loads(pixels_path.read_text(encoding='utf-8'))
    if not overdraw.get('passed') or not pixels.get('passed'):
        raise ValueError('source or ownership qualification failed')
    for key, root in [('control_report', control), ('trial_report', trial),
                      ('original_source_report', source)]:
        if sha(root / 'report.json') != overdraw['sha256'][key]:
            raise ValueError(f'overdraw {key} differs')
    for key, root in [('control_report', control), ('trial_report', trial),
                      ('resource_report', source), ('source_report', tap)]:
        if sha(root / 'report.json') != pixels['sha256'][key]:
            raise ValueError(f'pixel source {key} differs')
    if (overdraw['frame'] != pixels['completed_frame'] or
            overdraw['visible_page'] != pixels['visible_page']):
        raise ValueError('completed frame/page differs')
    old, old_receipt = native_scene(native_control)
    new, new_receipt = native_scene(native_trial)
    if (json.dumps(old_receipt) != json.dumps(pixels['native_control']) or
            json.dumps(new_receipt) != json.dumps(pixels['native_trial'])):
        raise ValueError('native packet sources differ')
    added = added_rows(old, new)
    if len(added) != pixels['added_packets']:
        raise ValueError('added packet count differs')
    frame, page = overdraw['frame'], overdraw['visible_page']
    paths_a, aa = planes(control, frame, page)
    paths_b, bb = planes(trial, frame, page)
    for root, prefix, paths in [(control, 'control', paths_a),
                                (trial, 'trial', paths_b)]:
        if sha(root / 'report.json') != pixels['sha256'][f'{prefix}_report']:
            raise ValueError('mirror source report differs')
        for i, path in enumerate(paths):
            if sha(path) != pixels['sha256'][f'{prefix}_plane{i}']:
                raise ValueError(f'{prefix} indexed plane differs')
    changed = (aa[0] != bb[0]) | (aa[1] != bb[1])
    prior = changed & ((aa[1] & 4) != 0)
    count = int(prior.sum())
    if count == 0 or count != overdraw['changed_prior_host_pixels']:
        raise ValueError('prior-host overlap differs')
    texture = source / 'run/capture/textureram.bin'
    if sha(texture) != pixels['sha256']['source_texture']:
        raise ValueError('source texture differs')
    data = texture.read_bytes()
    old_index, old_tag = render_quads([r['words'] for r in old], data)
    old_id, old_idtag = render_quads([r['words'] for r in old], data,
                                     debug_quad_id=True)
    new_index, new_tag = render_quads([r['words'] for r in added], data)
    new_id, new_idtag = render_quads([r['words'] for r in added], data,
                                     debug_quad_id=True)
    old_exact = prior & (old_tag != 0) & (old_idtag != 0) & (old_index == aa[0])
    new_exact = prior & (new_tag != 0) & (new_idtag != 0) & (new_index == bb[0])
    if int(old_exact.sum()) != count or int(new_exact.sum()) != count:
        raise ValueError(f'old/new isolated raster misses prior host: '
                         f'{int(old_exact.sum())}/{int(new_exact.sum())}/{count}')
    old_depth = np.asarray([r['depth'] for r in old], dtype=np.int64)[old_id[prior]]
    new_depth = np.asarray([r['depth'] for r in added], dtype=np.int64)[new_id[prior]]
    old_objects = Counter(hex(old[int(i)]['object']) for i in old_id[prior])
    new_objects = Counter(hex(added[int(i)]['object']) for i in new_id[prior])
    ys, xs = np.where(prior)
    return dict(schema=1, passed=True, completed_frame=frame, visible_page=page,
                scope='One source-qualified completed indexed page. Exact isolated '
                      'old/new packet indices; object-center depth only. No full '
                      'compositor, fragment-depth, temporal or 4K acceptance.',
                prior_host_pixels=count, old_raster_exact=count,
                added_raster_exact=count, added_packets=len(added),
                old_objects=dict(old_objects.most_common()),
                added_objects=dict(new_objects.most_common()),
                source_depth_order=dict(new_nearer=int(np.count_nonzero(new_depth < old_depth)),
                                        same=int(np.count_nonzero(new_depth == old_depth)),
                                        new_farther=int(np.count_nonzero(new_depth > old_depth)),
                                        old_range=[int(old_depth.min()), int(old_depth.max())],
                                        new_range=[int(new_depth.min()), int(new_depth.max())]),
                changed_bounds_xyxy_inclusive=[int(xs.min()), int(ys.min()),
                                               int(xs.max()), int(ys.max())],
                sha256={'overdraw_report': sha(overdraw_path),
                        'pixel_source_report': sha(pixels_path),
                        'native_control': sha(native_control),
                        'native_trial': sha(native_trial),
                        'texture': sha(texture)})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('overdraw', 'pixels', 'control', 'trial', 'source', 'tap',
                 'native-control', 'native-trial', 'report'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite prior-host source evidence')
    result = check(args.overdraw, args.pixels, args.control, args.trial,
                   args.source, args.tap, args.native_control, args.native_trial)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', result['prior_host_pixels'], result['source_depth_order'])


if __name__ == '__main__':
    main()
