"""Validate and summarize native global-distance counters, not visual quality."""
import argparse
import csv
from pathlib import Path
from verification import write_json, sha256_file
from world_distance import FAR_VALUES, MAXIMUM_LEAD

FIELDS = ['frame','far','lead','cpu_percent','profile_ok','far_tests',
          'extra_far_tests','extended_reads','maximum_index','pending_comparisons']


def summarize(path):
    path = Path(path)
    with path.open(newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError('unexpected native distance columns')
        rows = []
        for row in reader:
            if None in row or any(row[key] is None for key in FIELDS):
                raise ValueError('incomplete or extra distance fields')
            row = {k:int(v) for k,v in row.items()}
            if any(value < 0 for value in row.values()):
                raise ValueError('negative native distance value')
            if row['far'] not in FAR_VALUES or row['lead'] > MAXIMUM_LEAD or row['cpu_percent'] not in (100,125,150,200):
                raise ValueError('unsupported native distance configuration')
            if row['profile_ok'] not in (0,1) or row['extra_far_tests'] > row['far_tests']:
                raise ValueError('inconsistent native distance counters')
            if row['extended_reads']:
                if row['far']==80000 or not 5000 <= row['maximum_index'] <= row['far']//16:
                    raise ValueError('extended projection outside configured range')
            elif row['maximum_index']:
                raise ValueError('projection index without a read')
            if not row['lead'] and row['pending_comparisons']:
                raise ValueError('pending intervention while lookahead is disabled')
            rows.append(row)
    if not rows: raise ValueError('empty native distance log')
    frames = [r['frame'] for r in rows]
    if frames != list(range(frames[0],frames[-1]+1)):
        raise ValueError('distance frames must be contiguous and unique')
    configurations = {(r['far'],r['lead'],r['cpu_percent']) for r in rows}
    if len(configurations)!=1: raise ValueError('distance configuration changed during replay')
    ready = next((i for i,r in enumerate(rows) if r['profile_ok']), None)
    if ready is None: raise ValueError('World code profile was never observed')
    if any(r['profile_ok']!=1 for r in rows[ready:]):
        raise ValueError('World code profile disappeared after initialization')
    counters = ['far_tests','extra_far_tests','extended_reads','pending_comparisons']
    totals = {key:sum(r[key] for r in rows) for key in counters}
    if not totals['far_tests']: raise ValueError('no game distance tests observed')
    return {'schema':1, 'scope':__doc__, 'sha256':sha256_file(path), 'rows':len(rows),
            'frames':[frames[0],frames[-1]], 'first_profile_frame':rows[ready]['frame'],
            'far':rows[0]['far'], 'lead':rows[0]['lead'], 'cpu_percent':rows[0]['cpu_percent'],
            'totals':totals, 'maximum_index':max(r['maximum_index'] for r in rows),
            'peak_far_tests':max(r['far_tests'] for r in rows),
            'peak_extended_reads':max(r['extended_reads'] for r in rows)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path); parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args()
    write_json(args.report,summarize(args.log))


if __name__=='__main__': main()
