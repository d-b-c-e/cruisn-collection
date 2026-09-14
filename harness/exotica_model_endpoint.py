"""Explicit read-only original-model owner/endpoint observation, never a fade toggle."""
import csv
import math
from pathlib import Path
import re
import struct

FIELDS = ('id','commit_frame','commit_time','device_frame','device_time','epoch',
          'generation','slot','realm','section','source','end','opcode','base',
          'flags','packed','status','quads','changed','snapshot')
KEY = 'MIDZ_MODEL_ENDPOINT'
BOUNDS = ('first','last','snapshot')


def add_arguments(parser):
    parser.add_argument('--exotica-model-endpoint', choices=('off','observe','draw'))
    parser.add_argument('--exotica-early-visibility', choices=('off','endpoint'),
                        help='bounded private early visibility with original-state margin composition')
    parser.add_argument('--exotica-endpoint-admit-from',type=int,
                        help='observe actual private future/waiting admissions from this native frame')
    for name in BOUNDS:
        parser.add_argument('--exotica-endpoint-'+name, type=int,
                            help='bounded original-model diagnostic native frame')


def configure(args, rom, settings, lifetime, scene=None):
    mode = getattr(args,'exotica_model_endpoint',None)
    bounds = [getattr(args,'exotica_endpoint_'+k,None) for k in BOUNDS]
    admit=getattr(args,'exotica_endpoint_admit_from',None)
    early=getattr(args,'exotica_early_visibility',None)
    if early is None and settings.get('MIDZ_ENDPOINT_EARLY','0')!='0':
        raise ValueError('early visibility cannot be inherited from a recording')
    if early is not None:
        if not getattr(args,'candidate',None) or (early=='endpoint' and mode!='draw'):
            raise ValueError('early visibility requires explicit candidate and endpoint drawing')
        settings['MIDZ_ENDPOINT_EARLY']='1' if early=='endpoint' else '0'
    if mode is None:
        if any(v is not None for v in bounds) or admit is not None:
            raise ValueError('endpoint bounds require an explicit mode')
        if settings.get(KEY,'0') != '0' or any(KEY+'_'+k.upper() in settings for k in BOUNDS) or 'MIDZ_MODEL_ADMIT_FIRST' in settings:
            raise ValueError('endpoint observation cannot be inherited from a recording')
        return None
    if not getattr(args,'candidate',None):
        raise ValueError('endpoint observation requires an explicit candidate')
    if mode == 'off':
        if any(v is not None for v in bounds) or admit is not None:raise ValueError('disabled endpoint bounds')
        settings[KEY]='0'
        for k in BOUNDS:settings.pop(KEY+'_'+k.upper(),None)
        settings.pop('MIDZ_MODEL_ADMIT_FIRST',None)
        return dict(mode='off')
    first,last,snapshot=bounds
    if (mode not in ('observe','draw') or rom!='crusnexo' or not lifetime or lifetime['mode']!='observe'
            or any(v is None for v in bounds) or not 1800<=first<=snapshot<=last<=15998
            or last-first>120 or not lifetime['first']<first<=last<lifetime['last']):
        raise ValueError('endpoint interval requires surrounding Exotica lifetimes')
    # Replay is device-free; make this boundary explicit before prepare_run too.
    if admit is not None:
        if (not scene or scene.get('future')!=2 or not scene.get('materials')
                or not scene['first']<=admit<=first or scene['last']<last):
            raise ValueError('endpoint admissions require covered actual private drawing')
    if mode=='draw' and admit is None:raise ValueError('private endpoint drawing requires actual admission observation')
    if early=='endpoint' and (not scene or not scene.get('compose') or scene.get('active')!=2):
        raise ValueError('early visibility requires composed private margins')
    settings.update({KEY:'2' if mode=='draw' else '1','MIDV_FFB':'0',**{KEY+'_'+k.upper():str(v) for k,v in zip(BOUNDS,bounds)}})
    trial=dict(mode=mode,**dict(zip(BOUNDS,bounds)))
    if early is not None:trial['early']=early
    if admit is not None:settings['MIDZ_MODEL_ADMIT_FIRST']=str(admit);trial['admit_from']=admit
    else:settings.pop('MIDZ_MODEL_ADMIT_FIRST',None)
    return trial


def verify_receipt(trial, text, directory):
    directory=Path(directory);paths=list(directory.glob('exotica-endpoint-*'))
    enabled=bool(trial and trial.get('early')=='endpoint')
    early=re.findall(r'^MIDZ_ENDPOINT_EARLY=([01])$',text,re.M)
    if enabled and early!=['1']:raise ValueError('missing early visibility receipt')
    if not enabled and '1' in early:raise ValueError('unexpected early visibility')
    if not trial or trial['mode']=='off':
        if re.search(r'MIDZ_MODEL_ENDPOINT=[12]',text) or 'MIDZ_MODEL_ENDPOINT_RESULT' in text or 'MIDZ_ENDPOINT_GPU_RESULT' in text or paths or list(directory.glob('exotica-admission-*')):
            raise ValueError('disabled endpoint observer ran')
        return None
    mode='2' if trial['mode']=='draw' else '1'
    if re.findall(r'^MIDZ_MODEL_ENDPOINT='+mode+r' first=(\d+) last=(\d+) snapshot=(\d+)$',text,re.M)!=[
            tuple(str(trial[k]) for k in BOUNDS)]:raise ValueError('endpoint start receipt')
    names=('complete','commits','consumed','untracked','prepared','rejected','snapshots','bytes','remaining')
    final=re.findall(r'^MIDZ_MODEL_ENDPOINT_RESULT '+' '.join(n+r'=(\d+)' for n in names)+r'$',text,re.M)
    if len(final)!=1:raise ValueError('endpoint completion receipt')
    totals=dict(zip(names,map(int,final[0])))
    if (totals['complete']!=1 or totals['remaining'] or not 0<totals['commits']<=65536
            or totals['commits']!=totals['consumed'] or totals['snapshots']>1024
            or totals['bytes']>64*1024*1024):raise ValueError('incomplete endpoint observation')
    path=directory/'exotica-endpoint-models.csv'
    if not path.is_file() or path.stat().st_size>64*1024*1024:raise ValueError('endpoint journal size')
    with path.open(newline='') as stream:
        reader=csv.DictReader(stream)
        if tuple(reader.fieldnames or ())!=FIELDS:raise ValueError('endpoint journal schema')
        rows=[]
        for row in reader:
            if len(rows)>=65536 or set(row)!=set(FIELDS):raise ValueError('endpoint row extent')
            r={}
            for k in FIELDS:
                if k in ('commit_time','device_time'):
                    r[k]=float(row[k])
                    if not math.isfinite(r[k]):raise ValueError('endpoint nonfinite time')
                else:
                    if not re.fullmatch('[0-9]+',row[k] or ''):raise ValueError('endpoint integer')
                    r[k]=int(row[k])
                    if r[k]>(2**64-1 if k in ('epoch','generation','realm') else 2**32-1):
                        raise ValueError('endpoint integer width')
            rows.append(r)
    if len(rows)!=totals['consumed']:raise ValueError('endpoint journal count')
    expected={path.name,'exotica-endpoint-inputs.txt'};saved=[];size=0;prior_time=0.;prior_frame=0
    if 'admit_from' in trial:expected.add('exotica-endpoint-admissions.csv')
    if trial['mode']=='draw':expected.add('exotica-endpoint-gpu.csv')
    for i,r in enumerate(rows,1):
        if (r['id']!=i or not trial['first']<=r['commit_frame']<=trial['last']
                or not r['commit_frame']<=r['device_frame']<=trial['last']+4
                or not 0<=r['commit_time']<=r['device_time']<=r['commit_time']+.05
                or r['device_time']<prior_time or r['device_frame']<prior_frame
                or not all(r[k] for k in ('epoch','generation','realm','section','source','base'))
                or not 0x1000<=r['slot']<=0x40000-31
                or not (r['slot']+31<=0x30000 or r['slot']>=0x32000)
                or not 0x30000<=r['end']<0x32000 or r['opcode']>>16!=0x2486
                or r['opcode']&65535>0xc800 or r['status'] not in (0,1,2)
                or bool(r['flags']&0x04000000)!=(r['status']!=0)
                or not 0<=r['changed']<=r['quads']<=131072
                or (r['status']!=1 and (r['quads'] or r['changed']))
                or r['snapshot']!=int(r['device_frame']==trial['snapshot'] and r['status']!=0)):
            raise ValueError('endpoint owner/command/time/status contract')
        prior_time=r['device_time'];prior_frame=r['device_frame']
        if r['snapshot']:
            saved.append(r)
            if r['status']==1:
                pair=[]
                for kind in ('original','endpoint'):
                    name=f'exotica-endpoint-{i}-{kind}.bin';expected.add(name);p=directory/name
                    if not p.is_file() or p.stat().st_size!=260*r['quads']:raise ValueError('endpoint quad extent')
                    pair.append(p.read_bytes());size+=p.stat().st_size
                a,b=pair
                for j in range(0,len(a),260):
                    x,y=struct.unpack_from('<17I',a,j),struct.unpack_from('<17I',b,j)
                    if (a[j+68:j+260]!=b[j+68:j+260] or (x[9]^y[9])&~18
                            or any(x[k]!=y[k] for k in range(17) if k not in (7,8,9,10))):
                        raise ValueError('endpoint changed geometry or unrelated draw state')
                if sum(a[j:j+260]!=b[j:j+260] for j in range(0,len(a),260))!=r['changed']:
                    raise ValueError('endpoint changed-quad count')
    inputs=directory/'exotica-endpoint-inputs.txt'
    if not inputs.is_file() or inputs.stat().st_size>64*1024*1024:raise ValueError('endpoint input extent')
    lines=inputs.read_text().splitlines()
    if len(lines)!=len(saved):raise ValueError('endpoint snapshot input count')
    for line,r in zip(lines,saved):
        if not re.fullmatch(r'[0-9 ]+',line):raise ValueError('endpoint operand tokens')
        v=list(map(int,line.split()))
        if (len(v)<352 or any(w>0xffffffff for w in v)
                or v[:4]!=[r['id'],r['device_frame'],r['base'],r['opcode']&65535]
                or v[235]!=r['flags'] or v[253]!=r['packed']):
            raise ValueError('endpoint snapshot identity')
        # Fixed context/setup words, followed by counted defaults and model words.
        n=v[350]
        if not 1<=n<=16 or len(v)!=351+n+2*((r['opcode']&65535)+1):
            raise ValueError('endpoint snapshot counted operands')
    if ({p.name for p in paths}!=expected or len(saved)!=totals['snapshots'] or size!=totals['bytes']
            or sum(r['status']==1 for r in rows)!=totals['prepared']
            or sum(r['status']==2 for r in rows)!=totals['rejected']):raise ValueError('endpoint totals/artifacts')
    from exotica_admissions import verify as verify_admissions
    admissions=verify_admissions(trial,text,directory,rows)
    drawing=verify_draw(trial,text,directory,rows)
    return dict(passed=True,**totals,admissions=admissions,drawing=drawing,scope='Native owner/endpoint receipts and bounded snapshot structure. '
                      'Independent source joins, actual native quads and temporal visibility require separate checks.')


def verify_draw(trial,text,directory,originals):
    from exotica_admissions import bounded_csv
    directory=Path(directory);path=directory/'exotica-endpoint-gpu.csv'
    if trial['mode']!='draw':
        if path.exists() or 'MIDZ_ENDPOINT_GPU_RESULT' in text:raise ValueError('disabled endpoint private drawing ran')
        return None
    final=re.findall(r'^MIDZ_ENDPOINT_GPU_RESULT complete=(\d+) pairs=(\d+)$',text,re.M)
    if len(final)!=1 or final[0][0]!='1':raise ValueError('endpoint GPU completion')
    q=bounded_csv(directory/'exotica-endpoint-admissions.csv',65536)
    if len(q)!=len(originals):raise ValueError('endpoint GPU admission count')
    expected=[]
    for o,admission in zip(originals,q):
        if int(admission['id'])!=o['id']:raise ValueError('endpoint GPU original/admission order')
        if o['status']==1 and admission['admitted']=='1':
            expected.extend((o['device_frame'],o['id'],i,o['quads']) for i in range(o['quads']))
    rows=bounded_csv(path,131072);actual=[]
    for row in rows:
        if tuple(row)!=('frame','model','index','count') or any(not re.fullmatch('[0-9]+',v) for v in row.values()):
            raise ValueError('endpoint GPU row contract')
        actual.append(tuple(map(int,row.values())))
    if actual!=expected or len(actual)!=int(final[0][1]):raise ValueError('endpoint GPU original quad order/count')
    return dict(passed=True,pairs=len(actual),models=len({p[1] for p in actual}),
                scope='Consumer receipts for exactly one original/private pair per qualified quad; pixel and temporal checks separate.')
