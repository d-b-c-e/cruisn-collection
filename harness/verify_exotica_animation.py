"""Compare captured original animation writes with scalar and compiled helpers.

This qualifies a single update, not allocation generation or earlier drawing.
Raw tables and operands remain in local diagnostic output.
"""
import argparse
import json
from pathlib import Path
import subprocess

from exotica_animation import decode, step
from verification import sha256_file, write_json


def verify(run, native):
    summary=json.loads((run/'exotica-animation-capture.json').read_text(encoding='utf-8'))
    if not summary.get('complete') or summary.get('error'):
        raise ValueError('incomplete original animation capture')
    events_path=run/'exotica-animation-events.jsonl'
    if events_path.stat().st_size>16*1024*1024:
        raise ValueError('animation evidence budget')
    tables={};events=[];protocol=[];expected=[];owners=set();changes=wraps=0
    for line in events_path.read_text(encoding='utf-8').splitlines():
        row=json.loads(line)
        if row['kind']==2:continue  # Bounded raw tap troubleshooting only.
        if row['kind']==0:
            key=row['start'];values=row['values']
            if key in tables or len(tables)>=32:raise ValueError('duplicate table or budget')
            tables[key]=(row['header'],decode(row['header'],values))
            protocol.append('T '+' '.join(map(str,[key,row['header'],len(values),*values])))
        elif row['kind']==1:
            if len(events)>=8192 or row['id']!=len(events)+1:raise ValueError('event order or budget')
            key=row['start'];header,sequence=tables[key]
            if row['header']!=header:raise ValueError('captured node/table header mismatch')
            if not summary['first']<=row['frame']<=summary['last']:raise ValueError('event frame')
            before=(row['before_remaining'],row['before_cursor']-key,row['before_model'])
            after=(row['after_remaining'],row['after_cursor']-key,row['after_model'])
            actual=step(sequence,before)
            if actual!=after:raise ValueError(f"original animation mismatch at event {row['id']}: {actual} != {after}")
            protocol.append('E '+' '.join(map(str,[key,*before])))
            expected.append(after);events.append(row)
            owners.add((row['node'],row['owner'],key))
            changes+=before[2]!=after[2]
            wraps+=before[0]<=1 and before[1]==len(sequence['models'])
        else:raise ValueError('unknown animation record')
    if not events or len(events)!=summary['events'] or len(tables)!=summary['tables']:
        raise ValueError('empty or inconsistent capture counts')
    result=subprocess.run([str(native.resolve())],input='\n'.join(protocol)+'\n',
                          capture_output=True,text=True,timeout=30)
    if result.returncode:raise ValueError('native animation failed: '+result.stderr[:2000])
    observed=[tuple(map(int,line.split())) for line in result.stdout.splitlines()]
    if observed!=expected:raise ValueError('compiled animation differs from original writes')
    return dict(passed=True,events=len(events),tables=len(tables),observed_owner_tuples=len(owners),
                model_changes=changes,wraps=wraps,first_frame=events[0]['frame'],last_frame=events[-1]['frame'],
                events_sha256=sha256_file(events_path),native_sha256=sha256_file(native),
                scope='individual original updates; no lifecycle, scheduling or drawing acceptance')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('--native',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('output already exists')
    try:report=verify(a.run,a.native)
    except Exception as e:report=dict(passed=False,error=str(e))
    write_json(a.output,report);print(json.dumps(report));return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
