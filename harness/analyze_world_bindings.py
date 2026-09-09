"""Check captured World allocation writes without inferring a material decoder.

The write-tap's final value must equal the independently captured ready object.
This identifies actual producer PCs and source-register contexts; it does not
prove how to initialize future objects or that their resources are resident.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from verification import sha256_file, write_json


def check(placements, bindings):
    objects=[json.loads(line) for line in placements.read_text().splitlines()]
    writes=[json.loads(line) for line in bindings.read_text().splitlines()]
    if not objects or [r['serial'] for r in objects]!=list(range(1,len(objects)+1)):
        raise ValueError('empty/incomplete allocation trace')
    if not writes:
        raise ValueError('no binding writes observed')
    by_serial={r['serial']:r for r in objects}
    last={}; initial={}; pcs=Counter(); faults=[]
    for w in writes:
        r=by_serial.get(w['serial']);field=w['field']
        if r is None or r['object']!=w['object'] or field not in (16,17):
            raise ValueError('binding write has no matching allocation owner/field')
        if not r.get('binding_first_frame',r['frame'])<=w['frame']<=r['end_frame'] or w['mask']!=0xffffffff:
            raise ValueError('binding write is outside its allocation or partial')
        if len(w['registers'])!=8 or len(w['sources'])%10 or len(w['code'])!=6:
            raise ValueError('incomplete source-register or producer-code context')
        last[w['serial'],field]=w['value'];pcs[field,w['pc']]+=1
        if w.get('phase')==0:
            key=w['serial'],field
            if key in initial:
                raise ValueError('duplicate initial binding write')
            initial[key]=w['value']
    changed_without_write=0
    for r in objects:
        if 'initial' not in r or len(r['initial'])!=28 or len(r['actual'])!=28:
            raise ValueError('missing independent before/after object snapshot')
        for field in (16,17):
            key=r['serial'],field
            if r.get('binding_scope')==3:
                resources=r.get('binding_resources',[])
                if len(resources)!=6:
                    raise ValueError('incomplete resource lookup operands')
                if initial.get(key)!=resources[field-12]:
                    faults.append(dict(serial=r['serial'],field=field,reason='missing or incorrect initial resource lookup'))
            if key in last:
                if last[key]!=r['actual'][field]:
                    faults.append(dict(serial=r['serial'],field=field,reason='final write differs from ready object'))
            elif r['initial'][field]!=r['actual'][field]:
                changed_without_write+=1
                faults.append(dict(serial=r['serial'],field=field,reason='changed binding lacks a captured write'))
    return dict(schema=1,passed=not faults,objects=len(objects),writes=len(writes),
                observed_fields=len(last),changed_without_write=changed_without_write,
                preallocation_writes=sum(w.get('phase')==0 for w in writes),
                both_fields_observed_objects=sum(all((r['serial'],f) in last for f in (16,17)) for r in objects),
                allocator_scope_objects=sum(r.get('binding_scope')==3 for r in objects),
                initial_lookup_fields=len(initial),
                producers=[dict(field=f,pc=pc,writes=n) for (f,pc),n in sorted(pcs.items())],
                failures=faults,placements_sha256=sha256_file(placements),bindings_sha256=sha256_file(bindings),
                scope='captured allocation writes versus ready object; future material decoding/residency unverified')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('placements',type=Path);ap.add_argument('bindings',type=Path)
    ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    report=check(args.placements,args.bindings);write_json(args.report,report)
    print('PASS' if report['passed'] else 'FAIL',args.report)
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
