"""Verify saved Off-Road resident margin coverage against a source-joined control.

The control supplies same-run original DMA to identify the backdrop palette.
Both indexed mirrors must preserve their original-only planes. This checks one
completed native indexed page, not final CRT pixels, temporal quality or 4K.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path

import numpy as np

from screen_vunit_sky_gaps import candidates, ordinary_extensions, screen
from vunit_original_mirror import verify as verify_mirror
from verification import write_json


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def joined(mask, seeds):
    """Return only four-connected mask pixels reached from a strict gap."""
    if mask.shape != seeds.shape or mask.ndim != 2 or np.any(seeds & ~mask):
        raise ValueError('invalid connected sky-gap masks')
    result = np.zeros(mask.shape, dtype=bool)
    todo = deque(map(tuple, np.argwhere(seeds)))
    height, width = mask.shape
    while todo:
        y, x = todo.popleft()
        if result[y, x]:
            continue
        result[y, x] = True
        for yy, xx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
            if 0 <= yy < height and 0 <= xx < width and mask[yy, xx] and not result[yy, xx]:
                todo.append((yy, xx))
    return result


def check(control, candidate):
    control, candidate = Path(control), Path(candidate)
    reports = [json.loads((case / 'report.json').read_text(encoding='utf-8'))
               for case in (control, candidate)]
    if any(report.get('passed') is not True or report.get('comparison', {}).get('passed') is not True
           for report in reports) or reports[0]['case'] != reports[1]['case']:
        raise ValueError('control/candidate replay or original input comparison failed')
    invocations = [json.loads((case / 'run/invocation.json').read_text(encoding='utf-8'))
                   for case in (control, candidate)]
    environments = [invocation['environment'] for invocation in invocations]
    if (any(env.get('MIDV_FFB') != '0' for env in environments) or
            environments[0].get('MIDV_OFFROAD_HOST_RESIDENT_MARGINS', '0') != '0' or
            environments[1].get('MIDV_OFFROAD_HOST_RESIDENT_MARGINS') != '1'):
        raise ValueError('expected force-disabled control and opt-in resident candidate')
    source = screen(control)
    if source['rom'] != 'offroadc' or source['total_pixels'] <= 0:
        raise ValueError('no qualified Off-Road source gap')
    mirrors = [verify_mirror(report['vunit_original_mirror'], case / 'run')
               for case, report in zip((control, candidate), reports)]
    keys = ('frame', 'width', 'height', 'visible_page')
    if any(mirrors[0][key] != mirrors[1][key] for key in keys):
        raise ValueError('indexed mirrors have different completed geometry')
    frame, width, height, page = (mirrors[0][key] for key in keys)
    if source['completed_frame'] != frame or source['visible_page'] != page:
        raise ValueError('control DMA scene and mirrors differ')
    names = [f'vunit-mirror-{frame}-page{side}-plane{plane}.bin'
             for side in (0, 1) for plane in (2, 3)]
    original = {name: digest(control / 'run' / name) for name in names}
    if any(original[name] != digest(candidate / 'run' / name) for name in names):
        raise ValueError('candidate modified an original-only indexed plane')
    prefix = f'vunit-mirror-{frame}-page{page}-plane'
    paths = [[case / 'run' / (prefix + str(plane) + '.bin') for plane in (0, 1)]
             for case in (control, candidate)]
    indices = [np.fromfile(pair[0], dtype='<u2').reshape(height, width) for pair in paths]
    tags = [np.fromfile(pair[1], dtype='u1').reshape(height, width) for pair in paths]
    scale = int(environments[0]['MIDV_GL_SCALE'])
    margin = int(environments[0]['MIDV_GL_MARGIN']) * scale
    if (scale != int(environments[1]['MIDV_GL_SCALE']) or
            margin != int(environments[1]['MIDV_GL_MARGIN']) * scale):
        raise ValueError('control/candidate native scale or margin differs')
    sky = np.zeros((height, width), dtype=bool)
    for palette in source['sky_palettes']:
        sky |= (indices[0] >= palette) & (indices[0] < palette + 256)
    sky &= tags[0] == 1
    strict = candidates(sky, tags[0], margin, width - margin, 32 * scale)
    ordinary = ordinary_extensions(sky, tags[0], margin, width - margin, 32 * scale)
    connected = joined(strict | ordinary, strict)
    if (int(strict.sum()) != source['total_pixels'] or
            int(connected.sum()) != source['connected_envelope_pixels'] or
            not connected.any()):
        raise ValueError('control gap reconstruction differs from source screen')
    changed_index = indices[0] != indices[1]
    changed_tags = tags[0] != tags[1]
    center = slice(margin, width - margin)
    strict_host = int(((tags[1] & 4) != 0)[strict].sum())
    connected_host = int(((tags[1] & 4) != 0)[connected].sum())
    changed_strict_index = int(changed_index[strict].sum())
    candidate_sky_index = np.zeros((height, width), dtype=bool)
    for palette in source['sky_palettes']:
        candidate_sky_index |= (indices[1] >= palette) & (indices[1] < palette + 256)
    remaining_strict_sky_index = int(candidate_sky_index[strict].sum())
    if (strict_host != int(strict.sum()) or connected_host != int(connected.sum()) or
            changed_strict_index != int(strict.sum()) or remaining_strict_sky_index or
            int((indices[1][strict] == 0).sum()) or
            changed_index[:, center].any() or changed_tags[:, center].any()):
        raise ValueError('resident pixels did not cover gap or changed native center')
    tag_values, tag_counts = np.unique(tags[1][strict], return_counts=True)
    result = dict(passed=True, completed_frame=frame, visible_page=page,
                  indexed_size=[width, height], native_center=[margin, width-margin],
                  source_strict_gap_pixels=int(strict.sum()),
                  source_connected_envelope_pixels=int(connected.sum()),
                  candidate_host_owned_strict_pixels=strict_host,
                  candidate_host_owned_envelope_pixels=connected_host,
                  candidate_changed_index_strict_pixels=changed_strict_index,
                  candidate_remaining_sky_index_strict_pixels=remaining_strict_sky_index,
                  candidate_zero_index_strict_pixels=int((indices[1][strict] == 0).sum()),
                  candidate_tags_on_strict={str(int(k)): int(v) for k, v in zip(tag_values, tag_counts)},
                  changed_index_pixels=int(changed_index.sum()),
                  changed_tag_pixels=int(changed_tags.sum()),
                  changed_tag_pixels_outside_connected=int((changed_tags & ~connected).sum()),
                  changed_index_inside_native_center=0,
                  changed_tag_inside_native_center=0,
                  original_plane_sha256=original,
                  source_control=source,
                  evidence_sha256={str(path.resolve()): digest(path)
                                   for path in (control/'report.json', candidate/'report.json',
                                                *paths[0], *paths[1])},
                  scope=__doc__)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('control', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite prior gap evidence')
    try:
        result = check(args.control, args.candidate)
    except (OSError, ValueError, KeyError) as exc:
        result = dict(passed=False, error=str(exc))
    write_json(args.report, result)
    print(('PASS' if result['passed'] else 'FAIL') + ': ' + str(args.report))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
