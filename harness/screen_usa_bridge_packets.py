"""Join a saved USA completed mirror to a later detailed host trace.

The detailed replay must reproduce the saved completed image and selected host
scene exactly. Selected indexed pixels are then attributed by an independent
isolated raster. This is a point source test, not object-completeness proof.
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

from analyze_world_host import HASH_SEED, QUAD_FIELDS, hash_quad
from offroad_gap_loaded_screen import render_quads
from screen_world_active_overlap import planes
from screen_vunit_panorama_strips import sha
from vunit_host_completion import load as completion_scene


def traced_scene(run, selected):
    scene_path = run / 'usa-host-scenes.csv'
    with scene_path.open(newline='', encoding='utf-8') as stream:
        scenes = list(csv.DictReader(stream))
    row = scenes[selected['ordinal']]
    clock = (row['frame'], row['time'], row['page'])
    if ((int(row['frame']), int(row['page'])) !=
            (selected['frame'], selected['page_control']) or
            row['quads_hash'] != selected['prepared_quads_hash']):
        raise ValueError('completed USA host scene differs from detailed trace')
    quad_path = run / 'usa-host-quads.csv'
    rows, fingerprint = [], HASH_SEED
    with quad_path.open(newline='', encoding='utf-8') as stream:
        for item in csv.DictReader(stream):
            if (item['frame'], item['time'], item['page']) == clock:
                words = tuple(int(item[key]) for key in QUAD_FIELDS)
                fingerprint = hash_quad(fingerprint, words)
                rows.append(dict(words=words, object=int(item['object']),
                                 model=int(item['model']), depth=int(item['depth'])))
    if (len(rows) != selected['consumed_quads'] or len(rows) != int(row['quads']) or
            f'{fingerprint:016x}' != row['quads_hash']):
        raise ValueError('detailed USA scene count/fingerprint differs')
    return rows, dict(clock=list(clock), quads=len(rows),
                      fingerprint=row['quads_hash'],
                      sha256={'scenes': sha(scene_path), 'quads': sha(quad_path)})


def screen(source, traced, points):
    source_report = json.loads((source / 'report.json').read_text(encoding='utf-8'))
    posthoc = source / 'posthoc-qualification-v1.json'
    qualified = json.loads(posthoc.read_text(encoding='utf-8'))
    traced_report = json.loads((traced / 'report.json').read_text(encoding='utf-8'))
    if (source_report.get('passed') is not False or qualified.get('passed') is not True or
            qualified.get('raw_report_passed') is not False or
            traced_report.get('passed') is not True or
            traced_report['comparison']['passed'] is not True or
            traced_report['display_watch']['passed'] is not True or
            traced_report['vunit_runtime']['result']['completion'] != 'owned-worker-stop'):
        raise ValueError('saved or detailed replay qualification differs')
    if (qualified['sha256']['raw_report'] != sha(source / 'report.json') or
            source_report['case'] != traced_report['case'] or
            source_report['emulator_source']['executable_sha256'] !=
            traced_report['emulator_source']['executable_sha256']):
        raise ValueError('source posthoc/case/binary identity differs')
    for root in (source, traced):
        invocation = json.loads((root / 'run/invocation.json').read_text(encoding='utf-8'))
        if invocation['environment'].get('MIDV_FFB') != '0':
            raise ValueError('physical force was not explicitly disabled')
    old_image = source / 'run/gl-snap/mvgl_000.bmp'
    new_image = traced / 'run/gl-snap/mvgl_000.bmp'
    if sha(old_image) != sha(new_image):
        raise ValueError('completed USA image differs from saved source')
    if sha(old_image) != qualified['sha256']['completed_bmp']:
        raise ValueError('completed source image differs from posthoc qualification')
    receipt = json.loads((source / 'run/vunit-mirror.json').read_text(encoding='utf-8'))
    selected_old = completion_scene(source / 'run', 'usa', receipt)['visible']
    selected_new = completion_scene(traced / 'run', 'usa', receipt)['visible']
    if selected_old is None or selected_new is None or selected_old != selected_new or not selected_new['complete']:
        raise ValueError('detailed host source differs from completed source')
    rows, host = traced_scene(traced / 'run', selected_new)
    frame, page = receipt['frame'], receipt['visible_page']
    _, mirror = planes(source, frame, page)
    texture = source / 'run/capture/textureram.bin'
    index, tags = render_quads([row['words'] for row in rows], texture.read_bytes())
    ids, idtags = render_quads([row['words'] for row in rows], texture.read_bytes(),
                               debug_quad_id=True)
    found = []
    for x, y in points:
        if not (0 <= x < 2736 and 0 <= y < 1600):
            raise ValueError('point outside indexed mirror')
        combined = [int(mirror[0][y, x]), int(mirror[1][y, x])]
        original = [int(mirror[2][y, x]), int(mirror[3][y, x])]
        exact = bool((combined[1] & 4) and tags[y, x] and idtags[y, x] and
                     int(index[y, x]) == combined[0])
        source_row = rows[int(ids[y, x])] if exact else None
        found.append(dict(indexed=[x, y], combined=combined, original_only=original,
                          isolated_index=int(index[y, x]), isolated_tag=int(tags[y, x]),
                          exact_host_source=exact,
                          source=dict(ordinal=int(ids[y, x]),
                                      object=hex(source_row['object']),
                                      model=hex(source_row['model']),
                                      depth=source_row['depth'],
                                      quad_words=list(source_row['words'])) if exact else None))
    sampled_objects = sorted({int(row['source']['object'], 16) for row in found
                              if row['source'] is not None})
    valid = ((mirror[1][:, :344] & 4) != 0) & (tags[:, :344] != 0) & \
        (idtags[:, :344] != 0) & (index[:, :344] == mirror[0][:, :344])
    seen, counts = np.unique(ids[:, :344][valid], return_counts=True)
    visible_by_ordinal = {int(ordinal): int(count) for ordinal, count in zip(seen, counts)}
    object_summaries = []
    for object_id in sampled_objects:
        ordinals = [i for i, row in enumerate(rows) if row['object'] == object_id]
        object_summaries.append(dict(object=hex(object_id), packets=len(ordinals),
                                     exact_visible_margin_pixels=sum(visible_by_ordinal.get(i, 0)
                                                                     for i in ordinals),
                                     palettes=sorted({rows[i]['words'][1] for i in ordinals}),
                                     texture_bases=sorted({rows[i]['words'][14] for i in ordinals})))
    return dict(schema=1, passed=all(row['exact_host_source'] for row in found),
                scope='Three selected USA bridge indexed pixels at one completed frame. '
                      'No full object, missing-member, 4K or temporal qualification.',
                completed_frame=frame, visible_page=page, selected_host=selected_new,
                traced_host=host, source_raw_report_passed=False,
                source_posthoc_passed=True, detailed_replay_passed=True,
                completed_image_exact=True, points=found,
                sampled_object_summaries=object_summaries,
                sha256={'source_report': sha(source / 'report.json'),
                        'posthoc': sha(posthoc), 'detailed_report': sha(traced / 'report.json'),
                        'completed_image': sha(old_image), 'mirror': sha(source / 'run/vunit-mirror.json'),
                        'texture': sha(texture)})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--traced', type=Path, required=True)
    ap.add_argument('--point', action='append', required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite USA source screen')
    points = [tuple(int(x) for x in value.split(',')) for value in args.point]
    if any(len(point) != 2 for point in points):
        raise ValueError('points must be X,Y')
    result = screen(args.source, args.traced, points)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS' if result['passed'] else 'FAIL',
          sum(row['exact_host_source'] for row in result['points']), '/', len(points))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
