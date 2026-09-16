"""Explicit continuous candidate operation, completed by an owned worker stop."""
import re
from pathlib import Path
from vunit_bootstrap import PROFILES

KEY='MIDV_HOST_RUNTIME'


def add_arguments(parser):
    parser.add_argument('--vunit-runtime',choices=('continuous',),
                        help='candidate continuous scenery with owned graphics-worker shutdown')


def configure(args,rom,settings,frames,bootstrap):
    mode=getattr(args,'vunit_runtime',None)
    if mode is None:
        if KEY in settings:raise ValueError('V-Unit runtime requires explicit replay selection')
        return None
    if (mode!='continuous' or rom not in PROFILES or not bootstrap or
            not getattr(args,'candidate',None) or getattr(args,'headless',False) or
            getattr(args,'native_renderer',False) or settings.get('MIDV_GL')!='1' or
            settings.get('MIDV_FFB')!='0' or settings.get('MIDV_HOST_BOOTSTRAP')!='1'):
        raise ValueError('continuous V-Unit requires candidate verified bootstrap, live GL and FFB0')
    settings[KEY]=mode
    bootstrap['runtime_last']=frames-1
    return dict(mode=mode,rom=rom,reference_last=bootstrap['last'],verification_last=frames-1,
                completion='owned-worker-stop',capture_completed=False)


def verify(trial,directory,bootstrap):
    lines=[]
    for name in ('stdout.log','stderr.log'):
        path=Path(directory)/name
        if not path.is_file() or path.stat().st_size>16*1024*1024:
            raise ValueError('missing or oversized V-Unit runtime receipt stream')
        lines.extend(line for line in path.read_text(encoding='utf-8',errors='replace').splitlines()
                     if line.startswith('VUNIT_RUNTIME'))
    if trial is None:
        if lines:raise ValueError('unrequested V-Unit runtime receipt')
        return None
    acks=['VUNIT_RUNTIME cpu=continuous end=none','VUNIT_RUNTIME gpu=owned']
    if any(lines.count(ack)!=1 for ack in acks):raise ValueError('missing V-Unit runtime acknowledgment')
    cpu=[];gpu=[]
    for line in lines:
        if line in acks:continue
        c=re.fullmatch(r'VUNIT_RUNTIME_CPU frame=(\d+) scenes=(\d+) quads=(\d+) failed=(\d+)',line)
        g=re.fullmatch(r'VUNIT_RUNTIME_GPU joined=1 ready=([01]) written=(\d+) read=(\d+) dropped=(\d+) failed=([01]) pending_quads=(\d+) gl_errors=(\d+) completed=(\d+) presented=(\d+)',line)
        if c:cpu.append(tuple(map(int,c.groups())))
        elif g:gpu.append(tuple(map(int,g.groups())))
        else:raise ValueError('malformed V-Unit runtime receipt')
    if len(cpu)!=1 or len(gpu)!=1 or not bootstrap or not bootstrap.get('verified'):
        raise ValueError('incomplete V-Unit runtime completion')
    frame,scenes,quads,failed=cpu[0]
    ready,written,read,dropped,stream_failed,pending,gl_errors,completed,presented=gpu[0]
    if (failed or not ready or written!=read or dropped or stream_failed or pending or gl_errors
            or not bootstrap['first']<=frame<=trial['verification_last']
            or frame!=bootstrap['last_prepared'] or scenes!=bootstrap['scenes']
            or not 0<=presented<=completed<=trial['verification_last']):
        raise ValueError('V-Unit runtime did not stop with verified complete work')
    from analyze_world_host import rows
    game=PROFILES[trial['rom']][0]
    _,records=rows(Path(directory)/f'{game}-host-scenes.csv')
    if quads!=sum(int(r['quads']) for r in records):
        raise ValueError('V-Unit runtime submission count differs from scene journal')
    return dict(verified=True,completion='owned-worker-stop',capture_completed=False,
                prepared_frame=frame,scenes=scenes,quads=quads,ring_bytes=written,
                completed_frame=completed,presented_frame=presented,
                beyond_reference_end=frame>trial['reference_last'])
