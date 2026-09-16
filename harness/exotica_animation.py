"""Independent scalar model of the observed Exotica model-animation update.

This does not choose an initial random offset, establish object lifetime,
schedule updates, upload materials, or enable earlier animated geometry.
"""


def decode(header, values):
    if not isinstance(header, int) or not 0 <= header <= 0xffffffff:
        raise ValueError('animation header out of range')
    if not 2 <= len(values) <= 257 or any(not isinstance(v, int) or not 0 <= v <= 0xffffffff for v in values):
        raise ValueError('animation table size or word range')
    period, random_extent, count = header >> 24, (header >> 16) & 255, header & 65535
    if not period or count != len(values)-1 or random_extent > count or values[-1] != (-count & 0xffffffff):
        raise ValueError('animation period, count, random extent or sentinel')
    if any(not 0xa00000 <= v < 0x1000000 for v in values[:-1]):
        raise ValueError('animation model descriptor')
    return dict(period=period, random_extent=random_extent, models=list(values[:-1]))


def step(sequence, state):
    period, models = sequence['period'], sequence['models']
    remaining, cursor, model = state
    if (not 1 <= period <= 255 or not 1 <= len(models) <= 256
            or not 0 <= cursor <= len(models) or not 0 <= remaining <= period
            or not 0 <= model <= 0xffffffff or (model & 0xffffff) < 0xa00000):
        raise ValueError('animation state')
    remaining -= 1
    if remaining > 0:
        return remaining, cursor, model
    if cursor == len(models):
        cursor = 0
    if not 0xa00000 <= models[cursor] < 0x1000000:
        raise ValueError('animation selected descriptor')
    return period, cursor+1, models[cursor]


def initial_fields(definition, model, section, matrix, constants, trig, materials, node):
    """Initial fields with a supplied observed node; no future-source admission."""
    from exotica_sections import descriptor
    if (len(definition)!=6 or not definition[0]>>24
            or definition[5]&0xf00 in (0xa00,0xb00,0xc00,0xf00)
            or not 0x1000<=node<=0x40000-6 or (node<0x32000 and node+6>0x30000)):
        raise ValueError('unsupported animation initializer or node')
    plain=list(definition);plain[0]&=0xffffff
    fields=descriptor(plain,model,section,matrix,constants,trig,materials)
    if fields is None:raise ValueError('animation base fields')
    fields[15]|=0x2000
    fields[17],fields[24]=definition[0],node
    return fields
