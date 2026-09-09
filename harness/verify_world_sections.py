"""Independently reconstruct World section placement before any host loader trial.

New captures include the seven polynomial constants, allowing independent yaw
and section-matrix reconstruction. Palette/dynamic/list initialization stays out
of scope. Older captures explicitly report their missing orientation coverage.
"""
import argparse
import json
from pathlib import Path
from scenery_c31 import F, dot, signed
from verification import sha256_file, write_json


def yaw_matrix(angle, constants):
    """World B2DC/B304 range reduction and polynomial with C31 register precision."""
    if len(constants)!=7:raise ValueError('seven captured trig constants required')
    c=list(map(F.load,constants));half=F.load(0xff000000);pi_hi=F.load(0x01490000)
    def polynomial(v):
        square=v*v
        p=c[2]*square+c[3];p=p*square+c[4];p=p*square+c[5]
        return (p*square)*v+v
    negative=angle.value()<0;a=-angle if negative else angle
    n=(a*c[0]+half).fix();sign=-1 if negative else 1
    if n%2:sign=-sign
    sine=polynomial((a-F.integer(n)*pi_hi)-F.integer(n)*c[1])*F.integer(sign)
    n=((a+c[6])*c[0]+half).fix();v=F.integer(n)-half
    cosine=(polynomial((a-v*pi_hi)-v*c[1])*F.integer(-1 if n%2 else 1)).store()
    return [cosine,0x80000000,(-sine).store(),0x80000000,0,0x80000000,sine.store(),0x80000000,cosine]


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


def check(path,require_orientation=False):
    records=[json.loads(line) for line in path.read_text().splitlines()]
    if not records or [r['serial'] for r in records]!=list(range(1,len(records)+1)):
        raise ValueError('empty/incomplete section placement trace')
    evidence=[]
    for row in records:
        position,heading=placement(row)
        item=dict(serial=row['serial'],frame=row['frame'],object=row['object'],source=row['source'],
            section=row['section_tag']&65535,passed=position==row['actual'][1:4] and heading==row['actual'][20],
            position=position,actual_position=row['actual'][1:4],heading=heading,actual_heading=row['actual'][20])
        if 'trig_constants' in row:
            matrix=yaw_matrix(F.load(row['definition'][4])+F.load(row['heading']),row['trig_constants'])
            item['orientation_passed']=matrix==row['actual'][4:13]
            item['section_matrix_passed']=yaw_matrix(F.load(row['heading']),row['trig_constants'])==row['matrix']
            item['passed'] &= item['orientation_passed'] and item['section_matrix_passed']
        elif require_orientation:item['passed']=False
        evidence.append(item)
    return dict(schema=1,passed=all(r['passed'] for r in evidence),objects=len(records),
                sections=sorted({r['section_pointer'] for r in records}),
                distinct_section_headings=len({r['heading'] for r in records}),
                distinct_object_headings=len({r['actual'][20] for r in records}),
                offset_objects=sum(bool(r['section_flags']&8) for r in records),
                orientation_objects=sum('trig_constants' in r for r in records),
                require_orientation=require_orientation,
                source_sha256=sha256_file(path),evidence=evidence,
                scope='XYZ/heading; yaw and section matrix only when constants captured; other allocation effects unverified')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('trace',type=Path)
    ap.add_argument('--require-orientation',action='store_true')
    ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    result=check(args.trace,args.require_orientation);write_json(args.report,result)
    print('PASS' if result['passed'] else 'FAIL',args.report)
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
