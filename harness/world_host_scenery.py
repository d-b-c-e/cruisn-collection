"""Read-only World model decoder and host projection reference.

This reconstructs data, not game execution. No object list, guest RAM or DMA is
modified. Initially restricted to World 2.4's main packed-model path; clipping and
alternate road/car paths must be reported separately, never silently accepted.
"""
from scenery_c31 import F, dot, signed


def model_counts(header):
    pairs = ((header >> 10) & 255) + 1 if header & 0x300 else 0
    singles = header & 255
    vertices = singles + 2*pairs
    polygons = (header >> 18) + 1
    if not 0 < vertices <= 256 or not 0 < polygons <= 1024:
        raise ValueError('unsupported packed model counts')
    return pairs, singles, polygons


def camera_center(object_words, camera, view):
    delta = [F.load(a)-F.load(b) for a, b in zip(object_words[1:4], camera)]
    matrix = list(map(F.load, view))
    return [dot(delta, matrix[i:i+3]).reload() for i in (0, 3, 6)]


def rotation_matrix(object_words, view):
    obj = list(map(F.load, object_words[4:13]))
    view = list(map(F.load, view))
    return [dot(obj[col::3], view[row:row+3]).reload()
            for row in (0, 3, 6) for col in range(3)]


def project(record, reciprocals, *, matrix=None, center=None):
    """Return C31 vertex-buffer words reconstructed from the packed model.

    The two-vertex encoding stores the second vertex as a positive offset along
    one model axis. Its operation/store order differs from two full transforms.
    """
    words = record['model_words']
    pairs, singles, _ = model_counts(words[2])
    matrix = matrix if matrix is not None else list(map(F.load, record['matrix']))
    center = center if center is not None else list(map(F.load, record['camera_space'][:3]))
    origin = list(map(F.load, record['camera_space'][3:5]))
    yscale = F.load(0x00052000)  # C31 short immediate 0x0052: 1.0400390625
    output = []

    def reciprocal(z):
        index = z.fix() >> 4
        if not record['fast']:
            index = max(-80, min(4999, index))
        if index not in reciprocals:
            raise ValueError(f'uncaptured reciprocal index {index}')
        return F.load(reciprocals[index])

    def screen(x, y, z):
        r = reciprocal(z)
        return [(x*r + origin[0]).store(), ((y*r)*yscale + origin[1]).store(), z.store()]

    axis = ((words[2] >> 8) & 3)-1
    for i in range(pairs+singles):
        xy, second = words[3+2*i:5+2*i]
        paired = i < pairs
        local = list(map(F.integer, (signed(xy, 16), signed(xy >> 16, 16),
                                    signed(second >> 16, 16) if paired else signed(second))))
        x, y, z = [dot(local, matrix[j:j+3]) for j in (0, 3, 6)]
        # X is stored before adding the camera center; Y stays in a register.
        x = x.reload()+center[0]
        y = y+center[1]
        z = z+center[2]
        output.extend(screen(x, y, z))
        if paired:
            offset = F.integer(second & 65535)
            x2 = offset*matrix[axis] + x.reload()
            y2 = offset*matrix[axis+3] + y.reload()
            z2 = offset*matrix[axis+6] + z.reload()
            output.extend(screen(x2, y2, z2))
    return output


def fast_quads(record, projected):
    """Generate the main unclipped path's DMA words, in original model order."""
    if record['end_pc'] != 0x242:
        raise ValueError('clipped polygon path requires separate reconstruction')
    words = record['model_words']
    pairs, singles, polygons = model_counts(words[2])
    start = 3+2*(pairs+singles)
    result = []
    for i in range(polygons):
        flags, packed = words[start+2*i:start+2*i+2]
        indices = [(packed >> shift) & 255 for shift in (0, 8, 16, 24)]
        if max(indices)*3+2 >= len(projected):
            raise ValueError('polygon indexes outside projected vertices')
        points = [[F.load(projected[3*j+k]) for k in (0, 1)] for j in indices]
        a, b, c = points[:3]
        cross = (b[1]-c[1])*(b[0]-a[0]) - (b[0]-c[0])*(b[1]-a[1])
        if cross.value() > 0:
            continue
        uv0, uv1, tex = record['material_words'][3*i:3*i+3]
        # STF of R6 after an LDF copies the original palette word exactly.
        dma = [flags, record['object_words'][16]]
        dma.extend(p.fix() for point in points for p in point)
        dma.extend([uv0, uv0 >> 16, uv1, uv1 >> 16, tex+record['object_words'][17]])
        result.append([n & 65535 for n in dma])
    return result
