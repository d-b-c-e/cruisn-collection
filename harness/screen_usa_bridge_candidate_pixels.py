"""Attribute sampled earlier red USA bridge pixels to new source packets.

Requires the detailed replay's completed image to equal the earlier continuous
candidate. Indexed center samples and isolated host raster are checked against
the completed auxiliary mirror; CRT blur can also use neighboring samples.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np
from PIL import Image

from offroad_gap_loaded_screen import render_quads, resolve
from probe_vunit_pixel import screen_to_indexed
from screen_usa_bridge_packets import traced_scene
from screen_usa_bridge_red_transition import ROI, red
from screen_vunit_panorama_strips import sha
from usa_future_scene import collect
from verify_usa_future import Memory
from verify_usa_host import reference
from vunit_host_completion import load as completion_scene

FRAME, SOURCE_FRAME = 10476, 10473
TARGET = 0x800a0040


def mirror_planes(run, receipt):
    frame, page = receipt['frame'], receipt['visible_page']
    prefix = run / f'vunit-mirror-{frame}-page{page}-plane'
    result = []
    for i in range(4):
        dtype = '<u2' if i % 2 == 0 else 'u1'
        path = Path(str(prefix) + f'{i}.bin')
        words = np.fromfile(path, dtype=dtype)
        if words.size != 2736 * 1600:
            raise ValueError('incomplete indexed mirror plane')
        result.append(words.reshape(1600, 2736))
    return result


def screen(detailed, prior_on, prior_off, source, rom_path, source_screen, candidate_screen):
    reports = [json.loads((root / 'report.json').read_text(encoding='utf-8'))
               for root in (detailed, prior_on, prior_off, source)]
    run_report, on_report, off_report, source_report = reports
    if (not all(r['passed'] and r['comparison']['passed'] for r in reports) or
            not run_report['display_watch']['passed'] or
            run_report['vunit_runtime']['result']['completion'] != 'owned-worker-stop' or
            len({r['case'] for r in reports}) != 1 or
            len({r['emulator_source']['executable_sha256'] for r in reports}) != 1 or
            run_report['usa_host_scenery']['far_coverage'] != 'on' or
            run_report['usa_host_scenery']['log'] != 'quads'):
        raise ValueError('detailed/prior/source replay identity differs')
    invocation = json.loads((detailed / 'run/invocation.json').read_text(encoding='utf-8'))
    if invocation['environment'].get('MIDV_FFB') != '0':
        raise ValueError('physical force was not explicitly disabled')
    qualified_source = json.loads(source_screen.read_text(encoding='utf-8'))
    qualified_candidate = json.loads(candidate_screen.read_text(encoding='utf-8'))
    if (not qualified_source['passed'] or not qualified_candidate['passed'] or
            qualified_source['sha256']['source_report'] != sha(source / 'report.json') or
            qualified_candidate['sha256']['source_screen'] != sha(source_screen) or
            qualified_source['sha256']['rom'] != sha(rom_path)):
        raise ValueError('exact source qualification differs')
    run = detailed / 'run'
    source_run = source / 'run'
    for kind in ('ram', 'fast', 'textures', 'palettes'):
        name = f'usa-source-{SOURCE_FRAME}-{kind}.bin'
        if sha(run / name) != sha(source_run / name):
            raise ValueError(f'detailed source-time {kind} differs')
    captured = run / 'gl-snap/mvgl_000.bmp'
    prior = prior_on / 'run/gl-snap/mvgl_004.bmp'
    if sha(captured) != sha(prior):
        raise ValueError('short-window candidate image differs from continuous candidate')
    receipt_path = run / 'vunit-mirror.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    if (receipt['frame'], receipt['visible_page'], receipt['width'], receipt['height']) != \
            (FRAME, 0, 2736, 1600):
        raise ValueError('indexed mirror is not the completed candidate frame')
    selected = completion_scene(run, 'usa', receipt)['visible']
    if (selected is None or not selected['complete'] or selected['frame'] != SOURCE_FRAME or
            selected['page_control'] != 513 or selected['consumed_quads'] != 3782):
        raise ValueError('candidate source did not reach the completed page')
    traced, trace = traced_scene(run, selected)
    memory = Memory(rom_path.read_bytes(),
                    (run / f'usa-source-{SOURCE_FRAME}-ram.bin').read_bytes(),
                    (run / f'usa-source-{SOURCE_FRAME}-fast.bin').read_bytes())
    _, _, future = collect(memory)
    _, old = reference(memory, 240000, future=future)
    _, predicted = reference(memory, 240000, future=future, far_coverage=True)
    if (len(predicted) != len(traced) or any(
            tuple(row[:19]) != (actual['object'], actual['model'], actual['depth'],
                                *actual['words'])
            for row, actual in zip(predicted, traced))):
        raise ValueError('detailed candidate packets differ from source projection')
    remaining = Counter(tuple(row[:19]) for row in old)
    extra = set()
    for ordinal, row in enumerate(predicted):
        words = tuple(row[:19])
        if remaining[words]:
            remaining[words] -= 1
        else:
            extra.add(ordinal)
    if sum(remaining.values()) or len(extra) != 76:
        raise ValueError('new packet classification differs')
    planes = mirror_planes(run, receipt)
    with Image.open(captured) as source_image:
        actual_rgb = np.asarray(source_image.convert('RGB'))
    palette = run / f'usa-source-{SOURCE_FRAME}-palettes.bin'
    reconstructed = resolve(planes[0], planes[1], palette.read_bytes())
    rgb_delta = np.max(np.abs(actual_rgb.astype('i2') - reconstructed.astype('i2')), axis=2)
    if int(np.count_nonzero(rgb_delta > 1)) > 1000:
        raise ValueError('CRT/image palette reconstruction is not calibrated')
    texture = run / f'usa-source-{SOURCE_FRAME}-textures.bin'
    quad_words = [row['words'] for row in traced]
    isolated_index, isolated_tag = render_quads(quad_words, texture.read_bytes())
    isolated_id, id_tag = render_quads(quad_words, texture.read_bytes(), debug_quad_id=True)
    x0, y0, x1, y1 = ROI
    with Image.open(prior_off / 'run/gl-snap/mvgl_004.bmp') as image:
        ordinary_rgb = np.asarray(image.convert('RGB'))
    changed_red = red(actual_rgb[y0:y1, x0:x1]) & ~red(ordinary_rgb[y0:y1, x0:x1])
    candidates = np.argwhere(changed_red)
    mapped = {}
    for yy, xx in candidates:
        point = (int(x0 + xx), int(y0 + yy))
        mapped.setdefault(screen_to_indexed(*point), point)
    exact, added, target, examples = 0, 0, 0, []
    by_object = Counter()
    for (x, y), screen_point in mapped.items():
        if (not (planes[1][y, x] & 4) or not isolated_tag[y, x] or not id_tag[y, x] or
                isolated_index[y, x] != planes[0][y, x]):
            continue
        exact += 1
        ordinal = int(isolated_id[y, x])
        if ordinal not in extra:
            continue
        added += 1
        row = traced[ordinal]
        by_object[hex(row['object'])] += 1
        if row['object'] == TARGET:
            target += 1
        if len(examples) < 8 or (row['object'] == TARGET and
                                 not any(item['object'] == hex(TARGET) for item in examples)):
            item = dict(screen=list(screen_point), indexed=[x, y], ordinal=ordinal,
                        object=hex(row['object']), model=hex(row['model']),
                        depth=row['depth'], combined=[int(planes[0][y, x]),
                                                      int(planes[1][y, x])],
                        original_only=[int(planes[2][y, x]), int(planes[3][y, x])],
                        candidate_rgb=[int(v) for v in actual_rgb[screen_point[1], screen_point[0]]],
                        control_rgb=[int(v) for v in ordinary_rgb[screen_point[1], screen_point[0]]])
            if len(examples) < 8:
                examples.append(item)
            else:
                examples[-1] = item
    if not candidates.size or not added or not target:
        raise ValueError('no screenshot-selected red center sample traces to target extra packets')
    return dict(schema=1, passed=True,
                scope='One 1440p completed USA Golden Gate frame 10476. Red-color CRT '
                      'screen points are center samples; only exact indexed auxiliary '
                      'matches receive new packet IDs. No full silhouette, CRT neighbor '
                      'decomposition, transition smoothness, 4K or course-wide result.',
                source_frame=SOURCE_FRAME, completed_frame=FRAME, visible_page=0,
                source_packet_count=len(traced), new_source_packets=len(extra),
                detailed_completed_image_equals_continuous=True,
                source_resources_equal=True,
                palette_reconstruction_over_one=int(np.count_nonzero(rgb_delta > 1)),
                palette_reconstruction_max=int(rgb_delta.max()),
                red_predicate='R>110 and 100R>135G and 100R>125B', roi_xyxy=list(ROI),
                candidate_only_red_screen_pixels=int(candidates.shape[0]),
                unique_indexed_center_samples=len(mapped), exact_host_center_samples=exact,
                new_packet_center_samples=added, target_center_samples=target,
                new_packet_samples_by_object=dict(sorted(by_object.items())),
                examples=examples, selected_host=selected,
                sha256={'detailed_report': sha(detailed / 'report.json'),
                        'prior_control_report': sha(prior_off / 'report.json'),
                        'prior_candidate_report': sha(prior_on / 'report.json'),
                        'source_screen': sha(source_screen),
                        'candidate_scene_screen': sha(candidate_screen),
                        'completed_image': sha(captured),
                        'control_image': sha(prior_off / 'run/gl-snap/mvgl_004.bmp'),
                        'mirror_receipt': sha(receipt_path),
                        'trace_scenes': trace['sha256']['scenes'],
                        'trace_quads': trace['sha256']['quads'],
                        'texture': sha(texture), 'palette': sha(palette)})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('detailed', 'prior_on', 'prior_off', 'source', 'rom',
                 'source_screen', 'candidate_screen', 'report'):
        ap.add_argument('--' + name.replace('_', '-'), dest=name, type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite USA pixel attribution')
    result = screen(args.detailed, args.prior_on, args.prior_off, args.source,
                    args.rom, args.source_screen, args.candidate_screen)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', result['new_packet_center_samples'], result['target_center_samples'])


if __name__ == '__main__':
    main()
