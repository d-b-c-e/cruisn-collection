"""Validate USA distance counters; activity is not proof of visible scenery."""
import argparse
import csv
from pathlib import Path
from verification import write_json, sha256_file
from usa_distance import FAR_VALUES

FIELDS = ['frame','far','residency','profile_ok','far_tests','extra_far_tests',
          'extended_reads','effect_reads','maximum_index','pending_comparisons','removal_comparisons']
COUNTERS = ['far_tests','extra_far_tests','extended_reads','effect_reads',
            'pending_comparisons','removal_comparisons']


def summarize(path):
    path = Path(path)
    with path.open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError('unexpected USA distance columns')
        rows = []
        for row in reader:
            if None in row or any(row[key] is None for key in FIELDS):
                raise ValueError('incomplete or extra USA distance fields')
            row = {k:int(v) for k,v in row.items()}
            if any(v < 0 for v in row.values()):
                raise ValueError('negative USA distance value')
            if row['far'] not in FAR_VALUES or row['residency'] not in (0,1) or row['profile_ok'] not in (0,1):
                raise ValueError('unsupported USA distance configuration')
            if row['extra_far_tests'] > row['far_tests'] or row['effect_reads'] > row['extended_reads']:
                raise ValueError('inconsistent USA distance counters')
            if row['extended_reads']:
                if row['far']==80000 or not 5000 <= row['maximum_index'] <= row['far']//16:
                    raise ValueError('USA projection outside configured range')
            elif row['maximum_index']:
                raise ValueError('projection index without a read')
            if not row['profile_ok'] and any(row[k] for k in COUNTERS):
                raise ValueError('USA activity without a valid code profile')
            rows.append(row)
    if not rows: raise ValueError('empty USA distance log')
    frames = [r['frame'] for r in rows]
    if frames != list(range(frames[0],frames[-1]+1)):
        raise ValueError('USA distance frames must be contiguous and unique')
    if len({(r['far'],r['residency']) for r in rows}) != 1:
        raise ValueError('USA distance configuration changed')
    ready = next((i for i,r in enumerate(rows) if r['profile_ok']), None)
    if ready is None or any(r['profile_ok']!=1 for r in rows[ready:]):
        raise ValueError('USA code profile missing or lost')
    totals = {key:sum(r[key] for r in rows) for key in COUNTERS}
    if not all(totals[k] for k in ('far_tests','pending_comparisons','removal_comparisons')):
        raise ValueError('USA renderer/residency consumers not all observed')
    return {'schema':1,'scope':__doc__,'sha256':sha256_file(path),'rows':len(rows),
            'frames':[frames[0],frames[-1]],'first_profile_frame':rows[ready]['frame'],
            'far':rows[0]['far'],'residency':rows[0]['residency'],'totals':totals,
            'maximum_index':max(r['maximum_index'] for r in rows)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path); parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args()
    write_json(args.report,summarize(args.log))


if __name__=='__main__': main()
