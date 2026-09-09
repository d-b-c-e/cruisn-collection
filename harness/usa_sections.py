"""Independent USA section placement and ordinary final render fields.

Uses the shared C31 polynomial only after USA's constants and instruction order
were checked. USA's headers, palette binding, flags and field offsets differ
from World. Custom allocation handlers remain explicitly unsupported.
"""
from scenery_c31 import F, dot, signed
from verify_world_sections import yaw_matrix


def rom_span(p, n):
    return type(p) is int and 0xc00000 <= p and 0 <= n <= 65536 and p+n <= 0x1000000


def section_definitions(read, p):
    """USA's variable header, optional lists, and third-list heading override."""
    if not rom_span(p, 12):
        raise ValueError('USA section outside ROM')
    section = [read(p+i) for i in range(12)]
    flags = section[0]
    if flags == 0xffffffff:
        return [], p
    size = 6+int(bool(flags & 1))+(4 if flags & 8 else 0)+int(bool(flags & 0x1000))
    slots = [(0, 5)] + ([(1, 6)] if flags & 1 else []) + ([(2, size-1)] if flags & 0x1000 else [])
    rows = []
    for stage, slot in slots:
        block = section[slot]
        if not rom_span(block, 2):
            raise ValueError('USA list outside ROM')
        count = read(block+1)
        if not 0 < count <= 4096 or not rom_span(block+2, 6*count):
            raise ValueError('unsupported USA section list length')
        heading = section[9+int(bool(flags & 1))] if stage == 2 and flags & 8 else section[4]
        for index in range(count):
            source = block+2+6*index
            rows.append(dict(section_pointer=p, section_words=section, source=source, stage=stage,
                             heading=heading, section_flags=flags & ~8 if stage == 2 else flags,
                             definition=[read(source+i) for i in range(6)]))
    return rows, p+size


def material_operands(read, model):
    if not rom_span(model-1, 3):
        raise ValueError('USA model prefix outside ROM')
    prefix = read(model-1)
    table = read(0x9ea9)
    address = table+(prefix & 0xfff)
    if not 0 <= table <= address < 0x20000:
        raise ValueError('USA palette binding outside RAM')
    return dict(model_prefix=prefix, palette_base=table, palette_binding=read(address))


def palette_ownership(read, index):
    """9F25's mapping and reverse owner table; queued upload is a separate guard."""
    if not 0 <= index < 4096:
        raise ValueError('invalid USA palette index')
    table, owners = read(0x9ea9), read(0x9ea8)
    if not 0 <= table <= table+index < 0x20000 or not 0 <= owners <= owners+127 < 0x20000:
        raise ValueError('USA palette ownership table outside RAM')
    binding = read(table+index)
    if not binding:
        return None
    slot = binding >> 16
    if slot >= 128 or binding & 65535 == 0 or read(owners+slot) != (0x8000 | index):
        raise ValueError('USA palette mapping disagrees with current slot owner')
    return slot


def future(read, sections=64):
    """Bounded next-section enumeration; current partial section is excluded.

    USA advances E4A5 before allocating the current list. E49D catches up after
    allocation completes. Validate their relationship and section number before
    using E4A5. This deliberately does not guess an in-flight AR5 cursor.
    """
    if not 1 <= sections <= 128:
        raise ValueError('bounded USA section count required')
    start, loading, number = read(0xe4a5), read(0xe49d), read(0xe4a4)
    track = read(0xa12e)
    result = dict(start=start, loading=loading, number=number, partial=False, definitions=[], stop=None)
    if start == loading == 0:
        result['stop'] = 'track not initialized'
        return result
    if not rom_span(start, 1) or not rom_span(loading, 1) or not rom_span(track, 1) or not 0 <= number <= 4096:
        raise ValueError('invalid USA loader frontier')
    p, previous = track, None
    for _ in range(number):
        if not rom_span(p, 1) or read(p) == 0xffffffff:
            raise ValueError('USA section number crosses track end')
        flags = read(p)
        previous, p = p, p+6+int(bool(flags & 1))+(4 if flags & 8 else 0)+int(bool(flags & 0x1000))
    if p != start or (loading != start and loading != previous):
        raise ValueError('USA section number/cursor mismatch')
    result['partial'] = loading != start
    for relative in range(sections):
        if not rom_span(p, 1):
            raise ValueError('USA upcoming section outside ROM')
        if read(p) == 0xffffffff:
            result['stop'] = 'end marker'
            break
        rows, following = section_definitions(read, p)
        for row in rows:
            row['section_number'] = number+relative+1
            row['relative_section'] = relative
            result['definitions'].append(row)
        p = following
    return result


def placement(row):
    definition, section = row['definition'], row['section_words']
    if len(definition) != 6 or len(section) != 12 or len(row['trig_constants']) != 7:
        raise ValueError('incomplete USA section operands')
    heading = F.load(row['heading'])
    position = [F.integer(signed(v)).reload() for v in definition[1:4]]
    if row['section_flags'] & 8:
        offset = 6 + int(bool(section[0] & 1))
        position = [(v + F.load(section[offset+i])).reload() for i, v in enumerate(position)]
    matrix = list(map(F.load, yaw_matrix(heading, row['trig_constants'])))
    rotated = [dot(position, matrix[i:i+3]).reload() for i in (0, 3)]
    rotated.append((position[1]*matrix[7] + (position[2]*matrix[8] + position[0]*matrix[6])).reload())
    xyz = [(v + F.load(t)).store() for v, t in zip(rotated, section[1:4])]
    angle = F.load(definition[4]) + heading
    return xyz, angle.store(), yaw_matrix(angle, row['trig_constants'])


def base_flags(prefix, metadata):
    return (((metadata >> 16) & 0x3b) | (0x400 if prefix & 0x2000 else 0)
            | (0x40 if prefix & 0x1000 else 0) | ((1 << 26) if metadata & 0x1000 else 0))


def final_flags(prefix, metadata):
    return base_flags(prefix, metadata) | {3: 1 << 28, 9: 1 << 21, 6: 1 << 31,
                                          11: 1 << 28}.get((metadata >> 8) & 15, 0)


def check_record(row):
    metadata = row['definition'][5]
    if metadata & 0x2000:
        return None
    xyz, angle, matrix = placement(row)
    ready, actual = row['ready'], row['actual']
    if len(ready) != 34 or len(actual) != 34 or len(row['camera']) != 3 or len(row['view']) != 9:
        raise ValueError('incomplete USA ready/final descriptor or camera')
    if row['final_pc'] not in (0x7052, 0x414f):
        raise ValueError('unknown final allocation boundary')
    delta = [F.load(p)-F.load(c) for p, c in zip(xyz, row['camera'])]
    depth = dot(delta, list(map(F.load, row['view'][6:9]))).fix()
    membership = 0x1000 if -5000 <= depth < 80000 else 0x2000
    prefix = row['model_prefix']
    result = dict(position=ready[1:4] == actual[1:4] == xyz,
                  heading=ready[21] == actual[21] == angle,
                  matrix=ready[4:13] == actual[4:13] == matrix,
                  section_matrix=yaw_matrix(F.load(row['heading']), row['trig_constants']) == row['matrix'],
                  ready_flags=ready[14] == (base_flags(prefix, metadata) | membership),
                  final_flags=actual[14] == (final_flags(prefix, metadata) | membership),
                  depth=signed(ready[28]) == signed(actual[28]) == depth,
                  model=ready[13] == actual[13] == row['definition'][0],
                  ready_kind=ready[15] == (metadata & 0xfff),
                  section_tag=ready[31] == actual[31] and ready[31] & 255 == 0xaa)
    kind = (metadata >> 8) & 15
    result['final_kind'] = actual[15] == (0x300 if kind == 11 else metadata & 0xfff)
    if kind == 11:
        ordinal = metadata & 255
        if row['section_flags'] & 8:
            ordinal = 255-ordinal
        result['road_tag'] = actual[30] == ((ready[31] & ~255) | ordinal)
    if prefix & 0x2000:
        result['palette'] = (row['palette_binding'] != 0 and
            ready[16] == actual[16] == ((row['palette_binding'] >> 16) << 8))
    return result
