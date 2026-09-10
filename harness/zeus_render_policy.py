"""Independent #16094 depth/blend trial semantics; zero preserves old recordings."""
MODES={'legacy':0,'depth':1,'alpha':2,'blend':4,'all':7}
FLAG_DEPTH_FLOOR=512


def material(mask,mode,depth,blend,source):
    if type(mask) is not int or not 0<=mask<=7:raise ValueError('invalid Zeus render policy')
    alpha=mode&3==2 and bool(mode&0x80)
    enabled=(blend&0x02ff00==0x020200 if mask&4 else blend==0x020202) or (blend==0x021e0e and mode&3==2)
    return dict(blend=enabled,source_alpha=256 if mask&4 and blend&255==4 else min(source,256),
        depth_test=not depth&0x20 and (not alpha or bool(mask&2)),
        depth_write=not depth&0x1000 and (not alpha or bool(mask&2)))


def add_arguments(parser):
    parser.add_argument('--zeus-upstream',choices=tuple(MODES),
        help='Exotica diagnostic A/B for upstream #16094: depth floor, alpha depth, blend fields, or all; preserves old recordings when absent')


def configure(args,rom,settings):
    mode=getattr(args,'zeus_upstream',None)
    if mode is not None:
        if mode not in MODES or rom!='crusnexo':raise ValueError('Zeus rendering trial requires Exotica 2.4')
        if MODES[mode] and not getattr(args,'candidate',None):raise ValueError('Zeus rendering trial requires an explicit candidate')
        settings['MIDZ_UPSTREAM_RENDER']=str(MODES[mode])
    value=settings.get('MIDZ_UPSTREAM_RENDER')
    if value is None:return None
    if rom!='crusnexo' or value not in tuple(map(str,range(8))):raise ValueError('invalid frozen Zeus rendering trial')
    return dict(mask=int(value),upstream_pr=16094,head='54b7ec0720e1d3a3d26a2e881b06628f78732837',explicit=mode is not None)


def verify_receipt(trial,text):
    # Legacy0 is also accepted on archived binaries that predate this option.
    if trial and trial['mask'] and f"MIDZ_UPSTREAM_RENDER={trial['mask']} PR=16094" not in text:
        raise ValueError('candidate did not acknowledge the requested Zeus rendering semantics')
