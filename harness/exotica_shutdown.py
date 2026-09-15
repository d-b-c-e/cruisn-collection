"""Observe teardown without treating interrupted work as completed rendering."""
from pathlib import Path
import re

KEY='MIDZ_SHUTDOWN_OBSERVE'
FIELDS={
    'CPU':'frame scene_open loading pool_pending source_pending models_pending endpoints_pending fence_pending waiting_pending compose_pending prepared matched requested completed'.split(),
    'GPU':'frame endpoint_pending material_pending failed writer_failed'.split(),
    'JOIN':'written read joined'.split(),
}

def add_arguments(parser):
    parser.add_argument('--exotica-shutdown',choices=('observe',),help='record pre-teardown CPU work and joined GPU queue; does not change exit or drain')

def configure(args,rom,settings):
    mode=getattr(args,'exotica_shutdown',None)
    if mode is None:
        if KEY in settings:raise ValueError('shutdown observation requires explicit selection')
        return None
    if mode!='observe' or rom!='crusnexo' or not getattr(args,'candidate',None) or settings.get('MIDV_FFB')!='0' or settings.get('MIDZ_BOOTSTRAP')!='3':
        raise ValueError('shutdown observation requires Exotica candidate, guest scene startup and FFB0')
    settings[KEY]='1'
    return dict(mode=mode,changes_shutdown=False)

def verify(trial,directory):
    lines=[]
    for name in ('stdout.log','stderr.log'):
        path=Path(directory)/name
        if not path.is_file() or path.stat().st_size>16*1024*1024:raise ValueError('missing or oversized shutdown receipt stream')
        lines += [x for x in path.read_text(encoding='utf-8',errors='replace').splitlines() if x.startswith('MIDZ_SHUTDOWN')]
    if trial is None:
        if lines:raise ValueError('unrequested shutdown observer')
        return None
    if lines.count(KEY+'=1')!=1 or len(lines)!=4:raise ValueError('missing, extra or duplicate shutdown receipt')
    values={}
    for tag,names in FIELDS.items():
        pattern='MIDZ_SHUTDOWN_'+tag+' '+' '.join(k+r'=(\d+)' for k in names)
        matches=[re.fullmatch(pattern,line) for line in lines];matches=[m for m in matches if m]
        if len(matches)!=1:raise ValueError('malformed shutdown '+tag)
        row=dict(zip(names,map(int,matches[0].groups())))
        if any(v>2**64-1 for v in row.values()):raise ValueError('shutdown counter overflow')
        values[tag]=row
    cpu,gpu,join=(values[k] for k in ('CPU','GPU','JOIN'))
    flags=('scene_open','loading','pool_pending','source_pending','fence_pending','waiting_pending','compose_pending')
    if (any(cpu[k]>1 for k in flags) or any(gpu[k]>1 for k in ('endpoint_pending','material_pending','failed','writer_failed')) or
            cpu['models_pending']>4096 or cpu['endpoints_pending']>4096 or cpu['matched']>cpu['prepared'] or
            cpu['completed']>cpu['requested'] or gpu['frame']>cpu['frame']+1 or
            join['joined']!=1 or join['read']>join['written'] or join['written']-join['read']>64*1024*1024 or
            (join['read']|join['written'])&7):
        raise ValueError('shutdown counter/queue contract')
    pending=[k for k in flags if cpu[k]]
    pending += [k for k in ('models_pending','endpoints_pending') if cpu[k]]
    pending += [k for k in ('endpoint_pending','material_pending') if gpu[k]]
    if cpu['prepared']!=cpu['matched']:pending.append('unmatched_models')
    if cpu['requested']!=cpu['completed']:pending.append('unfinished_fences')
    queued=join['written']-join['read']
    if queued:pending.append('queued_gpu_bytes')
    failed=bool(gpu['failed'] or gpu['writer_failed'])
    return dict(observed=True,classification='failed' if failed else 'interrupted' if pending else 'quiescent',
                pending=pending,queued_bytes=queued,receipts=values,changes_shutdown=False,
                scope='Observed teardown state only; quiescence does not establish capture completion, reset safety or continuous operation.')
