"""Explicit Off Road 1.63 global far/clip/reciprocal trial; no guest writes."""
MULTIPLIERS=(0,1,2,3)


def add_arguments(parser):
    parser.add_argument('--offroad-distance',type=int,choices=MULTIPLIERS,
        help='Off Road 1.63 global distance: 0 disabled, 1 observed original, 2/3 extended')


def configure(args,rom,settings):
    multiplier=getattr(args,'offroad_distance',None)
    if multiplier is None:return None
    if multiplier not in MULTIPLIERS or rom!='offroadc':
        raise ValueError('global Off Road distance requires Off Road 1.63 and 0/1/2/3')
    if (getattr(args,'world_far',None) is not None or getattr(args,'usa_far',None) is not None
            or getattr(args,'exotica_visibility',None) is not None
            or settings.get('MIDV_WORLD_FAR') or settings.get('MIDV_USA_FAR')
            or settings.get('MIDZ_VISIBILITY','off')!='off'):
        raise ValueError('Off Road cannot combine with another game distance adapter')
    settings['MIDV_OFFROAD_DISTANCE']=str(multiplier)
    return dict(multiplier=multiplier,far=47296*max(1,multiplier),clip=63680*max(1,multiplier),
                maximum_index=63680*max(1,multiplier)-1)
