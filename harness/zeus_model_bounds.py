"""Independent conservative float32 bounds from actual Zeus model vertices.

Bounds do not establish material ownership or replace model validation. An
uncertain near-plane crossing is kept for the original polygon projector.
"""
import math
import struct
import numpy as np
from scenery_c31 import signed

F = np.float32


def down(x):
    return F(np.nextafter(F(x), F(-math.inf)))


def up(x):
    return F(np.nextafter(F(x), F(math.inf)))


def add(a, b):
    return down(F(a[0]+b[0])), up(F(a[1]+b[1]))


def multiply(a, b):
    products = [F(x*y) for x in a for y in b]
    return down(min(products)), up(max(products))


def divide(a, b):
    assert b[0] > 0
    quotients = [F(x/y) for x in a for y in b]
    return down(min(quotients)), up(max(quotients))


def finite(interval):
    return all(math.isfinite(v) for v in interval) and interval[0] <= interval[1]


def float_word(word):
    return F(struct.unpack('<f', struct.pack('<I', word))[0])


def model_bounds(words, quad_size):
    if quad_size not in (10, 12, 14) or len(words) % 2 or len(words) > 2*(0xc800+1):
        raise ValueError('model bound input budget')
    if any(type(w) is not int or not 0 <= w <= 0xffffffff for w in words):
        raise ValueError('model bound word')
    low = high = None
    index = 0
    while index < len(words):
        op = words[index] >> 24
        size = quad_size if op == 0x38 else 2
        if size > len(words)-index:
            raise ValueError('model bound truncated command')
        d = words[index:index+size];index += size
        if op in (0, 0x22):
            continue
        if op == 0x36:
            if (d[0] >> 16) & 127 != 0x20 or d[1] >> 24 >= 80 or d[1] >> 24 == 8:
                raise ValueError('model bound unsupported state')
            continue
        if op != 0x38:
            raise ValueError('model bound unsupported command')
        vertices = [[signed(d[2], 16), signed(d[3], 16), signed(d[6], 16)],
                    [signed(d[2] >> 16, 16), signed(d[3] >> 16, 16), signed(d[6] >> 16, 16)],
                    [signed(d[8], 16), signed(d[9], 16), signed(d[7], 16)],
                    [signed(d[8] >> 16, 16), signed(d[9] >> 16, 16), signed(d[7] >> 16, 16)]]
        for vertex in vertices:
            if low is None:
                low, high = vertex.copy(), vertex.copy()
            else:
                low = [min(a, b) for a, b in zip(low, vertex)]
                high = [max(a, b) for a, b in zip(high, vertex)]
    return None if low is None else list(zip(low, high))


def outside(bounds, context, margin):
    regs = context['regs'];matrix = context['matrix'];translation = context['translation'][:3]
    exponent = regs[0x66]-0x8e
    if (not math.isfinite(margin) or not 0 <= margin <= 256 or
            not -31 <= exponent <= 31 or not 0 <= regs[0x6c] <= 30):
        return False
    clip, ox, oy = (float_word(regs[i]) for i in (0x78, 0x6a, 0x6b))
    if not all(math.isfinite(v) for v in [clip, ox, oy, *matrix, *translation]):
        return False
    if bounds is None:
        return True
    scale = F(2.**exponent)
    local = [(F(a*scale), F(b*scale)) for a, b in bounds]
    if not all(finite(r) for r in local):
        return False
    transformed = []
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        for row in range(3):
            terms = [multiply(local[j], (F(matrix[row*3+j]),)*2) for j in range(3)]
            transformed.append(add(add(add(terms[0], terms[1]), terms[2]), (F(translation[row]),)*2))
        if not all(finite(r) for r in transformed):
            return False
        if transformed[2][1] < clip:
            return True
        if transformed[2][0] < max(clip, F(0)):
            return False
        denominator = add(transformed[2], (F(2), F(2)))
        if not finite(denominator) or denominator[0] <= 0:
            return False
        factor = divide((F(1 << regs[0x6c]),)*2, denominator)
        x = add(multiply(transformed[0], factor), (ox, ox))
        y = add(multiply(transformed[1], factor), (oy, oy))
        if not all(finite(r) for r in (factor, x, y)):
            return False
        return bool(x[1] < -margin or x[0] > 512+margin or y[1] < 0 or y[0] > 400)
