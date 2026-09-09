"""Verify PC-owned descriptor fields against final guest allocation snapshots."""
import argparse,json
from collections import Counter
from pathlib import Path
from verification import sha256_file,write_json
from world_future_sections import descriptor


def check(path):
    rows=[json.loads(l) for l in path.read_text().splitlines()]
    if not rows or [r['serial'] for r in rows]!=list(range(1,len(rows)+1)):
        raise ValueError('incomplete final allocation trace')
    compared=0;eligible=0;excluded=Counter();failures=[];changes=Counter()
    fields=[*range(1,18),20,27]
    for row in rows:
        if len(row['final'])!=28 or row['final_frame']<row['end_frame']:
            raise ValueError('incomplete final object state')
        kind=(row['definition'][5]>>8)&15
        for k,(a,b) in enumerate(zip(row['actual'],row['final'])):
            if a!=b:changes[kind,k]+=1
        expected=descriptor(row)
        if expected is None:excluded[kind]+=1;continue
        compared+=1;eligible+=not bool(expected[14]&0x861)
        for field in fields:
            if expected[field]!=row['final'][field]:
                failures.append(dict(serial=row['serial'],field=field,expected=expected[field],actual=row['final'][field]))
    return dict(passed=not failures,objects=len(rows),compared=compared,eligible_packed=eligible,
        excluded_classes=dict(sorted(excluded.items())),fields=fields,failures=failures,
        final_changes=[dict(kind=k,field=f,count=n) for (k,f),n in sorted(changes.items())],
        source_sha256=sha256_file(path),scope='Descriptor fields at final allocation boundary; future material residency, static lifetime, GPU rendering and handover unverified')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('trace',type=Path)
    ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    r=check(args.trace);write_json(args.report,r);print('PASS' if r['passed'] else 'FAIL',args.report)
    return 0 if r['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
