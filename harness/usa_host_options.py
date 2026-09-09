"""Explicit USA host-scene diagnostics, preserving absent/recorded options."""
MODES = {'off': '0', 'observe': '1', 'draw': '2'}
LAYERS = {'legacy': '0', 'coverage': '1', 'split': '2', 'both': '3'}
PREFIX = 'MIDV_USA_HOST_'


def add_arguments(parser):
    parser.add_argument('--usa-host-scenery', choices=MODES)
    parser.add_argument('--usa-host-first', type=int)
    parser.add_argument('--usa-host-last', type=int)
    parser.add_argument('--usa-host-far', type=int, choices=(80000, 160000, 240000))
    parser.add_argument('--usa-host-log', choices=('summary', 'quads'))
    parser.add_argument('--usa-host-layer', choices=LAYERS)


def configure(args, rom, settings):
    mode = getattr(args, 'usa_host_scenery', None)
    first, last, far, trace, layer = [getattr(args, 'usa_host_'+name, None)
                                     for name in ('first', 'last', 'far', 'log', 'layer')]
    if mode is None:
        if any(v is not None for v in (first, last, far, trace, layer)):
            raise ValueError('USA host controls require an explicit mode')
        saved = settings.get(PREFIX+'SCENERY', '0')
        if saved == '0':
            return None
        if saved not in ('1', '2'):
            raise ValueError('invalid recorded USA host mode')
        mode = {v: k for k, v in MODES.items()}[saved]
        try:
            first, last = int(settings[PREFIX+'FIRST']), int(settings[PREFIX+'LAST'])
            far = int(settings.get(PREFIX+'FAR', '80000'))
            trace = {'0': 'summary', '1': 'quads'}[settings.get(PREFIX+'QUADS', '0')]
            layer = {v: k for k, v in LAYERS.items()}[settings.get(PREFIX+'LAYER', '3')]
        except (ValueError, KeyError) as error:
            raise ValueError('invalid recorded USA host controls') from error
    if rom != 'crusnusa' or mode not in MODES:
        raise ValueError('USA host scenery requires USA 4.5')
    if mode == 'off':
        if any(v is not None for v in (first, last, far, trace, layer)):
            raise ValueError('USA host off does not take additional controls')
        for key in ('FIRST', 'LAST', 'FAR', 'QUADS', 'LAYER'):
            settings.pop(PREFIX+key, None)
        settings[PREFIX+'SCENERY'] = '0'
        return dict(mode='off')
    far = 80000 if far is None else far
    trace = 'summary' if trace is None else trace
    layer = 'both' if layer is None else layer
    if first is None or last is None or not 1 <= first <= last <= 1000000:
        raise ValueError('USA host requires bounded first/last frames')
    if far not in (80000, 160000, 240000) or trace not in ('summary', 'quads') or layer not in LAYERS:
        raise ValueError('invalid USA host controls')
    if settings.get('MIDV_USA_FAR') or getattr(args, 'usa_far', None) is not None:
        raise ValueError('USA host requires stock guest distance/residency')
    if mode == 'draw' and (getattr(args, 'headless', False) or getattr(args, 'native_renderer', False) or settings.get('MIDV_GL') != '1'):
        raise ValueError('USA host draw requires live GL')
    settings.update({PREFIX+'SCENERY': MODES[mode], PREFIX+'FIRST': str(first), PREFIX+'LAST': str(last),
                     PREFIX+'FAR': str(far), PREFIX+'QUADS': '1' if trace == 'quads' else '0', PREFIX+'LAYER': LAYERS[layer]})
    return dict(mode=mode, first=first, last=last, far=far, log=trace, layer=layer, source='pending')
