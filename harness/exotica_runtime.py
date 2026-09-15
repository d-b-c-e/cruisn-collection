"""Explicit continuous renderer policy; bounded trials do not certify a release."""
from pathlib import Path
import re
from exotica_journals import REQUIRED

KEY='MIDZ_RUNTIME'
ENDS=('MIDZ_HOST_LAST','MIDZ_LIFETIME_LAST','MIDZ_MODEL_ENDPOINT_LAST','MIDZ_DEPTH_LAST')

def add_arguments(parser):
    parser.add_argument('--exotica-runtime',choices=('continuous',),
        help='candidate-only continuous combined renderer; requires quiet journals, verified scenes and shutdown observation')

def configure(args,rom,settings):
    mode=getattr(args,'exotica_runtime',None)
    if mode is None:
        if KEY in settings:raise ValueError('runtime policy requires explicit selection')
        return None
    required=dict(REQUIRED,MIDZ_BOOTSTRAP='3',MIDZ_SHUTDOWN_OBSERVE='1',MIDZ_HOST_JOURNALS='quiet',MIDZ_DEPTH_FIRST='2')
    if (mode!='continuous' or rom!='crusnexo' or not getattr(args,'candidate',None) or
            getattr(args,'headless',False) or getattr(args,'native_renderer',False) or
            any(settings.get(k)!=v for k,v in required.items())):
        raise ValueError('continuous runtime requires candidate, quiet combined renderer, verified startup, shutdown observation and FFB0')
    if any(not re.fullmatch('[0-9]+',settings.get(k,'')) or not 1<=int(settings[k])<=16000 for k in ENDS):
        raise ValueError('continuous trial requires validated finite capture reference bounds')
    settings[KEY]=mode
    return dict(mode=mode,end=None,capture_reference_ends={k:int(settings[k]) for k in ENDS},
                capture_completed=False,machine_reset_supported=False)

def verify(trial,directory,shutdown):
    lines=[]
    for name in ('stdout.log','stderr.log'):
        path=Path(directory)/name
        if not path.is_file() or path.stat().st_size>16*1024*1024:raise ValueError('missing or oversized runtime receipt stream')
        lines.extend(x for x in path.read_text(encoding='utf-8',errors='replace').splitlines() if x.startswith(KEY))
    if trial is None:
        if lines:raise ValueError('unrequested continuous runtime')
        return None
    acks=[KEY+' '+side+'=continuous end=none completion=quiescence' for side in ('cpu','gpu')]
    values={}
    for side,field in (('CPU','prepared_frame'),('GPU','mirror_frame')):
        matches=[re.fullmatch(KEY+'_'+side+'_RESULT '+field+r'=(\d+)',x) for x in lines]
        matches=[m for m in matches if m]
        if len(matches)!=1:raise ValueError('missing or duplicate runtime progress '+side)
        value=int(matches[0][1])
        if not 0<value<2**32:raise ValueError('runtime frame extent')
        values[field]=value;acks.append(matches[0][0])
    if sorted(lines)!=sorted(acks):raise ValueError('missing, extra or inconsistent runtime policy acknowledgment')
    if (not shutdown or shutdown['classification']!='quiescent' or
            values['prepared_frame']>shutdown['receipts']['CPU']['frame'] or
            values['mirror_frame']!=shutdown['receipts']['GPU']['frame']):
        raise ValueError('continuous trial requires observed quiescent joined exit and consistent frame progress')
    return dict(passed=True,mode='continuous',capture_completed=False,**values,
        beyond_capture_limits=min(values.values())>max(trial['capture_reference_ends'].values()),
        scope='Continuous policy in this bounded trial; native transaction summaries and joined quiescent exit. Not finite-capture completion, independent event proof, machine-reset or multi-race acceptance.')
