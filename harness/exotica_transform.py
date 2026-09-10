"""Independent Exotica 2.4 ordinary camera/rotation preparation.

World-coordinate mode0 and already-transformed mode3 are accepted. Rotation operands are supplied explicitly:
the special flag0x80 path reads object+0x8b, rather than object+5. Preparing its
transform does not certify its different model-emission path. Matrix reuse and
material state remain the caller's responsibility. No game data is distributed.
"""
from scenery_c31 import F


def words(values, size):
    if len(values) != size or any(type(x) is not int or not 0 <= x <= 0xffffffff for x in values):
        raise ValueError('invalid Exotica transform operands')
    return list(values)


def prepare(position, camera, view, rotation, alternate, flags):
    position, camera = words(position, 3), words(camera, 3)
    view, rotation, alternate = words(view, 9), words(rotation, 9), words(alternate, 9)
    if type(flags) is not int or not 0 <= flags <= 0xffffffff or flags & 3 not in (0, 3):
        raise ValueError('unsupported Exotica coordinate mode')
    delta = [F.load(a)-F.load(b) for a, b in zip(position, camera)]
    m = list(map(F.load, view))
    center = []
    # The first row consumes extended X; later rows reload the stored scratch X.
    # Z is stored/reloaded before all rows, while Y remains extended.
    if flags & 3 == 3:
        center = list(map(F.load, position))
    else:
        for row in range(3):
            x = delta[0] if row == 0 else delta[0].reload()
            center.append((delta[1]*m[row*3+1]+x*m[row*3])+delta[2].reload()*m[row*3+2])
    if flags & 0x80000:
        matrix = alternate
    elif flags & 2:
        matrix = rotation
    else:
        r = list(map(F.load, rotation))
        matrix = [((r[col]*m[row*3]+r[col+3]*m[row*3+1])+r[col+6]*m[row*3+2]).store()
                  for row in range(3) for col in range(3)]
    return {'matrix': matrix, 'translation': [x.store() for x in center], 'depth': center[2].fix()}


def packet(prepared, scale, update):
    matrix, translation = words(prepared['matrix'], 9), words(prepared['translation'], 3)
    words([scale], 1)
    if type(update) is not int or update not in (0, 1):
        raise ValueError('invalid matrix-update decision')
    f = F.load(scale)
    return ([0x07000000]+[(F.load(w)*f).store() for w in matrix] if update else [0x16000000]) + [
        (F.load(w)*f).store() for w in translation]


def select_model(descriptor, alternate, depth):
    words([descriptor, alternate], 2)
    if type(depth) is not int or not -(1 << 31) <= depth < 1 << 31:
        raise ValueError('invalid signed model depth')
    return alternate if alternate and depth > 25000 else descriptor


def matrix_update(flags, previous_alpha, alpha):
    words([flags,previous_alpha,alpha],3)
    previous,current=F.load(previous_alpha),F.load(alpha)
    update=int((previous-current).exponent!=-128 or not flags&0x10)
    if flags&0x80000 and (previous-F.integer(254)).exponent==-128:
        update=0
    return update
