"""Opt-in periodic panorama continuation, isolated from saved display settings."""
import re
MODES={'off':0,'repeat':1}


def add_arguments(p):
    p.add_argument('--zeus-sky',choices=tuple(MODES),help='Exotica diagnostic: continue proven repeating panorama tiles; requires guarded palettes and page margin clearing')


def configure(args,rom,settings):
    mode=getattr(args,'zeus_sky',None)
    if mode is not None:
        if mode not in MODES or not getattr(args,'candidate',None):raise ValueError('Zeus sky trial requires an explicit candidate')
        settings['MIDZ_SKY_REPEAT']=str(MODES[mode])
    value=settings.get('MIDZ_SKY_REPEAT')
    if value is None:return None
    if (rom!='crusnexo' or value not in ('0','1') or settings.get('MIDZ_GL')!='1' or
        getattr(args,'headless',False) or getattr(args,'native_renderer',False)):
        raise ValueError('Zeus sky trial requires Exotica2.4/live GL')
    if value=='1' and (settings.get('MIDZ_PALETTE_GUARD')!='1' or settings.get('MIDZ_GL_MARGIN_PAGE_CLEAR')!='1'):
        raise ValueError('Zeus sky repeat requires palette guard and page margin clearing')
    return dict(enabled=int(value),explicit=mode is not None)


def verify_receipt(trial,text):
    if trial is None:return None
    enabled=trial['enabled']
    if len(re.findall(rf'^MIDZ_SKY_REPEAT={enabled}$',text,re.M))!=1:raise ValueError('missing sky policy acknowledgment')
    rows=re.findall(r'^MIDZ_SKY_REPEAT_RESULT enabled=([01]) groups=(\d+) accepted=(\d+) copied=(\d+) budget_rejected=(\d+)$',text,re.M)
    if len(rows)!=1:raise ValueError('missing or duplicate sky completion receipt')
    actual,groups,accepted,copied,budget=map(int,rows[0])
    if actual!=enabled or accepted>groups or copied>accepted*8 or (not enabled and (groups or accepted or copied or budget)):
        raise ValueError('sky completion counters disagree')
    return dict(enabled=enabled,groups=groups,accepted=accepted,copied=copied,budget_rejected=budget)
