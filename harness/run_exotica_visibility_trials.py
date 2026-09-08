"""Serialize bounded Exotica projection/margin trials with completed GL evidence.

Only the explicit Lua probe changes CPU read results; no ROM/RAM patch is used.
Completion, original input identity, sphere decisions, GL changes and timing have
independent verdicts. This runner does not grant product or visual acceptance.
"""
import argparse
import json
from pathlib import Path
import sys
from analyze_exotica_frustum import summarize
from analyze_session import summarize as timing
from diagnostic_runtime import ROOT,new_run
from gl_frames import requested_frames,compare_completed_frames
from run_usa_distance_trials import interval
from verification import sha256_file,write_json
import replay

TRIALS={'stock':(0,0),'reciprocal':(1,0),'margins':(0,88),'both':(1,88),'both-repeat':(1,88)}


def probe_source(first,last,reciprocal,margin):
    if not 1<=first<last or last-first>12000 or reciprocal not in (0,1) or margin not in (0,88):
        raise ValueError('invalid Exotica visibility trial')
    source=(ROOT/'lua/exotica_frustum.lua').read_text(encoding='utf-8')
    for key,default,value in [('FIRST',2500,first),('LAST',4300,last),('RECIPROCAL',0,reciprocal),('MARGIN',0,margin)]:
        old=f"os.getenv('CRUISN_EXOTICA_{key}') or '{default}'"
        if source.count(old)!=1:raise ValueError('Exotica probe binding changed')
        source=source.replace(old,str(value))
    return source


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('case',type=Path);p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',required=True);p.add_argument('--trials',nargs='+',choices=TRIALS,default=list(TRIALS))
    p.add_argument('--interval',type=interval,default=(2500,4300));p.add_argument('--gl-every',type=int,default=100)
    p.add_argument('--timeout',type=float,default=360)
    a=p.parse_args(argv)
    if a.trials[0]!='stock' or len(a.trials)!=len(set(a.trials)):p.error('unique trials must start with stock')
    if 'both-repeat' in a.trials and ('both' not in a.trials or a.trials.index('both')>a.trials.index('both-repeat')):
        p.error('both must precede both-repeat')
    work=new_run('exotica-visibility-trials',a.output)
    report=dict(schema=1,scope=__doc__,completed=False,physical_force=False,
                candidate_sha256=sha256_file(a.candidate),case_sha256=sha256_file(a.case/'case.json'),trials=[])
    try:
        manifest=json.loads((a.case/'case.json').read_text(encoding='utf-8'))
        if manifest['rom']!='crusnexo' or a.interval[1]+2>=manifest['evidence']['frames']:
            raise ValueError('Exotica2.4 recording must cover the trial and drain interval')
        frames=list(requested_frames(*a.interval,a.gl_every))
        for name in a.trials:
            reciprocal,margin=TRIALS[name];probe=work/(name+'.lua')
            probe.write_text(probe_source(*a.interval,reciprocal,margin),encoding='utf-8')
            run=work/name
            rc=replay.main([str(a.case),'--candidate',str(a.candidate),'--output',str(run),'--probe-script',str(probe),
                '--small-window','--timeout',str(a.timeout),'--gl-capture',f'{a.interval[0]}:{a.interval[1]}',
                '--gl-every',str(a.gl_every),'--gl-max',str(len(frames))])
            r=json.loads((run/'report.json').read_text(encoding='utf-8'))
            item=dict(name=name,probe_sha256=sha256_file(probe),original_identity_exit=rc,error=r.get('error'),comparison=r.get('comparison'))
            report['trials'].append(item)
            if item['error']:raise ValueError(f'{name}: {item["error"]}')
            item['frustum']=summarize(run/'run/exotica-frustum.csv')
            if item['frustum']['frames']!=list(a.interval) or item['frustum']['trial']!=dict(reciprocal=reciprocal,margin=margin):
                raise ValueError('incomplete or mismatched frustum trial')
            item['timing']=timing(run/'run',*a.interval)
            item['gl']=compare_completed_frames(work/'stock/run/gl-snap',run/'run/gl-snap',frames,True)
            if item['comparison']['input_or_time_mismatches']:raise ValueError('recorded frame input/time mismatch')
            if name=='stock' and rc!=0:raise ValueError('stock input/native control failed')
            if name=='both-repeat':
                item['repeat_gl']=compare_completed_frames(work/'both/run/gl-snap',run/'run/gl-snap',frames,True)
                item['repeat_frustum']=sha256_file(work/'both/run/exotica-frustum.csv')==sha256_file(run/'run/exotica-frustum.csv')
                if not item['repeat_gl']['passed'] or not item['repeat_frustum']:raise ValueError('candidate did not repeat')
            write_json(work/'report.json',report)
            print(f'{name}: complete, accepted={item["frustum"]["actual_reasons"].get("accepted",0)}, '
                  f'GL changed={len(item["gl"]["different_frames"])}/{len(frames)}, '
                  f'emulation={item["timing"]["emulation_ratio"]:.4%}',flush=True)
        report['completed']=True
    except (OSError,ValueError,KeyError) as error:report['error']=str(error)
    write_json(work/'report.json',report)
    return 0 if report['completed'] else 1


if __name__=='__main__':sys.exit(main())
