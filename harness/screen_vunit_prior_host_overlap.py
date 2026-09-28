"""Attribute changed prior-host pixels to a saved V-Unit host scene, if exact.

The completed auxiliary prefix selects the physical-page source scene because
completed frame/page clocks and host submission clocks differ. A matching
isolated raster is a source test, not visual acceptance.
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


def host_scene(run, frame, page):
    scenes = run / 'world-host-scenes.csv'
    with scenes.open(newline='', encoding='utf-8') as stream:
        matches = [row for row in csv.DictReader(stream)
                   if int(row['frame']) == frame and int(row['page']) == page]
    if len(matches) != 1 or matches[0]['quad_trace'] != '1':
        raise ValueError('no unique traced host scene at requested clock')
    quads = run / 'world-host-quads.csv'
    rows, digest = [], HASH_SEED
    with quads.open(newline='', encoding='utf-8') as stream:
        for row in csv.DictReader(stream):
            if int(row['frame']) == frame and int(row['page']) == page:
                words = tuple(int(row[key]) for key in QUAD_FIELDS)
                digest = hash_quad(digest, words)
                rows.append(dict(words=words, object=int(row['object']),
                                 model=int(row['model']), depth=int(row['depth'])))
    if len(rows) != int(matches[0]['quads']) or f'{digest:016x}' != matches[0]['quads_hash']:
        raise ValueError('host scene count/fingerprint differs from detailed trace')
    return rows, dict(frame=frame, page=page, quads=len(rows),
                      fingerprint=matches[0]['quads_hash'],
                      sha256={'scenes': sha(scenes), 'quads': sha(quads)})


def added_rows(control, trial):
    old = [(row['words'], row['object'], row['model'], row['depth']) for row in control]
    new = [(row['words'], row['object'], row['model'], row['depth']) for row in trial]
    cursor, added = 0, []
    for row, signature in zip(trial, new):
        if cursor < len(old) and signature == old[cursor]:
            cursor += 1
        else:
            added.append(row)
    if cursor != len(old):
        raise ValueError('control host packets are not an ordered trial subsequence')
    return added


def screen(report_path, control, trial, source):
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if not report['passed'] or not report['changed_prior_host_pixels']:
        raise ValueError('no qualified positive prior-host-overdraw sample')
    for key, root in [('control_report', control), ('trial_report', trial),
                      ('original_source_report', source)]:
        if sha(root / 'report.json') != report['sha256'][key]:
            raise ValueError(f'{key} differs from source qualification')
    completed, visible = report['frame'], report['visible_page']
    _, aa = planes(control, completed, visible)
    _, bb = planes(trial, completed, visible)
    if not all(np.array_equal(x, y) for x, y in zip(aa[2:], bb[2:])):
        raise ValueError('original-only planes differ')
    changed = (aa[0] != bb[0]) | (aa[1] != bb[1])
    prior = changed & ((aa[1] & 4) != 0)
    if int(prior.sum()) != report['changed_prior_host_pixels']:
        raise ValueError('prior-host pixel count differs from source qualification')
    mirror_receipt = json.loads((control / 'run/vunit-mirror.json').read_text(encoding='utf-8'))
    selected = completion_scene(control / 'run', 'world', mirror_receipt)['visible']
    if selected is None or not selected['complete']:
        raise ValueError('no completed visible-page host source scene')
    rows, receipt = host_scene(control / 'run', selected['frame'], selected['page_control'])
    if receipt['fingerprint'] != selected['prepared_quads_hash'] or len(rows) != selected['consumed_quads']:
        raise ValueError('traced host scene differs from completed submission prefix')
    trial_mirror = json.loads((trial / 'run/vunit-mirror.json').read_text(encoding='utf-8'))
    trial_selected = completion_scene(trial / 'run', 'world', trial_mirror)['visible']
    if (trial_selected is None or not trial_selected['complete'] or
            (trial_selected['frame'], trial_selected['page_control']) !=
            (selected['frame'], selected['page_control'])):
        raise ValueError('trial completed host source differs from control clock/page')
    trial_rows, trial_receipt = host_scene(trial / 'run', selected['frame'], selected['page_control'])
    if (trial_receipt['fingerprint'] != trial_selected['prepared_quads_hash'] or
            len(trial_rows) != trial_selected['consumed_quads']):
        raise ValueError('trial trace differs from completed submission prefix')
    new_rows = added_rows(rows, trial_rows)
    texture = source / 'run/capture/textureram.bin'
    index, tags = render_quads([r['words'] for r in rows], texture.read_bytes())
    ids, idtags = render_quads([r['words'] for r in rows], texture.read_bytes(),
                               debug_quad_id=True)
    covered = prior & (tags != 0) & (idtags != 0)
    exact = covered & (index == aa[0])
    ordinals, counts = np.unique(ids[exact], return_counts=True)
    attribution = [dict(host_ordinal=int(i), pixels=int(n), object=hex(rows[int(i)]['object']),
                        model=hex(rows[int(i)]['model']), depth=rows[int(i)]['depth'])
                   for i, n in zip(ordinals, counts)]
    attribution.sort(key=lambda r: r['pixels'], reverse=True)
    new_index, new_tags = render_quads([r['words'] for r in new_rows], texture.read_bytes())
    new_ids, new_idtags = render_quads([r['words'] for r in new_rows], texture.read_bytes(),
                                       debug_quad_id=True)
    new_covered = prior & (new_tags != 0) & (new_idtags != 0)
    new_exact = new_covered & (new_index == bb[0])
    new_ordinals, new_counts = np.unique(new_ids[new_exact], return_counts=True)
    new_attribution = [dict(added_ordinal=int(i), pixels=int(n),
                            object=hex(new_rows[int(i)]['object']),
                            model=hex(new_rows[int(i)]['model']),
                            depth=new_rows[int(i)]['depth'])
                       for i, n in zip(new_ordinals, new_counts)]
    new_attribution.sort(key=lambda r: r['pixels'], reverse=True)
    old_depth = np.asarray([r['depth'] for r in rows], dtype=np.int64)[ids[prior]]
    new_depth = np.asarray([r['depth'] for r in new_rows], dtype=np.int64)[new_ids[prior]]
    return dict(schema=2, passed=int(exact.sum()) == int(prior.sum()) and
                int(new_exact.sum()) == int(prior.sum()),
                scope='One completed indexed page and prefix-selected traced host '
                      'scene. No full ordered compositing, temporal or visual acceptance.',
                completed_frame=completed, visible_page=visible,
                selected_host_completion=selected, host_scene=receipt,
                prior_host_pixels=int(prior.sum()), isolated_covered=int(covered.sum()),
                isolated_index_exact=int(exact.sum()), attribution=attribution,
                selected_trial_completion=trial_selected, trial_host_scene=trial_receipt,
                added_host_packets=len(new_rows), added_isolated_covered=int(new_covered.sum()),
                added_isolated_index_exact=int(new_exact.sum()),
                added_attribution=new_attribution,
                source_depth_order=dict(new_nearer=int(np.count_nonzero(new_depth < old_depth)),
                                        same=int(np.count_nonzero(new_depth == old_depth)),
                                        new_farther=int(np.count_nonzero(new_depth > old_depth)),
                                        old_range=[int(old_depth.min()), int(old_depth.max())],
                                        new_range=[int(new_depth.min()), int(new_depth.max())]),
                sha256={'overdraw_report': sha(report_path),
                        'control_report': sha(control / 'report.json'),
                        'trial_report': sha(trial / 'report.json'),
                        'source_report': sha(source / 'report.json'),
                        'texture': sha(texture)})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('overdraw', 'control', 'trial', 'source', 'report'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite host-overlap screen')
    result = screen(args.overdraw, args.control, args.trial, args.source)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS' if result['passed'] else 'FAIL', result['isolated_index_exact'],
          '/', result['prior_host_pixels'], 'new', result['added_isolated_index_exact'])
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
