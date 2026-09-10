"""Explicit Zeus palette-lifetime trial; preserve absent recording settings."""
import re

MODES={'legacy':0,'guard':1}


def add_arguments(parser):
    parser.add_argument('--zeus-palette',choices=tuple(MODES),
        help='Exotica GL diagnostic: trace legacy palette-row reuse or flush before overwriting a pending row')


def configure(args,rom,settings):
    mode=getattr(args,'zeus_palette',None)
    if mode is not None:
        if mode not in MODES or not getattr(args,'candidate',None):
            raise ValueError('Zeus palette trial requires an explicit candidate')
        settings['MIDZ_PALETTE_GUARD']=str(MODES[mode])
    value=settings.get('MIDZ_PALETTE_GUARD')
    if value is None:return None
    if (rom!='crusnexo' or value not in ('0','1') or settings.get('MIDZ_GL')!='1' or
            getattr(args,'headless',False) or getattr(args,'native_renderer',False)):
        raise ValueError('Zeus palette trial requires Exotica 2.4 with live GL')
    return dict(guard=int(value),explicit=mode is not None)


def verify_receipt(trial,text):
    if trial is None:return None
    guard=trial['guard']
    if len(re.findall(rf'^MIDZ_PALETTE_GUARD={guard}$',text,re.M))!=1:
        raise ValueError('candidate did not acknowledge the requested palette policy')
    rows=re.findall(r'^MIDZ_PALETTE_RESULT guard=([01]) conflicts=(\d+) flushes=(\d+)$',text,re.M)
    if len(rows)!=1:raise ValueError('missing or duplicate palette completion receipt')
    actual,conflicts,flushes=map(int,rows[0])
    if actual!=guard or flushes!=(conflicts if guard else 0):
        raise ValueError('palette lifetime completion counters disagree')
    return dict(guard=guard,conflicts=conflicts,flushes=flushes)
