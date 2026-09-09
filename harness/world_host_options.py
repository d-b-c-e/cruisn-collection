"""Explicit, bounded World 2.4/2.5 host-scenery diagnostics; no product defaults."""
MODES={'off':'0','observe':'1','draw':'2'}
LAYERS={'legacy':'0','coverage':'1','split':'2','both':'3'}


def add_arguments(parser):
    parser.add_argument('--world-host-scenery',choices=MODES,
                        help='World 2.4/2.5 host-owned pending scenery: off/observe/draw (diagnostic)')
    parser.add_argument('--world-host-first',type=int)
    parser.add_argument('--world-host-last',type=int)
    parser.add_argument('--world-host-far',type=int,choices=(80000,160000,240000),
                        help='host-only far limit; guest distance and simulation remain original')
    parser.add_argument('--world-host-log',choices=('summary','quads'),
                        help='summary keeps scene counts/fingerprints/timing without per-quad CSV cost')
    parser.add_argument('--world-host-source',choices=('pending','future'),
                        help='future adds PC-owned upcoming section scenery to the pending-object path')
    parser.add_argument('--world-host-layer',choices=LAYERS,
                        help='isolate auxiliary coverage and vertex-batch ownership (diagnostic)')
    parser.add_argument('--world-host-roads',choices=('off','on'),
                        help='include separately decoded road templates (diagnostic)')


def configure(args,rom,settings):
    mode=getattr(args,'world_host_scenery',None)
    first=getattr(args,'world_host_first',None);last=getattr(args,'world_host_last',None)
    far=getattr(args,'world_host_far',None)
    trace=getattr(args,'world_host_log',None)
    source=getattr(args,'world_host_source',None)
    layer=getattr(args,'world_host_layer',None)
    roads=getattr(args,'world_host_roads',None)
    if mode is None:
        if any(value is not None for value in (first,last,far,trace,source,layer,roads)):
            raise ValueError('host bounds/logging require an explicit mode')
        inherited=settings.get('MIDV_WORLD_HOST_SCENERY','0')
        if inherited=='0':return None
        modes={v:k for k,v in MODES.items()}
        if inherited not in modes:raise ValueError('invalid recorded host scenery mode')
        mode=modes[inherited]
        first=int(settings['MIDV_WORLD_HOST_FIRST']);last=int(settings['MIDV_WORLD_HOST_LAST'])
        far=int(settings.get('MIDV_WORLD_HOST_FAR','80000'))
        saved_trace=settings.get('MIDV_WORLD_HOST_QUADS','1')
        if saved_trace not in ('0','1'):raise ValueError('invalid recorded host trace mode')
        trace='summary' if saved_trace=='0' else 'quads'
        saved_source=settings.get('MIDV_WORLD_HOST_FUTURE','0')
        if saved_source not in ('0','1'):raise ValueError('invalid recorded host source')
        if 'MIDV_WORLD_HOST_FUTURE' in settings:source='future' if saved_source=='1' else 'pending'
        if 'MIDV_WORLD_HOST_LAYER' in settings:
            layers={v:k for k,v in LAYERS.items()}
            if settings['MIDV_WORLD_HOST_LAYER'] not in layers:raise ValueError('invalid recorded host layer')
            layer=layers[settings['MIDV_WORLD_HOST_LAYER']]
        if 'MIDV_WORLD_HOST_ROADS' in settings:
            saved_roads=settings['MIDV_WORLD_HOST_ROADS']
            if saved_roads not in ('0','1'):raise ValueError('invalid recorded host roads')
            roads='on' if saved_roads=='1' else 'off'
    if rom not in ('crusnwld24','crusnwld') or mode not in MODES:
        raise ValueError('host scenery supports World 2.4/2.5 only')
    if mode!='off':
        trace='quads' if trace is None else trace
        if trace not in ('summary','quads'):raise ValueError('invalid host trace mode')
        if source not in (None,'pending','future'):raise ValueError('invalid host source')
        if layer is not None and layer not in LAYERS:raise ValueError('invalid host layer')
        if roads not in (None,'off','on'):raise ValueError('invalid host roads')
        if roads=='on' and rom!='crusnwld24':raise ValueError('host roads require World 2.4')
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
    elif any(value is not None for value in (first,last,far,trace,source,layer,roads)):
        raise ValueError('off mode does not take a frame interval')
    settings['MIDV_WORLD_HOST_SCENERY']=MODES[mode]
    for key,value in [('MIDV_WORLD_HOST_FIRST',first),('MIDV_WORLD_HOST_LAST',last),('MIDV_WORLD_HOST_FAR',far)]:
        if value is None:settings.pop(key,None)
        else:settings[key]=str(value)
    if trace is None:settings.pop('MIDV_WORLD_HOST_QUADS',None)
    else:settings['MIDV_WORLD_HOST_QUADS']='0' if trace=='summary' else '1'
    if source is None:settings.pop('MIDV_WORLD_HOST_FUTURE',None)
    else:settings['MIDV_WORLD_HOST_FUTURE']='1' if source=='future' else '0'
    if layer is None:settings.pop('MIDV_WORLD_HOST_LAYER',None)
    else:settings['MIDV_WORLD_HOST_LAYER']=LAYERS[layer]
    if roads is None:settings.pop('MIDV_WORLD_HOST_ROADS',None)
    else:settings['MIDV_WORLD_HOST_ROADS']='1' if roads=='on' else '0'
    return dict(mode=mode,first=first,last=last,far=far,log=trace,source=source or 'pending',layer=layer or 'legacy',roads=roads or 'off')
