"""Bounded quiet-renderer trial; summaries never substitute for per-event proof."""
from pathlib import Path
import re

KEY='MIDZ_HOST_JOURNALS'
REQUIRED=dict(MIDV_FFB='0',MIDZ_GL='1',MIDZ_HOST_SCENE='1',MIDZ_LIFETIME='1',
    MIDZ_HOST_MATERIALS='1',MIDZ_HOST_WAITING='1',MIDZ_HOST_FENCE='1',
    MIDZ_HOST_HANDOVER='2',MIDZ_HOST_ACTIVE='2',MIDZ_HOST_COMPOSE='1',
    MIDZ_HOST_FUTURE='2',MIDZ_HOST_FUTURE_PRESENT='1',MIDZ_DEPTH_MIRROR='2',
    MIDZ_MODEL_ENDPOINT='2',MIDZ_ENDPOINT_EARLY='1',MIDZ_ENDPOINT_MARKED='1')
JOURNALS=(
    'exotica-lifetime-events.csv','exotica-endpoint-models.csv',
    'exotica-admission-packets.bin','exotica-endpoint-admissions.csv','exotica-early-active.csv',
    'exotica-host-scenes.csv','exotica-host-materials.csv','exotica-host-fences.csv',
    'exotica-waiting-scenes.csv','exotica-handover-scenes.csv','exotica-handover-cohorts.bin',
    'exotica-active-scenes.csv','exotica-compose-scenes.csv','zeus-depth-mirror.csv',
    'exotica-host-materials-gpu.csv','exotica-endpoint-gpu.csv','exotica-active-gpu.csv',
    'exotica-future-gpu.csv','exotica-waiting-draw-gpu.csv')
SCHEMAS={
 'MIDZ_ENDPOINT_EARLY_RESULT':'complete scenes permissions',
 'MIDZ_MODEL_ADMIT_RESULT':'complete packets bytes',
 'MIDZ_MODEL_ENDPOINT_RESULT':'complete commits consumed untracked prepared rejected snapshots bytes remaining',
 'MIDZ_LIFETIME_RESULT':'complete records transitions bindings emissions owned draws first_draws fading opaque epochs',
 'MIDZ_HOST_COMPOSE_RESULT':'complete scenes',
 'MIDZ_HOST_HANDOVER_RESULT':'complete scenes captured submitted retired bytes snapshots remaining',
 'MIDZ_HOST_WAITING_RESULT':'complete scenes candidates quads snapshots remaining',
 'MIDZ_HOST_ACTIVE_RESULT':'complete scenes quads remaining',
 'MIDZ_HOST_FENCE_RESULT':'complete requested completed immediate',
 'MIDZ_HOST_MATERIALS_RESULT':'queued hash',
 'MIDZ_HOST_SCENE_RESULT':'complete prepared matched quads snapshots pending remaining',
 'MIDZ_ENDPOINT_GPU_RESULT':'complete pairs',
 'MIDZ_DEPTH_MIRROR_RESULT':'complete frames batches vertices clears snapshots remaining',
 'MIDZ_HOST_FUTURE_GPU_RESULT':'complete scenes quads snapshots written failed rejected',
 'MIDZ_HOST_WAITING_DRAW_GPU_RESULT':'complete scenes quads snapshots written failed rejected',
 'MIDZ_HOST_ACTIVE_GPU_RESULT':'complete scenes quads',
 'MIDZ_HOST_MATERIALS_GPU_RESULT':'complete received snapshots hash',
}
WRITER_FIELDS='submitted written failed rejected peak_bytes write_total_us write_max_us drain_us waits wait_us'
SCHEMAS.update({k:WRITER_FIELDS for k in ('MIDZ_DEPTH_MIRROR_WRITER','MIDZ_HOST_ACTIVE_WRITER')})


def add_arguments(parser):
    parser.add_argument('--exotica-journals',choices=('capture','quiet'),
        help='candidate-only bounded journal policy; quiet verifies native summaries and snapshots, not per-event journals')


def configure(args,rom,settings):
    mode=getattr(args,'exotica_journals',None)
    if mode is None:
        if KEY in settings:raise ValueError('journal policy requires explicit selection')
        return None
    if (mode not in ('capture','quiet') or rom!='crusnexo' or not getattr(args,'candidate',None)
            or getattr(args,'headless',False) or getattr(args,'native_renderer',False)):
        raise ValueError('journal policy requires an Exotica live-GL candidate')
    if mode=='quiet' and any(settings.get(k)!=v for k,v in REQUIRED.items()):
        raise ValueError('quiet journal trial requires the combined renderer, marked endpoints and FFB0')
    settings[KEY]=mode
    return dict(mode=mode,independent_event_journals=mode=='capture',continuous=False,
        snapshots=len([x for x in settings.get('MIDZ_HOST_SNAPSHOTS','').split(',') if x]),
        depth_snapshots=len([x for x in settings.get('MIDZ_DEPTH_SNAPSHOTS','').split(',') if x]))


def verify(trial,directory):
    directory=Path(directory);lines=[]
    for name in ('stdout.log','stderr.log'):
        path=directory/name
        if not path.is_file() or path.stat().st_size>16*1024*1024:
            raise ValueError('missing or oversized journal-policy receipt stream')
        lines+=path.read_text(encoding='utf-8',errors='replace').splitlines()
    ack=[x for x in lines if x.startswith(KEY)]
    if trial is None:
        if ack:raise ValueError('unrequested journal policy')
        return None
    mode=trial['mode']
    if sorted(ack)!=[KEY+' cpu='+mode,KEY+' gpu='+mode]:
        raise ValueError('missing, malformed or duplicated CPU/GPU journal acknowledgment')
    if mode=='capture':return dict(mode=mode,independent_event_journals=True)
    if any((directory/name).exists() for name in JOURNALS):
        raise ValueError('quiet renderer unexpectedly wrote a per-event journal')
    operands=directory/'exotica-endpoint-inputs.txt'
    if not operands.is_file() or operands.stat().st_size>64*1024*1024:
        raise ValueError('missing or oversized retained endpoint snapshot operands')
    receipts={}
    for tag,fields in SCHEMAS.items():
        selected=[x for x in lines if x.startswith(tag)]
        keys=fields.split()
        pattern=tag+''.join(' '+k+'=('+('[0-9a-f]{16}' if k=='hash' else '[0-9]+')+')' for k in keys)
        match=re.fullmatch(pattern,selected[0]) if len(selected)==1 else None
        if match is None:raise ValueError('missing, malformed or duplicated '+tag)
        row={k:(v if k=='hash' else int(v)) for k,v in zip(keys,match.groups())}
        if (('complete' in row and row['complete']!=1)
                or any(row.get(k,0) for k in ('remaining','pending','failed','rejected'))):
            raise ValueError('incomplete quiet renderer '+tag)
        receipts[tag]=row
    def get(tag):return receipts['MIDZ_'+tag]
    scene=get('HOST_SCENE_RESULT');n=scene['prepared'];snap=trial['snapshots'];depth_snap=trial['depth_snapshots']
    if not n or scene['matched']!=n or scene['snapshots']!=snap:
        raise ValueError('quiet scene count/snapshot mismatch')
    for tag in ('ENDPOINT_EARLY_RESULT','HOST_COMPOSE_RESULT','HOST_HANDOVER_RESULT',
                'HOST_WAITING_RESULT','HOST_ACTIVE_RESULT','HOST_FUTURE_GPU_RESULT',
                'HOST_WAITING_DRAW_GPU_RESULT','HOST_ACTIVE_GPU_RESULT'):
        row=get(tag)
        if row['scenes']!=n or ('snapshots' in row and row['snapshots']!=snap):
            raise ValueError('quiet scene ownership/count mismatch '+tag)
    fence=get('HOST_FENCE_RESULT');cpu=get('HOST_MATERIALS_RESULT');gpu=get('HOST_MATERIALS_GPU_RESULT')
    if (fence['requested']!=n or fence['completed']!=n or fence['immediate']>n
            or cpu['queued']!=3*n or gpu['received']!=cpu['queued'] or gpu['hash']!=cpu['hash']
            or gpu['snapshots']!=3*snap):
        raise ValueError('quiet fence/material completion mismatch')
    if (get('HOST_FUTURE_GPU_RESULT')['quads']!=scene['quads']
            or get('HOST_ACTIVE_RESULT')['quads']!=get('HOST_ACTIVE_GPU_RESULT')['quads']):
        raise ValueError('quiet CPU/GPU geometry mismatch')
    endpoint=get('MODEL_ENDPOINT_RESULT')
    if (not endpoint['commits'] or endpoint['commits']!=endpoint['consumed']
            or endpoint['prepared']!=endpoint['commits'] or not get('ENDPOINT_GPU_RESULT')['pairs']
            or not get('MODEL_ADMIT_RESULT')['packets'] or not get('LIFETIME_RESULT')['records']):
        raise ValueError('quiet endpoint/lifetime completion mismatch')
    if endpoint['snapshots'] and not operands.stat().st_size:
        raise ValueError('quiet endpoint snapshots lack retained operands')
    for tag in ('HOST_FUTURE_GPU_RESULT','HOST_WAITING_DRAW_GPU_RESULT'):
        if get(tag)['written']!=4*snap:raise ValueError('quiet snapshot writer count mismatch')
    if get('DEPTH_MIRROR_RESULT')['snapshots']!=depth_snap:
        raise ValueError('quiet depth snapshot count mismatch')
    for tag,count in (('DEPTH_MIRROR_WRITER',depth_snap),('HOST_ACTIVE_WRITER',snap)):
        row=get(tag)
        if (row['submitted']!=4*count or row['written']!=row['submitted']
                or not 0<=row['peak_bytes']<=512*1024*1024):
            raise ValueError('quiet writer completion mismatch '+tag)
    return dict(mode=mode,independent_event_journals=False,continuous=False,receipts=receipts,
        scope='Native completion summaries; independent input and optional snapshot checks are separate. No saved per-event ownership proof.')
