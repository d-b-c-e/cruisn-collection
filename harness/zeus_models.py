"""Bounded Zeus model-source journal reader. Raw game operands must stay local."""
import json
import math
from pathlib import Path
import struct
from verification import sha256_file

HEADER=struct.Struct('<16Id16f208I')
FIELDS=('version','frame','id','base','count','quad_size','system','first_quad',
        'last_quad','ucode','palette','texture','yscale','zoffset','raw_words','reserved')


def parse(path):
    path=Path(path)
    if not 8+HEADER.size<=path.stat().st_size<=64*1024*1024:
        raise ValueError('invalid Zeus model journal size')
    raw=path.read_bytes();offset=0;rows=[];last_quad=0;last_time=-1.;last_frame=0
    while offset<len(raw):
        if len(raw)-offset<8 or len(rows)>=4096:
            raise ValueError('truncated or oversized Zeus model journal')
        magic,size=struct.unpack_from('<II',raw,offset);offset+=8
        if magic!=0x31534d5a or size<HEADER.size or size>HEADER.size+2*(0xc800+1)*4 or size>len(raw)-offset:
            raise ValueError('invalid Zeus model record')
        values=HEADER.unpack_from(raw,offset);r=dict(zip(FIELDS,values[:16]))
        r['time']=values[16];r['matrix']=list(values[17:26]);r['translation']=list(values[26:30]);r['light']=list(values[30:33])
        r['regs']=list(values[33:161]);r['render']=list(values[161:241])
        valid_policy=(r['version']==1 and r['reserved']==0) or (r['version']==2 and 1<=r['reserved']<=7)
        r['render_policy']=r['reserved'] if r['version']==2 else 0
        if (not valid_policy or r['id']!=len(rows)+1 or r['system']!=1 or
                r['count']>0xc800 or r['quad_size'] not in (10,12,14) or
                r['raw_words']!=(2*(r['count']+1) if r['base'] else 0) or
                size!=HEADER.size+4*r['raw_words'] or r['yscale'] not in (0,1) or r['zoffset']!=0 or
                r['first_quad']<last_quad or r['last_quad']<r['first_quad'] or r['frame']<last_frame or
                not math.isfinite(r['time']) or r['time']<last_time or
                not all(math.isfinite(x) for x in values[17:33])):
            raise ValueError('invalid Zeus model identity/state/frontier')
        block=(r['base']%1024)+((r['base']>>16)%2048)*1024
        if block*2+r['raw_words']>1024*2048*2:
            raise ValueError('Zeus model source outside WaveRAM')
        r['words']=list(struct.unpack_from('<'+str(r['raw_words'])+'I',raw,offset+HEADER.size))
        if rows and r['render_policy']!=rows[0]['render_policy']:
            raise ValueError('Zeus render policy changed within one capture')
        rows.append(r);offset+=size;last_quad=r['last_quad'];last_time=r['time'];last_frame=r['frame']
    return rows


def validate(directory,frame,quad_count):
    directory=Path(directory);receipt=json.loads((directory/'models.json').read_text())
    rows=parse(directory/'models.bin')
    if (receipt.get('schema')!=1 or receipt.get('complete') is not True or
            receipt.get('models')!=len(rows) or receipt.get('bytes')!=(directory/'models.bin').stat().st_size or
            receipt.get('quads')!=quad_count or not rows or
            any(r['frame'] not in (frame-1,frame) or r['last_quad']>quad_count for r in rows)):
        raise ValueError('incomplete Zeus model capture')
    return {'passed':True,'models':len(rows),'covered_quads':sum(r['last_quad']-r['first_quad'] for r in rows),
            'render_policy':rows[0]['render_policy'],
            'total_quads':quad_count,'quad_sizes':sorted(set(r['quad_size'] for r in rows)),
            'scope':'Model source/state and projected-quad ownership journal; not an independent geometry or visual verdict.',
            'sha256':{name:sha256_file(directory/name) for name in ('models.bin','models.json')}}
