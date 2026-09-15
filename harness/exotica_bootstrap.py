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
    parser.add_argument('--exotica-bootstrap',choices=('observe','lifetimes','scenes'),help='verify guest readiness; optionally start lifetimes and the combined renderer at actual guest boundaries')

def configure(args,rom,settings,frames):
    mode=getattr(args,'exotica_bootstrap',None)
    if mode is None:
        if KEY in settings:raise ValueError('bootstrap observation requires explicit selection')
        return None
    if mode not in ('observe','lifetimes','scenes') or rom!='crusnexo' or not getattr(args,'candidate',None) or settings.get('MIDV_FFB')!='0':
        raise ValueError('bootstrap observation requires Exotica candidate and FFB0')
    continuous=getattr(args,'exotica_runtime',None)=='continuous' and mode=='scenes'
    if mode in ('lifetimes','scenes') and (settings.get('MIDZ_LIFETIME')!='1' or settings.get('MIDZ_HOST_JOURNALS','capture')!=('quiet' if continuous else 'capture')):
        raise ValueError('bootstrap lifetimes require captured lifetime observation')
    trial=dict(mode=mode,frames=frames,changes_startup=mode!='observe',continuous=continuous)
    if mode=='scenes':
        from exotica_journals import REQUIRED
        if any(settings.get(k)!=v for k,v in dict(REQUIRED,MIDZ_DEPTH_FIRST='2').items()):
            raise ValueError('bootstrap scenes require captured combined renderer and depth from frame2')
        trial['latest_scene_start']=min(int(settings[k]) for k in ('MIDZ_HOST_FIRST','MIDZ_MODEL_ENDPOINT_FIRST','MIDZ_MODEL_ADMIT_FIRST'))
    settings[KEY]=str(('observe','lifetimes','scenes').index(mode)+1)
    return trial

def lifetime_trial(trial,proof,lifetime):
    """Resolve the effective boundary only after independently checking its proof."""
    if not trial or trial['mode'] not in ('lifetimes','scenes'):return lifetime
    if (not proof or not proof.get('passed') or not proof.get('changes_startup') or
            not lifetime or lifetime.get('mode')!='observe' or not 0<=proof['frame'] or
            (not trial.get('continuous') and proof['frame']>lifetime['first'])):
        raise ValueError('bootstrap lifetime boundary does not precede requested coverage')
    return dict(lifetime,requested_first=lifetime['first'],first=proof['frame'],bootstrap_base=proof['base'])

def resolve_scenes(trial,proof,scene,waiting,handover,endpoint):
    if not trial or trial['mode']!='scenes':return
    if not proof or not proof.get('passed') or 'scene_frame' not in proof:
        raise ValueError('bootstrap scene activation requires verified proof')
    frame=proof['scene_frame']
    if (not all((scene,waiting,handover,endpoint)) or waiting.get('mode')!='observe' or handover.get('mode')!='draw' or
            endpoint.get('mode')!='draw' or not scene.get('compose') or
            frame<proof['frame'] or (not trial.get('continuous') and
            (any(frame>t['first'] for t in (scene,waiting,endpoint)) or frame>endpoint['admit_from'])) or
            'early_visibility' not in scene or 'early_visibility' not in handover):
        raise ValueError('bootstrap scene activation does not precede configured coverage')
    for t in (scene,waiting,endpoint):t.update(requested_first=t['first'],first=frame)
    endpoint.update(requested_admit_from=endpoint['admit_from'],admit_from=frame)
    for t in (scene,handover):t['early_visibility']=dict(t['early_visibility'],first=frame)

def verify(trial,directory):
    directory=Path(directory);lines=[];proof=directory/'exotica-bootstrap.bin';scene_proof=directory/'exotica-bootstrap-scene.bin'
    for name in ('stdout.log','stderr.log'):
        path=directory/name
        if not path.is_file() or path.stat().st_size>16*1024*1024:raise ValueError('missing or oversized bootstrap receipt stream')
        lines.extend(s for s in path.read_text(encoding='utf-8',errors='replace').splitlines() if s.startswith(KEY))
    if trial is None:
        if lines or proof.exists() or scene_proof.exists():raise ValueError('unrequested bootstrap observer')
        return None
    ready=[re.fullmatch(r'MIDZ_BOOTSTRAP_READY begin=(\d+) frame=(\d+) base=(\d+) links=1201',s) for s in lines]
    ready=[m for m in ready if m]
    if len(ready)!=1:raise ValueError('missing or duplicate bootstrap readiness')
    begin,frame,base=map(int,ready[0].groups())
    scenes=trial.get('mode')=='scenes';activates=scenes or trial.get('mode')=='lifetimes'
    expected=[KEY+('=3' if scenes else '=2' if activates else '=1'),ready[0][0],f'{KEY}_RESULT complete=1 frame={frame}']
    scene_result={}
    if scenes:
        found=[re.fullmatch(r'MIDZ_BOOTSTRAP_SCENE frame=(\d+) scene=(\d+)',s) for s in lines]
        found=[m for m in found if m]
        if len(found)!=1:raise ValueError('missing or duplicate bootstrap scene receipt')
        sf,serial=map(int,found[0].groups());expected.append(found[0][0])
        if not frame<=sf<trial['frames'] or (not trial.get('continuous') and sf>trial['latest_scene_start']) or not 0<serial<2**64 or not scene_proof.is_file() or scene_proof.stat().st_size!=64:
            raise ValueError('bootstrap scene bounds or proof extent')
        scene_words=(0x31534358,1,sf,frame,0x67f6,0xff2,0xffffffff,0xffffffff,0x67f5,0x15200ff2,0x681f,0x082fbbb5,0x6835,0x082fbbb9,serial&0xffffffff,serial>>32)
        if struct.unpack('<16I',scene_proof.read_bytes())!=scene_words:raise ValueError('bootstrap scene transaction/code proof')
        scene_result=dict(scene_frame=sf,scene_serial=serial,scene_proof_bytes=64)
    elif scene_proof.exists():raise ValueError('unrequested bootstrap scene proof')
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
                changes_startup=activates,**scene_result,scope='Verified guest pool/optional scene startup. Continuous exit and broader-course acceptance remain separate.')
