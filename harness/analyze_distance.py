"""Summarize the USA object far-gate probe without treating sentinels as scenery.

This measures objects reaching the far test. It does not enumerate unloaded
models or prove that earlier culling, linked-list selection or streaming is correct.
"""
import argparse
import csv
from pathlib import Path
from verification import sha256_file, write_json


def summarize(rows):
    if not rows:
        raise ValueError('empty object trace')
    between = [r for r in rows if int(r['far_limit']) < int(r['depth_minus_radius']) <= 2 * int(r['far_limit'])]
    beyond = [r for r in rows if int(r['depth_minus_radius']) > 2 * int(r['far_limit'])]
    ordinary = [r for r in rows if int(r['depth_minus_radius']) <= 2 * int(r['far_limit'])]
    seen, changes = {}, []
    for r in rows:
        key = (r['object'], r['base_model'])
        previous = seen.get(key)
        if previous and previous['model'] != r['model']:
            changes.append({'object':r['object'], 'base_model':r['base_model'],
                            'before':previous, 'after':r})
        seen[key] = r
    return {'schema':1, 'scope':__doc__.strip(), 'samples':len(rows),
            'frames':len({r['frame'] for r in rows}),
            'objects':len({r['object'] for r in rows}),
            'far_limits':sorted({int(r['far_limit']) for r in rows}),
            'samples_newly_admitted_by_doubling_far_limit':len(between),
            'objects_newly_admitted_by_doubling_far_limit':sorted({r['object'] for r in between}),
            'samples_still_beyond_doubled_far_limit':len(beyond),
            'beyond_doubled_objects':sorted({r['object'] for r in beyond}),
            'maximum_depth_within_doubled_limit':max((int(r['depth_minus_radius']) for r in ordinary),default=None),
            'model_transitions':changes}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('trace',type=Path);ap.add_argument('--report',required=True)
    args=ap.parse_args()
    with args.trace.open(newline='',encoding='utf-8') as stream:
        result=summarize(list(csv.DictReader(stream)))
    result['trace_sha256']=sha256_file(args.trace)
    write_json(args.report,result)
    print(f"{result['samples_newly_admitted_by_doubling_far_limit']} samples in proposed extension; {len(result['model_transitions'])} model transitions")


if __name__=='__main__':main()
