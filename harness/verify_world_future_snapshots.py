"""Compare future native descriptors and polygons with independent Python math.

Raw snapshots contain game resources and remain local. This does not validate
GPU visibility, palette contents, static lifetime or actual native scheduling.
"""
import argparse,csv,json,os,struct,subprocess
from collections import Counter
from pathlib import Path
from scenery_c31 import F
from world_future_sections import future,material_operands,descriptor
from verify_world_sections import yaw_matrix
from world_host_scenery import camera_center,rotation_matrix,model_counts,project,fast_quads,reciprocal_table
from verification import sha256_file,write_json


def check(run,allocations,binary,output):
    output.mkdir(parents=True,exist_ok=False)
    rom=(run/'world-future-rom.bin').read_bytes()
    if len(rom)!=0x1000000:raise ValueError('invalid ROM snapshot size')
    allocated=[json.loads(l) for l in allocations.read_text().splitlines()]
    bykey={}
    for a in allocated:bykey.setdefault((a['section_pointer'],a['source']),[]).append(a)
    env=dict(os.environ)
    if os.name=='nt':env['PATH']='E:/msys64/mingw64/bin;'+env.get('PATH','')
    results=[]
    for ram_path in sorted(run.glob('world-future-ram-*.bin')):
        frame=int(ram_path.stem.rsplit('-',1)[1]);fast_path=run/f'world-future-fast-{frame}.bin'
        ram=ram_path.read_bytes();fast=fast_path.read_bytes()
        if len(ram)!=0x80000 or len(fast)!=0x2000:raise ValueError('invalid RAM snapshot size')
        def read(p):
            if 0<=p<0x20000:return struct.unpack_from('<I',ram,p*4)[0]
            if 0xc00000<=p<0x1000000:return struct.unpack_from('<I',rom,(p-0xc00000)*4)[0]
            if 0x809800<=p<0x80a000:return struct.unpack_from('<I',fast,(p-0x809800)*4)[0]
            raise ValueError('unmapped snapshot read')
        def execute(mode,far):
            r=subprocess.run([str(binary.resolve()),mode,str(ram_path.resolve()),str((run/'world-future-rom.bin').resolve()),
                str(fast_path.resolve()),str(far)],env=env,capture_output=True,text=True)
            name=f'{frame}-{mode[2:]}-{far}'
            (output/(name+'.txt')).write_text(r.stdout);(output/(name+'.log')).write_text(r.stderr)
            if r.returncode:raise ValueError(r.stderr)
            return [list(map(int,l.split())) for l in r.stdout.splitlines()]
        raw=execute('--descriptors',240000)
        actual_native={(r[0],r[1]):(r[2],r[3:]) for r in raw[1:]}
        if len(actual_native)!=len(raw)-1:raise ValueError('duplicate future descriptor identity')
        listing=future(read);expected={};later=0;already=0;later_failures=[]
        for row in listing['definitions']:
            metadata=row['definition'][5]
            if ((metadata>>8)&15) in (10,11):continue
            resources,index,override=material_operands(read,row['definition'])
            row.update(binding_resources=resources,override_index=index,override_lookup=override,
                trig_constants=[read(0xcc35+i) for i in range(7)],section_tag=row['section_pointer'])
            row['matrix']=yaw_matrix(F.load(row['heading']),row['trig_constants'])
            obj=descriptor(row)
            if obj[14]&0x861 or any(v>65535 for v in obj[16:18]):continue
            key=row['section_pointer'],row['source'];expected[key]=obj+[0]*4
            for a in bykey.get(key,[]):
                if a['frame']<frame:already+=1;continue
                later+=1
                different=[i for i in [*range(1,18),20] if obj[i]!=a['final'][i]]
                if different:later_failures.append(dict(serial=a['serial'],fields=different))
        descriptor_ok=expected=={k:v[1] for k,v in actual_native.items()}
        if not descriptor_ok:raise ValueError(f'native descriptors differ at {frame}')
        camera=[read(read(0x41)+i) for i in range(3)];view=[read(read(0x43)+i) for i in range(9)]
        bill=[read(read(0x48)+i) for i in range(9)];origin=[read(read(0x47)+2+i) for i in range(2)]
        original={i:read(0xb66f+i) for i in range(-80,5000)}
        scenes=[]
        for far in (80000,160000,240000):
            rows=execute('--scene',far)[1:];actual_quads=[r for r in rows if r[0]>=0x80000000]
            projected=[];recip=reciprocal_table(original,far);objects=0
            for key,obj in expected.items():
                center=camera_center(obj,camera,view);depth=center[2].fix();model=obj[13];radius=read(model)
                if depth-radius<1000 or depth+radius>=far:continue
                pairs,singles,polygons=model_counts(read(model+2));objects+=1
                model_words=[read(model+i) for i in range(3+2*(pairs+singles)+2*polygons)]
                materials=[read(model_words[1]+i) for i in range(3*polygons)]
                matrix=bill if obj[14]&8 else [f.store() for f in rotation_matrix(obj,view)]
                record=dict(object_words=obj,model_words=model_words,material_words=materials,fast=1,end_pc=0x242,
                    matrix=matrix,camera_space=[f.store() for f in center]+origin)
                try:q=fast_quads(record,project(record,recip))
                except ValueError as error:
                    if 'uncaptured reciprocal index' in str(error):continue
                    raise
                identifier=actual_native[key][0]
                projected += [[identifier,model,depth,obj[27]&65535,*words,0] for words in q]
            projected.sort(key=lambda r:(-r[2],r[0]))
            scenes.append(dict(far=far,passed=projected==actual_quads,future_objects=objects,
                future_quads=len(actual_quads),expected_quads=len(projected),pending_quads=len(rows)-len(actual_quads)))
        results.append(dict(frame=frame,passed=descriptor_ok and not already and not later_failures and all(s['passed'] for s in scenes),
            descriptors=len(expected),later_allocations=later,already_allocated=already,later_failures=later_failures,
            native_counts=raw[0],stop=listing['stop'],scenes=scenes))
    return dict(passed=bool(results) and all(r['passed'] for r in results),results=results,
        binary_sha256=sha256_file(binary),allocation_sha256=sha256_file(allocations),
        input_hashes={p.name:sha256_file(p) for p in sorted(run.glob('world-future-*.bin'))},
        scope=__doc__)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('run',type=Path)
    ap.add_argument('allocations',type=Path);ap.add_argument('binary',type=Path)
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    report=check(args.run,args.allocations,args.binary,args.output)
    write_json(args.output/'report.json',report);print('PASS' if report['passed'] else 'FAIL',args.output/'report.json')
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
