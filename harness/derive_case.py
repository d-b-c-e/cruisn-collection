"""Record an explicit candidate case from an existing drive, preserving its source.

New game code can intentionally change pictures and subsequent game history.
This creates a separate reference, checks effective inputs against its parent,
and then requires identity replay. It never replaces or blesses the parent.
"""
import argparse
import json
from pathlib import Path
import sys

from diagnostic_runtime import diagnostic_env, execute, new_run
from game_patch import read_patch
from session_case import Recording, compare_evidence, session_evidence, tree_hashes
from session_clock import SessionClock
from verification import sha256_file, write_json
import replay


def validate_parent(case, manifest):
    if manifest.get('schema') != 1 or manifest.get('status') != 'recorded':
        raise ValueError('parent must be a completed schema-1 case')
    if tree_hashes(case / 'initial') != manifest['initial_hashes']:
        raise ValueError('parent initial state changed')
    if sha256_file(case / 'record/input/session.inp') != manifest['inp_sha256']:
        raise ValueError('parent INP changed')
    for path, digest in manifest['rom_containers'].items():
        if sha256_file(path) != digest:
            raise ValueError('parent ROM dependency changed')
    if session_evidence(case / 'record', manifest['every'], manifest['returncode']) != manifest['evidence']:
        raise ValueError('parent evidence changed')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('parent', type=Path)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--patch', type=Path, required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--title', required=True)
    ap.add_argument('--clock', action='store_true', help='show the external emulation clock in both runs')
    ap.add_argument('--timeout', type=float, default=300)
    args = ap.parse_args(argv)
    if args.timeout <= 0: ap.error('timeout must be positive')
    work = new_run('derived-case', args.output)
    report = {'schema': 1, 'passed': False, 'physical_force': False,
              'original_route_equivalence': 'not established by derivation or identity replay',
              'scope': 'new candidate repeatability; parent visual differences retained'}
    try:
        parent = args.parent.resolve()
        manifest = json.loads((parent / 'case.json').read_text(encoding='utf-8'))
        validate_parent(parent, manifest)
        read_patch(args.patch)
        command = [str(args.candidate.resolve()), *manifest['command'][1:]]
        settings = dict(manifest['settings'])
        settings['MIDV_PATCH'] = str(args.patch.resolve())
        env = diagnostic_env(settings)
        recording = Recording(work / 'case', every=manifest['every'],
                              stop_frame=manifest['evidence']['frames'], snapshot_mode='raw', clock=args.clock)
        cmd, run_env, runtime = recording.prepare(command, env, parent / 'initial',
                                                  stimulus=parent / 'record/input/session.inp')
        recording.manifest.update(title=args.title, derived_from={
            'case': str(parent), 'case_sha256': sha256_file(parent / 'case.json'),
            'inp_sha256': manifest['inp_sha256'], 'change': 'explicit candidate executable and game patch'})
        write_json(recording.path / 'case.json', recording.manifest)
        clock = SessionClock(runtime, args.title)
        if args.clock: clock.start()
        try:
            invocation = execute(cmd, runtime, run_env, args.timeout)
        finally:
            clock.close()
        (runtime / 'launch.log').write_bytes((runtime / 'stdout.log').read_bytes())
        recording.finish(invocation['returncode'])
        if invocation['error'] or recording.manifest['status'] != 'recorded':
            raise ValueError(invocation['error'] or recording.manifest.get('error'))
        comparison = compare_evidence(parent / 'record', runtime, manifest['evidence'],
                                      recording.manifest['evidence'])
        report['parent_comparison'] = comparison
        if comparison['input_or_time_mismatches']:
            raise ValueError('derived recording changed effective input or emulated time')
        report['identity_replay_passed'] = replay.main([
            str(recording.path), '--output', str(work / 'replay'), '--timeout', str(args.timeout),
            *(['--clock'] if args.clock else [])]) == 0
        report['passed'] = report['identity_replay_passed']
    except (OSError, ValueError, KeyError) as error:
        report['error'] = str(error)
    write_json(work / 'report.json', report)
    print('REPEATABILITY PASS' if report['passed'] else 'FAIL', work / 'report.json')
    print('Original route equivalence is not established; inspect parent differences and motion traces.')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
