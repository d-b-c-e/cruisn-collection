"""Independently reconstruct World section placement before any host loader trial.

The source section matrix is an explicit input. Orientation/trig, palette setup,
dynamic initialization and list membership are outside this placement-only check.
"""
import argparse
import json
from pathlib import Path
from scenery_c31 import F, dot, signed
from verification import sha256_file, write_json


def placement(row):
    definition,section=row['definition'],row['section_words']
    position=[F.integer(signed(v)).reload() for v in definition[1:4]]
    if row['section_flags']&8:
        position=[(v+F.load(t)).reload() for v,t in zip(position,section[8:11])]
    matrix=list(map(F.load,row['matrix']))
    transformed=[dot(position,matrix[i:i+3]).reload() for i in (0,3)]
    # 90CD..90D3 use (X+Y)+Z; 90D4..90D7 schedule the last row as Y+(Z+X).
    transformed.append((position[1]*matrix[7]+
        (position[2]*matrix[8]+position[0]*matrix[6])).reload())
    position=[(v+F.load(t)).store() for v,t in zip(transformed,section[1:4])]
    heading=(F.load(definition[4])+F.load(row['heading'])).store()
    return position,heading


def check(path):
    records=[json.loads(line) for line in path.read_text().splitlines()]
    if not records or [r['serial'] for r in records]!=list(range(1,len(records)+1)):
        raise ValueError('empty/incomplete section placement trace')
    evidence=[]
    for row in records:
        position,heading=placement(row)
        evidence.append(dict(serial=row['serial'],frame=row['frame'],object=row['object'],source=row['source'],
            section=row['section_tag']&65535,passed=position==row['actual'][1:4] and heading==row['actual'][20],
            position=position,actual_position=row['actual'][1:4],heading=heading,actual_heading=row['actual'][20]))
    return dict(schema=1,passed=all(r['passed'] for r in evidence),objects=len(records),
                sections=sorted({r['section_pointer'] for r in records}),
                offset_objects=sum(bool(r['section_flags']&8) for r in records),
                source_sha256=sha256_file(path),evidence=evidence,
                scope='XYZ and heading only; section matrix is captured, other allocation effects unverified')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('trace',type=Path)
    ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    result=check(args.trace);write_json(args.report,result)
    print('PASS' if result['passed'] else 'FAIL',args.report)
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
