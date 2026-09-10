"""Bounded private Zeus depth controls and independent readback integrity checks."""
import csv
import hashlib
import math
from pathlib import Path
import re
import numpy as np
import zeus_command_stream

KEYS=('MIDZ_DEPTH_MIRROR','MIDZ_DEPTH_FIRST','MIDZ_DEPTH_LAST','MIDZ_DEPTH_SNAPSHOTS','MIDZ_DEPTH_STREAM_FRAME')


def add_arguments(parser):
    parser.add_argument('--zeus-depth-mirror',choices=('off','observe','wide'),help='private D32F: strict compatibility or wider-depth observation; displayed target stays original')
    parser.add_argument('--zeus-depth-first',type=int)
    parser.add_argument('--zeus-depth-last',type=int)
    parser.add_argument('--zeus-depth-snapshots',help='up to16 comma-separated completed frames; omit for timing-only observation')
    parser.add_argument('--zeus-depth-stream-frame',type=int,help='capture one consumer command/upload interval; requires this and the preceding frame as raw snapshots')


def configure(args,rom,settings,frames):
    mode=getattr(args,'zeus_depth_mirror',None)
    values=[getattr(args,'zeus_depth_'+name,None) for name in ('first','last','snapshots','stream_frame')]
    if mode is None and any(v is not None for v in values):raise ValueError('depth mirror bounds require explicit mode')
    if mode is not None:
        if mode not in ('off','observe','wide') or not getattr(args,'candidate',None):raise ValueError('depth mirror requires an explicit candidate')
        for key in KEYS:settings.pop(key,None)
        if mode=='off':
            if any(v is not None for v in values):raise ValueError('disabled depth mirror has bounds')
            return dict(enabled=False,explicit=True)
        if values[0] is None or values[1] is None:raise ValueError('depth mirror requires first and last frames')
        settings.update(zip(KEYS,('2' if mode=='wide' else '1',str(values[0]),str(values[1]),values[2] or '')))
        if values[3] is not None:settings[KEYS[4]]=str(values[3])
    if 'MIDZ_DEPTH_MIRROR' not in settings:
        if any(k in settings for k in KEYS[1:]):raise ValueError('orphan depth mirror bounds')
        return None
    if (rom!='crusnexo' or settings['MIDZ_DEPTH_MIRROR'] not in ('1','2') or settings.get('MIDZ_GL')!='1' or
            getattr(args,'headless',False) or getattr(args,'native_renderer',False) or settings.get('MIDZ_HOST_ACTIVE','0')!='0'):
        raise ValueError('depth mirror requires Exotica/live GL and no late host drawing')
    if not all(re.fullmatch('[0-9]+',settings.get(k,'')) for k in KEYS[1:3]):raise ValueError('invalid depth mirror interval')
    first,last=(int(settings[k]) for k in KEYS[1:3]);limit=getattr(args,'until_frame',None) or frames
    if not 1<=first<=last<=16000 or last-first>10000 or last>=limit:raise ValueError('depth mirror interval exceeds replay bounds')
    raw=settings.get(KEYS[3],'')
    if raw and not re.fullmatch('[0-9]+(?:,[0-9]+)*',raw):raise ValueError('invalid depth mirror snapshots')
    snapshots=[int(v) for v in raw.split(',')] if raw else []
    if len(snapshots)>16 or len(snapshots)!=len(set(snapshots)) or any(not first<=v<=last for v in snapshots):raise ValueError('depth mirror snapshot bounds')
    stream=settings.get(KEYS[4])
    if stream is not None:
        if not re.fullmatch('[0-9]+',stream):raise ValueError('invalid command journal frame')
        stream=int(stream)
        if not first<stream<=last or stream-1 not in snapshots or stream not in snapshots:
            raise ValueError('command journal requires both boundary snapshots')
    return dict(enabled=True,explicit=mode is not None,mode='wide' if settings['MIDZ_DEPTH_MIRROR']=='2' else 'observe',first=first,last=last,snapshots=sorted(snapshots),
                **({'stream_frame':stream} if stream is not None else {}))


def compare_buffers(original_color,mirror_color,original_depth,mirror_depth):
    sizes={len(v) for v in (original_color,mirror_color,original_depth,mirror_depth)}
    if len(sizes)!=1 or not len(original_color) or len(original_color)%4:raise ValueError('depth mirror buffer dimensions')
    colors=np.frombuffer(original_color,np.uint8).reshape(-1,4);copy=np.frombuffer(mirror_color,np.uint8).reshape(-1,4)
    codes=np.frombuffer(original_depth,'<u4')>>8
    expected=np.ldexp(codes.astype(np.float32),-26);expected[codes==0xffffff]=1
    actual=np.frombuffer(mirror_depth,'<f4')
    color_count=int(np.count_nonzero(np.any(colors!=copy,axis=1)))
    depth_count=int(np.count_nonzero(actual!=expected))
    return dict(passed=not color_count and not depth_count,color_differences=color_count,depth_differences=depth_count,
        sha256=[hashlib.sha256(v).hexdigest() for v in (original_color,mirror_color,original_depth,mirror_depth)])


def inspect_wide_buffers(original_color,mirror_color,original_depth,mirror_depth):
    """Check integrity and quantify changes; D24 cannot recover pre-clamp depth."""
    result=compare_buffers(original_color,mirror_color,original_depth,mirror_depth)
    actual=np.frombuffer(mirror_depth,'<f4')
    valid=bool(np.all(np.isfinite(actual)) and np.all((actual>=0)&(actual<=1)))
    return dict(result,passed=valid,compatibility_equal=result['passed'],pixel_depth_policy_verified=False,
        minimum_depth=float(actual.min()) if valid else None,maximum_depth=float(actual.max()) if valid else None,
        scope='Wide readback integrity and differences from compatibility only; requires a separate pre-clamp geometry/clear oracle.')


def verify_receipt(trial,text,directory):
    initial=re.findall(r'^MIDZ_DEPTH_MIRROR=([12]) first=(\d+) last=(\d+) snapshots=(\d+)$',text,re.M)
    if len(re.findall(r'^MIDZ_DEPTH_MIRROR=.*$',text,re.M))!=len(initial):raise ValueError('invalid depth mirror acknowledgment')
    final=re.findall(r'^MIDZ_DEPTH_MIRROR_RESULT complete=(\d+) frames=(\d+) batches=(\d+) vertices=(\d+) clears=(\d+) snapshots=(\d+) remaining=(\d+)$',text,re.M)
    writer=re.findall(r'^MIDZ_DEPTH_MIRROR_WRITER submitted=(\d+) written=(\d+) failed=(\d+) rejected=(\d+) peak_bytes=(\d+) write_total_us=(\d+) write_max_us=(\d+) drain_us=(\d+) waits=(\d+) wait_us=(\d+)$',text,re.M)
    if not trial or not trial['enabled']:
        if initial or final or writer:raise ValueError('disabled depth mirror ran')
        zeus_command_stream.verify(None,text,directory)
        return None
    first,last,captures=trial['first'],trial['last'],trial['snapshots'];count=last-first+1
    mode=trial.get('mode','observe')
    if mode not in ('observe','wide'):raise ValueError('unknown depth mirror policy')
    wide=mode=='wide'
    if initial!=[('2' if wide else '1',str(first),str(last),str(len(captures)))] or len(final)!=1 or len(writer)!=1:raise ValueError('missing depth mirror acknowledgments')
    complete,frames,batches,vertices,clears,saved,remaining=map(int,final[0])
    if (complete!=1 or frames!=count or saved!=len(captures) or remaining or not 0<batches<=vertices or
            vertices%3 or not clears):raise ValueError('incomplete depth mirror')
    submitted,written,failed,rejected,peak,total,maximum,drain,waits,wait_us=map(int,writer[0])
    if submitted!=4*len(captures) or written!=submitted or failed or rejected or peak>512*1024*1024 or maximum>total or waits>submitted:raise ValueError('incomplete depth mirror writer')
    path=Path(directory)/'zeus-depth-mirror.csv'
    if path.stat().st_size>4*1024*1024:raise ValueError('depth mirror log budget')
    with path.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    if [int(r['frame']) for r in rows]!=list(range(first,last+1)):raise ValueError('depth mirror frame coverage')
    previous=(0,0,0);results=[]
    for row in rows:
        frame=int(row['frame']);width,height=int(row['width']),int(row['height']);scale=height//1024
        if scale not in (1,2,3,4) or height!=scale*1024 or width%scale or not 512<=width//scale<=752 or (width//scale-512)%2:raise ValueError('depth mirror framebuffer size')
        current=tuple(int(row[k]) for k in ('batches','vertices','clears'))
        if any(a>b for a,b in zip(previous,current)) or any(a>b for a,b in zip(current,(batches,vertices,clears))):raise ValueError('depth mirror cumulative counts')
        previous=current
        differences=tuple(int(row[k]) for k in ('color_differences','depth_differences'))
        if (int(row['snapshot'])!=int(frame in captures) or any(not 0<=v<=width*height for v in differences)
                or (not wide or frame not in captures) and any(differences) or
                any(not math.isfinite(float(row[k])) or float(row[k])<0 for k in ('mirror_us','snapshot_us'))):raise ValueError('depth mirror comparison failed')
        if frame in captures:
            buffers=[]
            for suffix in ('original-color','mirror-color','original-depth','mirror-depth'):
                p=Path(directory)/f'zeus-depth-{frame}-{suffix}.bin'
                if p.stat().st_size!=width*height*4:raise ValueError('incomplete depth mirror readback')
                buffers.append(p.read_bytes())
            result=(inspect_wide_buffers if wide else compare_buffers)(*buffers)
            if not result['passed']:raise ValueError(f'independent depth mirror comparison failed at{frame}')
            if (result['color_differences'],result['depth_differences'])!=differences:raise ValueError('native/independent depth readback counters differ')
            results.append(dict(frame=frame,**result))
    stream=zeus_command_stream.verify(trial.get('stream_frame'),text,directory)
    return dict(passed=True,frames=count,batches=batches,vertices=vertices,clears=clears,snapshots=results,
        **({'command_stream':stream} if stream is not None else {}),
        pixel_depth_policy_verified=not wide,
        scope=('Private wide readback integrity and original-command counters; pixel depth policy and any future drawing need separate oracles. No handover acceptance.' if wide else
               'Original-only private color/D32F comparison at requested frames. No farther scenery, general handover or full visual acceptance.'))
