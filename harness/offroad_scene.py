"""Independent ordinary Off Road host projection; standalone, no GPU acceptance."""
from collections import Counter
import struct

from scenery_c31 import F, signed
from offroad_sections import frontier, sections, span
from offroad_transform import prepare, select_lod, CONSTANTS
from offroad_model import quads


def position_and_order(obj, view, scale):
    v, m = list(map(F.load, obj[11:14])), list(map(F.load, view))
    p = [((v[0]*m[a]+m[a+3])+v[1]*m[a+1])+v[2]*m[a+2] for a in (0, 4, 8)]
    x, y, z = p[0].reload()*scale, p[1].reload()*scale, p[2]*scale
    score = ((x*x+z*z)+y*y)*F.integer(-1 if p[2].value() < 0 else 1)
    return p, score.fix()


def reciprocal(read, index):
    if index <= 63679:
        return read(0xcb0fc8+index)
    quotient, remainder = divmod(50400000000, index+1)
    if remainder*2 > index+1 or remainder*2 == index+1 and quotient % 2:
        quotient += 1
    ieee = struct.unpack('<I', struct.pack('<f', quotient/100000000))[0]
    return ((((ieee >> 23)-127) & 255) << 24) | (ieee & 0x7fffff)


def host_project(vertices, matrix, origin, read, multiplier):
    m = list(map(F.load, matrix)); points = []
    for i in range(0, len(vertices), 3):
        v = list(map(F.load, vertices[i:i+3]))
        x, y, z = [((v[0]*m[a]+m[a+3])+v[1]*m[a+1])+v[2]*m[a+2] for a in (0, 4, 8)]
        depth = z.fix()
        if not 503 <= depth < 63680*multiplier:
            return None
        r = F.load(reciprocal(read, depth))
        xy = [(x.reload()*r+F.load(origin)).fix(), (F.integer(200)-y.reload()*r).fix()]
        if any(not -32768 <= v <= 32767 for v in xy):
            return None
        points.extend(v & 0xffffffff for v in xy)
    return points


def scene(read, multiplier, use_future):
    if multiplier not in (1, 2, 3):
        raise ValueError('host multiplier')
    f = frontier(read)
    counts = Counter(dict(pending=0, future=0, unsupported=0, near=0, far=0,
                          projection=0, material=0, pretrack=int(f['pretrack']), partial=int(f['partial']), deferred=0))
    if f['pretrack']:
        return counts, []
    count, head, tail, busy = [read(p) for p in (0x11145, 0x11143, 0x11144, 0x19e20)]
    if (read(0x11141) != 0x9e0000 or read(0x11142) != 0x10390 or read(0x19e29) != 0xa00000 or
            not 0 <= count <= 32 or not 0 <= head < 32 or not 0 <= tail < 32 or
            (head+count) % 32 != tail or busy not in (0, 1)):
        raise ValueError('material upload state')
    pend, tend = read(0x19e21)*256, read(0x19e23)*256
    if not 0 <= pend <= 32768 or not 0 <= tend <= 4194304:
        raise ValueError('material allocation bounds')
    if count or busy:
        counts['deferred'] = 1
        return counts, []
    view = [read(read(0x1120b)+i) for i in range(12)]
    context = [read(p) for p in (0x19731, 0x1b4bd, 0x1d0af, 0x1b4c1, 0x1b4c2, 0x1b4c3, 0x1b4c4,
                                0x1122a, 0x1122b, 0x1122c, 0x1122d, 0x1122e, 0x1122f)]
    pool = read(0x111ee); candidates = []; seen = set(); p = read(0x1b73e)
    if read(0x111f5) != 0x1b73e or read(0x111a7) != 0xcb0fc8 or read(0x1117b) != 0xc23e97:
        raise ValueError('scene constants')
    while p:
        if p in seen or not pool <= p < pool+1200*22 or (p-pool) % 22:
            raise ValueError('pending list owner/cycle')
        seen.add(p); obj = [read(p+i) for i in range(22)]; candidates.append((p, obj)); p = obj[0]
        counts['pending'] += 1
    if use_future:
        for source in sections(read)['sources']:
            if not source['supported']:
                counts['unsupported'] += 1
                continue
            candidates.append((0x80000000 | source['source'], source['words']))
            counts['future'] += 1
    trig = [read(0xc23e97+i) for i in range(-1, 16385)]
    output = []
    for owner, obj in candidates:
        if obj[5] & 0x200e:
            counts['unsupported'] += 1
            continue
        if not span(obj[20], 7) or not span(obj[17], 1):
            raise ValueError('model/palette address')
        pos, order = position_and_order(obj, view, F.load(read(0x11238)))
        nearest = pos[2]-F.load(read(obj[20]))
        if nearest.value() < 1000:
            counts['near'] += 1
            continue
        if nearest.value() >= 47296*multiplier:
            counts['far'] += 1
            continue
        r = dict(object_words=obj, view=view, lod_context=context, trig_constants=CONSTANTS)
        matrix = prepare(r, trig); lod, _ = select_lod(r); d = obj[20]+7+5*lod
        dw = [read(d+i) for i in range(5)]; nv, np = dw[0]+1, dw[3]+1
        if not 0 < nv <= 512 or not 0 < np <= 1024 or not span(dw[1], 3*nv) or not span(dw[4], 6*np):
            raise ValueError('host model counts')
        vertices = [read(dw[1]+i) for i in range(3*nv)]
        polygons = [read(dw[4]+i) for i in range(6*np)]
        points = host_project(vertices, matrix, read(0x11230), read, multiplier)
        if points is None:
            counts['projection'] += 1
            continue
        palettes = [read(obj[17]+(polygons[6*i] >> 16)) for i in range(np)]
        r.update(matrix=matrix, model=obj[20], lod=d, lod_words=dw, vertices=nv, polygons=np,
                 object=0 if owner & 0x80000000 else owner, vertex_words=vertices, polygon_words=polygons,
                 palette_words=palettes, projected=[0]*(3*nv), origin_x=read(0x11230), path=0x1e03,
                 extra_flags=0x2000 if obj[5] & read(0x11249) else 0)
        qs = quads(r, points)
        bound = True
        for q in qs:
            if q[0] & 0x300 != 0x100:
                bound &= q[1]+(q[0] & 255) < pend
            else:
                u, v = max(x & 255 for x in q[10:14]), max(x >> 8 for x in q[10:14])
                bound &= q[1]+255 < pend and q[14]*256+min(v+1, 255)*256+min(u+1, 255) < tend
        if not bound:
            counts['material'] += 1
            continue
        output.append(dict(id=owner, model=obj[20], lod=lod, depth=pos[2].reload().fix(), order=order, quads=qs))
    output.sort(key=lambda o: (-o['order'], o['id']))
    return counts, output
