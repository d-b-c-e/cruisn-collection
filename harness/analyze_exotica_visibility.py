"""Validate buffered native Exotica visibility counters; admissions are not visible pixels."""
import argparse
from collections import Counter
import csv
from pathlib import Path
from exotica_visibility import MODES
from verification import sha256_file,write_json

FIELDS='frame mode profile_ok far_tests far_rejects extended_reads maximum_index lower_reads upper_reads accepted'.split()


def summarize(path,expected_frames=None):
    totals=Counter();previous=None;mode=None;count=0;maximum=0;valid=0
    with Path(path).open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=FIELDS:raise ValueError('unexpected native Exotica visibility columns')
        for row in reader:
            current=row['mode']
            if current not in MODES[1:] or (mode is not None and current!=mode):raise ValueError('invalid/changing visibility mode')
            mode=current
            r={k:int(row[k]) for k in FIELDS if k!='mode'}
            if any(n<0 for n in r.values()):raise ValueError('negative visibility counter')
            if previous is not None and r['frame']!=previous+1:raise ValueError('visibility frame gap/duplicate')
            previous=r['frame'];count+=1
            active=any(r[k] for k in FIELDS[3:])
            if r['profile_ok'] not in (0,1) or (active and not r['profile_ok']):raise ValueError('active counters without valid profile')
            valid+=r['profile_ok']
            index=r['maximum_index'];reads=r['extended_reads']
            if bool(reads)!=bool(index) or (reads and not 5000<=index<=12800):raise ValueError('invalid projection range')
            if mode in ('stock','margins') and reads:raise ValueError('projection disabled but modified reads recorded')
            maximum=max(maximum,index)
            totals.update({k:r[k] for k in FIELDS[3:] if k!='maximum_index'})
    if not count or not totals['far_tests'] or not totals['accepted']:raise ValueError('missing Exotica gameplay coverage')
    if totals['far_rejects']>totals['far_tests'] or totals['accepted']>totals['upper_reads']:raise ValueError('inconsistent native branch counts')
    if expected_frames is not None and count!=expected_frames:raise ValueError('incomplete native visibility log')
    return dict(verdict='PASS',scope=__doc__,sha256=sha256_file(path),mode=mode,frames=count,
                valid_profile_frames=valid,maximum_index=maximum,totals=dict(totals))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('csv',type=Path)
    ap.add_argument('--frames',type=int);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();report=summarize(args.csv,args.frames);write_json(args.output,report)
    print(report['verdict'],report['mode'],report['frames'],report['totals'])


if __name__=='__main__':main()
