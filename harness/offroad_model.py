"""Independent Off Road 1.63 ordinary projection and six-word polygon oracle.

No ROM operands are shipped. Transform preparation, LOD choice and scene/material
lifetime are outside this captured-operand contract.
"""
from scenery_c31 import F, signed

PATHS = (0x1e03, 0x1e3b, 0x1e60)


def span(address, count):
    return 0xc00000 <= address and 0 <= count <= 8192 and address+count <= 0x1000000


def validate(r):
    nv, np = r['vertices'], r['polygons']
    if type(nv) is not int or type(np) is not int or not 1 <= nv <= 512 or not 1 <= np <= 1024:
        raise ValueError('invalid model counts')
    for key, size in [('matrix', 12), ('object_words', 22), ('lod_words', 5),
                      ('vertex_words', 3*nv), ('polygon_words', 6*np),
                      ('projected', 3*nv), ('palette_words', np)]:
        if len(r[key]) != size or any(type(x) is not int or not 0 <= x <= 0xffffffff for x in r[key]):
            raise ValueError('invalid model words: '+key)
    for key in ('origin_x', 'extra_flags', 'model', 'lod', 'object'):
        if type(r[key]) is not int or not 0 <= r[key] <= 0xffffffff:
            raise ValueError('invalid scalar: '+key)
    if r['path'] not in PATHS or r['object_words'][5] & 0x2008:
        raise ValueError('unsupported projection path')
    lod = r['lod_words']
    if (not span(r['model'], 7) or not span(r['lod'], 5) or
            r['lod'] < r['model']+7 or (r['lod']-r['model']-7) % 5 or
            lod[0]+1 != nv or lod[3]+1 != np or
            not span(lod[1], 3*nv) or not span(lod[4], 6*np)):
        raise ValueError('invalid ROM LOD descriptor')
    if r['object_words'][20] != r['model'] or not 0 <= r['object'] <= 0x20000-22:
        raise ValueError('invalid model owner')
    palette = {}
    for i in range(np):
        p = r['polygon_words'][6*i:6*i+6]
        offsets = (p[4] & 65535, p[4] >> 16, p[5] & 65535, p[5] >> 16)
        if any(x % 3 or x >= 3*nv for x in offsets):
            raise ValueError('polygon outside three-word vertex buffer')
        index = p[0] >> 16
        if index in palette and palette[index] != r['palette_words'][i]:
            raise ValueError('inconsistent palette binding')
        palette[index] = r['palette_words'][i]


def project(r, reciprocals):
    validate(r)
    if len(reciprocals) != 67776:
        raise ValueError('incomplete reciprocal table')
    matrix = list(map(F.load, r['matrix']))
    points = []
    for offset in range(0, len(r['vertex_words']), 3):
        v = list(map(F.load, r['vertex_words'][offset:offset+3]))
        x, y, z = [((v[0]*matrix[a]+matrix[a+3])+v[1]*matrix[a+1])+v[2]*matrix[a+2]
                   for a in (0, 4, 8)]
        index = z.fix()
        if r['path'] == 0x1e3b:
            index = max(-4096, index)
        if r['path'] == 0x1e60:
            index = min(63679, index)
        if not -4096 <= index <= 63679:
            raise ValueError('projection outside captured reciprocal table')
        reciprocal = F.load(reciprocals[index+4096])
        points.extend([(x.reload()*reciprocal+F.load(r['origin_x'])).fix() & 0xffffffff,
                       (F.integer(200)-y.reload()*reciprocal).fix() & 0xffffffff])
    return points


def quads(r, points):
    validate(r)
    if len(points) != 2*r['vertices']:
        raise ValueError('invalid projected XY count')
    output = []
    for i in range(r['polygons']):
        p = r['polygon_words'][6*i:6*i+6]
        indices = (p[4] & 65535, p[4] >> 16, p[5] & 65535, p[5] >> 16)
        xy = [signed(points[2*(j//3)+k]) for j in indices for k in (0, 1)]
        x0, y0, x1, y1, x2, y2 = xy[:6]
        if signed((x0-x1)*(y2-y1)-(y0-y1)*(x2-x1)) > 0:
            continue
        palette = (r['object_words'][18]+r['palette_words'][i]) & 65535
        output.append([(p[0] | r['extra_flags']) & 65535, palette, *[n & 65535 for n in xy],
                       p[1] & 65535, p[1] >> 16, p[2] & 65535, p[2] >> 16,
                       (p[3]+r['object_words'][19]) & 65535, 0])
    return output
