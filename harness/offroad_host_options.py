"""Explicit Off Road host-scene diagnostics, preserving absent/recorded options."""
MODES = {'off': '0', 'observe': '1', 'draw': '2'}
LAYERS = {'legacy': '0', 'coverage': '1', 'split': '2', 'both': '3'}
PREFIX = 'MIDV_OFFROAD_HOST_'


def add_arguments(parser):
    parser.add_argument('--offroad-host-scenery', choices=MODES)
    parser.add_argument('--offroad-host-first', type=int)
    parser.add_argument('--offroad-host-last', type=int)
    parser.add_argument('--offroad-host-distance', type=int, choices=(1, 2, 3))
    parser.add_argument('--offroad-host-log', choices=('summary', 'quads'))
    parser.add_argument('--offroad-host-layer', choices=LAYERS)
    parser.add_argument('--offroad-host-source', choices=('pending', 'future'))


def configure(args, rom, settings):
    mode = getattr(args, 'offroad_host_scenery', None)
    first, last, distance, trace, layer, source = [getattr(args, 'offroad_host_'+name, None)
                                     for name in ('first', 'last', 'distance', 'log', 'layer', 'source')]
    if mode is None:
        if any(v is not None for v in (first, last, distance, trace, layer, source)):
            raise ValueError('Off Road host controls require an explicit mode')
        saved = settings.get(PREFIX+'SCENERY', '0')
        if saved == '0':
            return None
        if saved not in ('1', '2'):
            raise ValueError('invalid recorded Off Road host mode')
        mode = {v: k for k, v in MODES.items()}[saved]
        try:
            first, last = int(settings[PREFIX+'FIRST']), int(settings[PREFIX+'LAST'])
            distance = int(settings.get(PREFIX+'DISTANCE', '1'))
            trace = {'0': 'summary', '1': 'quads'}[settings.get(PREFIX+'QUADS', '0')]
            layer = {v: k for k, v in LAYERS.items()}[settings.get(PREFIX+'LAYER', '3')]
            source = {'0': 'pending', '1': 'future'}[settings[PREFIX+'FUTURE']] if PREFIX+'FUTURE' in settings else None
        except (ValueError, KeyError) as error:
            raise ValueError('invalid recorded Off Road host controls') from error
    if rom != 'offroadc' or mode not in MODES:
        raise ValueError('Off Road host scenery requires Off Road 1.63')
    if mode == 'off':
        if any(v is not None for v in (first, last, distance, trace, layer, source)):
            raise ValueError('Off Road host off does not take additional controls')
        for key in ('FIRST', 'LAST', 'DISTANCE', 'QUADS', 'LAYER', 'FUTURE'):
            settings.pop(PREFIX+key, None)
        settings[PREFIX+'SCENERY'] = '0'
        return dict(mode='off')
    distance = 1 if distance is None else distance
    trace = 'summary' if trace is None else trace
    layer = 'both' if layer is None else layer
    if first is None or last is None or not 1 <= first <= last <= 1000000:
        raise ValueError('Off Road host requires bounded first/last frames')
    if distance not in (1, 2, 3) or trace not in ('summary', 'quads') or layer not in LAYERS or source not in (None, 'pending', 'future'):
        raise ValueError('invalid Off Road host controls')
    if settings.get('MIDV_OFFROAD_DISTANCE', '0') != '0' or getattr(args, 'offroad_distance', None) not in (None, 0):
        raise ValueError('Off Road host requires stock guest distance/residency')
    if mode == 'draw' and (getattr(args, 'headless', False) or getattr(args, 'native_renderer', False) or settings.get('MIDV_GL') != '1'):
        raise ValueError('Off Road host draw requires live GL')
    settings.update({PREFIX+'SCENERY': MODES[mode], PREFIX+'FIRST': str(first), PREFIX+'LAST': str(last),
                     PREFIX+'DISTANCE': str(distance), PREFIX+'QUADS': '1' if trace == 'quads' else '0', PREFIX+'LAYER': LAYERS[layer]})
    if source is not None:
        settings[PREFIX+'FUTURE'] = '1' if source == 'future' else '0'
    return dict(mode=mode, first=first, last=last, distance=distance, log=trace, layer=layer,
                source='future' if settings.get(PREFIX+'FUTURE') == '1' else 'pending')
