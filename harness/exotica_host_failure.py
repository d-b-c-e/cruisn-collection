"""Narrow Exotica future-assembly retirement diagnostics, never parity acceptance."""
from pathlib import Path
import re

KEYS = ('MIDZ_HOST_FAILURE_POLICY', 'MIDZ_HOST_FAILURE_FRAME')


def add_arguments(parser):
    parser.add_argument('--exotica-host-failure', choices=('strict', 'original'))
    parser.add_argument('--exotica-host-inject-failure-frame', type=int,
                        help='candidate-only future assembly failure; combined private draw and FFB0 required')


def configure(args, rom, settings, frames):
    policy = getattr(args, 'exotica_host_failure', None)
    inject = getattr(args, 'exotica_host_inject_failure_frame', None)
    if policy is None:
        if inject is not None or any(k in settings for k in KEYS):
            raise ValueError('Exotica failure controls require explicit selection')
        return None
    required = {'MIDV_FFB':'0', 'MIDZ_GL':'1', 'MIDZ_HOST_FUTURE':'2',
                'MIDZ_HOST_COMPOSE':'1', 'MIDZ_HOST_FUTURE_PRESENT':'1'}
    if (policy not in ('strict','original') or rom != 'crusnexo' or not getattr(args, 'candidate', None)
            or getattr(args, 'headless', False) or getattr(args, 'native_renderer', False)
            or any(settings.get(k) != v for k,v in required.items())):
        raise ValueError('Exotica failure trial requires candidate combined private presentation, live GL and FFB0')
    first, last = int(settings.get('MIDZ_HOST_FIRST','0')), int(settings.get('MIDZ_HOST_LAST','0'))
    if not 1800 <= first <= last < frames-1:
        raise ValueError('Exotica failure trial requires bounded scenes before drain')
    reference_first,reference_last=first,last
    continuous=getattr(args,'exotica_runtime',None)=='continuous'
    if continuous and (getattr(args,'exotica_bootstrap',None)!='scenes' or
                       getattr(args,'exotica_journals',None)!='quiet'):
        raise ValueError('continuous Exotica failure trial requires quiet guest-based startup')
    if getattr(args,'exotica_bootstrap',None)=='scenes':first=1
    if continuous:last=frames-1
    # Leave two full frames for the ready fence and original presentation.
    injection_last=min(16000,frames-3) if continuous else last
    if inject is not None and (type(inject) is not int or not first <= inject <= injection_last):
        raise ValueError('Exotica injected failure outside scene interval')
    settings[KEYS[0]] = '1' if policy == 'original' else '0'
    settings.pop(KEYS[1], None)
    if inject is not None:
        # Late source snapshots cannot be silently omitted after retirement.
        for key in ('MIDZ_HOST_SNAPSHOTS','MIDZ_MODEL_ENDPOINT_SNAPSHOT'):
            if any(int(v) >= inject for v in settings.get(key,'').split(',') if v):
                raise ValueError('source snapshots must precede the injected failure')
        settings[KEYS[1]] = str(inject)
    return dict(policy=policy, inject=inject or 0, first=first, last=last,
                continuous=continuous,reference_first=reference_first,reference_last=reference_last)


def verify_receipt(trial, directory):
    lines=[]
    for name in ('stdout.log','stderr.log'):
        path=Path(directory)/name
        if not path.is_file() or path.stat().st_size>16*1024*1024:
            raise ValueError('missing or oversized Exotica failure receipt stream')
        lines += [s for s in path.read_text(encoding='utf-8',errors='replace').splitlines()
                  if s.startswith(('EXOTICA_HOST_FAILURE_POLICY','EXOTICA_HOST_PREP_FAILURE','EXOTICA_HOST_RETIRE_'))]
    if trial is None:
        if lines:raise ValueError('unrequested Exotica failure receipt')
        return None
    patterns = {
        'policy':r'EXOTICA_HOST_FAILURE_POLICY original=([01]) inject=(\d+)',
        'failure':r'EXOTICA_HOST_PREP_FAILURE frame=(\d+) scene=(\d+) injected=([01]) fallback=([01])',
        'queued':r'EXOTICA_HOST_RETIRE_QUEUED frame=(\d+) scene=(\d+)',
        'gpu':r'EXOTICA_HOST_RETIRE_GPU frame=(\d+) scene=(\d+)',
        'present':r'EXOTICA_HOST_RETIRE_PRESENT frame=(\d+) scene=(\d+)'}
    rows={k:[] for k in patterns}
    for line in lines:
        matches=[(k,re.fullmatch(p,line)) for k,p in patterns.items()]
        matches=[(k,m) for k,m in matches if m]
        if len(matches)!=1:raise ValueError('malformed Exotica failure receipt')
        key,m=matches[0];rows[key].append(tuple(map(int,m.groups())))
    fallback=int(trial['policy']=='original')
    if rows['policy']!=[(fallback,trial['inject'])] or any(len(v)>1 for v in rows.values()):
        raise ValueError('missing or duplicated Exotica failure acknowledgment')
    if not rows['failure']:
        if trial['inject'] or any(rows[k] for k in ('queued','gpu','present')):
            raise ValueError('Exotica failure trial was not exercised')
        return dict(degraded=False)
    frame,scene,injected,applied=rows['failure'][0]
    if (not trial['first']<=frame<=trial['last']+1 or not scene or applied!=fallback
            or injected!=bool(trial['inject']) or (injected and frame<trial['inject'])):
        raise ValueError('Exotica failure differs from requested trial')
    result=dict(degraded=True,failure=dict(frame=frame,scene=scene,injected=bool(injected),fallback=bool(applied)))
    if fallback:
        if (len(rows['queued'])!=1 or rows['gpu']!=rows['queued'] or len(rows['present'])!=1):
            raise ValueError('Exotica retirement did not reach CPU, GPU and presentation')
        ready,owner=rows['queued'][0];present,present_owner=rows['present'][0]
        if owner!=scene or present_owner!=scene or not frame<=ready<=frame+1 or not ready<=present<=ready+1:
            raise ValueError('Exotica retirement frame/scene mismatch')
        result.update(queued_frame=ready,presented_frame=present)
    elif any(rows[k] for k in ('queued','gpu','present')):
        raise ValueError('strict Exotica failure unexpectedly retired')
    return result
