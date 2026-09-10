"""Read-only Exotica 2.4 section descriptors, before guest activation.

Positions and render fields only: no physics links, guest allocation or drawing.
Material lookup values are rebound per snapshot, not a residency guarantee.
The caller must supply a checked bank and loader-in-progress state.
"""
from scenery_c31 import F, dot, signed
from verify_world_sections import yaw_matrix  # Shared C31 polynomial, also used by USA.

FIELDS = (*range(1, 4), *range(5, 31))


def code_matches(read):
    code = ((0xb7e8, 0x082e0597), (0xb804, 0x08442501), (0xb817, 0x152e0597),
            (0xb842, 0x084a2501), (0xb859, 0x082267c4), (0xb86f, 0x14420416),
            (0xb878, 0x08402501), (0xb8cb, 0x0840041d), (0xbc36, 0x08400202),
            (0xa032, 0x0221e67c), (0xa025, 0x0221e67d), (0x92e8, 0x24e02122),
            (0x92f8, 0xc00201c1), (0xb840, 0x1420059b), (0xbbaa, 0x80000), (0xbbb1, 0x4000000))
    return all(read(p) == value for p, value in code)


def span(p, n):
    return 0xa00000 <= p and 0 < n <= 65536 and p+n <= 0x1000000


def binding(read, token, table):
    if not 0 <= table < 0x40000-15:
        raise ValueError('Exotica material table')
    base = read(table+(token >> 28))
    slot = base+(token & 0x3fff)
    if not span(base, (token & 0x3fff)+1):
        raise ValueError('Exotica material lookup span')
    return read(slot)


def transform(position, matrix):
    m = list(map(F.load, matrix))
    result = [dot(position, m[i:i+3]).reload() for i in (0, 3)]
    result.append((position[1]*m[7]+(position[2]*m[8]+position[0]*m[6])).reload())
    return result


def descriptor(definition, model, section, matrix, constants, trig, materials):
    """Reproduce final ordinary render fields at B8CB, before early activation."""
    d = definition
    if len(d) != 6 or len(model) != 6 or len(constants) != 11 or len(materials) != 2:
        raise ValueError('Exotica descriptor cardinality')
    if d[0] >> 24 or d[5] & 0xf00 in (0xa00, 0xf00):
        return None
    if not span(d[0], 6):
        raise ValueError('Exotica model address')
    flags, header = section['flags'], section['header']
    position = [F.integer(signed(w)) for w in d[1:4]]
    if flags & 1:
        position = [v-F.load(w) for v, w in zip(position, header[:3])]
    transformed = transform([v.reload() for v in position], matrix)
    position = [(v+F.load(w)).store() for v, w in zip(transformed, section['position'])]
    heading = F.load(d[4])+F.load(section['heading'])
    if flags & 1:
        heading = heading-F.load(header[3])+F.load(0x01491000)
    rotation = matrix if heading.value() == F.load(section['section_heading']).value() else yaw_matrix(heading, trig)
    obj = [0]*32
    obj[1:4], obj[5:14] = position, rotation
    obj[14], obj[15] = d[5] & 0xfff, model[5] | ((d[5] & 0xf000) << 4) | 0x30
    obj[16:20] = [2, d[0], *materials]
    obj[21], obj[22] = model[1], 0x077e0000 if ((d[5] & 0xf000) << 4) & constants[0] else heading.store()
    offset = (d[5] >> 26) & 63
    if flags & 1:
        offset = section['gap']-offset
    obj[29] = (offset+section['cursor']) & 0xffffffff
    if not section['initial'] and not obj[15] & 0x4900:
        obj[15] |= 0x100 | constants[7]
        obj[16] |= 0x78080000
    if d[5] & 0xf00 in (0xb00, 0xc00):
        for bit, index in ((8, 1), (16, 2), (32, 8), (64, 9), (128, 10)):
            if flags & bit:
                obj[15] |= constants[index]
        tag = d[5] & 255
        obj[24] = (255-tag if flags & 1 else tag) | (section['index'] << 8)
    return obj


def sections(read, partial=False):
    if not code_matches(read):
        raise ValueError('Exotica revision guard')
    entry, number, cursor = [read(p) for p in (0x597, 0x590, 0x598)]
    if not any((entry, number, cursor)):
        return dict(pretrack=True, partial=False, frontier=0, sections=[], sources=[])
    table = read(0xe9)+read(0x1fbc)
    if not span(table, 1):
        raise ValueError('Exotica track lookup')
    track = read(table)
    if not span(track, 3) or entry < track+3 or (entry-track-3) % 4:
        raise ValueError('Exotica section frontier')
    trig, constants = [read(0xe991+i) for i in range(7)], [read(0xbbaa+i) for i in range(11)]
    rows, sources = [], []
    position, heading, offset = [0x80000000]*3, 0x80000000, 0
    matched, ended = False, False
    for index in range(128):
        pointer = track+3+4*index
        if not span(pointer, 4):
            raise ValueError('Exotica section span')
        lists = [read(pointer+i) for i in range(4)]
        if lists == [0xffffffff]*4:
            ended = True
            if pointer == entry and not partial:
                matched = offset == cursor and number == index*256 and position == [read(0x599+i) for i in range(3)] and heading == read(0x59c)
            break
        if not span(lists[0]-4, 5):
            raise ValueError('Exotica section header')
        header = [read(lists[0]-4+i) for i in range(5)]
        angle = F.load(heading)
        if lists[3] & 1:
            angle = angle-F.load(header[3])+F.load(0x01491000)
        matrix = yaw_matrix(angle, trig)
        row = dict(entry=pointer, index=index, cursor=offset, position=position.copy(), heading=heading,
                   section_heading=angle.store(), matrix=matrix, header=header, gap=(header[4] >> 16) & 255,
                   flags=lists[3], initial=index < 2)
        rows.append(row)
        if pointer == entry:
            matched = offset == cursor and number == index*256 and position == [read(0x599+i) for i in range(3)] and heading == read(0x59c)
        for list_index, base in enumerate(lists[:3]):
            if not base:
                continue
            if not span(base, 1):
                raise ValueError('Exotica object list')
            count = ((read(base) & 65535) if list_index == 0 else read(base))+1
            if not 1 <= count <= 4096 or not span(base+1, 6*count) or len(sources)+count > 32768:
                raise ValueError('Exotica object budget')
            for ordinal in range(count):
                source = base+1+6*ordinal
                d = [read(source+i) for i in range(6)]
                supported = not (d[0] >> 24 or d[5] & 0xf00 in (0xa00, 0xf00))
                obj = [0]*32
                if supported:
                    if not span(d[0], 6):
                        raise ValueError('Exotica model span')
                    model = [read(d[0]+i) for i in range(6)]
                    material = model[2]
                    tex = binding(read, material & 0xf0003fff, read(0xe67c))
                    override = (d[5] >> 16) & 1023
                    bank = read(0xf5)
                    if bank > 15:
                        raise ValueError('Exotica palette bank')
                    token = override | (bank << 28) if override else (material & 0xf0000000) | ((material & 0x0fffc000) >> 14)
                    pal = binding(read, token, read(0xe67d))
                    context = dict(row, flags=row['flags'] & ~1) if list_index == 2 else row
                    obj = descriptor(d, model, context, matrix, constants, trig, (pal, tex))
                sources.append(dict(entry=pointer, source=source, index=index, ordinal=ordinal,
                                    supported=supported, future=pointer >= entry+4*bool(partial), words=obj))
        delta = list(map(F.load, header[:3]))
        if row['flags'] & 1:
            delta = [-v for v in delta]
        position = [(v+F.load(w)).store() for v, w in zip(transform(delta, matrix), position)]
        heading = (F.load(heading)-F.load(header[3]) if row['flags'] & 1 else F.load(header[3])+F.load(heading)).store()
        offset += row['gap']+1
    if not ended or not matched:
        raise ValueError('Exotica incomplete section boundary')
    return dict(pretrack=False, partial=bool(partial), frontier=entry, sections=rows, sources=sources)
