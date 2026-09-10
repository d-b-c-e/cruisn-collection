"""Verify bounded Exotica2.4 transforms and actual ordinary model emissions.

Private captures are required; no ROM/model data is distributed. This verifies
camera/rotation math, matrix-cache decisions, scaled command words and model LOD
selection. It does not verify Zeus model contents, rasterization or future scenery.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import subprocess
import sys

from exotica_transform import prepare, packet, select_model, matrix_update, words
from scenery_c31 import signed
from verification import sha256_file, write_json


def read_rows(path):
    rows=[]
    with Path(path).open(encoding='utf-8') as stream:
        for line in stream:
            if len(line)>16000 or len(rows)>=65536:
                raise ValueError('Exotica capture budget exceeded')
            rows.append(json.loads(line))
    if not rows:
        raise ValueError('empty Exotica capture')
    return rows


def check_row(r, emission):
    for key,size in [('object_words',32),('rotation',9),('view',9),('camera',3),('alternate',9),
                     ('translation',3),('prepared',9),('primary',5),('metadata',5),('preceding',16)]:
        words(r[key],size)
    for key in ('id','frame','native_frame','pc','object','flags','descriptor','selected',
                'ring','scale','matrix_update','previous_alpha','matrix_cursor'):
        words([r[key]],1)
    if (r['schema']!=1 or r['pc']!=0x6964 or r['frame']-r['native_frame'] not in (0,1) or
            not 1800<=r['frame']<=16000 or not math.isfinite(r['time']) or r['time']<0 or
            not 0x1000<=r['object']<=0x40000-0x94 or not 0x30000<=r['ring']<0x32000 or
            r['object_words'][17]!=r['descriptor']):
        raise ValueError('invalid Exotica call identity')
    o=r['object_words'];flags=r['flags']
    p=prepare(o[1:4],r['camera'],r['view'],r['rotation'],r['alternate'],flags)
    update=matrix_update(flags,r['previous_alpha'],o[22])
    expected=packet(p,r['scale'],update)
    if (update!=r['matrix_update'] or p['translation']!=r['translation'] or p['depth']!=signed(o[20]) or
            expected!=r['preceding'][-len(expected):]):
        raise ValueError('Exotica transform/cache/command mismatch')
    chosen=select_model(r['descriptor'],r['primary'][0],p['depth'])
    if chosen!=r['selected'] or (chosen==r['descriptor'] and r['metadata']!=r['primary']):
        raise ValueError('Exotica model selection mismatch')
    special=bool(flags&0x80)
    if special:
        if emission is not None:
            raise ValueError('special Exotica branch emitted ordinary command')
    else:
        if emission is None:
            raise ValueError('missing Exotica model emission')
        e=emission
        if (e['pc']!=0x6970 or e['id']!=r['id'] or e['frame']!=r['frame'] or
                e['native_frame']-r['native_frame'] not in (0,1) or
                e['frame']-e['native_frame'] not in (0,1) or e['object']!=r['object'] or
                not math.isfinite(e['time']) or e['time']<r['time'] or
                e['selected']!=chosen or e['ring']!=0x30000+(r['ring']-0x30000+2)%0x2000 or
                e['packet']!=[0x24860000|r['metadata'][4],r['metadata'][3]]):
            raise ValueError('Exotica actual model packet mismatch')
    native_input=[r['id'],flags,r['scale'],r['previous_alpha'],o[22],r['descriptor'],r['primary'][0],
                  *o[1:4],*r['camera'],*r['view'],*r['rotation'],*r['alternate']]
    native_output=[r['id'],p['depth'],chosen,*p['translation'],*p['matrix'],len(expected),*expected]
    return native_input,native_output,special


def verify(directory,native=None):
    directory=Path(directory)
    capture=json.loads((directory/'exotica-model-capture.json').read_text())
    rows=read_rows(directory/'exotica-models.jsonl')
    emissions=read_rows(directory/'exotica-emissions.jsonl')
    if (capture['complete'] is not True or capture['calls']!=len(rows) or
            capture['emissions']!=len(emissions) or
            [r['id'] for r in rows]!=list(range(1,len(rows)+1)) or
            any(b['frame']<a['frame'] or b['time']<a['time'] for a,b in zip(rows,rows[1:]))):
        raise ValueError('incomplete or unordered Exotica capture')
    emit={r['id']:r for r in emissions}
    if len(emit)!=len(emissions) or list(emit)!=sorted(emit) or not set(emit)<=set(range(1,len(rows)+1)):
        raise ValueError('duplicate/unowned Exotica emission')
    frames=sorted(set(r['frame'] for r in rows))
    if (len(frames)!=capture['window_frames'] or frames[0]!=capture['first'] or frames[-1]!=capture['last']):
        raise ValueError('missing Exotica window coverage')
    inputs=[];outputs=[];special=0
    for r in rows:
        try:
            i,o,s=check_row(r,emit.get(r['id']))
        except ValueError as error:
            raise ValueError(f'call{r["id"]}: {error}') from error
        inputs.append(i);outputs.append(o);special+=s
    if native:
        data='\n'.join(' '.join(map(str,r)) for r in inputs)+'\n'
        result=subprocess.run([str(Path(native).resolve())],input=data,text=True,capture_output=True,timeout=120)
        if result.returncode:
            raise ValueError(f'native Exotica analyzer exit{result.returncode}: {result.stderr[:1000]}')
        actual=[list(map(int,line.split())) for line in result.stdout.splitlines()]
        if actual!=outputs:
            mismatch=next((i+1 for i,(a,b) in enumerate(zip(actual,outputs)) if a!=b),None)
            raise ValueError(f'native Exotica transform mismatch at{mismatch}; rows{len(actual)}/{len(outputs)}')
    return {'schema':1,'passed':True,'scope':__doc__.strip(),'calls':len(rows),'ordinary_emissions':len(emissions),
            'special_transforms_only':special,'frames':len(frames),'first':frames[0],'last':frames[-1],
            'models':len(set(r['selected'] for r in rows if not r['flags']&0x80)),
            'objects':len(set(r['object'] for r in rows)),
            'modes':dict(Counter(r['flags']&3 for r in rows)),
            'matrix_updates':sum(r['matrix_update'] for r in rows),
            'native_frame_offsets':dict(Counter(r['frame']-r['native_frame'] for r in rows)),
            'emissions_crossing_native_frame':sum(e['native_frame']!=rows[e['id']-1]['native_frame'] for e in emissions),
            'far_model_selections':sum(r['selected']!=r['descriptor'] for r in rows if not r['flags']&0x80),
            'native_verified':bool(native),'native_sha256':sha256_file(native) if native else None,
            'sources':{name:sha256_file(directory/name) for name in
                ('exotica-model-capture.json','exotica-models.jsonl','exotica-emissions.jsonl')}}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--native',type=Path)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args(argv)
    try:result=verify(args.directory,args.native)
    except (ValueError,KeyError,TypeError,OSError,subprocess.TimeoutExpired) as error:
        result={'schema':1,'passed':False,'error':str(error)}
    write_json(args.report,result);print('PASS' if result['passed'] else 'FAIL',args.report)
    return 0 if result['passed'] else 1


if __name__=='__main__':sys.exit(main())
