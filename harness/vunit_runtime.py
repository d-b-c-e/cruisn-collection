"""Explicit continuous candidate operation, completed by an owned worker stop."""
import re
from pathlib import Path
from vunit_bootstrap import PROFILES

KEY='MIDV_HOST_RUNTIME'
JOURNALS='MIDV_HOST_JOURNALS'


def add_arguments(parser):
    parser.add_argument('--vunit-runtime',choices=('continuous',),
                        help='candidate continuous scenery with owned graphics-worker shutdown')
    parser.add_argument('--vunit-journals',choices=('quiet',),
                        help='explicit continuous operation without scene journals or bootstrap RAM dumps')


def configure(args,rom,settings,frames,bootstrap):
    mode=getattr(args,'vunit_runtime',None)
    quiet=getattr(args,'vunit_journals',None)
    if quiet is None and JOURNALS in settings:
        raise ValueError('V-Unit journals require explicit replay selection')
    if mode is None:
        if KEY in settings or quiet:raise ValueError('V-Unit runtime requires explicit replay selection')
        return None
    if (mode!='continuous' or rom not in PROFILES or not bootstrap or
            not getattr(args,'candidate',None) or getattr(args,'headless',False) or
            getattr(args,'native_renderer',False) or settings.get('MIDV_GL')!='1' or
            settings.get('MIDV_FFB')!='0' or settings.get('MIDV_HOST_BOOTSTRAP')!='1'):
        raise ValueError('continuous V-Unit requires candidate verified bootstrap, live GL and FFB0')
    settings[KEY]=mode
    bootstrap['runtime_last']=frames-1
    if quiet:
        game=PROFILES[rom][0]
        if quiet!='quiet' or settings.get('MIDV_'+game.upper()+'_HOST_QUADS')!='0' or any(
                settings.get(k,'0')!='0' for k in ('MIDV_WORLD_HOST_FADE_METADATA','MIDV_GL_ORIGINAL_MIRROR',
                    'MIDV_WORLD_HOST_QUADS','MIDV_USA_HOST_QUADS','MIDV_OFFROAD_HOST_QUADS')):
            raise ValueError('quiet V-Unit requires summary geometry without detailed mirror/fade capture')
        settings[JOURNALS]='quiet'
        bootstrap['journals']='quiet'
    return dict(mode=mode,rom=rom,journals=quiet or 'capture',reference_last=bootstrap['last'],verification_last=frames-1,
                completion='owned-worker-stop',capture_completed=False)


def receipts(trial,directory):
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
    cpu=[];gpu=[];geometry=[]
    for line in lines:
        if line in acks:continue
        c=re.fullmatch(r'VUNIT_RUNTIME_CPU frame=(\d+) scenes=(\d+) quads=(\d+) failed=(\d+)',line)
        g=re.fullmatch(r'VUNIT_RUNTIME_GPU joined=1 ready=([01]) written=(\d+) read=(\d+) dropped=(\d+) failed=([01]) pending_quads=(\d+) gl_errors=(\d+) completed=(\d+) presented=(\d+)',line)
        j=re.fullmatch(r'VUNIT_RUNTIME_JOURNALS quiet=1 geometry=([0-9a-f]{16})',line)
        if c:cpu.append(tuple(map(int,c.groups())))
        elif g:gpu.append(tuple(map(int,g.groups())))
        elif j:geometry.append(j[1])
        else:raise ValueError('malformed V-Unit runtime receipt')
    if len(cpu)!=1 or len(gpu)!=1 or len(geometry)!=int(trial.get('journals')=='quiet'):
        raise ValueError('incomplete V-Unit runtime completion')
    return cpu[0],gpu[0],geometry[0] if geometry else None


def verify(trial,directory,bootstrap):
    parsed=receipts(trial,directory)
    if parsed is None:return None
    if not bootstrap or not bootstrap.get('verified'):
        raise ValueError('incomplete V-Unit runtime completion')
    cpu,gpu,geometry=parsed
    frame,scenes,quads,failed=cpu
    ready,written,read,dropped,stream_failed,pending,gl_errors,completed,presented=gpu
    if (failed or not ready or written!=read or dropped or stream_failed or pending or gl_errors
            or not bootstrap['first']<=frame<=trial['verification_last']
            or frame!=bootstrap['last_prepared'] or scenes!=bootstrap['scenes']
            or not 0<=presented<=completed<=trial['verification_last']):
        raise ValueError('V-Unit runtime did not stop with verified complete work')
    if trial.get('journals')!='quiet':
        from analyze_world_host import rows
        game=PROFILES[trial['rom']][0]
        _,records=rows(Path(directory)/f'{game}-host-scenes.csv')
        if quads!=sum(int(r['quads']) for r in records):
            raise ValueError('V-Unit runtime submission count differs from scene journal')
    return dict(verified=True,completion='owned-worker-stop',capture_completed=False,
                journals=trial.get('journals','capture'),geometry=geometry,
                prepared_frame=frame,scenes=scenes,quads=quads,ring_bytes=written,
                completed_frame=completed,presented_frame=presented,
                beyond_reference_end=frame>trial['reference_last'])
