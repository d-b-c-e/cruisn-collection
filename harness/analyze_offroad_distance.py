"""Validate Off Road far/vertex-table observations; not visual acceptance."""
import argparse
import csv
from pathlib import Path
import struct
from verification import sha256_file,write_json

FAR_FIELDS=['frame','far','far_tests','stock_rejects','far_rejects','extra_admissions']
TABLE_FIELDS=['frame','pc','opcode','reads','minimum_index','maximum_index','upper_clamps']


def summarize(directory):
    directory=Path(directory)
    with (directory/'offroad-distance.csv').open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=FAR_FIELDS:raise ValueError('unexpected far columns')
        rows=[]
        for row in reader:
            if None in row or any(v is None for v in row.values()):raise ValueError('incomplete far row')
            rows.append({k:int(v) for k,v in row.items()})
    if not rows:raise ValueError('empty far trace')
    first,last=rows[0]['frame'],rows[-1]['frame']
    if first<1 or [r['frame'] for r in rows]!=list(range(first,last+1)):
        raise ValueError('noncontiguous far trace')
    far=rows[0]['far']
    if far not in (47296,59120,94592,141888) or any(r['far']!=far for r in rows):
        raise ValueError('unexpected or changing far limit')
    maximum={47296:63679,59120:63679,94592:127359,141888:191039}[far]
    for r in rows:
        if (any(v<0 for v in r.values()) or r['stock_rejects']>r['far_tests']
                or r['far_rejects']+r['extra_admissions']!=r['stock_rejects']
                or (far==47296 and r['extra_admissions'])):
            raise ValueError('inconsistent far counters')
    totals={k:sum(r[k] for r in rows) for k in FAR_FIELDS[2:]}
    if not totals['far_tests']:raise ValueError('no culler observations')
    pcs={};previous=first;seen=set()
    with (directory/'offroad-projection.csv').open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=TABLE_FIELDS:raise ValueError('unexpected table columns')
        for r in reader:
            if None in r or any(v is None for v in r.values()):raise ValueError('incomplete table row')
            frame,pc,opcode=int(r['frame']),int(r['pc'],16),int(r['opcode'],16)
            n,lo,hi,clamps=(int(r[k]) for k in TABLE_FIELDS[3:])
            if (not previous<=frame<=last or not 0<pc<0x20000 or not 0<=opcode<=0xffffffff or not -4096<=lo<=hi<=maximum
                    or not 0<=clamps<=n or n<1 or (clamps and hi!=maximum) or (frame,pc) in seen):
                raise ValueError('invalid table observation/order/range')
            previous=frame;seen.add((frame,pc))
            v=pcs.setdefault(pc,dict(opcode=opcode,reads=0,minimum_index=lo,maximum_index=hi,upper_clamps=0,frames=0))
            if opcode!=v['opcode']:raise ValueError('table caller instruction changed')
            v['reads']+=n;v['frames']+=1;v['upper_clamps']+=clamps
            v['minimum_index']=min(lo,v['minimum_index']);v['maximum_index']=max(hi,v['maximum_index'])
    if 0x1c45 not in pcs:raise ValueError('main culler table consumer not observed')
    sources={n:sha256_file(directory/n) for n in ('offroad-distance.csv','offroad-projection.csv')}
    writes=None
    if (directory/'offroad-limit-writes.csv').is_file():
        writes=[]
        def c31(value):
            bits=struct.unpack('<I',struct.pack('<f',value))[0]
            return ((((bits>>23)-127)&255)<<24)|(bits&0x7fffff)
        expected={0x1b724:(0x1822,c31(far)),0x1b725:(0x1824,c31(maximum+1))}
        with (directory/'offroad-limit-writes.csv').open(newline='',encoding='utf-8') as f:
            reader=csv.DictReader(f)
            if reader.fieldnames!=['frame','pc','address','value']:raise ValueError('unexpected producer columns')
            for row in reader:
                if None in row or any(v is None for v in row.values()):raise ValueError('incomplete producer row')
                frame=int(row['frame']);pc,address,value=(int(row[k],16) for k in ('pc','address','value'))
                if not first<=frame<=last or expected.get(address)!=(pc,value):raise ValueError('unexpected limit producer/value')
                writes.append(dict(frame=frame,pc=pc,address=address,value=value))
        sources['offroad-limit-writes.csv']=sha256_file(directory/'offroad-limit-writes.csv')
    return dict(schema=1,scope=__doc__,frames=[first,last],far=far,totals=totals,limit_writes=writes,
                consumers={f'{pc:x}':v for pc,v in sorted(pcs.items())},
                table_maximum=maximum,table_reads=sum(v['reads'] for v in pcs.values()),
                table_clamps=sum(v['upper_clamps'] for v in pcs.values()),
                sources=sources)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    p.add_argument('--output',required=True,type=Path);a=p.parse_args();write_json(a.output,summarize(a.directory))
