"""Explicit allocated-waiting geometry observation; no additional drawing."""
import csv
import math
from pathlib import Path
import re
import struct

import exotica_lifetimes

FIELDS = ('scene','frame','device_time','epoch','sequence','records','historical','unowned','submitted',
          'future','bound_future','bound_future_submitted','candidates','instances','quads','hash','guest_cycles')


def add_arguments(parser):
    parser.add_argument('--exotica-host-waiting', choices=('off','observe'),
                        help='observe allocation-owned waiting scenery without changing future packets or drawing')


def configure(args, rom, settings, scene, lifetime):
    option = getattr(args,'exotica_host_waiting',None)
    if option is not None and not getattr(args,'candidate',None):
        raise ValueError('Exotica waiting requires an explicit candidate')
    value = settings.get('MIDZ_HOST_WAITING','0') if option is None else str(('off','observe').index(option))
    if value not in ('0','1'):
        raise ValueError('invalid recorded Exotica waiting mode')
    if value == '0':
        if option is not None:
            settings['MIDZ_HOST_WAITING']='0'
            return dict(mode='off')
        return None
    if (rom!='crusnexo' or not scene or scene.get('future') not in (1,2) or
            not lifetime or lifetime.get('mode')!='observe' or lifetime['first']!=1799 or
            lifetime['last']<=scene['last']):
        raise ValueError('Exotica waiting requires future mode and lifetime coverage from1799 through hostlast+1')
    # The caller has resolved and validated live GL/private-wide requirements.
    if (settings.get('MIDZ_GL')!='1' or settings.get('MIDZ_DEPTH_MIRROR')!='2' or
            settings.get('MIDZ_HOST_MATERIALS')!='1' or settings.get('MIDZ_HOST_ACTIVE','0')!='0' or
            'MIDZ_DEPTH_STREAM_FRAME' in settings or any(getattr(args,k,False) for k in ('headless','native_renderer','zeus_native'))):
        raise ValueError('Exotica waiting requires live private-wide future mode')
    settings['MIDZ_HOST_WAITING']='1'
    return dict(mode='observe', first=scene['first'], last=scene['last']+1,
                snapshots=list(scene['snapshots']), lifetime=dict(lifetime))


def bounded_rows(path, fields=None):
    if not path.is_file() or path.stat().st_size>64*1024*1024:
        raise ValueError('missing or oversized Exotica waiting input')
    with path.open(encoding='utf-8',newline='') as stream:
        reader=csv.DictReader(stream)
        if fields is not None and tuple(reader.fieldnames or ())!=tuple(fields):
            raise ValueError('Exotica waiting columns')
        rows=[]
        for row in reader:
            if None in row or any(v is None for v in row.values()):raise ValueError('malformed Exotica waiting row')
            rows.append(row)
            if len(rows)>200000:raise ValueError('Exotica waiting row budget')
    return rows


def fingerprint(data):
    h=14695981039346656037
    for byte in data:h=((h^byte)*1099511628211)&0xffffffffffffffff
    return f'{h:016x}'


def verify_receipt(trial, text, directory):
    directory=Path(directory);path=directory/'exotica-waiting-scenes.csv'
    files=list(directory.glob('exotica-waiting-*.bin'))
    if not trial or trial['mode']=='off':
        if 'MIDZ_HOST_WAITING=1' in text or 'MIDZ_HOST_WAITING_RESULT' in text or path.exists() or files:
            raise ValueError('disabled Exotica waiting observer ran')
        return None
    if re.findall(r'^MIDZ_HOST_WAITING=(\d+)$',text,re.M)!=['1']:
        raise ValueError('Exotica waiting start acknowledgment')
    names=('complete','scenes','candidates','quads','snapshots','remaining')
    final=re.findall(r'^MIDZ_HOST_WAITING_RESULT '+' '.join(n+r'=(\d+)' for n in names)+r'$',text,re.M)
    if len(final)!=1:raise ValueError('missing Exotica waiting completion')
    totals=dict(zip(names,map(int,final[0])))
    if totals['complete']!=1 or totals['remaining'] or not 0<totals['scenes']<=20000 or totals['snapshots']!=len(trial['snapshots']):
        raise ValueError('incomplete Exotica waiting observation')
    rows=bounded_rows(path,FIELDS)
    host=bounded_rows(directory/'exotica-host-scenes.csv')
    if len(rows)!=totals['scenes'] or len(rows)!=len(host):raise ValueError('Exotica waiting scene count')
    # Validate the complete underlying journal independently before consuming
    # exact record prefixes. Equal device timestamps alone cannot order events.
    exotica_lifetimes.verify_receipt(trial['lifetime'],text,directory)
    events=bounded_rows(directory/'exotica-lifetime-events.csv',exotica_lifetimes.FIELDS)
    cursor=0;live={};epoch=0;sequence=0;last_scene=0;last_frame=0;last_time=-1.
    candidates=quads=owned_snapshots=0;remaining=set(trial['snapshots']);expected_files=set()
    for row,original in zip(rows,host):
        if any(not re.fullmatch('[0-9]+',row[k]) for k in FIELDS if k not in ('device_time','hash')):
            raise ValueError('invalid Exotica waiting integer')
        r={k:int(row[k]) for k in FIELDS if k not in ('device_time','hash')}
        t=float(row['device_time'])
        if (not math.isfinite(t) or t<0 or t<last_time or r['scene']<=last_scene or r['frame']<last_frame or
                not trial['first']<=r['frame']<=trial['last'] or r['guest_cycles'] or
                any(row[k]!=original[k] for k in ('scene','frame','device_time')) or
                not re.fullmatch('[0-9a-f]{16}',row['hash'])):
            raise ValueError('Exotica waiting original scene/time join')
        if (r['historical']!=r['unowned']+r['submitted']+r['candidates'] or
                r['historical']+r['future']>32768 or not 0<=r['bound_future_submitted']<=r['bound_future']<=r['future'] or
                not 0<=r['instances']<=r['candidates']<=4096 or r['quads']>131072 or
                not max(1,cursor)<=r['records']<=len(events)):
            raise ValueError('Exotica waiting candidate/prefix bounds')
        while cursor<r['records']:
            e=events[cursor];cursor+=1;op=e['event'];slot=int(e['slot'])
            epoch=int(e['epoch']);sequence=int(e['sequence'])
            if float(e['time'])>t:raise ValueError('Exotica waiting future lifetime event')
            if op in ('L','R'):live.clear()
            elif op=='A':live[slot]=dict(generation=int(e['generation']),owner=None,drawn=False)
            elif op=='F':live.pop(slot,None)
            elif op=='B':live[slot]['owner']=(int(e['realm']),int(e['section']),int(e['source']))
            elif op=='D':live[slot]['drawn']=True
        if r['epoch']!=epoch or r['sequence']!=sequence:
            raise ValueError('Exotica waiting registry boundary')
        if cursor<len(events) and float(events[cursor]['time'])<t:
            raise ValueError('Exotica waiting skipped earlier lifetime event')
        if r['frame'] in remaining:
            remaining.remove(r['frame']);prefix=f"exotica-waiting-{r['frame']}"

            def binary(suffix,size):
                name=prefix+'-'+suffix+'.bin';expected_files.add(name);p=directory/name
                if not p.is_file() or p.stat().st_size!=size:raise ValueError('Exotica waiting snapshot extent')
                return p.read_bytes()

            owners=list(struct.iter_unpack('<6Q',binary('owners',48*r['candidates'])))
            seen=set();keys=set()
            for realm,section,source,slot,owner_epoch,generation in owners:
                life=live.get(slot);key=(realm,section,source)
                if (life is None or slot in seen or key in keys or owner_epoch!=epoch or
                        life['generation']!=generation or life['owner']!=key or life['drawn']):
                    raise ValueError('Exotica waiting stale/submitted/duplicate snapshot owner')
                seen.add(slot);keys.add(key);owned_snapshots+=1
            geometry=binary('quads',260*r['quads'])
            if fingerprint(geometry)!=row['hash']:raise ValueError('Exotica waiting geometry fingerprint')
            instances=list(struct.iter_unpack('<11I',binary('instances',44*r['instances'])))
            end=0;order={(owner[1],owner[2]):i for i,owner in enumerate(owners)};previous=-1
            for instance in instances:
                key=instance[:2];first,count=instance[-2:]
                if key not in order or order[key]<=previous or first!=end or count>r['quads']-end:
                    raise ValueError('Exotica waiting instance ownership/order/range')
                previous=order[key];end+=count
            if end!=r['quads']:raise ValueError('Exotica waiting uncovered geometry')
        last_scene=r['scene'];last_frame=r['frame'];last_time=t
        candidates+=r['candidates'];quads+=r['quads']
    if remaining or {p.name for p in files}!=expected_files or candidates!=totals['candidates'] or quads!=totals['quads']:
        raise ValueError('Exotica waiting final totals/snapshots')
    return dict(passed=True,**totals,snapshot_owners_verified=owned_snapshots,
                scope='Read-only proposal counts, exact lifecycle prefixes and captured owner/instance structure. '
                      'Independent source/geometry, original packet/route/pixel and fade/handover acceptance remain separate.')
