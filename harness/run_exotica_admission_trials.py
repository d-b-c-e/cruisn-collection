"""Bounded Exotica admission trials with fixed coherent CPU sphere projection.

This replaces two reads of the adaptive admission limit, not guest memory or the
far plane. Additional loader/admission work can change the subsequent drive.
"""
import argparse,json
from pathlib import Path
from analyze_exotica_frustum import summarize as frustum
from analyze_exotica_streaming import summarize as streaming
from analyze_session import summarize as timing
from diagnostic_runtime import ROOT,new_run
from gl_frames import compare_completed_frames,requested_frames
from run_exotica_visibility_trials import probe_source
from run_usa_distance_trials import interval
from verification import sha256_file,write_json
import replay

TRIALS={'coherent':0,'admit160':160000,'admit190':190000,'admit160-repeat':160000}


def admission_probe_source(first,last,limit):
    if not 1<=first<last or last-first>12000 or limit not in (0,160000,190000):
        raise ValueError('invalid bounded Exotica admission trial')
    source=(ROOT/'lua/exotica_streaming.lua').read_text(encoding='utf-8')
    for key,default,value in [('STREAM_FIRST',2500,first),('STREAM_LAST',5990,last),('ADMISSION',0,limit)]:
        old=f"os.getenv('CRUISN_EXOTICA_{key}') or '{default}'"
        if source.count(old)!=1:raise ValueError('streaming probe binding changed')
        source=source.replace(old,str(value))
    return ('local visibility=(function()\n'+probe_source(first,last,1,88)+'\nend)()\n'
        +'local streaming=(function()\n'+source+'\nend)()\n'
        +'return function(n) visibility(n);streaming(n) end\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('case',type=Path)
    ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--interval',type=interval,default=(4500,5990));ap.add_argument('--gl-every',type=int,default=100)
    ap.add_argument('--trials',nargs='+',choices=TRIALS,default=list(TRIALS));ap.add_argument('--timeout',type=float,default=360)
    args=ap.parse_args()
    if args.trials[0]!='coherent' or len(set(args.trials))!=len(args.trials):ap.error('unique trials must begin with coherent control')
    if 'admit160-repeat' in args.trials and ('admit160' not in args.trials or args.trials.index('admit160')>args.trials.index('admit160-repeat')):
        ap.error('admit160 must precede its repeat')
    work=new_run('exotica-admission-trials',args.output)
    report=dict(completed=False,scope=__doc__,physical_force=False,native_sha256=sha256_file(args.candidate),
        case_sha256=sha256_file(args.case/'case.json'),trials=[])
    try:
        manifest=json.loads((args.case/'case.json').read_text(encoding='utf-8'))
        if manifest['rom']!='crusnexo' or args.interval[1]+2>=manifest['evidence']['frames']:
            raise ValueError('Exotica2.4 case must cover the bounded trial and drain interval')
        frames=requested_frames(*args.interval,args.gl_every)
        for name in args.trials:
            limit=TRIALS[name];probe=work/(name+'.lua');run=work/name
            probe.write_text(admission_probe_source(*args.interval,limit),encoding='utf-8')
            rc=replay.main([str(args.case),'--candidate',str(args.candidate),'--output',str(run),'--probe-script',str(probe),
                '--exotica-visibility','off','--small-window','--gl-capture',f'{args.interval[0]}:{args.interval[1]}',
                '--gl-every',str(args.gl_every),'--gl-max',str(len(frames)),'--timeout',str(args.timeout)])
            r=json.loads((run/'report.json').read_text(encoding='utf-8'))
            item=dict(name=name,admission=limit,probe_sha256=sha256_file(probe),original_identity_exit=rc,error=r.get('error'))
            report['trials'].append(item)
            if item['error']:raise ValueError(item['error'])
            if r['comparison']['input_or_time_mismatches']:raise ValueError('original input/frame-time mismatch')
            item.update(frustum=frustum(run/'run/exotica-frustum.csv'),streaming=streaming(run/'run/exotica-streaming.csv'),
                timing=timing(run/'run',*args.interval),
                gl=compare_completed_frames(work/'coherent/run/gl-snap',run/'run/gl-snap',frames,True))
            if item['streaming']['admission_override']!=limit or item['streaming']['frames']!=list(args.interval):
                raise ValueError('incomplete or mismatched admission trace')
            if name=='admit160-repeat':
                item['repeat_gl']=compare_completed_frames(work/'admit160/run/gl-snap',run/'run/gl-snap',frames,True)
                item['repeat_traces']=all(sha256_file(work/'admit160/run'/n)==sha256_file(run/'run'/n)
                    for n in ('exotica-frustum.csv','exotica-streaming.csv'))
                if not item['repeat_gl']['passed'] or not item['repeat_traces']:raise ValueError('admission candidate did not repeat')
            write_json(work/'report.json',report);print(name,item['streaming']['admitted'],'admissions;',item['gl']['different_frames'],'changed GL',flush=True)
        report['completed']=True
    except (OSError,ValueError,KeyError) as error:report['error']=str(error)
    write_json(work/'report.json',report);return 0 if report['completed'] else 1


if __name__=='__main__':raise SystemExit(main())
