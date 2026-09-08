"""Compare Exotica far trials at equal captured poses, independently checking branches.

Only the requested far value is excluded from pose identity. This does not prove
unobserved simulation identity or visible benefit; pair with completed GPU images.
"""
import argparse
from collections import Counter
import csv
from itertools import zip_longest
from pathlib import Path

from analyze_exotica_frustum import TRIAL_FIELDS,evaluate
from compare_exotica_visibility import POSE
from verification import sha256_file,write_json

DISTANCE_POSE=[key for key in POSE if key!='far']


def compare(reference,candidate):
    reference,candidate=Path(reference),Path(candidate)
    rows=[0,0];matched=mismatched=added=lost=0;first=None;configs=[None,None]
    reasons=[Counter(),Counter()];models=Counter();lists=Counter()
    with reference.open(newline='',encoding='utf-8') as a,candidate.open(newline='',encoding='utf-8') as b:
        readers=[csv.DictReader(a),csv.DictReader(b)]
        if any(r.fieldnames!=TRIAL_FIELDS for r in readers):raise ValueError('far comparison requires full trial traces')
        previous=[0,0]
        for pair in zip_longest(*readers):
            observations=[]
            for i,row in enumerate(pair):
                if row is None:observations.append(None);continue
                if None in row or any(v is None for v in row.values()):raise ValueError('incomplete far trial row')
                r=evaluate(row);rows[i]+=1
                if r['sequence']!=rows[i] or r['frame']<previous[i]:raise ValueError('noncontiguous far trace')
                previous[i]=r['frame']
                config=(r['reciprocal'],r['margin'],r['far'])
                if config[0]!=1 or (configs[i] is not None and configs[i]!=config):
                    raise ValueError('far comparison requires stable coherent trials')
                configs[i]=config;reasons[i][r['reason']]+=1;observations.append(r)
            if None in pair or any(pair[0][key]!=pair[1][key] for key in DISTANCE_POSE):
                mismatched+=1
                if first is None:first=dict(reference=pair[0],candidate=pair[1])
                continue
            matched+=1;ra,rb=observations
            if not ra['accepted'] and rb['accepted']:
                added+=1;models[f'{rb["model"]:x}']+=1;lists[f'{rb["list"]:x}']+=1
            lost+=bool(ra['accepted'] and not rb['accepted'])
    if not matched:raise ValueError('no matching far trial poses')
    if configs[0][:2]!=configs[1][:2] or configs[0][2]>configs[1][2]:
        raise ValueError('comparison must hold projection/margins fixed and increase far')
    return dict(schema=1,scope=__doc__,reference_sha256=sha256_file(reference),candidate_sha256=sha256_file(candidate),
        reference_trial=configs[0],candidate_trial=configs[1],pose_fields=DISTANCE_POSE,
        rows=rows,matched_poses=matched,mismatched_poses=mismatched,first_pose_mismatch=first,
        actual_reasons=[dict(v) for v in reasons],additions_at_equal_pose=added,losses_at_equal_pose=lost,
        addition_models=dict(models),addition_lists=dict(lists),passed=mismatched==0 and lost==0)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('reference',type=Path);p.add_argument('candidate',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=compare(a.reference,a.candidate);write_json(a.output,r)
    raise SystemExit(0 if r['passed'] else 1)
