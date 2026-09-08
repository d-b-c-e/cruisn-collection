"""Validate actual Exotica CPU sphere branches and model an unclamped reciprocal.

Predicted CPU admissions are not visible pixels, Zeus draws or resource acceptance.
"""
import argparse
from collections import Counter
import csv
import math
from pathlib import Path
import struct
from verification import sha256_file,write_json

FIELDS='frame sequence list object flags model depth radius index far x y z factor yl yu xl xu accepted'.split()
TRIAL_FIELDS=FIELDS+['original_factor','reciprocal','margin']


def c31(word):
    if word==0x80000000:return 0.0
    e=word>>24
    if e>=128:e-=256
    return ((word&0x7fffff)/8388608+(-2 if word&0x800000 else 1))*2.0**e


def ieee(text):
    value=struct.unpack('<f',struct.pack('<I',int(text,16)))[0]
    if not math.isfinite(value):raise ValueError('nonfinite register operand')
    return value


def planes(x,y,r,factor):
    return dict(yl=(y+r)*factor,yu=(y-r)*factor,xl=(x+r)*factor,xu=(x-r)*factor+256)


def rejection(depth,radius,far,p,margin=0):
    if depth+radius>far:return 'far'
    if p['yl']+200<0:return 'yl'
    if p['yu']>200:return 'yu'
    if p['xl']+256 < -margin:return 'xl'
    if p['xu']>511+margin:return 'xu'
    return 'accepted'


def evaluate(row):
    r={k:int(row[k]) for k in ('frame','sequence','depth','radius','index','far','accepted')}
    if (r['frame']<1 or r['sequence']<1 or r['accepted'] not in (0,1) or r['far']!=204800
            or not 0<=r['radius']<10000000 or r['depth']+r['radius']<0
            or r['index']!=min(4999,max(0,r['depth'])//16)):
        raise ValueError('invalid culler sample')
    raw={k:int(row[k],16) for k in ('list','object','flags','model','x','y','z','factor')}
    reciprocal=int(row.get('reciprocal',0));margin=int(row.get('margin',0))
    original_factor=int(row.get('original_factor',row['factor']),16)
    if reciprocal not in (0,1) or margin not in (0,88):raise ValueError('unsupported frustum trial')
    if raw['list'] not in (0,0xbbb5,0xbbb6,0xbbb7,0xbbb8) or not 0x1000<=raw['object']<0x40000-0x16:
        raise ValueError('unexpected list/object')
    x,y,z,factor=(c31(raw[k]) for k in ('x','y','z','factor'))
    if not all(math.isfinite(v) for v in (x,y,z,factor)) or factor<=0 or abs(z-r['depth'])>1.01:
        raise ValueError('pose/depth/factor mismatch')
    observed={k:ieee(row[k]) for k in ('yl','yu','xl','xu') if row[k]}
    if 'xu' in observed:observed['xu']-=margin # normalize the shifted center to original coordinates
    index=max(0,r['depth'])//16
    true_factor=struct.unpack('<f',struct.pack('<f',math.floor(512/(index*16+1)*1000000+.5)/1000000))[0] if index>4999 else c31(original_factor)
    expected_factor=true_factor if reciprocal and index>4999 and r['depth']+r['radius']<=r['far'] else c31(original_factor)
    if factor!=expected_factor:raise ValueError('effective factor does not match the requested trial')
    expected=planes(x,y,r['radius'],factor)
    errors={k:abs(v-expected[k]) for k,v in observed.items()}
    if any(error>max(.002,abs(expected[k])*3e-6) for k,error in errors.items()):
        raise ValueError('actual sphere operands disagree with captured pose/reciprocal')
    reason=rejection(r['depth'],r['radius'],r['far'],{**expected,**observed},margin)
    # Delayed branches execute some later operands even when already rejected.
    stages={'far':set(),'yl':{'yl','yu'},'yu':{'yl','yu','xl'},
            'xl':{'yl','yu','xl','xu'},'xu':{'yl','yu','xl','xu'},'accepted':{'yl','yu','xl','xu'}}
    if set(observed)!=stages[reason] or r['accepted']!=(reason=='accepted'):
        raise ValueError('observed stage/acceptance contradicts branch conditions')
    actual_factor=factor
    if index>4999:
        factor=struct.unpack('<f',struct.pack('<f',math.floor(512/(index*16+1)*1000000+.5)/1000000))[0]
    predicted=rejection(r['depth'],r['radius'],r['far'],planes(x,y,r['radius'],factor))
    # Current Zeus GL defaults to an 88-pixel horizontal margin. This is an
    # explicit separate counterfactual, not an assertion that CPU culling was fixed.
    wide=rejection(r['depth'],r['radius'],r['far'],expected,88)
    combined=rejection(r['depth'],r['radius'],r['far'],planes(x,y,r['radius'],factor),88)
    return dict(**r,**raw,reason=reason,predicted=predicted,unclamped_index=index,
                reciprocal=reciprocal,margin=margin,original_factor=original_factor,
                predicted_wide88=wide,predicted_combined88=combined,
                extended=index>4999,factor_value=actual_factor,predicted_factor=factor,
                maximum_operand_error=max(errors.values(),default=0))


def summarize(path):
    path=Path(path);count=0;previous_frame=0;reasons=Counter();predicted=Counter();by_list={};new=[];lost=[]
    first=None;last=None;extended=0;max_error=0;max_depth=0;wide=Counter();combined=Counter();config=None
    with path.open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames not in (FIELDS,TRIAL_FIELDS):raise ValueError('unexpected frustum columns')
        for row in reader:
            if None in row or any(v is None for v in row.values()):raise ValueError('incomplete frustum row')
            r=evaluate(row);count+=1
            pair=(r['reciprocal'],r['margin'])
            if config is not None and config!=pair:raise ValueError('frustum trial changed during observation')
            config=pair
            if r['sequence']!=count or r['frame']<previous_frame:raise ValueError('noncontiguous sequence or frame order')
            previous_frame=r['frame'];first=r['frame'] if first is None else first;last=r['frame']
            reasons[r['reason']]+=1;predicted[r['predicted']]+=1
            wide[r['predicted_wide88']]+=1;combined[r['predicted_combined88']]+=1
            extended+=r['extended'];max_error=max(max_error,r['maximum_operand_error']);max_depth=max(max_depth,r['depth'])
            key=f'{r["list"]:x}';v=by_list.setdefault(key,dict(samples=0,accepted=0,predicted_accepted=0,extended=0,new=0,lost=0))
            v['samples']+=1;v['accepted']+=r['accepted'];v['predicted_accepted']+=r['predicted']=='accepted';v['extended']+=r['extended']
            if r['predicted']=='accepted' and not r['accepted']:new.append(r);v['new']+=1
            if r['predicted']!='accepted' and r['accepted']:lost.append(r);v['lost']+=1
    if not count:raise ValueError('empty frustum trace')
    def additions(rows):
        objects={}
        for r in rows:
            k=f'{r["model"]:x}'
            v=objects.setdefault(k,dict(samples=0,first_frame=r['frame'],last_frame=r['frame'],minimum_depth=r['depth'],maximum_depth=r['depth']))
            v['samples']+=1;v['last_frame']=r['frame'];v['minimum_depth']=min(v['minimum_depth'],r['depth']);v['maximum_depth']=max(v['maximum_depth'],r['depth'])
        return objects
    return dict(schema=1,scope=__doc__,source_sha256=sha256_file(path),frames=[first,last],samples=count,
                trial=dict(reciprocal=config[0],margin=config[1]),
                extended_samples=extended,maximum_depth=max_depth,maximum_operand_error=max_error,
                actual_reasons=dict(reasons),predicted_reasons=dict(predicted),by_list=by_list,
                predicted_wide88_reasons=dict(wide),predicted_combined88_reasons=dict(combined),
                predicted_additions=len(new),predicted_losses=len(lost),addition_models=additions(new),loss_models=additions(lost))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trace',type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();write_json(a.output,summarize(a.trace))
