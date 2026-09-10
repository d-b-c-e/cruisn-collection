"""Verify Exotica's private CPU-side state packets against actual ring commands.

Includes complete setup, transform and three before/after CPU caches. Hardware
state inheritance, palette colors and WaveRAM readiness require separate checks.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from exotica_state import setup,operands
from exotica_transform import prepare,packet,matrix_update,words
from verify_exotica_transforms import verify as verify_transforms,read_rows
from verification import sha256_file,write_json

BRANCHES=('cached','light','fade','flag400','flag200','default')


def check(row):
    args=operands(row);result=setup(*args)
    o=row['object_words']
    transformed=prepare(o[1:4],row['camera'],row['view'],row['rotation'],row['alternate'],row['flags'])
    expected=result['packet']+packet(transformed,row['scale'],matrix_update(row['flags'],row['previous_alpha'],o[22]))
    actual=words(row['state_packet'],len(row['state_packet']))
    if not 4<=len(actual)<=128 or actual!=expected or words(row['state_after'],3)!=result['cache']:
        raise ValueError('Exotica setup packet/cache mismatch')
    obj,flags,cache,constants,commands,programs,bodies,defaults,palette_setup=args
    input_row=[row['id'],flags,palette_setup,*obj,*cache,*constants,*commands,*programs,
               *(w for body in bodies for w in body),len(defaults),*defaults]
    output_row=[row['id'],BRANCHES.index(result['branch']),result['program'],*result['cache'],
                len(result['packet']),*result['packet']]
    return result,input_row,output_row


def verify(directory,native=None):
    directory=Path(directory)
    receipt=json.loads((directory/'exotica-model-capture.json').read_text())
    if receipt.get('state_capture') is not True:raise ValueError('missing Exotica state capture mode')
    transforms=verify_transforms(directory)
    rows=read_rows(directory/'exotica-models.jsonl')
    branches=Counter();programs=Counter();inputs=[];outputs=[];palette_updates=0
    for row in rows:
        try:r,i,o=check(row)
        except (ValueError,KeyError,TypeError) as error:raise ValueError(f'call{row["id"]}: {error}') from error
        branches[r['branch']]+=1;programs[r['program']]+=1
        palette_updates+=r['cache'][0]!=row['state_cache'][0];inputs.append(i);outputs.append(o)
    if native:
        result=subprocess.run([str(Path(native).resolve())],input='\n'.join(' '.join(map(str,r)) for r in inputs)+'\n',
                              capture_output=True,text=True,timeout=120)
        if result.returncode:raise ValueError(f'native Exotica state exit{result.returncode}: {result.stderr[:1000]}')
        actual=[list(map(int,line.split())) for line in result.stdout.splitlines()]
        if actual!=outputs:raise ValueError('native Exotica setup/cache mismatch')
    return dict(schema=1,passed=True,scope=__doc__.strip(),calls=len(rows),branches=dict(branches),
                programs=dict(programs),palette_updates=palette_updates,transforms=transforms,
                native_verified=bool(native),native_sha256=sha256_file(native) if native else None,
                sources={name:sha256_file(directory/name) for name in
                         ('exotica-model-capture.json','exotica-models.jsonl','exotica-emissions.jsonl')})


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    parser.add_argument('--native',type=Path);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args(argv)
    try:result=verify(args.directory,args.native)
    except (ValueError,KeyError,TypeError,OSError,subprocess.TimeoutExpired) as error:
        result=dict(schema=1,passed=False,error=str(error))
    write_json(args.report,result);print('PASS' if result['passed'] else 'FAIL',args.report)
    return 0 if result['passed'] else 1


if __name__=='__main__':sys.exit(main())
