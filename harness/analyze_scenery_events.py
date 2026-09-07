"""Rank submitted-object appearances for targeted gameplay captures.

Rectangle area is a search priority, not visible pixel area. Distance-band hits
are hypotheses, not proof: frustum/face tests, loading and occlusion also matter.
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path

NUMERIC = ('scene','first_frame','last_frame','missing_scenes','quads','x0','y0',
           'x1','y1','depth_minus_radius','radius','first_texture','first_palette',
           'first_far_observation')
HEX = ('object','model','previous_model','object_flags')
EVENTS = {'initial_observation','first_submission','model_change','reappeared'}


def load(path):
    rows=[]
    previous=0
    with open(path, newline='', encoding='utf-8') as stream:
        reader=csv.DictReader(stream)
        if not set((*NUMERIC,*HEX,'event')).issubset(reader.fieldnames or []):
            raise ValueError('missing scenery-event columns')
        for line,row in enumerate(reader,2):
            try:
                if None in row: raise ValueError('extra columns')
                r={k:int(row[k]) for k in NUMERIC}
                r.update({k:int(row[k],16) for k in HEX})
                r['event']=row['event']
                if not (r['scene']>=previous and r['scene']>0 and r['first_frame']>0
                        and r['last_frame']>=r['first_frame'] and r['quads']>0
                        and r['x0']<=r['x1'] and r['y0']<=r['y1']
                        and r['event'] in EVENTS and r['missing_scenes']>=-1
                        and 0<r['first_far_observation']<=r['last_frame']):
                    raise ValueError('invalid event/order/geometry')
            except (KeyError,TypeError,ValueError) as error:
                raise ValueError(f'{path}:{line}: {error}') from error
            rows.append(r);previous=r['scene']
    if not rows: raise ValueError('empty scenery-event trace')
    return rows


def rank(rows, margin=86, height=400, minimum_area=256, limit=30):
    candidates=[]
    batches=defaultdict(list)
    for row in rows:
        if row['event']=='initial_observation':continue
        r=dict(row)
        # Static-looking World object flags are only a grouping aid. A reused
        # object address/model pair is not a persistent world-object identity.
        if r['object_flags'] & 0x7fffffff in (0x1000,0x1008):
            batches[r['first_frame']].append(row)
        width=max(0,min(r['x1'],511+margin)-max(r['x0'],-margin)+1)
        h=max(0,min(r['y1'],height-1)-max(r['y0'],0)+1)
        area=width*h
        if area<minimum_area:continue
        r.update(clipped_bounds_area=area, extent=[r['x1']-r['x0'],r['y1']-r['y0']],
                 observed_at_far_earlier=r['first_far_observation']<r['first_frame'],
                 near_original_far_gate=78000<=r['depth_minus_radius']<=80000,
                 suggested_capture_frames=[max(1,r['first_frame']-12),r['last_frame']+24])
        for k in HEX:r[k]=f'{r[k]:x}'
        candidates.append(r)
    candidates.sort(key=lambda r:(-r['clipped_bounds_area'],r['first_frame']))
    return {'schema':1,'scope':'submitted bounds only; confirm actual pop and cause with completed GL',
            'events':len(rows),'event_types':dict(Counter(r['event'] for r in rows)),
            'candidate_events':len(candidates),'minimum_bounds_area':minimum_area,
            'viewport':{'margin':margin,'height':height},'largest':candidates[:limit],
            'appearance_batches':[{'frame':f,'objects':len(group),
                'first_far_observed_now':sum(r['first_far_observation']==f for r in group),
                'models':sorted({f"{r['model']:x}" for r in group})}
                for f,group in sorted(batches.items(),key=lambda item:(-len(item[1]),item[0]))[:limit]],
            'near_far_gate':sorted((r for r in candidates if r['near_original_far_gate']
                                    and r['observed_at_far_earlier']),
                                   key=lambda r:(-r['clipped_bounds_area'],r['first_frame']))[:limit]}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('events',type=Path)
    ap.add_argument('--margin',type=int,default=86)
    ap.add_argument('--height',type=int,default=400)
    ap.add_argument('--minimum-area',type=int,default=256)
    ap.add_argument('--limit',type=int,default=30)
    ap.add_argument('--report',type=Path,required=True)
    args=ap.parse_args()
    try:
        if args.margin<0 or args.height<1 or args.minimum_area<1 or args.limit<1:
            raise ValueError('invalid viewport or candidate limits')
        result=rank(load(args.events),args.margin,args.height,args.minimum_area,args.limit)
        result['source']=str(args.events.resolve())
        result['parsed']=True
    except (OSError,ValueError) as error:
        result={'schema':1,'parsed':False,'error':str(error)}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PARSED' if result['parsed'] else 'FAIL',args.report)
    return 0 if result['parsed'] else 1


if __name__=='__main__':raise SystemExit(main())
