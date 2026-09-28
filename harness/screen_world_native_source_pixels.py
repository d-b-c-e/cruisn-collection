"""Join saved World source-time native scenes to a completed margin change.

The source-time standalone helper output must match both live completed-scene
fingerprints before any changed pixel is attributed. This avoids broad quad
journals; isolated added-packet raster is not full ordered/depth compositing.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

import numpy as np

from analyze_world_host import HASH_SEED, hash_quad
from offroad_gap_loaded_screen import render_quads
from screen_vunit_prior_host_overlap import added_rows
from screen_world_active_overlap import planes
from screen_vunit_panorama_strips import sha
from screen_world_added_packet_coverage import read_run
from vunit_host_completion import load as completion_scene


def native_scene(path):
    lines = path.read_text(encoding='utf-8').splitlines()
    if not lines or len(lines[0].split()) != 7:
        raise ValueError(f'invalid native scene header: {path}')
    header = tuple(int(v) for v in lines[0].split())
    rows, digest = [], HASH_SEED
    for line in lines[1:]:
        values = tuple(int(v) for v in line.split())
        if len(values) not in (20, 24):
            raise ValueError(f'invalid native scene packet: {path}')
        words = values[4:20]
        digest = hash_quad(digest, words)
        rows.append(dict(words=words, object=values[0], model=values[1],
                         depth=values[2], section=values[3]))
    return rows, dict(header=header, quads=len(rows),
                      fingerprint=f'{digest:016x}', sha256=sha(path))


def check(control, trial, source, resource, native_control, native_trial):
    a, b, s, r = (read_run(path) for path in (control, trial, source, resource))
    if (len({x['case'] for x in (a, b, s, r)}) != 1 or
            len({x['emulator_source']['executable_sha256'] for x in (a, b, s, r)}) != 1 or
            len({json.dumps(x['display_target'], sort_keys=True) for x in (a, b, s, r)}) != 1):
        raise ValueError('case, binary or physical display differs')
    mode_a, mode_b = dict(a['world_host_scenery']), dict(b['world_host_scenery'])
    mode_a.pop('active_nonroads', None)
    mode_b.pop('active_nonroads', None)
    if (mode_a != mode_b or a['world_host_scenery'].get('active_nonroads', 'off') != 'off' or
            b['world_host_scenery'].get('active_nonroads') != 'margins' or
            s['world_host_scenery'] != a['world_host_scenery']):
        raise ValueError('source/control/trial modes differ beyond non-road toggle')
    ma, mb, ms = (x['vunit_original_mirror']['result'] for x in (a, b, s))
    frame, page = ma['frame'], ma['visible_page']
    if ((frame, page) != (mb['frame'], mb['visible_page']) or
            (frame, page) != (ms['frame'], ms['visible_page']) or
            ma['sha256'] != ms['sha256'] or
            a['evidence']['gl_captures']['files'] != s['evidence']['gl_captures']['files']):
        raise ValueError('source replay does not reproduce original completed control')
    ca = completion_scene(control / 'run', 'world',
                          json.loads((control / 'run/vunit-mirror.json').read_text()))['visible']
    cb = completion_scene(trial / 'run', 'world',
                          json.loads((trial / 'run/vunit-mirror.json').read_text()))['visible']
    if (ca is None or cb is None or not ca['complete'] or not cb['complete'] or
            (ca['frame'], ca['page_control']) != (cb['frame'], cb['page_control'])):
        raise ValueError('completed source clocks/pages differ or are incomplete')
    source_frame = ca['frame']
    stem = f'world-source-{source_frame}'
    receipt = source / 'run' / f'{stem}-receipt.csv'
    with receipt.open(newline='', encoding='utf-8') as stream:
        tap = list(csv.DictReader(stream))
    rom = a['vunit_runtime']['rom']
    if rom not in ('crusnwld24', 'crusnwld'):
        raise ValueError('unsupported World revision')
    if tap != [dict(frame=str(source_frame), pc='6a',
                    scene_address='61ee' if rom == 'crusnwld24' else '658f',
                    rom=rom)]:
        raise ValueError('source-time read tap did not select completed scene')
    old, old_receipt = native_scene(native_control)
    new, new_receipt = native_scene(native_trial)
    if (old_receipt['fingerprint'] != ca['prepared_quads_hash'] or
            new_receipt['fingerprint'] != cb['prepared_quads_hash'] or
            len(old) != ca['consumed_quads'] or len(new) != cb['consumed_quads']):
        raise ValueError('offline native scene differs from completed live source')
    added = added_rows(old, new)
    paths_a, aa = planes(control, frame, page)
    paths_b, bb = planes(trial, frame, page)
    paths_s, ss = planes(source, frame, page)
    if (not all(np.array_equal(x, y) for x, y in zip(aa, ss)) or
            not all(np.array_equal(x, y) for x, y in zip(aa[2:], bb[2:])) or
            not all(np.array_equal(x[:, 344:2392], y[:, 344:2392])
                    for x, y in zip(aa[:2], bb[:2]))):
        raise ValueError('original control or original-only/4:3 candidate planes differ')
    texture = source / 'run' / f'{stem}-textures.bin'
    completed_texture = resource / 'run/capture/textureram.bin'
    if sha(texture) != sha(completed_texture):
        raise ValueError('source and completed texture resources differ')
    changed = (aa[0] != bb[0]) | (aa[1] != bb[1])
    if not changed.any() or np.any(changed & ((bb[1] & 4) == 0)):
        raise ValueError('no host-owned candidate pixel change')
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
                scope='One completed World indexed page, source-time standalone native '
                      'scenes matched to exact live source fingerprints, and isolated '
                      'added-packet raster. Not full compositor/depth, temporal or 4K proof.',
                source_frame=source_frame, source_page_control=ca['page_control'],
                completed_frame=frame, visible_page=page,
                control_completed_source=ca, candidate_completed_source=cb,
                native_control=old_receipt, native_trial=new_receipt,
                old_packets=len(old), trial_packets=len(new), added_packets=len(added),
                added_objects=len({row['object'] for row in added}),
                changed_indexed_pixels=int(changed.sum()),
                changed_bounds_xyxy_inclusive=[int(xs.min()), int(ys.min()),
                                               int(xs.max()), int(ys.max())],
                added_raster_covered_pixels=int(covered.sum()),
                added_raster_index_exact_pixels=int(exact.sum()),
                attributed_objects=dict(objects.most_common()),
                attributed_models=dict(models.most_common()),
                sha256={**{name: sha(root / 'report.json') for name, root in
                          (('control_report', control), ('trial_report', trial),
                           ('source_report', source), ('resource_report', resource))},
                        'source_receipt': sha(receipt), 'source_texture': sha(texture),
                        'completed_texture': sha(completed_texture),
                        **{f'control_plane{i}': sha(path) for i, path in enumerate(paths_a)},
                        **{f'trial_plane{i}': sha(path) for i, path in enumerate(paths_b)},
                        **{f'source_plane{i}': sha(path) for i, path in enumerate(paths_s)}})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('control', 'trial', 'source', 'resource', 'native-control',
                 'native-trial', 'report'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite source pixel report')
    result = check(args.control, args.trial, args.source, args.resource,
                   args.native_control, args.native_trial)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS' if result['passed'] else 'FAIL', result['changed_indexed_pixels'],
          result['added_raster_index_exact_pixels'])
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
