"""Independent duplicate/material joins for explicitly composed private margins."""
from pathlib import Path
import re
import struct
from exotica_waiting import bounded_rows
from zeus_resource_lease import texture_pages
from zeus_host_materials import palette_bytes


def filtered_geometry(active, aq, waiting, wq, owners, proposal, ready):
    if (len(active)%44 or len(waiting)%44 or len(aq)%260 or len(wq)%260 or len(owners)%48 or
            max(len(active),len(waiting))>4096*44 or max(len(aq),len(wq))>131072*260 or
            len(owners)>4096*48 or len(proposal)!=16777216 or len(ready)!=16777216):
        raise ValueError('composition snapshot size')
    def layout(data, quads):
        rows=list(struct.iter_unpack('<11I',data));end=0;keys=set()
        for i in rows:
            if i[:2] in keys or i[9]!=end or i[10]>len(quads)//260-end:
                raise ValueError('composition geometry layout')
            keys.add(i[:2]);end+=i[10]
        if end!=len(quads)//260:raise ValueError('composition orphaned geometry')
        return rows
    ai=layout(active,aq);wi=layout(waiting,wq)
    bindings={};slots=set();epochs=set();realms=set()
    for realm,entry,source,slot,epoch,generation in struct.iter_unpack('<6Q',owners):
        if (not all((realm,entry,source,slot,epoch,generation)) or max(entry,source,slot)>0xffffffff or
                (entry,source) in bindings or slot in slots):raise ValueError('composition owner identity')
        bindings[entry,source]=slot;slots.add(slot);epochs.add(epoch);realms.add(realm)
    if len(epochs)>1 or len(realms)>1:raise ValueError('composition mixed owners')
    if any(i[:2] not in bindings for i in wi):raise ValueError('composition missing owner')
    by_slot={bindings[i[:2]]:i for i in wi};kept=[];quads=[];count=0;removed=0;removed_quads=0;seen=set()
    for i in ai:
        if i[1] in seen:raise ValueError('composition duplicate active slot')
        seen.add(i[1]);x=aq[i[9]*260:(i[9]+i[10])*260]
        if i[1] in by_slot:
            j=by_slot[i[1]];y=wq[j[9]*260:(j[9]+j[10])*260]
            if i[2:9]!=j[2:9] or x!=y:raise ValueError('composition overlapping render data differs')
            if palette_bytes(proposal,j[6])!=palette_bytes(ready,i[6]):raise ValueError('composition palette differs')
            for page in texture_pages(x):
                if proposal[page*4096:(page+1)*4096]!=ready[page*4096:(page+1)*4096]:raise ValueError('composition texture differs')
            removed+=1;removed_quads+=i[10];continue
        kept.append(struct.pack('<11I',*i[:9],count,i[10]));quads.append(x);count+=i[10]
    return b''.join(kept),b''.join(quads),removed,removed_quads


def endpoint_geometry(original,replacement):
    if len(original)!=len(replacement) or len(original)%260:raise ValueError('composition endpoint extent')
    for offset in range(0,len(original),260):
        a=struct.unpack_from('<17I',original,offset);b=struct.unpack_from('<17I',replacement,offset)
        if (original[offset+68:offset+260]!=replacement[offset+68:offset+260] or (a[9]^b[9])&~18
                or any(a[k]!=b[k] for k in range(17) if k not in (7,8,9,10))):
            raise ValueError('composition endpoint changed geometry/materials/depth test')


def verify(directory,scenes,text,enabled,captures,early=None):
    directory=Path(directory)
    initial=re.findall(r'^MIDZ_HOST_COMPOSE=(\d+)$',text,re.M)
    final=re.findall(r'^MIDZ_HOST_COMPOSE_RESULT complete=(\d+) scenes=(\d+)$',text,re.M)
    path=directory/'exotica-compose-scenes.csv'
    if not enabled:
        if initial or final or path.exists():raise ValueError('disabled composition ran')
        return None
    rows=bounded_rows(path);active=bounded_rows(directory/'exotica-active-scenes.csv');completed=bounded_rows(directory/'exotica-handover-scenes.csv')
    if initial!=['1'] or final!=[('1',str(len(scenes)))] or any(len(x)!=len(scenes) for x in (rows,active,completed)):
        raise ValueError('incomplete composition')
    sampled=[]
    for source,row,a,w in zip(scenes,rows,active,completed):
        if (any(row[k]!=source[k] for k in ('scene','frame')) or a['scene']!=row['scene'] or w['scene']!=row['scene'] or
                int(row['end_records'])>int(row['ready_records']) or row['end_records']!=w['end_records'] or row['ready_records']!=w['ready_records'] or
                int(row['input_instances'])!=int(row['instances'])+int(row['overlaps']) or
                int(row['input_quads'])!=int(row['quads'])+int(row['removed_quads']) or
                row['instances']!=a['instances'] or row['quads']!=a['quads'] or
                not 0<=int(row['texture_pages'])<=4096):raise ValueError('composition scene/lifetime/count join')
        frame=int(row['frame'])
        if frame not in captures:continue
        def read(prefix,suffix,limit):
            p=directory/f'exotica-{prefix}-{frame}-{suffix}.bin'
            if p.stat().st_size>limit:raise ValueError('composition snapshot budget')
            return p.read_bytes()
        trial=early and early['first']<=frame<=early['last']
        if trial and re.findall(r'^MIDZ_ENDPOINT_EARLY=([01])$',text,re.M)!=['1']:
            raise ValueError('composition missing explicit early visibility')
        waiting=read('handover','quads',131072*260);active_quads=read('active','quads',131072*260)
        if trial:
            original_waiting=read('handover','control-quads',131072*260);original_active=read('active','control-quads',131072*260)
            endpoint_geometry(original_waiting,waiting);endpoint_geometry(original_active,active_quads)
        else:
            original_waiting=waiting;original_active=active_quads
        expected=filtered_geometry(read('compose','input-instances',4096*44),read('compose','input-quads',131072*260),
            read('handover','instances',4096*44),original_waiting,read('handover','owners',4096*48),
            read('waiting-draw','wave',16777216),read('active','wave',16777216))
        if (expected[0]!=read('active','instances',4096*44) or expected[1]!=original_active or
                expected[2]!=int(row['overlaps']) or expected[3]!=int(row['removed_quads'])):
            raise ValueError('composition independent filtered geometry differs')
        sampled.append(dict(frame=frame,removed_instances=expected[2],removed_quads=expected[3],byte_exact=True))
    if len(sampled)!=len(captures):raise ValueError('composition missing snapshots')
    return dict(passed=True,scenes=len(rows),snapshots=sampled,
                scope='Native composition receipts and independent sampled duplicate/material joins; original resource and temporal acceptance remain separate.')
