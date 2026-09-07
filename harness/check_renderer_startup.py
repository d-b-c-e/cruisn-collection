"""Repeated full-window renderer boots with completed GL evidence and physical FFB off.

Uses four existing local recordings, forces scale4/CRT on, and retains their
recorded game patches. This is startup stress, not complete release gameplay.
Every repeat must preserve native replay and match the first repeat's GL pixels.
"""
import argparse
import json
from pathlib import Path
import sys

from diagnostic_runtime import ROOT, new_run
from gl_frames import compare_completed_frames, requested_frames
from release_identity import source_identity
from run_regressions import visual_content
from graphics_options import VUNIT_HEIGHT, family
from verification import sha256_file, write_json
import replay

CASE_IDS = ('usa-widescreen','world24-germany','offroad','exotica')


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--repeats',type=int,default=3)
    ap.add_argument('--only',choices=CASE_IDS,nargs='+',help='diagnostic subset, never reported as full coverage')
    ap.add_argument('--small-window',action='store_true',help='diagnostic reduced-output variant')
    args=ap.parse_args(argv)
    if not 1 <= args.repeats <= 20:ap.error('repeats must be 1..20')
    suite_path=ROOT/'fixtures/regressions/collection.json'
    suite=json.loads(suite_path.read_text(encoding='utf-8'))
    cases={row['id']:ROOT/row['path'] for row in suite['cases']}
    out=new_run('renderer-startup',args.output)
    report={'passed':False,'physical_force':False,'scope':__doc__,
            'candidate_sha256':sha256_file(args.candidate),'source_identity':source_identity(ROOT)['sha256'],
            'suite_sha256':sha256_file(suite_path),'repeats':args.repeats,
            'subset':args.only,'small_window':args.small_window,'cases':[]}
    expected=requested_frames(1700,1800,50)
    for name in args.only or CASE_IDS:
        for iteration in range(args.repeats):
            work=out/f'{name}-{iteration+1}'
            options=['--small-window'] if args.small_window else []
            rom=json.loads((cases[name]/'case.json').read_text(encoding='utf-8'))['rom']
            if rom != 'crusnexo':options+=['--gl-height',str(VUNIT_HEIGHT.get(family(rom),400))]
            code=replay.main([str(cases[name]),'--candidate',str(args.candidate),'--output',str(work),
                '--until-frame','1804','--gl-capture','1700:1800','--gl-every','50','--gl-max','3',
                '--gl-scale','4','--gl-crt','on','--timeout','180',*options])
            row={'id':name,'iteration':iteration+1,'passed':False,'replay_exit':code,
                 'report':str(work/'report.json')}
            try:
                row['visual_content']=visual_content(work/'run/gl-snap')
                row['repeat_gl']=compare_completed_frames(out/f'{name}-1/run/gl-snap',work/'run/gl-snap',expected)
                row['passed']=code==0 and row['repeat_gl']['passed']
            except (OSError,ValueError,KeyError) as error:row['error']=str(error)
            report['cases'].append(row);write_json(out/'report.json',report)
            print(name,iteration+1,'PASS' if row['passed'] else 'FAIL',flush=True)
    report['passed']=all(row['passed'] for row in report['cases'])
    report['full_coverage']=not args.only and not args.small_window and args.repeats>=3
    write_json(out/'report.json',report)
    return 0 if report['passed'] else 1


if __name__=='__main__':sys.exit(main())
