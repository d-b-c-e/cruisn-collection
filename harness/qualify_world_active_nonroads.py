"""Qualify the saved World active-nonroad replay after a strict reader update.

The original FAIL report remains untouched. This rechecks its raw evidence and
separates input/native identity, indexed ownership, and completed pixels.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from raw_snapshots import convert_raw_snapshots
from screen_world_active_gap import component
from session_case import compare_evidence, session_evidence
from vunit_bootstrap import verify as verify_bootstrap
from vunit_host_failure import verify_receipt as verify_failure
from vunit_original_mirror import verify as verify_mirror
from vunit_runtime import verify as verify_runtime


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def planes(root, frame, page):
    paths = [root/'run'/f'vunit-mirror-{frame}-page{page}-plane{i}.bin'
             for i in range(4)]
    return paths, [np.fromfile(path, dtype='<u2' if i%2==0 else 'u1')
                   .reshape(1600, 2736) for i, path in enumerate(paths)]


def qualify(control, failed, geometry_paths):
    raw_path = failed/'report.json'
    raw = json.loads(raw_path.read_text(encoding='utf-8'))
    old = json.loads((control/'report.json').read_text(encoding='utf-8'))
    case = Path(raw['case'])
    manifest = json.loads((case/'case.json').read_text(encoding='utf-8'))
    run = failed/'run'
    invocation = json.loads((run/'invocation.json').read_text(encoding='utf-8'))
    if (raw.get('passed') is not False or raw.get('error') !=
            'invalid fade metadata identity or policy' or old.get('passed') is not True
            or old['case'] != raw['case'] or invocation['returncode'] != 0
            or invocation['environment']['MIDV_FFB'] != '0'
            or invocation['environment']['MIDV_WORLD_HOST_ACTIVE_ROADS'] != '1'
            or invocation['environment']['MIDV_WORLD_HOST_ACTIVE_NONROADS'] != '1'
            or not raw['display_watch']['passed']):
        raise ValueError('raw run is not the single expected validator failure')
    reference = session_evidence(case/'record', manifest['every'], manifest['returncode'])
    if reference != manifest['evidence']:
        raise ValueError('recorded reference changed')
    prefix = raw['comparison_scope']['last_frame']
    reference = dict(reference, frames=prefix,
                     snapshots={n:v for n,v in reference['snapshots'].items()
                                if int(n) <= prefix})
    convert_raw_snapshots(run)
    evidence = session_evidence(run, manifest['every'], invocation['returncode'], require_gl=True)
    comparison = compare_evidence(case/'record', run, reference, evidence)
    bootstrap = verify_bootstrap(raw['vunit_bootstrap'], run)
    runtime = verify_runtime(raw['vunit_runtime'], run, bootstrap)
    failure = verify_failure(raw['vunit_host_failure'], run)
    trial = dict(raw['vunit_original_mirror'], nonroad_margin_coverage=True)
    mirror = verify_mirror(trial, run)
    old_mirror = old['vunit_original_mirror']['result']
    frame, page = mirror['frame'], mirror['visible_page']
    if (frame != old_mirror['frame'] or page != old_mirror['visible_page'] or
            mirror['host_completion']['visible']['frame'] !=
            old_mirror['host_completion']['visible']['frame']):
        raise ValueError('candidate and control use different completed source/page')
    old_paths, original = planes(control, frame, page)
    new_paths, candidate = planes(failed, frame, page)
    original_planes_exact = all(np.array_equal(a,b) for a,b in zip(original[2:], candidate[2:]))
    center = slice(344, 2392)
    center_exact = all(np.array_equal(a[:,center],b[:,center])
                       for a,b in zip(original[:2],candidate[:2]))
    if not original_planes_exact or not center_exact:
        raise ValueError('original indexed planes or 4:3 center changed')
    margin = np.zeros_like(original[1], dtype=bool)
    margin[:,:344] = True
    margin[:,2392:] = True
    changed = margin & ((original[0] != candidate[0]) | (original[1] != candidate[1]))
    prior_owned = changed & (original[1] != 0)
    newly_owned = changed & (original[1] == 0) & (candidate[1] != 0)
    gaps = {}
    for name, path in geometry_paths.items():
        geometry = json.loads(path.read_text(encoding='utf-8'))
        if geometry['source_frame'] != mirror['host_completion']['visible']['frame']:
            raise ValueError('gap geometry source differs from completed visible scene')
        mask = component(original, geometry)
        gained = mask & (candidate[1] != 0)
        gaps[name] = {'unowned_control_pixels': int(mask.sum()),
                      'newly_owned_pixels': int(gained.sum()),
                      'coverage_fraction': float(gained.sum()/mask.sum()),
                      'remaining_unowned_pixels': int((mask & (candidate[1] == 0)).sum())}
    old_image = np.asarray(Image.open(control/'run/gl-snap/mvgl_000.bmp').convert('RGB'))
    new_image = np.asarray(Image.open(failed/'run/gl-snap/mvgl_000.bmp').convert('RGB'))
    if old_image.shape != new_image.shape:
        raise ValueError('completed capture sizes differ')
    rgb_changed = np.any(old_image != new_image, axis=2)
    ys, xs = np.where(rgb_changed)
    result = {'passed': bool(comparison['passed'] and all(g['newly_owned_pixels'] > 0
                                                        for g in gaps.values()) and len(xs) > 0),
              'scope': 'Same raw candidate replay, requalified after opt-in policy-2 reader fix. '
                       'One World2.4 New York frame; no cross-frame/other-course/4K acceptance.',
              'raw_report_passed': False, 'raw_report_error': raw['error'],
              'raw_report_sha256': sha(raw_path), 'candidate': raw['emulator_source'],
              'comparison': comparison, 'bootstrap': bootstrap, 'runtime': runtime,
              'host_failure': failure, 'mirror_frame': frame, 'mirror_page': page,
              'source_frame': mirror['host_completion']['visible']['frame'],
              'fade_metadata': mirror['fade_metadata'],
              'original_indexed_planes_exact': original_planes_exact,
              'center_indexed_exact': center_exact,
              'margin_changed_indexed_pixels': int(changed.sum()),
              'margin_newly_owned_pixels': int(newly_owned.sum()),
              'margin_previously_owned_changed_pixels': int(prior_owned.sum()),
              'gaps': gaps,
              'completed_rgb_changed_pixels': len(xs),
              'completed_rgb_changed_bounds': ([int(xs.min()),int(ys.min()),
                                                int(xs.max()),int(ys.max())] if len(xs) else None),
              'source_sha256': {'control_completed': sha(control/'run/gl-snap/mvgl_000.bmp'),
                                'candidate_completed': sha(failed/'run/gl-snap/mvgl_000.bmp'),
                                **{f'control_{p.name}': sha(p) for p in old_paths},
                                **{f'candidate_{p.name}': sha(p) for p in new_paths}},
              'geometry_sha256': {name: sha(path) for name,path in geometry_paths.items()}}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--failed', type=Path, required=True)
    parser.add_argument('--left-geometry', type=Path, required=True)
    parser.add_argument('--right-geometry', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite qualified evidence')
    result = qualify(args.control, args.failed,
                     {'left':args.left_geometry,'right':args.right_geometry})
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('PASS' if result['passed'] else 'FAIL', result['gaps'],
          'center exact', result['center_indexed_exact'])
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
