"""Bounded emulator actions that MAME INP does not encode.

Only explicit frame-scheduled soft resets are supported. Device force is disabled
by the owning recorder/replayer; these are diagnostic cases, not live UI macros.
"""
import csv
import math
from pathlib import Path
import re

from verification import sha256_file

PLAN='session-actions.csv'
EVENTS='session-action-events.csv'


def normalize(actions,stop):
    if not isinstance(actions,list) or not 1<=len(actions)<=16 or type(stop) is not int:
        raise ValueError('session action count or stop frame')
    result=[];previous=-1
    for row in actions:
        if (not isinstance(row,dict) or set(row)!={'frame','action'} or row['action']!='soft_reset'
                or type(row['frame']) is not int or not 1<=row['frame']<=stop-2
                or row['frame']<previous+2):
            raise ValueError('unsupported, unordered or out-of-range session action')
        previous=row['frame'];result.append(dict(row))
    return result


def write_schedule(path,actions,stop):
    rows=normalize(actions,stop)
    Path(path).write_text('frame,action\n'+''.join(f"{r['frame']},soft_reset\n" for r in rows),encoding='utf-8')
    return rows


def read_schedule(path,stop):
    path=Path(path)
    if path.stat().st_size>4096:raise ValueError('session action schedule budget')
    with path.open(encoding='utf-8',newline='') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=['frame','action']:raise ValueError('session action columns')
        rows=[]
        for row in reader:
            if set(row)!={'frame','action'} or not re.fullmatch('[0-9]+',row['frame'] or ''):
                raise ValueError('invalid session action row')
            rows.append(dict(frame=int(row['frame']),action=row['action']))
    return normalize(rows,stop)


def configure(runtime,manifest,stop):
    runtime=Path(runtime);path=runtime/PLAN;actions=manifest.get('session_actions')
    if actions is None:
        if path.exists():raise ValueError('unrequested session action schedule')
        return {}
    expected=normalize(actions,stop)
    if read_schedule(path,stop)!=expected or not (runtime/'session_actions.lua').is_file():
        raise ValueError('frozen session action schedule/loader differs')
    return dict(SNAP_ACTIONS=str(path),SNAP_ACTION_LOG=str(runtime/EVENTS))


def verify(directory,frames):
    directory=Path(directory);plan=directory/PLAN;events=directory/EVENTS
    if not plan.exists():
        if events.exists():raise ValueError('unrequested session action receipts')
        return None
    actions=read_schedule(plan,frames)
    if not events.is_file() or events.stat().st_size>8192:
        raise ValueError('missing or oversized session action receipts')
    with events.open(encoding='utf-8',newline='') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=['id','event','frame','time']:raise ValueError('session action receipt columns')
        rows=list(reader)
    if len(rows)!=len(actions)*2:raise ValueError('incomplete session actions')
    last_time=-1.
    for index,action in enumerate(actions):
        request_time=None
        for offset,event in enumerate(('request','complete')):
            row=rows[index*2+offset]
            if (set(row)!={'id','event','frame','time'} or row['event']!=event
                    or any(not re.fullmatch('[0-9]+',row[k] or '') for k in ('id','frame'))):
                raise ValueError('malformed session action receipt')
            frame=int(row['frame']);time=float(row['time'])
            if (int(row['id'])!=index+1 or not math.isfinite(time) or time<0 or time<last_time
                    or not action['frame']<=frame<=action['frame']+offset):
                raise ValueError('session action ownership, frame or time mismatch')
            if offset==0:request_time=time
            elif time-request_time>.1:raise ValueError('session reset completion delayed')
            last_time=time
    return dict(completed=len(actions),schedule_sha256=sha256_file(plan),events_sha256=sha256_file(events))
