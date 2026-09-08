"""Compare actual Exotica CPU decisions at matching object poses across two trials.

Equal poses do not establish traffic/physics identity outside this observed span.
Prediction checks apply only to the unchanged stock reference and matching rows.
"""
import argparse
import csv
from itertools import zip_longest
from pathlib import Path
from analyze_exotica_frustum import FIELDS,TRIAL_FIELDS,evaluate
from verification import sha256_file,write_json

POSE='frame sequence list object flags model depth radius index far x y z original_factor'.split()


def pose(row):
    return tuple(row.get(k,row['factor'] if k=='original_factor' else None) for k in POSE)


def compare(reference,candidate):
    reference,candidate=Path(reference),Path(candidate)
    matched=0;mismatched=0;first=None;new=0;lost=0;prediction_errors=0;first_prediction=None;rows=[0,0]
    with reference.open(newline='',encoding='utf-8') as a,candidate.open(newline='',encoding='utf-8') as b:
        ar,br=csv.DictReader(a),csv.DictReader(b)
        if ar.fieldnames not in (FIELDS,TRIAL_FIELDS) or br.fieldnames not in (FIELDS,TRIAL_FIELDS):
            raise ValueError('unexpected frustum columns')
        for ra,rb in zip_longest(ar,br):
            for i,r in enumerate((ra,rb)):
                if r is not None:
                    rows[i]+=1
                    if None in r or any(v is None for v in r.values()):raise ValueError('incomplete frustum row')
            if ra is None or rb is None or pose(ra)!=pose(rb):
                mismatched+=1
                if first is None:first=dict(reference=None if ra is None else dict(zip(POSE,pose(ra))),candidate=None if rb is None else dict(zip(POSE,pose(rb))))
                continue
            oa,ob=evaluate(ra),evaluate(rb)
            if oa['reciprocal'] or oa['margin']:raise ValueError('prediction comparison requires a stock reference')
            matched+=1;new+=not oa['accepted'] and ob['accepted'];lost+=oa['accepted'] and not ob['accepted']
            prediction={(0,0):oa['reason'],(1,0):oa['predicted'],(0,88):oa['predicted_wide88'],(1,88):oa['predicted_combined88']}[(ob['reciprocal'],ob['margin'])]
            if (prediction=='accepted')!=bool(ob['accepted']):
                prediction_errors+=1
                if first_prediction is None:first_prediction=dict(frame=ob['frame'],object=ob['object'],prediction=prediction,actual=ob['reason'])
    if not matched:raise ValueError('no matching object poses')
    return dict(schema=1,scope=__doc__,reference_sha256=sha256_file(reference),candidate_sha256=sha256_file(candidate),rows=rows,
                matched_poses=matched,mismatched_poses=mismatched,first_pose_mismatch=first,
                additions_at_equal_pose=new,losses_at_equal_pose=lost,prediction_errors=prediction_errors,first_prediction_error=first_prediction,
                passed=mismatched==0 and lost==0 and prediction_errors==0)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('reference',type=Path);p.add_argument('candidate',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=compare(a.reference,a.candidate);write_json(a.output,r)
    raise SystemExit(0 if r['passed'] else 1)
