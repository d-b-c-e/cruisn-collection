"""Strict bounded Zeus GPU-consumer journal, including ordered texture uploads."""
from collections import Counter
import hashlib,math,re,struct
from pathlib import Path

MAGIC=0x3143475a
LIMIT=64*1024*1024

def parse(raw):
    if not 40<len(raw)<=LIMIT:raise ValueError('command journal size')
    magic,version,frame,width,height,margin,scale,palette,flags,reserved=struct.unpack_from('<10I',raw)
    if (magic!=MAGIC or version!=1 or not 2<=frame<=16000 or scale not in (1,2,3,4) or
        height!=1024*scale or not 0<=margin<=120 or width!=(512+2*margin)*scale or
        palette>255 or flags&~15 or reserved):raise ValueError('command journal header')
    offset=40;records=[]
    while offset<len(raw):
        if len(raw)-offset<8 or len(records)>=131072:raise ValueError('command journal truncated/header budget')
        kind,size=struct.unpack_from('<II',raw,offset);offset+=8
        if kind not in (1,2,3,4,5,6) or size>len(raw)-offset:raise ValueError('command journal type/payload')
        payload=raw[offset:offset+size];offset+=size
        expected={1:(260,),2:(1024,),3:(16,),4:(24,),6:(4,16)}
        if kind!=5 and size not in expected[kind]:raise ValueError('command journal record size')
        if kind==1:
            _,vertices=struct.unpack_from('<2I',payload)
            if not 3<=vertices<=8 or not all(math.isfinite(v) for v in struct.unpack_from('<'+str(vertices*6)+'f',payload,68)):
                raise ValueError('command journal geometry')
        if kind==5:
            if size<9:raise ValueError('command journal upload empty')
            start,length=struct.unpack_from('<2I',payload)
            if not length or length!=size-8 or start+length>16777216:raise ValueError('command journal upload range')
        # A legacy display-address notification is four bytes and is ignored by
        # the current consumer. Only the16-byte FrameTick ends this interval.
        if kind==6 and size==16:
            base,actual,seconds=struct.unpack('<2Id',payload)
            if actual!=frame or not math.isfinite(seconds) or seconds<0 or offset!=len(raw):
                raise ValueError('command journal end marker')
        records.append((kind,payload))
    if records[-1][0]!=6 or len(records[-1][1])!=16:raise ValueError('command journal incomplete')
    return dict(frame=frame,width=width,height=height,margin=margin,scale=scale,palette=palette,flags=flags),records

def load(directory,frame):
    directory=Path(directory);prefix=f'zeus-stream-{frame}'
    paths={suffix:directory/(prefix+'-'+suffix+'.bin') for suffix in ('wave','palette','records')}
    if (paths['wave'].stat().st_size!=16777216 or paths['palette'].stat().st_size!=262144 or
            not 40<paths['records'].stat().st_size<=LIMIT):raise ValueError('command journal file budgets')
    files={suffix:path.read_bytes() for suffix,path in paths.items()}
    if len(files['wave'])!=16777216 or len(files['palette'])!=262144:raise ValueError('command journal initial materials')
    header,records=parse(files['records'])
    if header['frame']!=frame:raise ValueError('command journal requested frame')
    return header,records,files

def verify(frame,text,directory):
    lines=re.findall(r'^MIDZ_DEPTH_STREAM_RESULT .*$',text,re.M)
    if not frame:
        if lines:raise ValueError('unrequested command journal')
        return None
    rows=re.findall(r'^MIDZ_DEPTH_STREAM_RESULT complete=(\d+) frame=(\d+) commands=(\d+) bytes=(\d+) written=(\d+) failed=(\d+) rejected=(\d+)$',text,re.M)
    if len(lines)!=1 or len(rows)!=1:raise ValueError('missing command journal completion')
    complete,actual,count,size,written,failed,rejected=map(int,rows[0])
    header,records,files=load(directory,frame)
    if (complete!=1 or actual!=frame or count!=len(records) or size!=len(files['records']) or written!=3 or failed or rejected):
        raise ValueError('command journal completion mismatch')
    return dict(passed=True,header=header,commands=count,record_counts=dict(sorted(Counter(k for k,_ in records).items())),
        upload_bytes=sum(len(p)-8 for k,p in records if k==5),
        sha256={k:hashlib.sha256(v).hexdigest() for k,v in files.items()},
        scope='Journal structure, material images, ordered upload bounds and completion only; pixels require independent playback.')
