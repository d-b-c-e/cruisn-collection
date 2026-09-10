"""Compare private Exotica state transitions with consecutive original models.

Object/source/translation/time joins exclude nonordinary calls and unobserved
intervening submissions. Each compared pair starts from the preceding original
context, advances its model-local state, then applies independently reconstructed
CPU setup. Complete registers, transforms and material-load metadata must match.
Palette colors, ucode bytes and WaveRAM readiness are NOT verified here.
"""
import argparse
from collections import defaultdict,Counter
import json
from pathlib import Path
import struct
import subprocess
import sys
from exotica_state import setup,operands
from exotica_transform import prepare,packet,matrix_update
from verify_exotica_state import verify as verify_setup
from verify_exotica_transforms import read_rows
from zeus_state import transition,floating,SCALARS,FLOATS
import zeus_models
from verification import sha256_file,write_json


def floats(row):
    obj=row['object_words']
    p=prepare(obj[1:4],row['camera'],row['view'],row['rotation'],row['alternate'],row['flags'])
    return p,tuple(floating(w) for w in packet(p,row['scale'],0)[1:])


def serialized(ctx):
    return [*[ctx[k] for k in SCALARS],
            *[struct.unpack('<I',struct.pack('<f',v))[0] for k,_ in FLOATS for v in ctx[k]],
            *ctx['regs'],*ctx['render']]


def verify(directory,native=None):
    directory=Path(directory);cpu=verify_setup(directory)
    rows=read_rows(directory/'exotica-models.jsonl')
    source=directory/'zeus-capture';models=zeus_models.parse(source/'models.bin')
    receipt=json.loads((source/'models.json').read_text())
    if (receipt.get('complete') is not True or receipt.get('models')!=len(models) or
            receipt.get('bytes')!=(source/'models.bin').stat().st_size):raise ValueError('incomplete Zeus state journal')
    by_key=defaultdict(list)
    for row in rows:
        if not row['flags']&0x80:
            _,translation=floats(row);by_key[(row['metadata'][3],row['metadata'][4],*translation)].append(row)
    joins=[]
    for model in models:
        key=(model['base'],model['count'],*model['translation'][:3])
        candidates=[r for r in by_key[key] if r['native_frame'] in (model['frame'],model['frame']-1)
                    and 0<=model['time']-r['time']<0.0176]
        if len(candidates)>1:raise ValueError('ambiguous Exotica object/model join')
        joins.append(candidates[0] if candidates else None)
    inputs=[];outputs=[];loads=Counter();pairs=[]
    for index in range(1,len(models)):
        row,prior=joins[index],joins[index-1]
        if row is None or prior is None or row['id']!=prior['id']+1:continue
        p,_=floats(row);state=setup(*operands(row))
        command=state['packet']+packet(p,row['scale'],matrix_update(row['flags'],row['previous_alpha'],row['object_words'][22]))
        previous,actual=models[index-1],models[index]
        result,requests=transition(previous,previous['words'],command,row['metadata'][3])
        if serialized(result)!=serialized(actual):raise ValueError(f'original Zeus state mismatch at model{actual["id"]}')
        for request in requests:loads[request['kind']]+=1
        inputs.append([actual['id'],*serialized(previous),len(previous['words']),*previous['words'],len(command),*command,row['metadata'][3]])
        outputs.append([actual['id'],*serialized(actual),len(requests),*[w for r in requests for w in (r['kind'],r['source'],r['control'])]])
        pairs.append(dict(model=actual['id'],object_call=row['id'],frame=actual['frame']))
    if not pairs:raise ValueError('empty consecutive Zeus state coverage')
    if native:
        run=subprocess.run([str(Path(native).resolve())],input='\n'.join(' '.join(map(str,r)) for r in inputs)+'\n',capture_output=True,text=True,timeout=120)
        if run.returncode:raise ValueError(f'native Zeus state exit{run.returncode}: {run.stderr[:1000]}')
        if [list(map(int,line.split())) for line in run.stdout.splitlines()]!=outputs:raise ValueError('native Zeus state mismatch')
    return dict(schema=1,passed=True,scope=__doc__.strip(),models=len(models),joined=sum(r is not None for r in joins),
        consecutive_contexts=len(pairs),excluded_models=[m['id'] for m,r in zip(models,joins) if r is None],
        material_requests=dict(loads),pairs=pairs,cpu_setup=cpu,native_verified=bool(native),
        native_sha256=sha256_file(native) if native else None,
        sources={p.name:sha256_file(p) for p in (source/'models.bin',source/'models.json')})


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    p.add_argument('--native',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args(argv)
    try:r=verify(a.directory,a.native)
    except (ValueError,KeyError,TypeError,OSError,OverflowError,subprocess.TimeoutExpired) as e:r=dict(schema=1,passed=False,error=str(e))
    write_json(a.report,r);print('PASS' if r['passed'] else 'FAIL',a.report);return 0 if r['passed'] else 1


if __name__=='__main__':sys.exit(main())
