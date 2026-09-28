"""Join a completed World margin change to exact added packets in saved traces.

Detailed traces may come from longer matched replays, provided their selected
source scene fingerprints equal the completed mirror's submission prefixes.
The isolated raster tests changed indexed pixels, not full draw order or depth.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np

from offroad_gap_loaded_screen import render_quads
from screen_vunit_panorama_strips import sha
from screen_vunit_prior_host_overlap import added_rows, host_scene
from screen_world_active_overlap import planes
from vunit_host_completion import load as completion_scene


def read_run(root):
    report = json.loads((root / 'report.json').read_text(encoding='utf-8'))
    invocation = json.loads((root / 'run/invocation.json').read_text(encoding='utf-8'))
    if (not report['passed'] or not report['comparison']['passed'] or
            not report['display_watch']['passed'] or
            report['vunit_runtime']['result']['completion'] != 'owned-worker-stop' or
            invocation['environment'].get('MIDV_FFB') != '0' or
            invocation['returncode'] != 0):
        raise ValueError(f'unqualified input/native/display/FFB/shutdown: {root}')
    return report


def options(report):
    result = dict(report['world_host_scenery'])
    result.pop('last', None)
    result.pop('log', None)
    return result


def screen(control, trial, control_trace, trial_trace, resource):
    roots = (control, trial, control_trace, trial_trace, resource)
    reports = [read_run(root) for root in roots]
    a, b, at, bt, source = reports
    if (len({r['case'] for r in reports}) != 1 or
            len({r['emulator_source']['executable_sha256'] for r in reports}) != 1 or
            len({json.dumps(r['display_target'], sort_keys=True) for r in reports}) != 1):
        raise ValueError('case, binary or physical display differs')
    if (a['comparison_scope'] != b['comparison_scope'] or
            a['presentation_overrides'] != b['presentation_overrides']):
        raise ValueError('completed replay prefix or presentation differs')
    settings = [options(r) for r in reports[:4]]
    for pair in ((0, 1), (2, 3), (0, 2), (1, 3)):
        left, right = dict(settings[pair[0]]), dict(settings[pair[1]])
        left.pop('active_nonroads', None)
        right.pop('active_nonroads', None)
        if left != right:
            raise ValueError('renderer modes differ beyond capture and non-road toggle')
    if (a['world_host_scenery'].get('active_nonroads', 'off') != 'off' or
            at['world_host_scenery'].get('active_nonroads', 'off') != 'off' or
            b['world_host_scenery'].get('active_nonroads') != 'margins' or
            bt['world_host_scenery'].get('active_nonroads') != 'margins' or
            any(r['world_host_scenery']['log'] != 'quads' for r in (at, bt))):
        raise ValueError('expected off/on mirrors and detailed off/on traces')
    ma = a['vunit_original_mirror']['result']
    mb = b['vunit_original_mirror']['result']
    ms = source['vunit_original_mirror']['result']
    frame, page = ma['frame'], ma['visible_page']
    if (frame != mb['frame'] or page != mb['visible_page'] or
            frame != ms['frame'] or page != ms['visible_page'] or
            ma['sha256'] != ms['sha256'] or
            a['evidence']['gl_captures']['files'] != source['evidence']['gl_captures']['files']):
        raise ValueError('original source does not reproduce completed control')
    ca = completion_scene(control / 'run', 'world',
                          json.loads((control / 'run/vunit-mirror.json').read_text()))['visible']
    cb = completion_scene(trial / 'run', 'world',
                          json.loads((trial / 'run/vunit-mirror.json').read_text()))['visible']
    if (ca is None or cb is None or not ca['complete'] or not cb['complete'] or
            (ca['frame'], ca['page_control']) != (cb['frame'], cb['page_control'])):
        raise ValueError('completed source scenes differ or are incomplete')
    old, old_receipt = host_scene(control_trace / 'run', ca['frame'], ca['page_control'])
    new, new_receipt = host_scene(trial_trace / 'run', cb['frame'], cb['page_control'])
    if (old_receipt['fingerprint'] != ca['prepared_quads_hash'] or
            new_receipt['fingerprint'] != cb['prepared_quads_hash'] or
            len(old) != ca['consumed_quads'] or len(new) != cb['consumed_quads']):
        raise ValueError('detailed scene differs from completed auxiliary prefix')
    added = added_rows(old, new)
    paths_a, aa = planes(control, frame, page)
    paths_b, bb = planes(trial, frame, page)
    if (not all(np.array_equal(x, y) for x, y in zip(aa[2:], bb[2:])) or
            not all(np.array_equal(x[:, 344:2392], y[:, 344:2392])
                    for x, y in zip(aa[:2], bb[:2]))):
        raise ValueError('original-only or 4:3 indexed pixels changed')
    changed = (aa[0] != bb[0]) | (aa[1] != bb[1])
    if not changed.any() or np.any(changed & ((bb[1] & 4) == 0)):
        raise ValueError('no host-owned candidate pixel change')
    texture = resource / 'run/capture/textureram.bin'
    words = [row['words'] for row in added]
    index, tags = render_quads(words, texture.read_bytes())
    ids, idtags = render_quads(words, texture.read_bytes(), debug_quad_id=True)
    covered = changed & (tags != 0) & (idtags != 0)
    exact = covered & (index == bb[0])
    ordinals, counts = np.unique(ids[exact], return_counts=True)
    objects, models = Counter(), Counter()
    for ordinal, count in zip(ordinals, counts):
        row = added[int(ordinal)]
        objects[hex(row['object'])] += int(count)
        models[hex(row['model'])] += int(count)
    ys, xs = np.where(changed)
    return dict(schema=1, passed=int(exact.sum()) == int(changed.sum()),
                scope='One completed World indexed page, exact cross-replay source scene '
                      'fingerprints and isolated added-packet raster with completed-frame '
                      'texture. Not full ordered compositing, depth proof, temporal or 4K acceptance.',
                source_frame=ca['frame'], source_page_control=ca['page_control'],
                completed_frame=frame, visible_page=page,
                control_scene=old_receipt, candidate_scene=new_receipt,
                control_completed_source=ca, candidate_completed_source=cb,
                old_packets=len(old), trial_packets=len(new), added_packets=len(added),
                added_objects=len({row['object'] for row in added}),
                changed_indexed_pixels=int(changed.sum()),
                changed_bounds_xyxy_inclusive=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                added_raster_covered_pixels=int(covered.sum()),
                added_raster_index_exact_pixels=int(exact.sum()),
                attributed_objects=dict(objects.most_common()),
                attributed_models=dict(models.most_common()),
                sha256={**{name: sha(root / 'report.json') for name, root in zip(
                    ('control_report', 'trial_report', 'control_trace_report',
                     'trial_trace_report', 'resource_report'), roots)},
                        'texture': sha(texture),
                        **{f'control_plane{i}': sha(path) for i, path in enumerate(paths_a)},
                        **{f'trial_plane{i}': sha(path) for i, path in enumerate(paths_b)}})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('control', 'trial', 'control-trace', 'trial-trace', 'resource', 'report'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite packet coverage evidence')
    result = screen(args.control, args.trial, args.control_trace, args.trial_trace, args.resource)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS' if result['passed'] else 'FAIL', result['added_raster_index_exact_pixels'],
          '/', result['changed_indexed_pixels'], 'pixels from', result['added_packets'], 'added packets')
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
