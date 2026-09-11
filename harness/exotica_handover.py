"""Observe waiting cohorts at actual CPU/device completion; no extra drawing."""
import math
from pathlib import Path
import re
import struct

import exotica_waiting as waiting

FIELDS = ('scene','proposal_frame','proposal_time','proposal_records','end_records',
          'ready_frame','ready_time','ready_records','epoch','captured','submitted','retired',
          'retained','owners_hash','instances','quads','geometry_hash','guest_cycles')


def add_arguments(parser):
    parser.add_argument('--exotica-host-handover', choices=('off','observe'),
                        help='observe actual waiting-cohort retirement at the command fence; no extra drawing')


def configure(args, rom, settings, scene, waiting_trial):
    option = getattr(args, 'exotica_host_handover', None)
    if option is not None and not getattr(args, 'candidate', None):
        raise ValueError('Exotica completion requires an explicit candidate')
    value = settings.get('MIDZ_HOST_HANDOVER', '0') if option is None else str(('off','observe').index(option))
    if value not in ('0','1'):
        raise ValueError('invalid recorded Exotica completion mode')
    if value == '0':
        if option is not None:
            settings['MIDZ_HOST_HANDOVER'] = '0'
            return dict(mode='off')
        return None
    if (rom != 'crusnexo' or not waiting_trial or waiting_trial.get('mode') != 'observe'
            or not scene or scene.get('fence') is not True):
        raise ValueError('Exotica completion requires waiting and actual command-fence observation')
    settings['MIDZ_HOST_HANDOVER'] = '1'
    return dict(mode='observe', waiting=waiting_trial, snapshots=list(waiting_trial['snapshots']))


def verify_receipt(trial, text, directory):
    directory=Path(directory);path=directory/'exotica-handover-scenes.csv'
    files=list(directory.glob('exotica-handover-*.bin'))
    if not trial or trial['mode']=='off':
        if 'MIDZ_HOST_HANDOVER=1' in text or 'MIDZ_HOST_HANDOVER_RESULT' in text or path.exists() or files:
            raise ValueError('disabled Exotica completion observer ran')
        return None
    if re.findall(r'^MIDZ_HOST_HANDOVER=(\d+)$',text,re.M)!=['1']:
        raise ValueError('Exotica completion start acknowledgment')
    names=('complete','scenes','captured','submitted','retired','bytes','snapshots','remaining')
    final=re.findall(r'^MIDZ_HOST_HANDOVER_RESULT '+' '.join(n+r'=(\d+)' for n in names)+r'$',text,re.M)
    if len(final)!=1:raise ValueError('missing Exotica completion receipt')
    totals=dict(zip(names,map(int,final[0])))
    if (totals['complete']!=1 or totals['remaining'] or not 0<totals['scenes']<=20000
            or totals['snapshots']!=len(trial['snapshots'])):
        raise ValueError('incomplete Exotica completion observation')
    waiting.verify_receipt(trial['waiting'],text,directory)
    rows=waiting.bounded_rows(path,FIELDS)
    proposals=waiting.bounded_rows(directory/'exotica-waiting-scenes.csv',waiting.FIELDS)
    fences=waiting.bounded_rows(directory/'exotica-host-fences.csv')
    events=waiting.bounded_rows(directory/'exotica-lifetime-events.csv',waiting.exotica_lifetimes.FIELDS)
    cohort_path=directory/'exotica-handover-cohorts.bin'
    if (not cohort_path.is_file() or cohort_path.stat().st_size!=totals['bytes'] or totals['bytes']>64*1024*1024
            or len(rows)!=totals['scenes'] or len(rows)!=len(proposals) or len(rows)!=len(fences)):
        raise ValueError('Exotica completion extent/scene counts')
    cursor=0;epoch=0;live={};last_scene=0;last_ready_time=0.

    def fold(count,time):
        nonlocal cursor,epoch
        if not math.isfinite(time) or not max(1,cursor)<=count<=len(events):
            raise ValueError('Exotica completion event watermark')
        while cursor<count:
            event=events[cursor];cursor+=1;op=event['event'];slot=int(event['slot'])
            if float(event['time'])>time+1e-12:raise ValueError('completion includes future event')
            epoch=int(event['epoch'])
            if op in ('L','R'):live.clear()
            elif op=='A':live[slot]=dict(epoch=epoch,generation=int(event['generation']),key=None,drawn=False)
            elif op=='F':live.pop(slot,None)
            elif op=='B':live[slot]['key']=(int(event['realm']),int(event['section']),int(event['source']))
            elif op=='D':live[slot]['drawn']=True
        if cursor<len(events) and float(events[cursor]['time'])<time-1e-12:
            raise ValueError('completion omits earlier event')

    def status(handle):
        realm,section,source,slot,owner_epoch,generation=handle
        state=live.get(slot)
        if (state is None or owner_epoch!=epoch or state['epoch']!=owner_epoch
                or state['generation']!=generation or state['key']!=(realm,section,source)):
            return 'retired'
        return 'submitted' if state['drawn'] else 'retained'

    sums=dict(captured=0,submitted=0,retired=0);remaining=set(trial['snapshots'])
    expected_files={'exotica-handover-cohorts.bin'};changed_after_end=0
    with cohort_path.open('rb') as stream:
        def read(size):
            data=stream.read(size)
            if len(data)!=size:raise ValueError('truncated Exotica cohort')
            return data
        for row,proposal,fence in zip(rows,proposals,fences):
            if any(not re.fullmatch('[0-9]+',row[k]) for k in FIELDS if k not in ('proposal_time','ready_time','owners_hash','geometry_hash')):
                raise ValueError('invalid Exotica completion integer')
            values={k:int(row[k]) for k in FIELDS if k not in ('proposal_time','ready_time','owners_hash','geometry_hash')}
            ptime,rtime,etime=float(row['proposal_time']),float(row['ready_time']),float(fence['end_time'])
            if (not all(math.isfinite(t) for t in (ptime,rtime,etime)) or not last_ready_time<=ptime<=etime<=rtime
                    or values['scene']<=last_scene or row['scene']!=proposal['scene'] or row['scene']!=fence['scene']
                    or row['proposal_frame']!=proposal['frame'] or row['proposal_time']!=proposal['device_time']
                    or row['proposal_records']!=proposal['records'] or row['ready_frame']!=fence['ready_frame']
                    or row['ready_time']!=fence['ready_time'] or values['guest_cycles']
                    or values['captured']!=int(proposal['candidates']) or values['captured']>4096
                    or not values['proposal_records']<=values['end_records']<=values['ready_records']
                    or not 0<=values['instances']<=values['retained']<=values['captured']
                    or values['quads']>131072
                    or any(not re.fullmatch('[0-9a-f]{16}',row[k]) for k in ('owners_hash','geometry_hash'))):
                raise ValueError('Exotica completion proposal/fence/count join')
            fold(values['proposal_records'],ptime)
            magic,scene,records,cohort_epoch,count=struct.unpack('<5Q',read(40))
            if ((magic,scene,records,cohort_epoch,count)!=(0x31484357,values['scene'],values['proposal_records'],epoch,values['captured'])):
                raise ValueError('Exotica cohort header')
            owner_bytes=read(count*48);owners=list(struct.iter_unpack('<6Q',owner_bytes))
            if len(set(h[3] for h in owners))!=count or len(set(h[:3] for h in owners))!=count or any(status(h)!='retained' for h in owners):
                raise ValueError('Exotica proposal owner not live/unsubmitted/unique')
            fold(values['end_records'],etime)
            ended=[status(h) for h in owners]
            fold(values['ready_records'],rtime)
            completed=[status(h) for h in owners]
            if epoch!=values['epoch'] or epoch!=cohort_epoch:
                raise ValueError('Exotica completion reset boundary')
            for name in ('submitted','retired','retained'):
                if completed.count(name)!=values[name]:raise ValueError('Exotica cohort reconciliation mismatch')
            retained=[h for h,s in zip(owners,completed) if s=='retained']
            retained_bytes=b''.join(struct.pack('<6Q',*h) for h in retained)
            if waiting.fingerprint(retained_bytes)!=row['owners_hash']:
                raise ValueError('Exotica retained ownership/order fingerprint')
            changed_after_end+=sum(a!=b for a,b in zip(ended,completed))
            if values['proposal_frame'] in remaining:
                frame=values['proposal_frame'];remaining.remove(frame)
                if (directory/f'exotica-waiting-{frame}-owners.bin').read_bytes()!=owner_bytes:
                    raise ValueError('Exotica original proposal snapshot differs')
                old_instances=list(struct.iter_unpack('<11I',(directory/f'exotica-waiting-{frame}-instances.bin').read_bytes()))
                old_quads=(directory/f'exotica-waiting-{frame}-quads.bin').read_bytes()
                keys={h[1:3] for h in retained};quads=bytearray();instances=[]
                for instance in old_instances:
                    if instance[:2] not in keys:continue
                    new=list(instance);new[9]=len(quads)//260;instances.append(tuple(new))
                    quads.extend(old_quads[instance[9]*260:(instance[9]+instance[10])*260])
                expected={'owners':retained_bytes,'instances':b''.join(struct.pack('<11I',*h) for h in instances),'quads':quads}
                if (len(instances)!=values['instances'] or len(quads)!=260*values['quads']
                        or waiting.fingerprint(quads)!=row['geometry_hash']):
                    raise ValueError('Exotica filtered geometry count/fingerprint')
                for kind,data in expected.items():
                    name=f'exotica-handover-{frame}-{kind}.bin';expected_files.add(name)
                    p=directory/name
                    if not p.is_file() or p.stat().st_size!=len(data) or p.read_bytes()!=data:
                        raise ValueError('Exotica filtered proposal geometry/order differs')
            for name in sums:sums[name]+=values[name]
            last_scene=values['scene']
            last_ready_time=rtime
        if stream.read(1):raise ValueError('trailing Exotica cohort bytes')
    if remaining or {p.name for p in files}!=expected_files or any(sums[k]!=totals[k] for k in sums):
        raise ValueError('Exotica completion final totals/artifacts')
    return dict(passed=True,**totals,owners_changed_after_cpu_end=changed_after_end,
                scope='Actual event-watermark/owner reconciliation for every cohort and filtered proposal geometry for snapshots. '
                      'No waiting draw, material residency, alpha-order, performance or temporal visual acceptance.')
