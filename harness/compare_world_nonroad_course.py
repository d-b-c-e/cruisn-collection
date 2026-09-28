"""Compare two passing World replays that differ only in active non-road margins.

Completed-pixel equality is evidence of preservation, not visible improvement.
"""
import argparse
import hashlib
import json
from pathlib import Path

from gl_frames import compare_completed_frames


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_presentation(invocations, required):
    """Reject an internally matched pair that omits a requested display mode."""
    for key, expected in required.items():
        observed = [run['environment'].get(key) for run in invocations]
        if observed != [expected, expected]:
            raise ValueError(f'required {key}={expected} absent or differs: {observed}')
    return required


def compare(control, trial, required_presentation=None):
    paths = [root/'report.json' for root in (control,trial)]
    reports = [json.loads(path.read_text(encoding='utf-8')) for path in paths]
    a,b = reports
    options_a = dict(a['world_host_scenery'])
    options_b = dict(b['world_host_scenery'])
    # Older controls omit the disabled option; explicit replay controls report
    # it as "off". Both describe the same renderer state.
    control_nonroads=options_a.pop('active_nonroads',None)
    trial_nonroads=options_b.pop('active_nonroads',None)
    if control_nonroads not in (None,'off') or trial_nonroads != 'margins' or options_a != options_b:
        raise ValueError('replays differ in more than active non-road margin selection')
    if options_a.get('active_roads') != 'margins' or options_a.get('mode') != 'draw':
        raise ValueError('control is not the active-road draw baseline')
    invocations = [json.loads((root/'run/invocation.json').read_text(encoding='utf-8'))
                   for root in (control,trial)]
    if any(i['environment'].get('MIDV_FFB') != '0' or i['returncode'] != 0 for i in invocations):
        raise ValueError('both replays must finish with physical FFB off')
    verified_presentation = require_presentation(invocations, required_presentation or {})
    if any(not r['passed'] or not r['comparison']['passed'] or
           not r['display_watch']['passed'] or
           r['vunit_runtime']['result']['completion'] != 'owned-worker-stop'
           for r in reports):
        raise ValueError('input/native/display/shutdown replay gate failed')
    if (a['case'] != b['case'] or a['emulator_source'] != b['emulator_source'] or
            a['display_target'] != b['display_target'] or
            a['presentation_overrides'] != b['presentation_overrides'] or
            a['comparison_scope'] != b['comparison_scope']):
        raise ValueError('source, binary, presentation or prefix differs')
    images = compare_completed_frames(control/'run/gl-snap', trial/'run/gl-snap', details=True)
    center_changed = sum(row[1] for frame in images['pixel_changes']
                         for row in frame['changed_pixels_by_thirds'])
    if center_changed:
        raise ValueError(f'non-road margin trial changed {center_changed} center-third pixels')
    runtime = [r['vunit_runtime']['result'] for r in reports]
    if runtime[0]['scenes'] != runtime[1]['scenes']:
        raise ValueError('host scene count differs')
    return {'passed':True,
            'scope':'One recorded World course prefix on the same binary/display with physical FFB0. '
                    'Sparse completed images do not prove full-course visual safety or benefit.',
            'rom':json.loads((Path(a['case'])/'case.json').read_text(encoding='utf-8'))['rom'],
            'input_frames':a['comparison_scope']['last_frame'],
            'host_scenes':runtime[0]['scenes'],
            'host_quads_control':runtime[0]['quads'],
            'host_quads_trial':runtime[1]['quads'],
            'additional_submitted_quads':runtime[1]['quads']-runtime[0]['quads'],
            'verified_presentation':verified_presentation,
            'completed_center_third_changed_pixels':center_changed,
            'completed':images,
            'sha256':{'control_report':sha(paths[0]),'trial_report':sha(paths[1]),
                      'control_capture_index':sha(control/'run/gl-snap/captures.csv'),
                      'trial_capture_index':sha(trial/'run/gl-snap/captures.csv')}}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--control',type=Path,required=True)
    ap.add_argument('--trial',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True)
    ap.add_argument('--require-crt-on',action='store_true',
                    help='require explicit MIDV_GL_CRT=1 in both raw invocations')
    ap.add_argument('--require-gl-scale',type=int,
                    help='require explicit internal GL scale in both raw invocations')
    ap.add_argument('--require-native-height',type=int,choices=(400,401),
                    help='require explicit native V-Unit height in both raw invocations')
    args=ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite paired evidence')
    required = {}
    if args.require_crt_on:
        required['MIDV_GL_CRT'] = '1'
    if args.require_gl_scale is not None:
        required['MIDV_GL_SCALE'] = str(args.require_gl_scale)
    if args.require_native_height is not None:
        required['MIDV_GL_HEIGHT'] = str(args.require_native_height)
    result=compare(args.control,args.trial,required)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS',result['rom'],result['completed']['frames'],'completed images',
          result['additional_submitted_quads'],'added quads',
          len(result['completed']['different_frames']),'different images')


if __name__=='__main__':
    main()
