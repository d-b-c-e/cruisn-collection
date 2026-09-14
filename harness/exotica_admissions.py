"""Independent lifecycle/packet-watermark checks for native private admissions."""
import csv
from pathlib import Path
import re
import struct


def bounded_csv(path, limit=200000):
    if not path.is_file() or path.stat().st_size>64*1024*1024:raise ValueError('admission CSV extent')
    with path.open(newline='') as f:
        reader=csv.DictReader(f);rows=[]
        for row in reader:
            if len(rows)>=limit or None in row or any(v is None for v in row.values()):
                raise ValueError('admission CSV row extent')
            rows.append(row)
    return rows


def verify(trial,text,directory,originals):
    directory=Path(directory);binary=directory/'exotica-admission-packets.bin';queries=directory/'exotica-endpoint-admissions.csv'
    if 'admit_from' not in trial:
        if binary.exists() or queries.exists() or 'MIDZ_MODEL_ADMIT_' in text:
            raise ValueError('disabled admission observer ran')
        return None
    if re.findall(r'^MIDZ_MODEL_ADMIT_FIRST=(\d+)$',text,re.M)!=[str(trial['admit_from'])]:
        raise ValueError('admission start receipt')
    final=re.findall(r'^MIDZ_MODEL_ADMIT_RESULT complete=(\d+) packets=(\d+) bytes=(\d+)$',text,re.M)
    if len(final)!=1:raise ValueError('admission completion receipt')
    complete,total,size=map(int,final[0])
    if (complete!=1 or not 0<total<=20000 or not binary.is_file()
            or binary.stat().st_size!=size or not 72<=size<=64*1024*1024):raise ValueError('admission completion/extent')
    packets=[]
    with binary.open('rb') as f:
        for index in range(1,total+1):
            head=f.read(72)
            if len(head)!=72:raise ValueError('admission truncated header')
            magic,sequence,scene,frame,epoch,realm,n,records,waiting=struct.unpack('<9Q',head)
            if (magic!=0x31444158 or sequence!=index or not scene or not epoch or n>32768 or waiting not in (0,1)
                    or not trial['admit_from']<=frame<=trial['last'] or not records or (n and not realm)):
                raise ValueError('admission packet header')
            data=f.read(n*12)
            if len(data)!=n*12:raise ValueError('admission truncated sources')
            draws=list(struct.iter_unpack('<3I',data))
            if len({d[:2] for d in draws})!=n or any(not a or not b or not 0<q<=131072 for a,b,q in draws):
                raise ValueError('admission empty/duplicate draw claim')
            packets.append(dict(sequence=sequence,scene=scene,frame=frame,epoch=epoch,realm=realm,records=records,waiting=waiting,draws=draws))
        if f.read(1):raise ValueError('admission trailing bytes')
    fields=('id','admitted','first_sequence','first_frame','last_sequence','last_frame','packets','records')
    qrows=bounded_csv(queries,65536)
    if len(qrows)!=len(originals):raise ValueError('admission query count')
    for q in qrows:
        if tuple(q)!=fields or any(not re.fullmatch('[0-9]+',v) for v in q.values()):
            raise ValueError('admission query schema/integers')
    life=bounded_csv(directory/'exotica-lifetime-events.csv')
    future={int(e['scene']):e for e in bounded_csv(directory/'exotica-future-gpu.csv',20000)}
    waiting_path=directory/'exotica-waiting-draw-gpu.csv'
    waiting={int(e['scene']):e for e in bounded_csv(waiting_path,20000)} if waiting_path.exists() else {}
    fences={int(e['scene']):e for e in bounded_csv(directory/'exotica-host-fences.csv',20000)} if waiting else {}
    combined=[({k:int(v) for k,v in q.items()},o,False) for q,o in zip(qrows,originals)]
    def ordered(rows):
        keys=[(q['packets'],q['records']) for q,o,early in rows]
        if keys!=sorted(keys):raise ValueError('admission query order')
    ordered(combined)
    early_path=directory/'exotica-early-active.csv';early_rows=[]
    if trial.get('early')=='endpoint':
        final_early=re.findall(r'^MIDZ_ENDPOINT_EARLY_RESULT complete=(\d+) scenes=(\d+) permissions=(\d+)$',text,re.M)
        expected_scenes=sum(trial['first']<=int(e['frame'])<=trial['last'] for e in future.values())
        if len(final_early)!=1 or final_early[0][:2]!=('1',str(expected_scenes)) or not expected_scenes:
            raise ValueError('early visibility completion/scene coverage')
        early_fields=('scene','frame','records','packets','slot','epoch','generation','realm','section','source',
                      'first_sequence','first_frame','last_sequence','last_frame')
        handovers={int(e['scene']):e for e in bounded_csv(directory/'exotica-handover-scenes.csv',20000)}
        seen=set()
        for row in bounded_csv(early_path,200000 if trial.get('scope')=='marked' else 65536):
            if tuple(row)!=early_fields or any(not re.fullmatch('[0-9]+',v) for v in row.values()):
                raise ValueError('early visibility permission schema')
            o={k:int(v) for k,v in row.items()};scene=future.get(o['scene']);handover=handovers.get(o['scene'])
            identity=(o['scene'],o['slot'])
            if (not scene or not handover or identity in seen or not trial['first']<=o['frame']<=trial['last']
                    or int(scene['frame'])!=o['frame'] or int(handover['end_records'])!=o['records']):
                raise ValueError('early visibility sealed scene identity')
            seen.add(identity);o['id']=len(early_rows)+1
            q={k:o[k] for k in fields if k!='admitted'};q['admitted']=1
            early_rows.append((q,o,True))
        if len(early_rows)!=int(final_early[0][2]):raise ValueError('early visibility permission count')
        ordered(early_rows)
        combined=sorted(combined+early_rows,key=lambda row:(row[0]['packets'],row[0]['records']))
    elif early_path.exists() or 'MIDZ_ENDPOINT_EARLY_RESULT' in text:
        raise ValueError('disabled early visibility ran')
    live={};by_key={};admitted={};cursor=0;epoch=0;packet_index=0;last_frame=0;yes=0
    def fold(count):
        nonlocal cursor,epoch
        if not cursor<=count<=len(life):raise ValueError('admission lifecycle watermark')
        while cursor<count:
            e=life[cursor];cursor+=1;op=e['event'];slot=int(e['slot'])
            if op in ('L','R'):
                epoch=int(e['epoch']);live.clear();by_key.clear();admitted.clear()
            elif op in ('A','F'):
                old=live.pop(slot,None)
                if old:
                    by_key.pop(old[3:],None)
                    if old[3:] in admitted:
                        if admitted[old[3:]]['owner']!=old:raise ValueError('admission retirement identity')
                        admitted.pop(old[3:])
            elif op=='B':
                h=tuple(int(e[k]) for k in ('slot','epoch','generation','realm','section','source'))
                live[slot]=h;by_key[h[3:]]=h
                if h[3:] in admitted:
                    if admitted[h[3:]]['owner'] is not None:raise ValueError('admission duplicate/missed binding')
                    admitted[h[3:]]['owner']=h
    def advance(limit):
        nonlocal packet_index,last_frame
        if not packet_index<=limit<=len(packets):raise ValueError('admission packet watermark')
        while packet_index<limit:
            p=packets[packet_index];packet_index+=1;fold(p['records'])
            if epoch!=p['epoch'] or p['frame']<last_frame:raise ValueError('admission packet epoch/frame')
            last_frame=p['frame']
            receipts=waiting if p['waiting'] else future;gpu=receipts.get(p['scene'])
            if not gpu or int(gpu['quads'])!=sum(d[2] for d in p['draws']):raise ValueError('admission GPU draw count')
            if p['waiting']:
                if int(fences[p['scene']]['ready_frame'])!=p['frame']:raise ValueError('admission completion frame')
            elif int(gpu['frame'])!=p['frame'] or gpu['mode']!='2':raise ValueError('admission future frame/draw mode')
            for a,b,n in p['draws']:
                key=(p['realm'],a,b);h=by_key.get(key)
                if key not in admitted:admitted[key]=dict(owner=h,first_sequence=p['sequence'],first_frame=p['frame'])
                elif admitted[key]['owner']!=h:raise ValueError('admission missed source lifecycle')
                admitted[key].update(last_sequence=p['sequence'],last_frame=p['frame'])
    for q,o,is_early in combined:
        advance(q['packets']);fold(q['records'])
        h=tuple(o[k] for k in ('slot','epoch','generation','realm','section','source'))
        if q['id']!=o['id'] or live.get(h[0])!=h:raise ValueError('admission original owner join')
        state=admitted.get(h[3:]);matched=state is not None and state['owner']==h
        if state is not None and not matched:raise ValueError('admission stale query owner')
        expected=[state[k] if matched else 0 for k in fields[2:6]]
        if q['admitted']!=int(matched) or [q[k] for k in fields[2:6]]!=expected:
            raise ValueError('admission original qualification differs')
        yes+=matched and not is_early
    advance(len(packets))
    return dict(passed=True,packets=total,bytes=size,queries=len(qrows),admitted=yes,early_permissions=len(early_rows),
                scope='Every recorded admission/query folded against exact lifecycle/packet watermarks and GPU draw counts. '
                      'Individual source/geometry equality requires snapshot checks; no opacity or visibility policy.')
