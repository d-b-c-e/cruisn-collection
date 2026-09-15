"""Verified guest pool readiness and optional earlier lifetime tracking."""
from pathlib import Path
import re,struct

KEY='MIDZ_BOOTSTRAP'
CODE=((0xbbf6,0x152010a8),(0xbbf9,0x152010a9),(0xbc64,0x152a10a8),(0xbc67,0x152010a9),
      (0xbbc7,0x086004b0),(0xbbc8,0x152010a9),(0xbbcc,0x1549c000),(0xbbce,0x0269001f),
      (0xbbd4,0x1540c000),(0xbbcb,0x087b04af),(0xbbcf,0x6400bbd2),(0xbbd0,0x1549c000),
      (0xbbd1,0x08080009),(0xbbd2,0x0269001f),(0xb859,0x082267c4),(0xb8cb,0x0840041d),
      (0x696f,0x152d046e),(0x6963,0x0820b47d))

def add_arguments(parser):
    parser.add_argument('--exotica-bootstrap',choices=('observe','lifetimes'),help='verify first guest pool rebuild; optionally start lifetime tracking there (scene start unchanged)')

def configure(args,rom,settings,frames):
    mode=getattr(args,'exotica_bootstrap',None)
    if mode is None:
        if KEY in settings:raise ValueError('bootstrap observation requires explicit selection')
        return None
    if mode not in ('observe','lifetimes') or rom!='crusnexo' or not getattr(args,'candidate',None) or settings.get('MIDV_FFB')!='0':
        raise ValueError('bootstrap observation requires Exotica candidate and FFB0')
    if mode=='lifetimes' and (settings.get('MIDZ_LIFETIME')!='1' or settings.get('MIDZ_HOST_JOURNALS','capture')!='capture'):
        raise ValueError('bootstrap lifetimes require captured lifetime observation')
    settings[KEY]='2' if mode=='lifetimes' else '1'
    return dict(mode=mode,frames=frames,changes_startup=mode=='lifetimes')

def lifetime_trial(trial,proof,lifetime):
    """Resolve the effective boundary only after independently checking its proof."""
    if not trial or trial['mode']!='lifetimes':return lifetime
    if (not proof or not proof.get('passed') or not proof.get('changes_startup') or
            not lifetime or lifetime.get('mode')!='observe' or not 0<=proof['frame']<=lifetime['first']):
        raise ValueError('bootstrap lifetime boundary does not precede requested coverage')
    return dict(lifetime,requested_first=lifetime['first'],first=proof['frame'],bootstrap_base=proof['base'])

def verify(trial,directory):
    directory=Path(directory);lines=[];proof=directory/'exotica-bootstrap.bin'
    for name in ('stdout.log','stderr.log'):
        path=directory/name
        if not path.is_file() or path.stat().st_size>16*1024*1024:raise ValueError('missing or oversized bootstrap receipt stream')
        lines.extend(s for s in path.read_text(encoding='utf-8',errors='replace').splitlines() if s.startswith(KEY))
    if trial is None:
        if lines or proof.exists():raise ValueError('unrequested bootstrap observer')
        return None
    ready=[re.fullmatch(r'MIDZ_BOOTSTRAP_READY begin=(\d+) frame=(\d+) base=(\d+) links=1201',s) for s in lines]
    ready=[m for m in ready if m]
    if len(ready)!=1:raise ValueError('missing or duplicate bootstrap readiness')
    begin,frame,base=map(int,ready[0].groups())
    activates=trial.get('mode')=='lifetimes'
    expected=[KEY+('=2' if activates else '=1'),ready[0][0],f'{KEY}_RESULT complete=1 frame={frame}']
    if sorted(lines)!=sorted(expected) or not 0<=begin<=frame<=begin+1 or frame>=trial['frames']:
        raise ValueError('bootstrap receipt order/completion bounds')
    if not 0x1000<=base or base+1201*31>0x40000 or not (base+1201*31<=0x30000 or base>=0x32000):
        raise ValueError('bootstrap pool extent')
    words=16+2*len(CODE)+1201
    if not proof.is_file() or proof.stat().st_size!=words*4:raise ValueError('missing or incomplete bootstrap proof')
    data=struct.unpack('<'+'I'*words,proof.read_bytes());tail=base+1200*31
    header=(0x31534258,1,begin,frame,base,len(CODE),1201,0xbbc9,0xbbd5,tail,tail,0,0xffffffff,base,1200,0)
    if data[:16]!=header:raise ValueError('bootstrap instruction/transaction proof')
    code=tuple(v for pair in CODE for v in pair)
    if data[16:16+len(code)]!=code:raise ValueError('bootstrap code signatures differ')
    links=tuple(base+(i+1)*31 for i in range(1200))+(0,)
    if data[16+len(code):]!=links:raise ValueError('bootstrap pool links differ')
    return dict(passed=True,begin=begin,frame=frame,base=base,links=1201,code_words=len(CODE),bytes=words*4,
                changes_startup=activates,scope='First verified guest pool rebuild; optional lifetime activation, not continuous scene/reset/exit acceptance.')
