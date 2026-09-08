"""Bounded Exotica global far trials; independent CPU decisions and completed pixels."""
import argparse,json
from pathlib import Path
from analyze_exotica_frustum import summarize
from compare_exotica_distance import compare as compare_poses
from analyze_session import summarize as timing
from diagnostic_runtime import new_run
from gl_frames import requested_frames,compare_completed_frames
from run_usa_distance_trials import interval
from run_exotica_visibility_trials import probe_source
from verification import sha256_file,write_json
import replay

TRIALS={'stock':(0,0,204800),'coherent':(1,88,204800),'far2':(1,88,409600),
        'far3':(1,88,614400),'far2-repeat':(1,88,409600)}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('case',type=Path)
    ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--interval',type=interval,default=(4500,5990));ap.add_argument('--gl-every',type=int,default=100)
    ap.add_argument('--trials',nargs='+',choices=TRIALS,default=list(TRIALS));ap.add_argument('--timeout',type=float,default=360)
    args=ap.parse_args()
    if args.trials[0]!='stock' or len(args.trials)!=len(set(args.trials)):ap.error('unique trials must start with stock')
    if 'far2-repeat' in args.trials and ('far2' not in args.trials or args.trials.index('far2')>args.trials.index('far2-repeat')):
        ap.error('far2 must precede far2-repeat')
    work=new_run('exotica-distance-trials',args.output)
    report=dict(completed=False,scope=__doc__,physical_force=False,candidate_sha256=sha256_file(args.candidate),
                case_sha256=sha256_file(args.case/'case.json'),trials=[])
    try:
        manifest=json.loads((args.case/'case.json').read_text());stop=manifest['evidence']['frames']
        if manifest['rom']!='crusnexo' or args.interval[1]+2>=stop:raise ValueError('Exotica2.4 recording must cover the trial drain interval')
        frames=requested_frames(*args.interval,args.gl_every)
        for name in args.trials:
            reciprocal,margin,far=TRIALS[name];run=work/name;probe=work/(name+'.lua')
            probe.write_text(probe_source(*args.interval,reciprocal,margin,far),encoding='utf-8')
            rc=replay.main([str(args.case),'--candidate',str(args.candidate),'--output',str(run),'--probe-script',str(probe),
                '--exotica-visibility','off','--small-window','--timeout',str(args.timeout),
                '--gl-capture',f'{args.interval[0]}:{args.interval[1]}','--gl-every',str(args.gl_every),'--gl-max',str(len(frames))])
            r=json.loads((run/'report.json').read_text())
            item=dict(name=name,probe_sha256=sha256_file(probe),original_identity_exit=rc,error=r.get('error'),comparison=r.get('comparison'))
            report['trials'].append(item)
            if item['error']:raise ValueError(f'{name}: {item["error"]}')
            item['frustum']=summarize(run/'run/exotica-frustum.csv')
            expected=dict(reciprocal=reciprocal,margin=margin)
            if far!=204800:expected['far']=far
            if item['frustum']['frames']!=list(args.interval) or item['frustum']['trial']!=expected:
                raise ValueError('incomplete/mismatched far trial')
            item['timing']=timing(run/'run',*args.interval)
            item['gl_stock']=compare_completed_frames(work/'stock/run/gl-snap',run/'run/gl-snap',frames,True)
            if name in ('far2','far3','far2-repeat') and (work/'coherent/run/gl-snap').is_dir():
                item['gl_coherent']=compare_completed_frames(work/'coherent/run/gl-snap',run/'run/gl-snap',frames,True)
                item['pose_coherent']=compare_poses(work/'coherent/run/exotica-frustum.csv',run/'run/exotica-frustum.csv')
            if item['comparison']['input_or_time_mismatches']:raise ValueError('original input/frame-time mismatch')
            if name=='stock' and rc:raise ValueError('stock identity control failed')
            if name=='far2-repeat':
                item['repeat_gl']=compare_completed_frames(work/'far2/run/gl-snap',run/'run/gl-snap',frames,True)
                item['repeat_trace']=sha256_file(work/'far2/run/exotica-frustum.csv')==sha256_file(run/'run/exotica-frustum.csv')
                if not item['repeat_gl']['passed'] or not item['repeat_trace']:raise ValueError('far2 candidate did not repeat')
            write_json(work/'report.json',report)
            print(name,item['frustum']['actual_reasons'],'emulation',item['timing']['emulation_ratio'],flush=True)
        report['completed']=True
    except (OSError,ValueError,KeyError) as error:report['error']=str(error)
    write_json(work/'report.json',report)
    return 0 if report['completed'] else 1


if __name__=='__main__':raise SystemExit(main())
