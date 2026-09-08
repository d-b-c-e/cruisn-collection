"""Check native host math and captured pending scenes against independent Python."""
import argparse
import csv
import json
import lzma
import os
from pathlib import Path
import struct
import subprocess

from scenery_c31 import F
from world_host_scenery import camera_center, rotation_matrix, project, fast_quads
from verification import sha256_file, write_json


def memory_for_scene(rows,recip):
    if not rows or len({r['object'] for r in rows}) != len(rows):
        raise ValueError('ambiguous pending scene')
    first=rows[0]
    memory={0x41:0xd4b7,0x43:0x8099db,0x48:0x809a04,0x47:0x8099f7,0x4d:0xb66f,
            0x61ec:0x1000,0x1000:first['object']}
    def put(p,values):
        for i,v in enumerate(values):
            if p+i in memory and memory[p+i]!=v:raise ValueError('inconsistent captured memory')
            memory[p+i]=v
    put(0xd4b7,first['camera']);put(0x8099db,first['view'])
    put(0x809a04,first['billboard']);put(0x8099f9,first['origin'])
    for index,value in recip.items():put(0xb66f+index,[value])
    for row in rows:
        # World objects have 28-word stride. Extra trailing words were captured
        # to inspect the next allocation, but are not part of this object's state.
        put(row['object'],row['object_words'])
        if 'model_words' in row:
            put(row['model'],row['model_words']);put(row['model_words'][1],row['material_words'])
    return memory


def check(binary,run=None):
    env=dict(os.environ)
    if os.name=='nt':env['PATH']='E:/msys64/mingw64/bin;'+env.get('PATH','')
    fixture=Path(__file__).resolve().parents[1]/'fixtures/scenery/c31-vectors.json.xz'
    rows=json.loads(lzma.decompress(fixture.read_bytes()))['vectors']
    inputs=''.join(' '.join(map(str,r[:4]))+'\n' for r in rows)
    result=subprocess.run([str(binary),'--math'],input=inputs,capture_output=True,text=True,env=env,check=True)
    actual=[list(map(int,line.split())) for line in result.stdout.splitlines()]
    math_ok=actual==[r[4] for r in rows]
    scenes=[]
    runtime={}
    if run and (run/'world-host-quads.csv').is_file():
        for row in csv.DictReader((run/'world-host-quads.csv').open()):
            key=(int(row['frame']),int(row['page']))
            runtime.setdefault(key,[]).append([int(row[k]) for k in
                ('object','model','depth','section','flags','palette','x0','y0','x1','y1',
                 'x2','y2','x3','y3','uv0','uv1','uv2','uv3','texture','word15')])
    runtime_seen=set()
    if run:
        pending=[json.loads(x) for x in (run/'world-pending-models.jsonl').read_text().splitlines()]
        recip=dict(zip(range(-80,5000),struct.unpack('<5080I',(run/'world-transform-reciprocals.bin').read_bytes())))
        for frame in sorted({r['frame'] for r in pending}):
            entries=[r for r in pending if r['frame']==frame]
            memory=memory_for_scene(entries,recip)
            result=subprocess.run([str(binary),'--scene'],input=''.join(f'{a} {b}\n' for a,b in sorted(memory.items())),
                                  capture_output=True,text=True,env=env)
            if result.returncode:
                scenes.append(dict(frame=frame,passed=False,error=result.stderr.strip()));continue
            lines=[list(map(int,x.split())) for x in result.stdout.splitlines()]
            expected=[]
            for r in entries:
                if 'model_words' not in r:continue
                center=camera_center(r['object_words'],r['camera'],r['view'])
                depth=center[2].fix();radius=r['model_words'][0]
                if depth-radius<1000 or depth+radius>=80000:continue
                matrix=r['billboard'] if r['object_words'][14]&8 else [x.store() for x in rotation_matrix(r['object_words'],r['view'])]
                record=dict(r,fast=1,end_pc=0x242,matrix=matrix,camera_space=[x.store() for x in center]+r['origin'])
                quads=fast_quads(record,project(record,recip))
                for q in quads:expected.append([r['object'],r['model'],depth,r['object_words'][27]&65535,*q,0])
            expected.sort(key=lambda r:(-r[2],r[0]))
            item=dict(frame=frame,passed=lines[1:]==expected,counts=lines[0],quads=len(lines)-1,
                      host_quads=len(expected))
            if runtime:
                key=(entries[0]['emulator_frame'],entries[0]['page'])
                if key in runtime_seen:raise ValueError('duplicated emulator scene clock')
                runtime_seen.add(key)
                item['emulator_frame']=key[0]
                item['runtime_passed']=runtime.get(key,[])==expected
                item['passed'] &= item['runtime_passed']
            scenes.append(item)
    uncovered=sorted(set(runtime)-runtime_seen)
    return dict(schema=1,passed=math_ok and not uncovered and all(s['passed'] for s in scenes),
                math_vectors=len(rows),math_passed=math_ok,scenes=scenes,
                uncovered_runtime_scenes=uncovered,
                native_sha256=sha256_file(binary),fixture_sha256=sha256_file(fixture))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary',type=Path)
    parser.add_argument('--run',type=Path)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();result=check(args.binary,args.run)
    write_json(args.report,result);print('PASS' if result['passed'] else 'FAIL',args.report)
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
