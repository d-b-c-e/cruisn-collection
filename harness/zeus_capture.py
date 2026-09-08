"""Strict Zeus submission/resource capture validation; live CPU buffers are not a visual oracle."""
from collections import Counter
import math
from pathlib import Path
import struct
from verification import required_files,sha256_file

SIZES={1:260,2:1024,3:16,4:24}
ARTIFACTS=('records.bin','regs.txt','waveram.bin','pal_table.bin','pre_color.bin','pre_depth.bin','post_color.bin','post_depth.bin')


def parse_records(path):
    raw=Path(path).read_bytes();records=[];offset=0
    while offset<len(raw):
        if len(raw)-offset<8:raise ValueError('truncated Zeus record header')
        kind,size=struct.unpack_from('<II',raw,offset);offset+=8
        if kind not in SIZES or size!=SIZES[kind]:raise ValueError('unknown Zeus record type or invalid payload size')
        if size>len(raw)-offset:raise ValueError('truncated Zeus record payload')
        payload=raw[offset:offset+size];offset+=size
        if kind==1:
            frame,vertices=struct.unpack_from('<II',payload)
            if not 3<=vertices<=8:raise ValueError('invalid Zeus vertex count')
            if not all(math.isfinite(v) for v in struct.unpack_from('<'+str(vertices*6)+'f',payload,68)):
                raise ValueError('nonfinite Zeus vertex')
        records.append((kind,payload))
    if not records:raise ValueError('empty Zeus record stream')
    return records


def validate(directory,frame):
    directory=Path(directory);required_files(directory,ARTIFACTS)
    sizes={'waveram.bin':16777216,'pal_table.bin':1024,
           **{n:4194304 for n in ('pre_color.bin','pre_depth.bin','post_color.bin','post_depth.bin')}}
    for name,size in sizes.items():
        if (directory/name).stat().st_size!=size:raise ValueError('unexpected Zeus resource size: '+name)
    records=parse_records(directory/'records.bin');counts=Counter(kind for kind,_ in records)
    frames=Counter(struct.unpack_from('<I',payload)[0] for kind,payload in records if kind==1)
    if not frames or any(n not in (frame-1,frame) for n in frames):raise ValueError('Zeus quads do not cover the requested frame window')
    return dict(scope=__doc__,requested_frame=frame,quad_frames=dict(sorted(frames.items())),
                record_counts=dict(sorted(counts.items())),sha256={n:sha256_file(directory/n) for n in ARTIFACTS})
