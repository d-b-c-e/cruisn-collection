"""Explicit enhanced-margin page-clear trial; preserve absent recordings."""
import re

MODES={'legacy':0,'page':1}


def add_arguments(parser):
    parser.add_argument('--zeus-margin-clear',choices=tuple(MODES),
        help='Exotica GL diagnostic: clear partial rows or the same full page in widened margins')


def configure(args,rom,settings):
    mode=getattr(args,'zeus_margin_clear',None)
    if mode is not None:
        if mode not in MODES or not getattr(args,'candidate',None):
            raise ValueError('Zeus margin-clear trial requires an explicit candidate')
        settings['MIDZ_GL_MARGIN_PAGE_CLEAR']=str(MODES[mode])
    value=settings.get('MIDZ_GL_MARGIN_PAGE_CLEAR')
    if value is None:return None
    if (rom!='crusnexo' or value not in ('0','1') or settings.get('MIDZ_GL')!='1' or
            getattr(args,'headless',False) or getattr(args,'native_renderer',False)):
        raise ValueError('Zeus margin-clear trial requires Exotica 2.4 with live GL')
    return dict(page=int(value),explicit=mode is not None)


def verify_receipt(trial,text):
    if trial is None:return None
    page=trial['page']
    if len(re.findall(rf'^MIDZ_GL_MARGIN_PAGE_CLEAR={page}$',text,re.M))!=1:
        raise ValueError('candidate did not acknowledge the requested margin-clear policy')
    rows=re.findall(r'^MIDZ_MARGIN_RESULT page=([01]) clears=(\d+) expanded=(\d+)$',text,re.M)
    if len(rows)!=1:raise ValueError('missing or duplicate margin-clear completion receipt')
    actual,clears,expanded=map(int,rows[0])
    if actual!=page or expanded>clears or (not page and expanded):
        raise ValueError('margin-clear completion counters disagree')
    return dict(page=page,clears=clears,expanded=expanded)
