"""Bounded Off Road global far/clip/reciprocal trials, with physical force off.

This diagnostic mutates five guarded guest words and restores them after the
requested interval. It is not a launcher patch or a visual-acceptance verdict.
"""
import argparse
import json
from pathlib import Path
import sys
from analyze_session import summarize as timing
from analyze_offroad_distance import summarize as distance
from compare_world_motion import compare as motion
from diagnostic_runtime import ROOT,new_run
from gl_frames import compare_completed_frames,requested_frames
from run_usa_distance_trials import interval
from verification import sha256_file,write_json
import replay

TRIALS={'original':1,'far2':2,'far3':3}


def trial_script(first,last,multiplier):
    if not 1<=first<last or last-first>12000 or multiplier not in (1,2,3):
        raise ValueError('invalid bounded Off Road trial')
    source=(ROOT/'lua/offroad_distance.lua').read_text(encoding='utf-8')
    for key,default,value in [('FIRST',1800,first),('LAST',5990,last),('MULTIPLIER',0,multiplier)]:
        old=f"os.getenv('CRUISN_OFFROAD_{key}') or '{default}'"
        if source.count(old)!=1:raise ValueError('probe binding changed')
        source=source.replace(old,str(value))
    return source


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('case',type=Path);p.add_argument('--candidate',required=True,type=Path)
    p.add_argument('--output',required=True);p.add_argument('--trials',nargs='+',choices=TRIALS,default=list(TRIALS))
    p.add_argument('--interval',type=interval,default=(1800,5990))
    p.add_argument('--gl-frames',type=interval,default=(1800,5900));p.add_argument('--gl-every',type=int,default=100)
    p.add_argument('--timeout',type=float,default=360)
    a=p.parse_args(argv)
    if a.trials[0]!='original' or len(a.trials)!=len(set(a.trials)):p.error('unique trials must start with original')
    work=new_run('offroad-distance-trials',a.output)
    report=dict(schema=1,completed=False,scope=__doc__,physical_force=False,
                candidate_sha256=sha256_file(a.candidate),case_sha256=sha256_file(a.case/'case.json'),trials=[])
    try:
        manifest=json.loads((a.case/'case.json').read_text(encoding='utf-8'))
        if manifest['rom']!='offroadc' or a.interval[1]>=manifest['evidence']['frames']:
            raise ValueError('Off Road1.63 recording must cover the complete trial interval')
        if not a.interval[0]<=a.gl_frames[0]<=a.gl_frames[1]<=a.interval[1]:
            raise ValueError('GL captures must fall inside the bounded trial')
        frames=list(requested_frames(*a.gl_frames,a.gl_every))
        for name in a.trials:
            probe=work/f'{name}.lua';probe.write_text(trial_script(*a.interval,TRIALS[name]),encoding='utf-8')
            run=work/name
            rc=replay.main([str(a.case),'--candidate',str(a.candidate),'--output',str(run),
                '--probe-script',str(probe),'--small-window','--timeout',str(a.timeout),
                '--gl-capture',f'{a.gl_frames[0]}:{a.gl_frames[1]}','--gl-every',str(a.gl_every),'--gl-max',str(len(frames))])
            evidence=json.loads((run/'report.json').read_text(encoding='utf-8'))
            item=dict(name=name,probe_sha256=sha256_file(probe),original_identity_exit=rc,
                      error=evidence.get('error'),comparison=evidence.get('comparison'))
            report['trials'].append(item)
            if item['error']:raise ValueError(f'{name}: {item["error"]}')
            item['distance']=distance(run/'run')
            if item['distance']['frames']!=list(a.interval):raise ValueError('incomplete diagnostic trace')
            item['timing']=timing(run/'run',*a.interval)
            item['motion']=motion(work/'original/run',run/'run','offroad')
            item['gl']=compare_completed_frames(work/'original/run/gl-snap',run/'run/gl-snap',frames,True)
            write_json(work/'report.json',report)
            print(f'{name}: complete; original identity={rc==0}; camera equal={item["motion"]["camera_equal"]}; '
                  f'emulation={item["timing"]["emulation_ratio"]:.4%}',flush=True)
            if item['comparison']['input_or_time_mismatches']:raise ValueError('frame input/time mismatch')
            if name=='original' and rc!=0:raise ValueError('unchanged control failed original recording')
        report['completed']=True
    except (OSError,ValueError,KeyError) as error:report['error']=str(error)
    write_json(work/'report.json',report)
    return 0 if report['completed'] else 1


if __name__=='__main__':sys.exit(main())
