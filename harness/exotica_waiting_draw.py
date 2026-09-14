"""Join private waiting draw receipts to actual completed ownership cohorts."""
from pathlib import Path
import re
from exotica_waiting import bounded_rows
from exotica_future_gpu import verify as verify_gpu


def verify(directory,text,enabled,captures):
    directory=Path(directory)
    if not enabled:
        if ('MIDZ_HOST_WAITING_DRAW' in text or list(directory.glob('exotica-waiting-draw-*'))):
            raise ValueError('disabled private waiting drawing ran')
        return None
    if re.findall(r'^MIDZ_HOST_WAITING_DRAW=(\d+)$',text,re.M)!=['2']:
        raise ValueError('missing private waiting draw acknowledgment')
    sources=bounded_rows(directory/'exotica-host-scenes.csv')
    completed=bounded_rows(directory/'exotica-handover-scenes.csv')
    if not sources or len(sources)!=len(completed):raise ValueError('waiting draw completion count')
    scenes=[]
    for source,completion in zip(sources,completed):
        if source['scene']!=completion['scene'] or source['frame']!=completion['proposal_frame']:
            raise ValueError('waiting draw proposal/completion order')
        scenes.append(dict(source,quads=completion['quads'],hash=completion['geometry_hash']))
    for frame in captures:
        for suffix in ('quads','instances'):
            a=directory/f'exotica-waiting-draw-{frame}-{suffix}.bin'
            b=directory/f'exotica-handover-{frame}-{suffix}.bin'
            if a.read_bytes()!=b.read_bytes():raise ValueError('waiting packet differs from completed geometry')
    result=verify_gpu(directory,scenes,text,2,captures,waiting=True,kind='waiting-draw')
    result['scope']='Private draw delivery and retained material/geometry bindings at actual completed cohorts; independent pixel/temporal/performance acceptance remains separate.'
    return result
