"""Qualify a matched USA partial-far-coverage interval without visual overclaim.

The exact GL comparator must report differences. This checker separately
requires recorded input/native agreement, stable display/FFB-off, identical
frame clocks, bounded margin-only completed changes and owned shutdown.
"""
import argparse
import csv
import json
from pathlib import Path

from screen_vunit_panorama_strips import sha


def frames(path):
    with path.open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        fields = [name for name in reader.fieldnames if name not in ('host_seconds', 'speed_percent')]
        return [tuple(row[name] for name in fields) for row in reader]


def qualify(off, on, rgb, prior):
    reports = [json.loads((root / 'report.json').read_text(encoding='utf-8'))
               for root in (off, on)]
    a, b = reports
    if not all(r['passed'] and r['comparison']['passed'] and r['display_watch']['passed'] and
               r['vunit_runtime']['result']['completion'] == 'owned-worker-stop'
               for r in reports):
        raise ValueError('one replay lacks input/native/display/owned-stop qualification')
    if (a['case'] != b['case'] or a['emulator_source']['executable_sha256'] !=
            b['emulator_source']['executable_sha256'] or a['display_target'] != b['display_target'] or
            a['comparison_scope'] != b['comparison_scope']):
        raise ValueError('paired case/binary/display/input scope differs')
    for root in (off, on):
        invocation = json.loads((root / 'run/invocation.json').read_text(encoding='utf-8'))
        if invocation['environment'].get('MIDV_FFB') != '0':
            raise ValueError('physical force not explicitly disabled')
    modes = [dict(r['usa_host_scenery']) for r in reports]
    selected = [m.pop('far_coverage') for m in modes]
    if selected != ['off', 'on'] or modes[0] != modes[1]:
        raise ValueError('replays differ in more than USA partial far coverage')
    old_frames = frames(off / 'run/frames.csv')
    new_frames = frames(on / 'run/frames.csv')
    if old_frames != new_frames or len(old_frames) != a['comparison_scope']['last_frame']:
        raise ValueError('recorded frame clocks or inputs differ')
    gl = json.loads(rgb.read_text(encoding='utf-8'))
    if (gl.get('passed') is not False or gl.get('error') or gl.get('size_mismatches') or
            gl.get('frames') != 11 or len(gl.get('pixel_changes', [])) != 11 or
            sorted(gl['different_frames']) != list(range(10460, 10501, 4)) or
            any(row['bounds_xyxy_exclusive'][2] > 300 for row in gl['pixel_changes'])):
        raise ValueError('completed image schedule/left-margin change differs')
    prior_report = json.loads((prior / 'posthoc-qualification-v1.json').read_text(encoding='utf-8'))
    saved = prior / 'run/gl-snap/mvgl_000.bmp'
    off_final = off / 'run/gl-snap/mvgl_010.bmp'
    if (prior_report.get('passed') is not True or
            prior_report['sha256']['completed_bmp'] != sha(saved) or
            sha(saved) != sha(off_final)):
        raise ValueError('control final image differs from prior source-qualified frame')
    changes = gl['pixel_changes']
    return dict(schema=1, passed=True,
                scope='Matched 40-frame USA Golden Gate interval at physical 1440p/FFB0. '
                      'Intentional completed changes are far-left only; no original indexed '
                      'mirror, 4K, full route, source-packet attribution or visual acceptance.',
                frames=len(old_frames), completed_frames=gl['frames'],
                changed_frames=gl['different_frames'],
                changed_frame_pixels=sum(row['changed_pixels'] for row in changes),
                changed_range=[min(row['changed_pixels'] for row in changes),
                               max(row['changed_pixels'] for row in changes)],
                completed_change_bounds=[min(row['bounds_xyxy_exclusive'][0] for row in changes),
                                         min(row['bounds_xyxy_exclusive'][1] for row in changes),
                                         max(row['bounds_xyxy_exclusive'][2] for row in changes),
                                         max(row['bounds_xyxy_exclusive'][3] for row in changes)],
                candidate_new_near_black_frame_pixels=sum(row['candidate_new_near_black']
                                                           for row in changes),
                original_native_comparisons_passed=True, identical_recorded_frame_clocks=True,
                control_10500_equals_prior_source=True,
                total_auxiliary_quads=[r['vunit_runtime']['result']['quads'] for r in reports],
                exact_gl_comparator_passed=False,
                sha256={'control_report': sha(off / 'report.json'),
                        'candidate_report': sha(on / 'report.json'),
                        'rgb_difference_report': sha(rgb),
                        'prior_posthoc': sha(prior / 'posthoc-qualification-v1.json'),
                        'control_frames': sha(off / 'run/frames.csv'),
                        'candidate_frames': sha(on / 'run/frames.csv'),
                        'control_final_bmp': sha(off_final),
                        'candidate_final_bmp': sha(on / 'run/gl-snap/mvgl_010.bmp')})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('off', 'on', 'rgb', 'prior', 'report'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite interval qualification')
    result = qualify(args.off, args.on, args.rgb, args.prior)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', result['completed_frames'], result['changed_frame_pixels'])


if __name__ == '__main__':
    main()
