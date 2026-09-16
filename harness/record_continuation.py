"""Record a preserved drive plus a labeled scripted tail into a new case.

One recording only: candidate replay, motion comparison and visual acceptance
are separate steps. Never modifies the source or enables physical force.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

from derive_case import configure_gl, inherited_settings, validate_parent
from diagnostic_runtime import diagnostic_env, execute, new_run
from display_target import choose_size, monitors, parse_size
from extend_input import extend
from gl_frames import read_completed_frames
from session_case import Recording, read_trace, set_option
from verification import sha256_file, write_json


def compare_prefix(parent, recorded, original_frames, total_frames):
    """Compare every effective input/time; host speed is not emulated state."""
    if not 0 < original_frames < total_frames:
        raise ValueError('continuation must extend the complete original trace')
    fields, before = read_trace(parent)
    other, after = read_trace(recorded)
    if fields != other or len(before) != original_frames or len(after) != total_frames:
        raise ValueError('continuation trace columns or complete frame counts differ')
    keys = [key for key in fields if key not in ('host_seconds', 'speed_percent')]
    for old, new in zip(before, after):
        if any(old[key] != new[key] for key in keys):
            raise ValueError('continuation changed original input/time at frame ' + old['frame'])
    return dict(original_inputs_exact=len(before), tail_frames=len(after)-len(before))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('parent', type=Path, help='completed recorded case directory')
    ap.add_argument('scenario', type=Path, help='tail-relative analog keyframes and button pulses')
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--output', required=True, help='new output directory')
    ap.add_argument('--title', required=True)
    ap.add_argument('--timeout', type=float, default=450)
    ap.add_argument('--display-size', type=parse_size)
    ap.add_argument('--gl-capture', help='FIRST:LAST completed frames, relative to the entire case')
    ap.add_argument('--gl-every', type=int, default=300)
    args = ap.parse_args(argv)
    if args.timeout <= 0:
        ap.error('timeout must be positive')
    work = new_run('continuation', args.output)
    report = dict(schema=1, passed=False, physical_force=False,
                  scope='New MAME recording and original input/time prefix only; no identity replay, route or visual acceptance.')
    try:
        parent = args.parent.resolve()
        manifest = json.loads((parent/'case.json').read_text(encoding='utf-8'))
        validate_parent(parent, manifest)
        scenario_bytes = args.scenario.read_bytes()
        stimulus, provenance = extend((parent/'record/input/session.inp').read_bytes(),
                                     json.loads(scenario_bytes.decode('utf-8')))
        if provenance['recorded_frames'] != manifest['evidence']['frames']:
            raise ValueError('parent INP and trace frame counts differ')
        stop = provenance['total_frames']
        (work/'stimulus.inp').write_bytes(stimulus)
        (work/'scenario.json').write_bytes(scenario_bytes)
        provenance.update(parent=str(parent), parent_case_sha256=sha256_file(parent/'case.json'),
                          scenario_sha256=sha256_file(work/'scenario.json'))
        write_json(work/'provenance.json', provenance)
        command = [str(args.candidate.resolve()), *manifest['command'][1:]]
        command = set_option(command, '-seconds_to_run', stop//50+30)
        if args.display_size:
            target = choose_size(args.display_size, monitors())
            command = set_option(command, '-screen', target['selected']['device'])
            command = set_option(command, '-resolution', 'x'.join(map(str,args.display_size)))
            command = [arg for arg in command if arg != '-nomaximize']+['-maximize']
            report['display_target'] = target
        settings = inherited_settings(parent, manifest['settings'])
        # Captures are explicit for this longer case; do not inherit stale ranges.
        settings = {k:v for k,v in settings.items()
                    if not k.startswith(('MIDV_GL_SNAP', 'MIDZ_GL_SNAP'))}
        expected = configure_gl(settings, manifest['rom'], args.gl_capture, args.gl_every, stop)
        recording = Recording(work/'case', every=manifest['every'], stop_frame=stop)
        actions = parent/'record/cheats/actions.csv'
        command, env, runtime = recording.prepare(command, diagnostic_env(settings), parent/'initial',
            stimulus=work/'stimulus.inp', cheat_actions=actions if actions.exists() else None)
        recording.manifest.update(title=args.title, derived_from=provenance)
        write_json(recording.path/'case.json', recording.manifest)
        invocation = execute(command, runtime, env, args.timeout)
        if (runtime/'stdout.log').exists():
            shutil.copy2(runtime/'stdout.log', runtime/'launch.log')
        recording.finish(invocation['returncode'])
        if invocation['error'] or recording.manifest['status'] != 'recorded':
            raise ValueError(invocation['error'] or recording.manifest.get('error'))
        report.update(compare_prefix(parent/'record/frames.csv', runtime/'frames.csv',
                                     provenance['recorded_frames'], stop))
        if expected:
            read_completed_frames(runtime/'gl-snap', expected)
            report['completed_gl_frames'] = expected
        report['passed'] = True
    except (OSError, ValueError, KeyError) as exc:
        report['error'] = str(exc)
    write_json(work/'report.json', report)
    print('CONTINUATION RECORDED' if report['passed'] else 'FAIL', work/'report.json')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
