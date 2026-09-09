"""Independent USA two-word/interleaved model and C31 projection reference.

Raw model operands are local evidence. This is the original unclipped path,
including the game's reciprocal clamp and signed16 DMA wrap, not a host scene
admission rule. A matching projection does not establish material residency.
"""
from scenery_c31 import F, dot, signed


def prepare(record):
    """Reconstruct ordinary object-to-camera operands; reject alternate paths."""
    obj = record['object_words']
    if obj[14] & 0xa3:
        raise ValueError('unsupported alternate object transform')
    view = list(map(F.load, record['view']))
    local = list(map(F.load, obj))
    delta = [local[1+i]-F.load(record['camera'][i]) for i in range(3)]
    center = [dot(delta, view[i:i+3]).store() for i in (0, 3, 6)]
    if obj[14] & 8:
        matrix = record['billboard_compact' if record['compact'] else 'billboard_full']
    elif record['compact']:
        matrix = [(local[4+a]*view[b]+local[6+a]*view[6+b]).store()
                  for a, b in ((0, 0), (0, 2), (6, 0), (6, 2))]
    else:
        matrix = [dot([local[4+c], local[7+c], local[10+c]], view[i:i+3]).store()
                  for i in (0, 3, 6) for c in range(3)]
    return center, matrix


def validate(record):
    words = record['model_words']
    if len(words) < 2 or any(type(w) is not int or not 0 <= w <= 0xffffffff for w in words):
        raise ValueError('invalid model words')
    vertices, polygons = (words[1] & 255)+1, (words[1] >> 16)+1
    if polygons > 1024 or len(words) != 2+2*vertices+5*polygons:
        raise ValueError('invalid model counts/span')
    if record['vertices'] != vertices or record['polygons'] != polygons:
        raise ValueError('captured count mismatch')
    if record['compact'] not in (0, 1) or record['palette_kind'] not in (0, 1) or record['fast'] not in (0, 1):
        raise ValueError('invalid path selector')
    for name, size in [('matrix', 4 if record['compact'] else 9), ('camera_space', 3),
                       ('projected', 3*vertices), ('palette_words', polygons), ('object_words', 32)]:
        if len(record[name]) != size or any(type(w) is not int or not 0 <= w <= 0xffffffff for w in record[name]):
            raise ValueError('invalid '+name)
    if bool(record['object_words'][14] & 0x400) != bool(record['palette_kind']):
        raise ValueError('palette path disagrees with object flags')
    if record['palette_kind'] and any(w != record['object_words'][16] for w in record['palette_words']):
        raise ValueError('direct palette disagrees with object')
    if record.get('schema', 0) >= 2:
        for name, size in [('camera', 3), ('view', 9), ('billboard_full', 9), ('billboard_compact', 4)]:
            if len(record[name]) != size or any(type(w) is not int or not 0 <= w <= 0xffffffff for w in record[name]):
                raise ValueError('invalid '+name)
    for i in range(polygons):
        packed = words[3+2*vertices+5*i]
        if any(((packed >> shift) & 255) >= vertices for shift in (0, 8, 16, 24)):
            raise ValueError('polygon vertex outside model')
    return vertices, polygons


def project(record, reciprocals):
    vertices, _ = validate(record)
    if len(reciprocals) != 5080:
        raise ValueError('expected complete stock reciprocal table')
    matrix = list(map(F.load, record['matrix']))
    center = list(map(F.load, record['camera_space']))
    # Legacy v4 captured only the normal 200 origin. New probes capture the
    # actual operand and mark their schema. Do not silently infer new captures.
    if record.get('schema', 0) >= 1 and 'origin_y' not in record:
        raise ValueError('missing captured vertical origin')
    origin = F.load(record.get('origin_y', F.integer(200).store()))
    buffer = []
    for i in range(vertices):
        xy, z = record['model_words'][2+2*i:4+2*i]
        local = [F.integer(signed(xy, 16)), F.integer(signed(xy >> 16, 16)), F.integer(signed(z))]
        if record['compact']:
            x = (local[0]*matrix[0]+center[0])+local[2]*matrix[1]
            y = local[1]+center[1]
            z = (local[0]*matrix[2]+center[2])+local[2]*matrix[3]
        else:
            x, y, z = [dot(local, matrix[j:j+3]) for j in (0, 3, 6)]
            x = x.reload()+center[0]
            y, z = y+center[1], z+center[2]
        reciprocal = F.load(reciprocals[max(-80, min(4999, z.fix() >> 4))+80])
        buffer.extend([(x*reciprocal+F.integer(256)).store(),
                       ((y*reciprocal)*F.load(0x00052000)+origin).store(), z.store()])
    return buffer


def quads(record, buffer):
    vertices, polygons = validate(record)
    if len(buffer) != 3*vertices:
        raise ValueError('incomplete projected buffer')
    result = []
    for i in range(polygons):
        flags, packed, uv0, uv1, texture = record['model_words'][2+2*vertices+5*i:7+2*vertices+5*i]
        indices = [(packed >> shift) & 255 for shift in (0, 8, 16, 24)]
        points = [[F.load(buffer[3*j+k]) for k in (0, 1)] for j in indices]
        a, b, c = points[:3]
        cross = (b[1]-c[1])*(b[0]-a[0])-(b[0]-c[0])*(b[1]-a[1])
        if cross.value() > 0:
            continue
        palette = record['palette_words'][i]
        if not record['palette_kind']:
            palette = (palette >> 16) << 8
        result.append([v & 65535 for v in [flags, palette,
            *[p.fix() for point in points for p in point], uv0, uv0 >> 16, uv1, uv1 >> 16, texture, 0]])
    return result
