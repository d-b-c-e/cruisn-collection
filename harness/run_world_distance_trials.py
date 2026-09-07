"""Run isolated World global-distance trials and retain independent verdicts.

Pixel changes are expected in an experiment, not a visual-quality PASS. Reports
separate launch/completeness, native guard counters, input timing, camera state,
completed GL images and host speed. One emulator runs at a time, force disabled.
The 'original' trial uses original distance/lookahead at the requested CPU clock;
its identity comparison still checks the untouched source recording.
"""
import argparse
import json
from pathlib import Path
import sys

from analyze_session import summarize as timing
from analyze_world_distance import summarize as distance
from compare_world_motion import compare as motion
from diagnostic_runtime import ROOT, new_run
from gl_frames import compare_completed_frames, requested_frames
from verification import sha256_file, write_json
import replay

TRIALS = {'original': (80000,0), 'far125': (100000,0), 'lead4': (80000,4),
          'far125-lead4': (100000,4), 'far2-lead4': (160000,4), 'far2-lead8': (160000,8)}


def interval(text):
    try:
        first,last = map(int,text.split(':'))
        if 1 <= first < last:
            return first,last
    except ValueError:
        pass
    raise argparse.ArgumentTypeError('expected positive FIRST:LAST with FIRST < LAST')


def motion_script(first, last):
    source = (ROOT/'lua/world_motion_trace.lua').read_text(encoding='utf-8')
    if not 1 <= first < last or last-first > 12000:
        raise ValueError('invalid bounded motion interval')
    for name, default, value in [('FIRST',1800,first),('LAST',3300,last)]:
        old = f"os.getenv('CRUISN_MOTION_{name}') or '{default}'"
        if source.count(old) != 1:
            raise ValueError('motion probe changed; update its explicit interval binding')
        source = source.replace(old, str(value))
    return source


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', type=Path)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--output', required=True)
    parser.add_argument('--trials', nargs='+', choices=TRIALS, default=list(TRIALS))
    parser.add_argument('--motion', type=interval, required=True, help='camera/ADC trace interval')
    parser.add_argument('--gl-frames', type=interval, required=True)
    parser.add_argument('--gl-every', type=int, default=20)
    parser.add_argument('--until-frame', type=int, help='explicit recording prefix')
    parser.add_argument('--cpu-percent', type=int, choices=(100,125,150,200), default=100,
                        help='same clock for every trial, including its control; diagnostic only')
    parser.add_argument('--timeout', type=float, default=420)
    args = parser.parse_args(argv)
    if args.trials[0] != 'original' or len(set(args.trials)) != len(args.trials):
        parser.error('unique trials must begin with original, the matched control')
    work = new_run('world-distance-trials', args.output)
    report = {'schema':1, 'completed':False, 'visual_acceptance':'not established by automated metrics',
              'physical_force':False, 'candidate_sha256':sha256_file(args.candidate),
              'case_sha256':sha256_file(args.case/'case.json'), 'cpu_percent':args.cpu_percent, 'trials':[]}
    try:
        manifest = json.loads((args.case/'case.json').read_text(encoding='utf-8'))
        stop = args.until_frame or manifest['evidence']['frames']
        if manifest['rom'] != 'crusnwld24' or not args.motion[1] < stop <= manifest['evidence']['frames']:
            raise ValueError('World 2.4 recording must cover the motion interval and stop')
        if args.gl_frames[1] >= stop:
            raise ValueError('leave frames after the GL interval for completed capture delivery')
        frames = requested_frames(*args.gl_frames, args.gl_every)
        probe = work/'motion.lua'
        probe.write_text(motion_script(*args.motion), encoding='utf-8')
        report['motion_script_sha256'] = sha256_file(probe)
        for name in args.trials:
            far,lead = TRIALS[name]
            run = work/name
            options = ['--until-frame', str(stop)] if args.until_frame else []
            rc = replay.main([str(args.case), '--candidate',str(args.candidate), '--output',str(run),
                '--world-far',str(far), '--world-lead',str(lead), '--world-cpu',str(args.cpu_percent),
                '--probe-script',str(probe), '--small-window', '--timeout',str(args.timeout),
                '--gl-capture',f'{args.gl_frames[0]}:{args.gl_frames[1]}', '--gl-every',str(args.gl_every),
                '--gl-max',str(len(frames)), *options])
            evidence = json.loads((run/'report.json').read_text(encoding='utf-8'))
            item = {'name':name, 'original_identity_exit':rc, 'error':evidence.get('error'),
                    'comparison':evidence.get('comparison')}
            report['trials'].append(item)
            if item['error']:
                raise ValueError(f'{name}: {item["error"]}')
            item['native_distance'] = distance(run/'run/world-distance.csv')
            if item['native_distance']['frames'] != [0,stop-1]:
                raise ValueError(f'{name}: native counters do not cover the entire replay')
            item['timing'] = timing(run/'run',*args.motion)
            item['motion'] = motion(work/'original/run', run/'run')
            item['gl'] = compare_completed_frames(work/'original/run/gl-snap',run/'run/gl-snap',frames,True)
            write_json(work/'report.json',report)
            print(f'{name}: complete; original pixel identity={rc==0}; '
                  f'camera equal={item["motion"]["camera_equal"]}; '
                  f'emulation={item["timing"]["emulation_ratio"]:.4%}',flush=True)
            if item['comparison']['input_or_time_mismatches']:
                raise ValueError(f'{name}: frame input/time mismatch')
        report['completed'] = True
    except (OSError,ValueError,KeyError) as error:
        report['error'] = str(error)
    write_json(work/'report.json',report)
    return 0 if report['completed'] else 1


if __name__=='__main__': sys.exit(main())
