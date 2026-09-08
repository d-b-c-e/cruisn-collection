"""Validate native Off Road global-distance traces, not visual or route acceptance."""
import argparse
from collections import Counter
import csv
from pathlib import Path
import re
from verification import sha256_file,write_json

FIELDS='frame multiplier profile_ok far_tests stock_rejects far_rejects extra_admissions clip_reads ceiling_reads'.split()
TABLE_FIELDS='frame pc opcode reads extended_reads minimum_index maximum_index upper_clamps'.split()


def projection_sites():
    source=(Path(__file__).resolve().parents[1]/'native/offroad_distance.h').read_text(encoding='utf-8')
    block=source.split('constexpr word projection_sites[]={',1)[1].split('};',1)[0]
    pairs=re.findall(r'\{(0x[0-9a-f]+),(0x[0-9a-f]+)\}',block)
    sites={int(a,16)+1:int(v,16) for a,v in pairs}
    if len(sites)!=59 or len(pairs)!=59:raise ValueError('unexpected Off Road consumer profile')
    return sites


def rows(path,fields):
    with Path(path).open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=fields:raise ValueError('unexpected Off Road native columns')
        for row in reader:
            if None in row or any(v is None for v in row.values()):raise ValueError('incomplete Off Road native row')
            yield {k:int(v,16 if k in ('pc','opcode') else 10) for k,v in row.items()}


def summarize(directory,expected_frames=None):
    directory=Path(directory);totals=Counter();frames={};multiplier=None
    for r in rows(directory/'offroad-native.csv',FIELDS):
        frame=r['frame'];m=r['multiplier']
        if frame!=len(frames) or m not in (1,2,3) or (multiplier is not None and m!=multiplier):
            raise ValueError('missing/duplicate frame or invalid/changing multiplier')
        multiplier=m
        if (any(v<0 for v in r.values()) or r['profile_ok'] not in (0,1)
                or (any(r[k] for k in FIELDS[3:]) and not r['profile_ok'])
                or r['stock_rejects']>r['far_tests']
                or r['far_rejects']+r['extra_admissions']!=r['stock_rejects']
                or (m==1 and r['extra_admissions'])):
            raise ValueError('inconsistent Off Road native culler counters')
        frames[frame]=r;totals.update({k:r[k] for k in FIELDS[3:]})
    if not frames or (expected_frames is not None and len(frames)!=expected_frames):
        raise ValueError('empty/incomplete native distance log')
    if not all(totals[k] for k in ('far_tests','clip_reads','ceiling_reads')):
        raise ValueError('missing gameplay limit-consumer coverage')
    limit=63680*multiplier-1;sites=projection_sites();previous=(-1,-1);consumers={}
    for r in rows(directory/'offroad-native-projection.csv',TABLE_FIELDS):
        frame,pc=r['frame'],r['pc'];key=(frame,pc)
        n,extra,lo,hi,clamps=(r[k] for k in TABLE_FIELDS[3:])
        if (key<=previous or frame not in frames or not frames[frame]['profile_ok']
                or sites.get(pc)!=r['opcode'] or not -4096<=lo<=hi<=limit
                or n<1 or not 0<=extra<=n or not 0<=clamps<=n
                or (clamps and hi!=limit) or (hi==limit and not clamps)
                or bool(extra)!=(hi>=63680) or (lo>=63680 and extra!=n)):
            raise ValueError('invalid native projection consumer/range/count/order')
        previous=key
        v=consumers.setdefault(f'{pc:x}',dict(opcode=r['opcode'],reads=0,extended_reads=0,
                                            minimum_index=lo,maximum_index=hi,upper_clamps=0,frames=0))
        for k in ('reads','extended_reads','upper_clamps'):v[k]+=r[k]
        v['frames']+=1;v['minimum_index']=min(v['minimum_index'],lo);v['maximum_index']=max(v['maximum_index'],hi)
    if '1c45' not in consumers:raise ValueError('missing main culler reciprocal consumer')
    return dict(verdict='PASS',scope=__doc__,frames=len(frames),multiplier=multiplier,far=47296*multiplier,
                clip=limit+1,totals=dict(totals),consumers=consumers,
                table_reads=sum(v['reads'] for v in consumers.values()),
                extended_reads=sum(v['extended_reads'] for v in consumers.values()),
                maximum_index=max(v['maximum_index'] for v in consumers.values()),
                table_clamps=sum(v['upper_clamps'] for v in consumers.values()),
                sources={n:sha256_file(directory/n) for n in ('offroad-native.csv','offroad-native-projection.csv')})


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('directory',type=Path)
    ap.add_argument('--frames',type=int);ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args();report=summarize(args.directory,args.frames);write_json(args.output,report)
    print(report['verdict'],report['frames'],report['totals'],report['extended_reads'])
