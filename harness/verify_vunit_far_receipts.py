"""Verify ordered private far-quad transport and GPU preparation, offline.

Receipts precede DrawArrays. They prove identical packet delivery and shader-mask
preparation, not completed rasterization or live material ownership. Callers must
separately verify frame completion, original resources, display and timing.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gpu'))
from renderer import build_vertices

PACKET=struct.Struct('<IHH16H5I')
GPU_BYTES=124
MAX_BYTES=256*1024*1024

def expected_masks(packets,margin):
    quads=np.array([v[3:19] for v in packets],dtype='<u2')
    f,_=build_vertices(quads,margin,dilate2d=True)
    positions=f[::6,2:10].reshape(-1,4,2).astype('float64')
    masks=np.zeros((len(packets),16),dtype='<f4')
    for row,(packet,xy) in enumerate(zip(packets,positions)):
        far=packet[19]
        if far!=240000:raise ValueError('unsupported far-quad limit')
        depths=[]
        for word in packet[20:24]:
            exponent=word>>24
            if word&0x800000 or not 9<=exponent<=18:raise ValueError('invalid C31 depth encoding')
            depths.append(float((word&0x7fffff)|0x800000)*2.0**(exponent-23))
        if min(depths)<1000 or max(depths)>=480000 or not min(depths)<far<=max(depths):
            raise ValueError('far-quad depths do not describe a bounded crossing')
        vertices=[]
        for i in range(4):
            j=(i-1)%4
            if (depths[j]<far)!=(depths[i]<far):
                t=(1.0/far-1.0/depths[j])/(1.0/depths[i]-1.0/depths[j])
                if not 0<=t<=1:raise ValueError('invalid projected clipping fraction')
                vertices.append(xy[j]+t*(xy[i]-xy[j]))
            if depths[i]<far:vertices.append(xy[i])
        if not 3<=len(vertices)<=6:raise ValueError('invalid far coverage polygon')
        masks[row,0]=len(vertices);masks[row,4:4+2*len(vertices)]=np.array(vertices).ravel()
    return masks

def compare(source,gpu,first,last,*,margin=86):
    if not 0<=first<=last or not 0<=margin<=256:raise ValueError('invalid frame range or margin')
    source,gpu=Path(source),Path(gpu)
    sizes=[p.stat().st_size for p in (source,gpu)]
    if any(n<=4 or n>MAX_BYTES for n in sizes) or (sizes[0]-4)%60 or (sizes[1]-4)%GPU_BYTES:
        raise ValueError('empty, incomplete or oversized far receipt file')
    count=(sizes[0]-4)//60
    if count!=(sizes[1]-4)//GPU_BYTES:raise ValueError('producer/GPU receipt counts differ')
    hashes=[hashlib.sha256(),hashlib.sha256()];previous=-1;frames=set();clipped=0
    with source.open('rb') as a,gpu.open('rb') as b:
        for stream,magic,h in zip((a,b),(b'VFP1',b'VFG1'),hashes):
            header=stream.read(4)
            if header!=magic:raise ValueError('invalid far receipt header')
            h.update(header)
        for start in range(0,count,512):
            size=min(512,count-start);raw=a.read(size*60);prepared=b.read(size*GPU_BYTES)
            if len(raw)!=size*60 or len(prepared)!=size*GPU_BYTES:raise ValueError('far receipt changed while reading')
            hashes[0].update(raw);hashes[1].update(prepared)
            packets=list(PACKET.iter_unpack(raw));expected=expected_masks(packets,margin)
            for i,packet in enumerate(packets):
                frame=packet[0]
                if not first<=frame<=last or frame<previous:raise ValueError('far receipt frames outside scope or reordered')
                previous=frame;frames.add(frame)
                record=prepared[i*GPU_BYTES:(i+1)*GPU_BYTES]
                if record[:60]!=raw[i*60:(i+1)*60]:raise ValueError(f'far packet delivery differs at {start+i}')
                if record[60:]!=expected[i].tobytes():raise ValueError(f'GPU coverage preparation differs at {start+i}')
                clipped+=int(expected[i,0]>0)
        if a.read(1) or b.read(1):raise ValueError('far receipts grew during comparison')
    return dict(passed=True,packets=count,clipped=clipped,frames=len(frames),first=min(frames),last=max(frames),
        margin=margin,source_sha256=hashes[0].hexdigest(),gpu_sha256=hashes[1].hexdigest(),
        scope='Exact ordered producer packets and independently reconstructed GPU masks. Requires unaligned inclusive/dilated V-Unit corners; not completed pixel or material-lifetime acceptance.')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('source',type=Path);ap.add_argument('gpu',type=Path)
    ap.add_argument('--first',type=int,required=True);ap.add_argument('--last',type=int,required=True)
    ap.add_argument('--margin',type=int,default=86);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    try:result=compare(args.source,args.gpu,args.first,args.last,margin=args.margin)
    except (OSError,ValueError,struct.error) as exc:result=dict(passed=False,error=str(exc))
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS' if result['passed'] else 'FAIL',args.report)
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
