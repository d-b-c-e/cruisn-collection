"""Qualify intentional World active-margin differences in matched completed frames."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def qualify(control, candidate, raw_gl):
    a = json.loads((control/'report.json').read_text(encoding='utf-8'))
    b = json.loads((candidate/'report.json').read_text(encoding='utf-8'))
    gl = json.loads(raw_gl.read_text(encoding='utf-8'))
    if (not a.get('passed') or not b.get('passed') or a['case'] != b['case'] or
            not a['comparison']['passed'] or not b['comparison']['passed'] or
            not a['display_watch']['passed'] or not b['display_watch']['passed'] or
            not a['vunit_runtime']['result']['verified'] or
            not b['vunit_runtime']['result']['verified'] or
            gl.get('error') or gl.get('passed') is not False or gl['frames'] != 9):
        raise ValueError('matched replays or raw intentional-difference report unqualified')
    envs = [json.loads((run/'run/invocation.json').read_text(encoding='utf-8'))['environment']
            for run in (control, candidate)]
    if (any(env['MIDV_FFB'] != '0' for env in envs) or
            envs[0].get('MIDV_WORLD_HOST_ACTIVE_NONROADS', '0') != '0' or
            envs[1]['MIDV_WORLD_HOST_ACTIVE_NONROADS'] != '1'):
        raise ValueError('comparison does not isolate the gated non-road switch')
    am = a['vunit_original_mirror']['result']
    bm = b['vunit_original_mirror']['result']
    if (am['frame'] != 6000 or bm['frame'] != 6000 or
            am['visible_page'] != bm['visible_page'] or
            am['host_completion']['visible']['frame'] !=
            bm['host_completion']['visible']['frame']):
        raise ValueError('indexed source/display pair differs')
    if any(am['sha256'][name] != bm['sha256'][name] for name in am['sha256']
           if '-plane2.bin' in name or '-plane3.bin' in name):
        raise ValueError('original indexed planes changed')
    changes = gl['pixel_changes']
    expected = list(range(5960, 6041, 10))
    if (any(request['expected_frames'] != expected for request in gl['capture_requests']) or
            [item['frame'] for item in changes] != gl['different_frames'] or
            not set(gl['different_frames']) <= set(expected) or
            any(sum(row[1] for row in item['changed_pixels_by_thirds'])
                for item in changes)):
        raise ValueError('capture cadence changed or completed center third differs')
    return {'passed': True,
            'scope': 'Nine sparse matched completed 1440p frames around one New York interval. '
                     'Middle third, original indexed planes and recorded input/native images '
                     'remain exact; near-black color counts are visual hints only.',
            'frames': expected,
            'different_frames': gl['different_frames'],
            'total_changed_pixels': sum(item['changed_pixels'] for item in changes),
            'total_new_near_black_hint': sum(item['candidate_new_near_black'] for item in changes),
            'total_recovered_near_black_hint': sum(item['candidate_recovered_near_black'] for item in changes),
            'completed_center_third_changed_pixels': 0,
            'original_indexed_planes_exact': True,
            'frame_detail': changes,
            'raw_gl_report_passed': False,
            'raw_gl_report_sha256': sha(raw_gl),
            'report_sha256': {'control': sha(control/'report.json'),
                              'candidate': sha(candidate/'report.json')}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--raw-gl', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite temporal evidence')
    result = qualify(args.control, args.candidate, args.raw_gl)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('PASS', result['different_frames'], result['total_changed_pixels'])


if __name__ == '__main__':
    main()
