"""Compare Zeus submissions with their effective palettes; retain strict ordering failures."""
import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import struct

from zeus_capture import parse_records, validate


def digest(data):
    return hashlib.sha256(data).hexdigest()


def signatures(directory,alignment='frame'):
    if alignment not in ('frame','scene'):raise ValueError('unsupported Zeus alignment')
    directory=Path(directory)
    palette=digest((directory/'pal_table.bin').read_bytes())
    result=[]
    for kind,payload in parse_records(directory/'records.bin'):
        if kind==2:palette=digest(payload)
        if kind==1 and alignment=='scene':payload=bytes(4)+payload[4:]
        result.append((kind,digest(payload),palette if kind==1 else None))
    return result


def compare(reference,candidate,frame,alignment='frame'):
    reference,candidate=Path(reference),Path(candidate)
    refs,cands=validate(reference,frame),validate(candidate,frame)
    original,changed=signatures(reference,alignment),signatures(candidate,alignment)
    ops=difflib.SequenceMatcher(a=original,b=changed,autojunk=False).get_opcodes()
    edits=[dict(operation=op,reference=[a,b],candidate=[c,d]) for op,a,b,c,d in ops if op!='equal']
    only_additions=all(e['operation']=='insert' for e in edits)
    resources_equal=all(refs['sha256'][n]==cands['sha256'][n] for n in ('waveram.bin','pal_table.bin'))
    records=parse_records(candidate/'records.bin')
    additions=[]
    for op,a,b,c,d in ops:
        if op=='equal':continue
        for index in range(c,d):
            kind,payload=records[index]
            if kind!=1:continue
            n=struct.unpack_from('<I',payload,4)[0]
            vertices=struct.unpack_from('<'+str(n*6)+'f',payload,68)
            additions.append(dict(record=index,frame=struct.unpack_from('<I',payload)[0],
                sha256=digest(payload),xy=[[vertices[i*6],vertices[i*6+1]] for i in range(n)]))
    result=dict(verdict='PASS' if only_additions and resources_equal else 'FAIL',
        scope='Original submissions and effective palettes preserved in order, with optional additions; pair with completed GL and pose evidence.',
        reference=refs,candidate=cands,resources_equal=resources_equal,only_additions=only_additions,
        edits=edits,original_records=len(original),candidate_records=len(changed),
        equal_records=sum(b-a for op,a,b,c,d in ops if op=='equal'),
        changed_candidate_quads=additions,reference_signatures=original,candidate_signatures=changed)
    if alignment=='scene':
        reference_records=parse_records(reference/'records.bin')
        frame_changes=[]
        for op,a,b,c,d in ops:
            if op!='equal':continue
            for i,j in zip(range(a,b),range(c,d)):
                ka,pa=reference_records[i];kb,pb=records[j]
                if ka==1 and pa[:4]!=pb[:4]:
                    frame_changes.append(dict(reference_record=i,candidate_record=j,
                        reference_frame=struct.unpack_from('<I',pa)[0],candidate_frame=struct.unpack_from('<I',pb)[0]))
        result.update(alignment='scene',ignored_frame_changes=frame_changes,
            scope='Original ordered submissions and effective palettes, excluding ONLY quad frame stamps. Does not establish frame timing equality; retain the strict frame comparison.')
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('reference',type=Path);ap.add_argument('candidate',type=Path)
    ap.add_argument('--frame',type=int,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--alignment',choices=('frame','scene'),default='frame',help='scene excludes only quad frame stamps; retain a separate strict comparison')
    args=ap.parse_args();report=compare(args.reference,args.candidate,args.frame,args.alignment)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['verdict'],len(report['edits']),'edits;',report['equal_records'],'unchanged records')
    return int(report['verdict']!='PASS')


if __name__=='__main__':raise SystemExit(main())
