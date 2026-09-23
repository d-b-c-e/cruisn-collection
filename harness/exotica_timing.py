"""Bounded CPU phase measurements; separate from rendering and input proof."""
import csv
import math
from pathlib import Path
import re
from verification import sha256_file

KEY='MIDZ_HOST_TIMING'
PHASES=('source','waiting_build','future_build','future_material',
        'active_seal','waiting_ready','active_build','active_material',
        'future_stage','future_encode','future_submit','future_commit',
        'lifetime_install','lifetime_complete','lifetime_remove')
EVENTS={'lifetime_install','lifetime_complete','lifetime_remove'}
NESTED={'future_stage','future_encode','future_submit','future_commit','lifetime_remove'}


def add_arguments(parser):
    parser.add_argument('--exotica-timing',help='CPU phase timing FIRST:LAST (up to 2000 frames), written only at exit')


def configure(args,rom,settings,frames):
    text=args.exotica_timing
    if text is None:
        if KEY in settings:raise ValueError('inherited timing requires an explicit --exotica-timing range')
        return None
    if (rom!='crusnexo' or not args.candidate or args.headless or args.native_renderer
            or settings.get('MIDZ_HOST_SCENE')!='1' or settings.get('MIDZ_GL')!='1'
            or settings.get('MIDV_FFB')!='0'):
        raise ValueError('CPU phase timing requires an explicit Exotica host candidate with FFB0')
    if not re.fullmatch(r'[0-9]+:[0-9]+',text):raise ValueError('invalid timing range')
    first,last=map(int,text.split(':'))
    if not 1<=first<=last<min(frames-1,2**32) or last-first>=2000:raise ValueError('invalid timing range')
    settings[KEY]=f'{first}:{last}'
    return dict(first=first,last=last,scope='CPU scene phases only; not GPU or physical input latency')


def verify(trial,directory):
    directory=Path(directory)
    text=(directory/'stderr.log').read_text(encoding='utf-8',errors='replace')
    path=directory/'exotica-host-timing.csv'
    ack=re.findall(r'^MIDZ_HOST_TIMING first=(\d+) last=(\d+)$',text,re.M)
    end=re.findall(r'^MIDZ_HOST_TIMING_RESULT complete=(\d+) rows=(\d+) final_frame=(\d+)$',text,re.M)
    if trial is None:
        if ack or end or path.exists():raise ValueError('unrequested CPU timing output')
        return None
    if ack!=[(str(trial['first']),str(trial['last']))] or len(end)!=1 or end[0][0]!='1' or int(end[0][2])<trial['last']:
        raise ValueError('incomplete CPU timing receipt')
    if not path.is_file() or path.stat().st_size>8*1024*1024:raise ValueError('missing or oversized CPU timing data')
    with path.open(encoding='utf-8',newline='') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=['frame','scene','phase','microseconds','units']:raise ValueError('CPU timing columns')
        rows=list(reader)
    if not 0<len(rows)<=65536 or len(rows)!=int(end[0][1]):raise ValueError('CPU timing row count')
    seen=set();phases={};frames={};events={}
    for row in rows:
        frame,scene,units=int(row['frame']),int(row['scene']),int(row['units'])
        us=float(row['microseconds']);phase=row['phase'];key=(scene,phase,frame if phase in EVENTS else None)
        if (None in row or not trial['first']<=frame<=trial['last'] or not (0 if phase in EVENTS else 1)<=scene<2**64 or not (1 if phase in EVENTS else 0)<=units<2**64
                or phase not in PHASES or not math.isfinite(us) or us<0 or key in seen):
            raise ValueError('invalid or duplicate CPU timing row')
        seen.add(key);phases.setdefault(phase,[]).append(us)
        if phase in EVENTS:
            events.setdefault(phase,[]).append(dict(frame=frame,scene=scene,callbacks=units,microseconds=us))
        if phase not in NESTED:frames[frame]=frames.get(frame,0)+us
    return dict(passed=True,rows=len(rows),sha256=sha256_file(path),
                phases={k:dict(count=len(v),mean_us=sum(v)/len(v),max_us=max(v)) for k,v in phases.items()},
                callback_events={k:dict(
                    buckets=len(v),callbacks=sum(r['callbacks'] for r in v),
                    total_us=sum(r['microseconds'] for r in v),
                    mean_us_per_callback=sum(r['microseconds'] for r in v)/sum(r['callbacks'] for r in v),
                    largest_buckets=sorted(v,key=lambda r:r['microseconds'],reverse=True)[:10],
                    scope='Aggregate callback time; bucket duration is not the maximum individual callback latency')
                    for k,v in events.items()},
                largest_cpu_frames=sorted(frames.items(),key=lambda p:p[1],reverse=True)[:10],
                scope=trial['scope'])
