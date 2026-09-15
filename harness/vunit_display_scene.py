"""Select displayed V-Unit commands from an exact original-mirror receipt.

The receipt's ordinary_quads count fences the original DMA journal at the
completed GPU capture. Frame subtraction and the final draw-page group do not.
Selection alone does not reproduce CPU overlays, resource changes, host layers,
margin clears or the entire older framebuffer history.
"""
from dataclasses import dataclass
from pathlib import Path
import argparse,hashlib,json
import numpy as np

RECORD=np.dtype([('frame','<u4'),('page','<u2'),('dma','<u2',(16,))])
MAX_JOURNAL_BYTES=2*1024*1024*1024


@dataclass(frozen=True)
class DisplayScene:
    current: np.ndarray
    history: np.ndarray
    report: dict


def select(records,receipt):
    """Return current and prior same-page DMA groups, with explicit provenance.

    ``records`` must be the complete journal from the same native invocation as
    ``receipt``. Its immutable prefix is bounded by the consumed-command count.
    Caller resource/presentation checks remain necessary for pixel acceptance.
    """
    if not isinstance(receipt,dict) or not isinstance(records,np.ndarray) or records.dtype!=RECORD or records.ndim!=1:
        raise ValueError('expected native DMA records and a mirror receipt')
    for key in ('frame','ordinary_quads','visible_page'):
        if type(receipt.get(key)) is not int:
            raise ValueError(f'mirror {key} must be an integer')
    count,frame,visible=(receipt[k] for k in ('ordinary_quads','frame','visible_page'))
    if not 0<=frame<=0xffffffff or visible not in (0,1) or not 0<count<=len(records):
        raise ValueError('invalid mirror frame/page or consumed original-command count')
    if np.any(records['frame'][1:]<records['frame'][:-1]):
        raise ValueError('original DMA journal frame order differs')
    prefix=records[:count]
    if int(prefix['frame'][-1])>frame:
        raise ValueError('mirror count consumes commands after its completed frame')
    pages=prefix['page']
    changes=np.flatnonzero(pages[1:]!=pages[:-1])+1
    starts=np.concatenate(([0],changes));ends=np.concatenate((changes,[count]))
    matches=np.flatnonzero(((pages[starts]>>2)&1)==visible)
    if not len(matches):raise ValueError('visible page has no consumed original DMA group')
    selected=int(matches[-1]);start,end=int(starts[selected]),int(ends[selected])
    def describe(index):
        a,b=int(starts[index]),int(ends[index])
        return dict(first_record=a,end_record_exclusive=b,quads=b-a,
            first_frame=int(records['frame'][a]),last_frame=int(records['frame'][b-1]),
            page_control=int(pages[a]),physical_draw_page=int((pages[a]>>2)&1))
    history=records['dma'][:0];prior=None
    if len(matches)>1:
        previous=int(matches[-2]);a,b=int(starts[previous]),int(ends[previous])
        history=records['dma'][a:b];prior=describe(previous)
    report=dict(schema=1,basis='completed-mirror-original-command-count',completed_frame=frame,
        visible_page=visible,consumed_original_commands=count,total_journal_commands=len(records),
        consumed_prefix_sha256=hashlib.sha256(np.ascontiguousarray(prefix)).hexdigest(),
        excluded_unconsumed_commands=len(records)-count,current=describe(selected),history=prior,
        older_same_page_groups=max(0,len(matches)-2),pixel_reproduction_verified=False,
        scope='Same-invocation original DMA selection; current materials, CPU overlays, host commands and older page history require separate qualification.')
    return DisplayScene(records['dma'][start:end],history,report)


def load(run):
    """Read a journal and its completed mirror from one diagnostic run directory."""
    run=Path(run);path=run/'capture/quads.bin'
    size=path.stat().st_size
    if not 4<size<=MAX_JOURNAL_BYTES or (size-4)%RECORD.itemsize:
        raise ValueError('incomplete or oversized native DMA journal')
    with path.open('rb') as stream:
        if stream.read(4)!=b'MVQ1':raise ValueError('invalid native DMA journal magic')
    receipt=json.loads((run/'vunit-mirror.json').read_text(encoding='utf-8'))
    records=np.memmap(path,dtype=RECORD,mode='r',offset=4,shape=((size-4)//RECORD.itemsize,))
    return select(records,receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--quads',type=Path,help='optional local NPZ of original current/history DMA')
    args=parser.parse_args();scene=load(args.run)
    if args.quads:
        np.savez_compressed(args.quads,current=scene.current,history=scene.history)
    args.report.write_text(json.dumps(scene.report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(scene.report))


if __name__=='__main__':main()
