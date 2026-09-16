"""Original bit4/four-vertex Off-Road billboard arithmetic; no future admission.

The separate current billboard basis is an input, not inferred from the view.
Persistent damage state, materials, clipping and ordered DMA are separate proof
obligations. This helper does not enable billboard drawing in the emulator.
"""
from scenery_c31 import F


def words(values, size):
    if len(values) != size or any(type(w) is not int or not 0 <= w < 2**32 for w in values):
        raise ValueError('billboard word extent')


def prepare(obj, view, basis):
    words(obj, 22); words(view, 12); words(basis, 12)
    if obj[5] & 6 != 4:
        raise ValueError('bit4 billboard without alternate bit2 required')
    m = list(map(F.load, view)); v = list(map(F.load, obj[11:14]))
    result = [0]*12
    for a in (0, 4, 8):
        result[a+3] = (((v[0]*m[a]+m[a+3])+v[1]*m[a+1])+v[2]*m[a+2]).store()
        result[a:a+3] = basis[a:a+3]
    return result


def project(vertices, matrix, origin, reciprocal):
    words(vertices, 12); words(matrix, 12); words([origin], 1)
    m = list(map(F.load, matrix)); result = []
    for offset in range(0, 12, 3):
        v = list(map(F.load, vertices[offset:offset+3]))
        x, y, z = [((v[0]*m[a]+m[a+3])+v[1]*m[a+1])+v[2]*m[a+2] for a in (0, 4, 8)]
        depth = z.fix()
        if not 0 <= depth <= 63679:
            raise ValueError('unclamped original billboard depth')
        word = reciprocal(depth); words([word], 1)
        r = F.load(word)
        result.extend([(x.reload()*r+F.load(origin)).fix() & 0xffffffff,
                       (F.integer(200)-y.reload()*r).fix() & 0xffffffff, depth])
    return result


def quad(obj, polygon, projected, palette_lookup, extra_flags):
    words(obj, 22); words(polygon, 6); words(projected, 12)
    words([palette_lookup, extra_flags], 2)
    if obj[5] & 6 != 4 or extra_flags not in (0, 0x2000):
        raise ValueError('billboard quad branch/flags')
    offsets = [polygon[4] & 65535, polygon[4] >> 16, polygon[5] & 65535, polygon[5] >> 16]
    if any(i % 3 or i >= 12 for i in offsets):
        raise ValueError('billboard polygon vertex offset')
    # The first billboard polygon enters1F94 directly, bypassing ordinary
    # backface rejection. Clipped variants need separate qualification.
    return [(polygon[0] | extra_flags) & 65535, (obj[18]+palette_lookup) & 65535,
            *[projected[i+k] & 65535 for i in offsets for k in (0, 1)],
            polygon[1] & 65535, polygon[1] >> 16, polygon[2] & 65535, polygon[2] >> 16,
            (polygon[3]+obj[19]) & 65535, 0]
