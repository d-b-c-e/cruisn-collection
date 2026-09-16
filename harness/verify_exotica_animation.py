"""Compare captured original animation writes with scalar and compiled helpers.

This qualifies a single update, not allocation generation or earlier drawing.
Raw tables and operands remain in local diagnostic output.
"""
import argparse
import json
from pathlib import Path
import subprocess

from exotica_animation import decode, step, initial_fields
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
    p.add_argument('--initial-fields',action='store_true',help='use a saved original section-allocation capture')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('output already exists')
    try:report=verify_initial(a.run,a.native) if a.initial_fields else verify(a.run,a.native)
    except Exception as e:report=dict(passed=False,error=str(e))
    write_json(a.output,report);print(json.dumps(report));return 0 if report['passed'] else 1


def verify_initial(run,native):
    from exotica_sections import FIELDS
    receipt=json.loads((run/'exotica-section-capture.json').read_text(encoding='utf-8'))
    path=run/'exotica-section-allocations.jsonl'
    if not receipt.get('complete') or path.stat().st_size>64*1024*1024:
        raise ValueError('incomplete or oversized allocation capture')
    rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    if len(rows)!=receipt['allocations'] or not 1<=len(rows)<=10000:
        raise ValueError('allocation count')
    protocol=[];expected=[];tags=set();excluded=0;identities=[]
    # Node24 is an observed input, not independently predicted allocation state.
    fields=[i for i in FIELDS if i!=24]
    for row in rows:
        d=row['definition']
        if not d[0]>>24:continue
        if d[5]&0xf00 in (0xa00,0xb00,0xc00,0xf00):excluded+=1;continue
        s=row['scalars'];node=row['actual'][24]
        context=dict(flags=row['flags'],header=row['list_header'],position=s[11:14],heading=s[14],
                     section_heading=s[15],gap=row['gap'],cursor=s[10],index=s[2]>>8,initial=bool(s[8]))
        materials=[row['override_binding'][3] if row['override_binding'] else row['palette_binding'][3],
                   row['texture_binding'][3]]
        predicted=initial_fields(d,row['model_words'],context,row['matrix'],row['constants'],row['trig'],materials,node)
        if any(predicted[i]!=row['actual'][i] for i in fields):
            raise ValueError(f"original initial-field mismatch at allocation {row['id']}")
        operands=[*d,*row['model_words'],context['flags'],context['gap'],context['cursor'],context['index'],
                  int(context['initial']),*context['header'],*context['position'],context['heading'],
                  context['section_heading'],*row['matrix'],*row['constants'],*row['trig'],*materials,node]
        protocol.append('I '+' '.join(map(str,operands)));expected.append(predicted)
        tags.add(d[0]>>24);identities.append(dict(id=row['id'],frame=row['frame'],source=row['source'],node=node))
    if not expected:raise ValueError('no supported captured animation initializers')
    result=subprocess.run([str(native.resolve())],input='\n'.join(protocol)+'\n',capture_output=True,text=True,timeout=30)
    if result.returncode:raise ValueError('compiled initial fields failed: '+result.stderr[:2000])
    actual=[list(map(int,line.split())) for line in result.stdout.splitlines()]
    if actual!=expected:raise ValueError('compiled initial fields differ from independent reconstruction')
    return dict(passed=True,allocations=len(expected),excluded_tagged_custom=excluded,tags=sorted(tags),
                independently_compared_fields=fields,identities=identities,
                operands_sha256=sha256_file(path),native_sha256=sha256_file(native),
                scope='initial render fields; supplied observed node, no allocation/phase/residency/admission proof')


if __name__=='__main__':raise SystemExit(main())
