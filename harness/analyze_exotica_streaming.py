"""Validate bounded Exotica loader/admission traces; counts are not visible scenery."""
import argparse
from collections import Counter
import csv
from pathlib import Path
from verification import sha256_file,write_json

FIELDS='frame sequence kind pc object model flags depth threshold cursor pointer section lead tail upper'.split()
TRIAL_FIELDS=FIELDS+['effective_threshold']


def summarize(path):
    path=Path(path);count=0;first=last=None;pending=None;mode=None
    kinds=Counter();limits=Counter();effective=Counter();models=Counter();loads=[]
    accepted=rejected=0;depths=[];lookahead=[];sections=[]
    with path.open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames not in (FIELDS,TRIAL_FIELDS):raise ValueError('unexpected streaming columns')
        for row in reader:
            if None in row or any(v is None for v in row.values()):raise ValueError('incomplete streaming row')
            r={k:(row[k] if k=='kind' else int(row[k],16 if k in ('pc','object','model','flags','pointer') else 10)) for k in reader.fieldnames}
            count+=1
            if r['sequence']!=count or r['frame']<1 or (last is not None and r['frame']<last):raise ValueError('noncontiguous streaming trace')
            first=r['frame'] if first is None else first;last=r['frame'];kind=r['kind'];kinds[kind]+=1
            if min(r[k] for k in ('section','lead','tail','upper'))<0:raise ValueError('invalid streaming position')
            value=r.get('effective_threshold',r['threshold'])
            if pending is not None:
                if kind!='admission_check' or any(r[k]!=pending[k] for k in ('object','model','flags','depth','threshold')) or value!=pending['effective']:
                    raise ValueError('admitted object lacks the independently observed second comparison')
                pending=None
            elif kind=='admission_check':raise ValueError('orphan second admission comparison')
            if kind in ('admission','admission_check'):
                if r['pc']!=(0xb773 if kind=='admission' else 0xb776) or not 0x1000<=r['object']<0x40000-0x1d:
                    raise ValueError('invalid admission consumer/object')
                if not -0x80000000<=r['depth']<=0x7fffffff or not 0<r['threshold']<=204800:
                    raise ValueError('invalid original admission bound')
                current_mode=0 if value==r['threshold'] else value
                if current_mode not in (0,160000,190000) or (mode is not None and current_mode!=mode):
                    raise ValueError('admission trial changed or is unsupported')
                mode=current_mode
                if kind=='admission':
                    limits[r['threshold']]+=1;effective[value]+=1
                    if r['depth']<value:
                        accepted+=1;pending={**r,'effective':value}
                    else:rejected+=1;models[f'{r["model"]:x}']+=1;depths.append(r['depth'])
                elif r['depth']>=value:raise ValueError('second comparison reached for a rejected object')
            elif kind=='lookahead':
                if r['pc']!=0xb7bc or r['threshold']!=r['upper']+12 or value!=r['threshold'] or r['cursor']<0:
                    raise ValueError('loader lookahead operands disagree')
                lookahead.append(r['cursor']-r['threshold']);sections.append(r['section'])
            elif kind=='load':
                if r['pc']!=0xb7e9 or not 0xa00000<=r['pointer']<0xc00000 or value!=0:
                    raise ValueError('invalid loader entry')
                loads.append(dict(frame=r['frame'],pointer=f'{r["pointer"]:x}',section=r['section'],upper=r['upper']))
            else:raise ValueError('unknown streaming observation')
    if not count or not limits or not lookahead or pending is not None:raise ValueError('empty or incomplete streaming interval')
    return dict(schema=1,scope=__doc__,source_sha256=sha256_file(path),frames=[first,last],rows=count,
        admission_override=mode,kinds=dict(kinds),admitted=accepted,rejected=rejected,
        original_limit_range=[min(limits),max(limits)],effective_limit_range=[min(effective),max(effective)],
        distinct_original_limits=len(limits),rejected_depth_range=[min(depths),max(depths)] if depths else None,
        rejection_models=dict(models),loader_cursor_minus_threshold=[min(lookahead),max(lookahead)],
        section_range=[min(sections),max(sections)],loads=loads)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trace',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();write_json(args.output,summarize(args.trace))
