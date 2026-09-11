"""Bounded read-only native Exotica lifetime observation and receipt checks."""
import csv
import math
from pathlib import Path
import re

KEYS=('MIDZ_LIFETIME_FIRST','MIDZ_LIFETIME_LAST')
FIELDS=('event','frame','time','sequence','epoch','generation','slot','owner','realm','section','source','reason','flags')

def add_arguments(parser):
    parser.add_argument('--exotica-lifetimes',choices=('off','observe'),help='observe original pool/source/model lifetimes without extra rendering')
    parser.add_argument('--exotica-lifetime-first',type=int,help='first native frame, inclusive')
    parser.add_argument('--exotica-lifetime-last',type=int,help='last native frame, inclusive')

def configure(args,rom,settings):
    mode=getattr(args,'exotica_lifetimes',None)
    bounds=[getattr(args,'exotica_lifetime_'+name,None) for name in ('first','last')]
    if mode is not None:
        if mode not in ('off','observe'):raise ValueError('invalid Exotica lifetime mode')
        if not getattr(args,'candidate',None):raise ValueError('Exotica lifetimes require an explicit candidate')
    else:
        if any(v is not None for v in bounds):raise ValueError('Exotica lifetime bounds require an explicit mode')
        recorded=settings.get('MIDZ_LIFETIME','0')
        if recorded=='0':
            if any(k in settings for k in KEYS):raise ValueError('orphan Exotica lifetime bounds')
            return None
        if recorded!='1':raise ValueError('invalid recorded Exotica lifetime mode')
        mode='observe'
        if any(not re.fullmatch('[0-9]+',settings.get(k,'')) for k in KEYS):raise ValueError('missing or invalid recorded lifetime bounds')
        bounds=[int(settings[k]) for k in KEYS]
    if rom!='crusnexo':raise ValueError('Exotica lifetimes support Exotica2.4 only')
    if mode=='off':
        if any(v is not None for v in bounds):raise ValueError('disabled Exotica lifetimes do not take bounds')
        settings['MIDZ_LIFETIME']='0'
        for k in KEYS:settings.pop(k,None)
        return dict(mode='off')
    first,last=bounds
    if first is None or last is None or not 1799<=first<=last<=15999 or last-first>10000:
        raise ValueError('Exotica lifetime frame bounds')
    settings.update(MIDZ_LIFETIME='1',MIDZ_LIFETIME_FIRST=str(first),MIDZ_LIFETIME_LAST=str(last))
    return dict(mode='observe',first=first,last=last)

def verify_receipt(trial,text,directory):
    path=Path(directory)/'exotica-lifetime-events.csv'
    if not trial or trial['mode']=='off':
        if 'MIDZ_LIFETIME=1' in text or 'MIDZ_LIFETIME_RESULT' in text or path.exists():
            raise ValueError('disabled Exotica lifetime observer ran')
        return None
    start=re.findall(r'^MIDZ_LIFETIME=1 first=(\d+) last=(\d+)$',text,re.M)
    if start!=[(str(trial['first']),str(trial['last']))]:raise ValueError('Exotica lifetime start acknowledgment')
    names=('complete','records','transitions','bindings','emissions','owned','draws','first_draws','fading','opaque','epochs')
    final=re.findall(r'^MIDZ_LIFETIME_RESULT '+' '.join(n+r'=(\d+)' for n in names)+r'$',text,re.M)
    if len(final)!=1:raise ValueError('missing Exotica lifetime completion')
    totals=dict(zip(names,map(int,final[0])))
    if totals['complete']!=1 or not 0<totals['records']<=200000 or not path.is_file() or path.stat().st_size>64*1024*1024:
        raise ValueError('incomplete or oversized Exotica lifetime journal')
    with path.open(encoding='utf-8',newline='') as stream:
        reader=csv.DictReader(stream)
        if tuple(reader.fieldnames or ())!=FIELDS:raise ValueError('Exotica lifetime journal columns')
        rows=[]
        for row in reader:
            rows.append(row)
            if len(rows)>200000:raise ValueError('Exotica lifetime row budget')
    if len(rows)!=totals['records']:raise ValueError('Exotica lifetime journal count')
    live={};known=set();sources={};seen_draws=set();faded=set();opaque=set()
    sequence=0;epoch=1;bindings=draws=firsts=fades=completions=unknowns=0
    count=None;last_time=-1.;last_frame=-1;allow_unknown=True
    for index,row in enumerate(rows):
        if set(row)!=set(FIELDS) or any(row[k] is None for k in FIELDS):raise ValueError('incomplete lifetime row')
        try:
            if any(not re.fullmatch('[0-9]+',row[k]) for k in FIELDS[1:] if k!='time'):raise ValueError('noninteger lifetime operand')
            r={k:int(row[k]) for k in FIELDS[1:] if k!='time'};time=float(row['time']);op=row['event']
        except (TypeError,ValueError) as exc:raise ValueError('invalid lifetime operand') from exc
        if any(v>(0xffffffff if k in ('frame','slot','section','source','reason','flags') else 0xffffffffffffffff) for k,v in r.items()):
            raise ValueError('lifetime integer width')
        if not math.isfinite(time) or time<0 or time<last_time or not trial['first']<=r['frame']<=trial['last'] or r['frame']<last_frame:
            raise ValueError('lifetime time/frame order')
        last_time=time;last_frame=r['frame'];slot=r['slot']
        if slot and not (0x1000<=slot<=0x40000-31 and (slot+31<=0x30000 or slot>=0x32000)):
            raise ValueError('lifetime slot bounds')
        if index==0:
            if op!='L' or r['sequence'] or r['epoch']!=1 or r['generation'] or r['owner'] or r['realm'] or r['section'] or r['source'] or r['flags'] or r['reason']>4096:
                raise ValueError('lifetime initialization')
            count=r['reason'];continue
        if op in ('A','F','R'):
            sequence+=1
            if r['owner'] or r['realm'] or r['section'] or r['source']:raise ValueError('pool event has source binding')
            if op=='R':
                if r['reason']!=1201 or r['flags']!=1200 or r['generation']:raise ValueError('lifetime reset extent')
                end=slot+1201*31
                if not slot or end>0x40000 or (slot<0x32000 and end>0x30000):raise ValueError('lifetime reset pool bounds')
                live.clear();known.clear();sources.clear();allow_unknown=False;epoch+=1;count=1200
            elif op=='A':
                if not slot or slot in live or r['generation']!=sequence or r['reason'] or count<=0:raise ValueError('lifetime allocation')
                live[slot]=dict(generation=sequence,key=None,owner=None);known.add(slot);count-=1
            else:
                unknown=slot not in known
                if not slot or (slot not in live and not (unknown and allow_unknown)) or r['reason']!=int(unknown) or r['generation']:
                    raise ValueError('lifetime removal')
                old=live.pop(slot,None)
                if old and old['key'] is not None:sources.pop(old['key'])
                known.add(slot);unknowns+=unknown;count+=1
            if r['flags']!=count or not 0<=count<=4096:raise ValueError('lifetime available counter')
        elif op in ('B','D'):
            life=live.get(slot);key=r['realm'],r['section'],r['source']
            if life is None or life['generation']!=r['generation']:raise ValueError('stale lifetime source')
            if not 1<=r['realm']>>32<=3 or not 0xa00000<=(r['realm']&0xffffffff)<0x1000000 or not 0xa00000<=r['section']<=0x1000000-4 or not 0xa00000<=r['source']<=0x1000000-6:
                raise ValueError('lifetime source realm/bounds')
            if op=='B':
                bindings+=1
                if life['key'] is not None or key in sources or r['owner']!=bindings or r['reason']:raise ValueError('lifetime source binding')
                life.update(key=key,owner=bindings);sources[key]=slot
            else:
                if life['key']!=key or life['owner']!=r['owner']:raise ValueError('lifetime model owner')
                generation=r['generation'];reason=0
                if generation not in seen_draws:reason|=1;seen_draws.add(generation);firsts+=1
                if r['flags']&0x04000000:reason|=2;faded.add(generation);fades+=1
                elif generation in faded and generation not in opaque:reason|=4;opaque.add(generation);completions+=1
                if not reason or r['reason']!=reason:raise ValueError('lifetime model transition')
                draws+=1
        else:raise ValueError('unknown lifetime event')
        if r['sequence']!=sequence or r['epoch']!=epoch:raise ValueError('lifetime generation/epoch sequence')
        if len(known)>4096:raise ValueError('lifetime tracked-address budget')
    if any(totals[k]!=v for k,v in dict(transitions=sequence,bindings=bindings,draws=draws,first_draws=firsts,fading=fades,opaque=completions,epochs=epoch).items()):
        raise ValueError('lifetime final totals')
    if not draws<=totals['owned']<=totals['emissions']<=20000000:raise ValueError('lifetime emission totals')
    return dict(passed=True,**totals,unknown_frees=unknowns,
        scope='Observed native pool/source/submission structure and generation fold. Independent original-route/trace comparisons, resources and rendering acceptance remain separate.')
