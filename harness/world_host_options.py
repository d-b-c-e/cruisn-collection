"""Explicit, bounded World 2.4 host-scenery diagnostics; no product defaults."""
MODES={'off':'0','observe':'1','draw':'2'}


def add_arguments(parser):
    parser.add_argument('--world-host-scenery',choices=MODES,
                        help='World 2.4 host-owned pending scenery: off/observe/draw (diagnostic)')
    parser.add_argument('--world-host-first',type=int)
    parser.add_argument('--world-host-last',type=int)
    parser.add_argument('--world-host-far',type=int,choices=(80000,160000,240000),
                        help='host-only far limit; guest distance and simulation remain original')


def configure(args,rom,settings):
    mode=getattr(args,'world_host_scenery',None)
    first=getattr(args,'world_host_first',None);last=getattr(args,'world_host_last',None)
    far=getattr(args,'world_host_far',None)
    if mode is None:
        if first is not None or last is not None or far is not None:raise ValueError('host bounds require an explicit mode')
        inherited=settings.get('MIDV_WORLD_HOST_SCENERY','0')
        if inherited=='0':return None
        modes={v:k for k,v in MODES.items()}
        if inherited not in modes:raise ValueError('invalid recorded host scenery mode')
        mode=modes[inherited]
        first=int(settings['MIDV_WORLD_HOST_FIRST']);last=int(settings['MIDV_WORLD_HOST_LAST'])
        far=int(settings.get('MIDV_WORLD_HOST_FAR','80000'))
    if rom!='crusnwld24' or mode not in MODES:raise ValueError('host scenery supports World 2.4 only')
    if mode!='off':
        far=80000 if far is None else far
        if far not in (80000,160000,240000):raise ValueError('invalid host far limit')
        if first is None or last is None or not 1<=first<=last<=1000000:
            raise ValueError('host scenery requires bounded --world-host-first/last')
        if (settings.get('MIDV_WORLD_FAR') or settings.get('MIDV_SCENERY','off') not in ('off','0')
                or getattr(args,'world_far',None) is not None):
            raise ValueError('host scenery requires stock distance and activation')
        if mode=='draw' and (getattr(args,'headless',False) or getattr(args,'native_renderer',False)
                            or settings.get('MIDV_GL')!='1'):
            raise ValueError('host scenery drawing requires live GL presentation')
    elif first is not None or last is not None or far is not None:
        raise ValueError('off mode does not take a frame interval')
    settings['MIDV_WORLD_HOST_SCENERY']=MODES[mode]
    for key,value in [('MIDV_WORLD_HOST_FIRST',first),('MIDV_WORLD_HOST_LAST',last),('MIDV_WORLD_HOST_FAR',far)]:
        if value is None:settings.pop(key,None)
        else:settings[key]=str(value)
    return dict(mode=mode,first=first,last=last,far=far)
