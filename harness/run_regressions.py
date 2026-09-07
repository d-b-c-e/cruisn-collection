"""Run the local multi-game recording suite serially with physical outputs off.

Cases and ROMs stay local. Missing fixtures fail the requested suite; they are
never silently skipped. Timings describe emulation callbacks, not GPU latency.
"""
import argparse
import json
from pathlib import Path
import sys
from PIL import Image
from analyze_session import summarize
from diagnostic_runtime import ROOT, new_run
from verification import write_json, sha256_file
import replay
from analyze_drivetrain import analyze as analyze_drivetrain
from analyze_force_gate import analyze as analyze_force_gate
from release_identity import source_identity


def visual_content(directory):
    files=sorted(directory.glob('*.bmp')) or sorted(directory.glob('*.png'))
    if not files: raise ValueError('no visual evidence')
    # Only a basic false-oracle check, not a judgement of image correctness.
    with Image.open(files[-1]) as image:
        extrema=image.convert('RGB').getextrema()
        if all(lo==hi for lo,hi in extrema):
            raise ValueError('last visual reference is uniform; cannot certify gameplay from a blank framebuffer')
    return {'files':len(files),'last_image':files[-1].name,'last_extrema':extrema}


def validate(plan):
    if plan.get('schema')!=1 or not plan.get('cases'): raise ValueError('nonempty schema-1 suite required')
    names=set()
    for case in plan['cases']:
        name=case['id']
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in name) or name in names:
            raise ValueError('case IDs must be unique local directory names')
        names.add(name)
        if case.get('presentation','recorded') not in ('recorded','headless'): raise ValueError('invalid presentation')
        if case.get('compare_gl') and case.get('presentation')=='headless': raise ValueError('GL comparison cannot be headless')
        for timing in case.get('timings',[]):
            if not 1<=timing['first']<timing['last'] or not 0<timing.get('minimum_ratio',.95)<=1:
                raise ValueError('invalid timing gate')
    return plan


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--suite',type=Path,default=ROOT/'fixtures/regressions/collection.json')
    ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--only',nargs='+',help='explicit subset, retained in the report')
    ap.add_argument('--output');ap.add_argument('--timeout',type=float,default=240)
    args=ap.parse_args(argv)
    plan=validate(json.loads(args.suite.read_text(encoding='utf-8')))
    if args.only and set(args.only)-{c['id'] for c in plan['cases']}:ap.error('unknown --only case')
    work=new_run('regressions',args.output)
    report={'schema':1,'passed':False,'suite_sha256':sha256_file(args.suite),
            'source_identity':source_identity(ROOT)['sha256'],
            'candidate_sha256':sha256_file(args.candidate),'subset':args.only,'physical_force':False,'cases':[]}
    for case in plan['cases']:
        if args.only and case['id'] not in args.only: continue
        item={'id':case['id'],'passed':False,'coverage':case['coverage']}
        try:
            path=ROOT/case['path'];run=work/case['id']
            visual=path/'record'/('gl-snap' if case.get('compare_gl') else 'snap')
            item['visual_reference']=visual_content(visual)
            options=['--headless'] if case.get('presentation')=='headless' else []
            if case.get('compare_gl'):options+=['--compare-gl']
            if case.get('telemetry'):options+=['--telemetry-loopback']
            telemetry=case.get('telemetry',{})
            if telemetry.get('probe'): options+=['--probe-script',str(ROOT/telemetry['probe'])]
            result=replay.main([str(path),'--candidate',str(args.candidate),*options,
                               '--output',str(run),'--timeout',str(args.timeout)])
            item['passed']=result==0
            if case.get('telemetry') and result==0:
                memory=run/'run'/telemetry['memory'] if telemetry.get('memory') else None
                item['telemetry']=analyze_drivetrain(run/'run',memory)
                minimum=case['telemetry'].get('minimum_active_frames',500)
                speed=case['telemetry'].get('minimum_speed_mph',10)
                item['telemetry']['coverage_passed']=(item['telemetry']['game_state_samples']>=minimum and
                    item['telemetry']['wire']['maximum_speed_mph']>=speed)
                item['passed'] &= item['telemetry']['coverage_passed']
                if telemetry.get('force_gate_game'):
                    item['force_gate']=analyze_force_gate(run/'run',memory,telemetry['force_gate_game'])
                    item['passed'] &= item['force_gate']['passed']
            item['report']=str(run/'report.json')
            item['timings']=[]
            for timing in case.get('timings',[]):
                stats=summarize(run/'run',timing['first'],timing['last'])
                stats['minimum_ratio']=timing.get('minimum_ratio',.95)
                stats['passed']=stats['emulation_ratio']>=stats['minimum_ratio']
                item['timings'].append(stats)
                item['passed'] &= stats['passed']
        except (OSError,ValueError,KeyError) as error:
            item['passed']=False
            item['error']=str(error)
        report['cases'].append(item)
        write_json(work/'report.json',report)
        print(case['id'], 'PASS' if item['passed'] else 'FAIL',flush=True)
    report['passed']=bool(report['cases']) and all(c['passed'] for c in report['cases'])
    write_json(work/'report.json',report)
    return 0 if report['passed'] else 1


if __name__=='__main__':sys.exit(main())
