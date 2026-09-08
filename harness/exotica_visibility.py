"""Explicit Exotica 2.4 CPU visibility trials. All modes preserve the 204800 far plane."""
MODES=('off','stock','projection','margins','both')


def add_arguments(parser):
    parser.add_argument('--exotica-visibility',choices=MODES,
        help='Exotica 2.4 CPU sphere experiment: unclamped projection, wide margins, or both; off is default')


def configure(args,rom,settings):
    mode=getattr(args,'exotica_visibility',None)
    if mode is None:return None
    if mode not in MODES or rom!='crusnexo':raise ValueError('visibility trial requires Exotica 2.4')
    if (getattr(args,'world_far',None) is not None or getattr(args,'usa_far',None) is not None
            or settings.get('MIDV_WORLD_FAR') or settings.get('MIDV_USA_FAR')):
        raise ValueError('Exotica cannot use a V-Unit distance adapter')
    settings['MIDZ_VISIBILITY']=mode
    return dict(mode=mode,far=204800,margin=88 if mode in ('margins','both') else 0,
                projection=mode in ('projection','both'))
