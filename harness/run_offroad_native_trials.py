"""Run serialized native Off Road trials with independent image, route and timing verdicts."""
import argparse,json
from pathlib import Path
from analyze_offroad_native import summarize as distance
from analyze_session import summarize as timing
from compare_world_motion import compare as motion
from diagnostic_runtime import ROOT,new_run
from gl_frames import compare_completed_frames,requested_frames
from verification import sha256_file,write_json
from run_usa_distance_trials import interval
import replay


def motion_script(first,last):
    if not 1<=first<last or last-first>12000:raise ValueError('invalid motion interval')
    source=(ROOT/'lua/offroad_motion_trace.lua').read_text(encoding='utf-8')
    for name,default,value in [('FIRST',1800,first),('LAST',5990,last)]:
        old=f"os.getenv('CRUISN_MOTION_{name}') or '{default}'"
        if source.count(old)!=1:raise ValueError('Off Road motion probe binding changed')
        source=source.replace(old,str(value))
    return source


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('case',type=Path)
    ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--multipliers',type=int,nargs='+',choices=(1,2,3),default=[1,2,3,2])
    ap.add_argument('--motion',type=interval,default=(1800,5990))
    ap.add_argument('--gl-frames',type=interval,default=(1800,5900));ap.add_argument('--gl-every',type=int,default=100)
    ap.add_argument('--timeout',type=float,default=300);args=ap.parse_args()
    if args.multipliers[0]!=1:ap.error('first multiplier must be observed original (1)')
    work=new_run('offroad-native-trials',args.output)
    report=dict(completed=False,scope=__doc__,physical_force=False,visual_acceptance='not established',
                candidate_sha256=sha256_file(args.candidate),case_sha256=sha256_file(args.case/'case.json'),trials=[])
    try:
        manifest=json.loads((args.case/'case.json').read_text(encoding='utf-8'));stop=manifest['evidence']['frames']
        if manifest['rom']!='offroadc' or args.motion[1]>=stop or args.gl_frames[1]>=stop:
            raise ValueError('Off Road1.63 recording must cover motion and GL intervals')
        frames=requested_frames(*args.gl_frames,args.gl_every);probe=work/'motion.lua'
        probe.write_text(motion_script(*args.motion),encoding='utf-8');report['motion_sha256']=sha256_file(probe)
        previous_trials={}
        for index,multiplier in enumerate(args.multipliers):
            run=work/f'{index}-x{multiplier}'
            rc=replay.main([str(args.case),'--candidate',str(args.candidate),'--output',str(run),
                '--offroad-distance',str(multiplier),'--probe-script',str(probe),'--small-window','--timeout',str(args.timeout),
                '--gl-capture',f'{args.gl_frames[0]}:{args.gl_frames[1]}','--gl-every',str(args.gl_every),'--gl-max',str(len(frames))])
            evidence=json.loads((run/'report.json').read_text(encoding='utf-8'))
            item=dict(name=run.name,original_identity_exit=rc,error=evidence.get('error'),comparison=evidence.get('comparison'))
            report['trials'].append(item)
            if item['error']:raise ValueError(f'{run.name}: {item["error"]}')
            item['native_distance']=distance(run/'run',stop);item['timing']=timing(run/'run',*args.motion)
            item['motion']=motion(work/'0-x1/run',run/'run','offroad')
            item['gl']=compare_completed_frames(work/'0-x1/run/gl-snap',run/'run/gl-snap',frames,True)
            if multiplier in previous_trials:
                previous=previous_trials[multiplier]
                item['repeat']=dict(motion=motion(previous/'run',run/'run','offroad'),
                    gl=compare_completed_frames(previous/'run/gl-snap',run/'run/gl-snap',frames,True),
                    native_logs_equal=all(sha256_file(previous/'run'/n)==sha256_file(run/'run'/n)
                        for n in ('offroad-native.csv','offroad-native-projection.csv')))
                if not (item['repeat']['motion']['passed'] and item['repeat']['gl']['passed'] and item['repeat']['native_logs_equal']):
                    raise ValueError(f'{run.name}: candidate did not repeat')
            previous_trials[multiplier]=run
            write_json(work/'report.json',report)
            print(f'{run.name}: complete; original image identity={rc==0}; camera equal={item["motion"]["camera_equal"]}; '
                  f'emulation={item["timing"]["emulation_ratio"]:.4%}',flush=True)
            if item['comparison']['input_or_time_mismatches']:raise ValueError('frame input/time mismatch')
            if index==0 and rc:raise ValueError('stock adapter changed original replay')
        report['completed']=True
    except (OSError,ValueError,KeyError) as error:report['error']=str(error)
    write_json(work/'report.json',report)
    return 0 if report['completed'] else 1


if __name__=='__main__':raise SystemExit(main())
