"""Validate requested force gating against independent game-state samples.

This checks software requests with physical outputs disabled, not rim torque.
"""
import argparse
import csv
from pathlib import Path

from verification import sha256_file, write_json


def analyze(directory, memory, game):
    directory=Path(directory);memory=Path(memory);path=directory/'force-gate.csv'
    with path.open(encoding='utf-8') as stream: rows=list(csv.DictReader(stream))
    with memory.open(encoding='utf-8') as stream:
        reference={int(r['frame']):r for r in csv.DictReader(stream)}
    if not rows: raise ValueError('empty force gate trace')
    if game not in ('crusnwld24','crusnwld','crusnexo'): raise ValueError('unverified game-state layout')
    matched=0;bad=[];disabled=0;suppressed=0;enabled=0
    for row in rows:
        flag=int(row['enabled']);request=int(row['requested_level'])
        if flag not in (0,1) or abs(request)>32767: raise ValueError('invalid force request')
        if not flag:
            disabled+=1
            if request: raise ValueError('inactive game requested nonzero force')
            if int(row['raw']) not in (0,-128): suppressed+=1
        else: enabled+=1
        sample=reference.get(int(row['frame'])+1)
        if sample is None: continue
        state=int(sample['state']);flags=int(sample['flags'],16)
        expected=(state==1 and flags==1) if game=='crusnexo' else (state==4 and bool(flags&4))
        matched+=1
        if bool(flag)!=expected: bad.append(int(row['frame']))
    if not matched or bad: raise ValueError(f'game-state force gate mismatch: {bad[:12]}, matched {matched}')
    if not enabled or not disabled: raise ValueError('recording must cover inactive and driving states')
    return {'passed':True,'scope':__doc__,'physical_force':False,'game':game,
            'trace_sha256':sha256_file(path),'memory_sha256':sha256_file(memory),
            'source_writes':len(rows),'independent_state_samples':matched,'lua_frame_offset':1,
            'enabled_writes':enabled,'disabled_writes':disabled,'nonzero_raw_suppressed':suppressed}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('directory',type=Path);ap.add_argument('--memory',type=Path,required=True)
    ap.add_argument('--game',required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    try: report=analyze(args.directory,args.memory,args.game)
    except (OSError,ValueError,KeyError) as error: report={'passed':False,'error':str(error)}
    write_json(args.output,report)
    print(('PASS' if report['passed'] else 'FAIL')+f': {args.output}')
    return 0 if report['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
