"""Check read-only World road transforms, template selection and ordered DMA.

Raw model/texture data stays local. Reports contain scalar verdicts and hashes.
Clipped polygon calls remain explicitly outside this reconstruction.
"""
import argparse,collections,csv,json,struct,os,subprocess
from pathlib import Path
from scenery_c31 import F
from world_host_scenery import camera_center,rotation_matrix,project,fast_quads
from verify_world_transform import DMA_KEYS
from verification import sha256_file,write_json


def verify(run,native=None):
    names=['world-road-transform.jsonl','world-road-draws.csv',
           'world-road-reciprocals.bin','world-road-summary.json']
    hashes={name:sha256_file(run/name) for name in names}
    summary=json.loads((run/names[-1]).read_text())
    if not summary['completed']:raise ValueError('road capture did not complete')
    rows=[json.loads(line) for line in (run/names[0]).read_text().splitlines()]
    if not rows or [r['call'] for r in rows]!=list(range(1,len(rows)+1)):
        raise ValueError('missing or duplicated road calls')
    reciprocals=dict(zip(range(-80,5000),struct.unpack('<5080I',(run/names[2]).read_bytes())))
    draws=collections.defaultdict(list)
    for row in csv.DictReader((run/names[1]).open()):
        draws[int(row['call'])].append([int(row[k]) for k in DMA_KEYS])
    if (summary['starts']!=len(rows) or summary['projected']!=len(rows)
        or summary['draws']!=sum(map(len,draws.values())) or set(draws)-{r['call'] for r in rows}):
        raise ValueError('incomplete road evidence')
    failures=[];counts=collections.Counter();native_input=[];native_expected=[]
    def check(kind,actual,expected,call):
        counts[kind+'_checked']+=1;counts[kind+'_passed']+=actual==expected
        if actual!=expected:failures.append(dict(call=call,kind=kind))
    for row in rows:
        call=row['call'];obj=row['object_words']
        if obj[14]&0x801!=1 or row['model_words'][2]&0x300:
            raise ValueError('unsupported road dispatch or paired vertex layout')
        center=camera_center(obj,row['camera'],row['view'])
        matrix=rotation_matrix(obj,row['view'])
        check('center',[v.store() for v in center],row['camera_space'][:3],call)
        check('matrix',[v.store() for v in matrix],row['matrix'],call)
        far=center[2].fix()>=row['lod_threshold']
        counts['far_template_calls']+=far
        check('template_slot',((obj[15]&0xf000)>>12)-1,row['template_slot'],call)
        check('selected_model',row['template_model'] if far else row['original_model'],row['model'],call)
        if not far:check('near_header',row['original_header'],row['model_words'][2],call)
        if native:
            original=row['original_model'];words=row['model_words'];selected=row['model']
            memory={original:words[0],original+1:words[1] if not far else 0,
                    original+2:row['original_header'],0xd4c0:row['lod_threshold'],
                    0x624:row['template_table'],row['template_table']+row['template_slot']:row['template_model']}
            if far:memory.update({selected:words[2],selected+1:words[1]})
            native_input.append(' '.join(map(str,[center[2].fix(),*obj,len(memory),
                                *(v for pair in memory.items() for v in pair)])))
            native_expected.append([selected,words[0],words[2],row['vertices'],row['polygons'],original+3,
                                    selected+2 if far else original+3+2*row['vertices'],words[1],int(far)])
        projected=project(row,reciprocals,matrix=matrix,center=center)
        check('projected_vertices',projected,row['projected'],call)
        if row['end_pc']==0x242:
            check('ordered_dma',fast_quads(row,projected),draws[call],call)
        else:counts['clipped_calls_excluded']+=1
    if native:
        env=dict(os.environ)
        if os.name=='nt':env['PATH']='E:/msys64/mingw64/bin;'+env.get('PATH','')
        process=subprocess.run([str(native.resolve()),'--road-model'],input='\n'.join(native_input)+'\n',
                               text=True,capture_output=True,env=env,timeout=120)
        if process.returncode:raise ValueError('native road selector failed: '+process.stderr)
        actual=[list(map(int,line.split())) for line in process.stdout.splitlines()]
        if len(actual)!=len(rows):raise ValueError('missing native road selector output')
        for row,a,e in zip(rows,actual,native_expected):check('native_template',a,e,row['call'])
        hashes['native_binary']=sha256_file(native)
    return dict(passed=not failures,scope=__doc__,hashes=hashes,summary=summary,
                counts=dict(counts),failures=failures,
                limitations=['Captured vertex/material resources are adapter inputs',
                             'Clipped polygon output and host-added road visibility are unverified'])


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('run',type=Path)
    ap.add_argument('--report',type=Path,required=True);ap.add_argument('--native',type=Path);args=ap.parse_args()
    try:report=verify(args.run,args.native)
    except (ValueError,OSError,KeyError,struct.error) as error:report=dict(passed=False,error=str(error))
    write_json(args.report,report);print('PASS' if report['passed'] else 'FAIL',args.report)
    return int(not report['passed'])


if __name__=='__main__':raise SystemExit(main())
