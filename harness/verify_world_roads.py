"""Check read-only World road transforms, template selection and ordered DMA.

Raw model/texture data stays local. Reports contain scalar verdicts and hashes.
Clipped polygon calls remain explicitly outside this reconstruction.
"""
import argparse,collections,csv,json,struct
from pathlib import Path
from scenery_c31 import F
from world_host_scenery import camera_center,rotation_matrix,project,fast_quads
from verify_world_transform import DMA_KEYS
from verification import sha256_file,write_json


def verify(run):
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
    failures=[];counts=collections.Counter()
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
        projected=project(row,reciprocals,matrix=matrix,center=center)
        check('projected_vertices',projected,row['projected'],call)
        if row['end_pc']==0x242:
            check('ordered_dma',fast_quads(row,projected),draws[call],call)
        else:counts['clipped_calls_excluded']+=1
    return dict(passed=not failures,scope=__doc__,hashes=hashes,summary=summary,
                counts=dict(counts),failures=failures,
                limitations=['Captured vertex/material resources are adapter inputs',
                             'Clipped polygon output and host-added road visibility are unverified'])


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('run',type=Path)
    ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    try:report=verify(args.run)
    except (ValueError,OSError,KeyError,struct.error) as error:report=dict(passed=False,error=str(error))
    write_json(args.report,report);print('PASS' if report['passed'] else 'FAIL',args.report)
    return int(not report['passed'])


if __name__=='__main__':raise SystemExit(main())
