"""Independent Off Road 1.63 transform/LOD arithmetic using captured ROM tables."""
from scenery_c31 import F, signed

CONSTANTS = [0x1ffff, 0x3fff, 0xef000040, 0xc23e97]


def validate(r, table):
    if r['trig_constants'] != CONSTANTS or len(table) != 16386:
        raise ValueError('unsupported Off Road trigonometry resources')
    for field, length in [('view', 12), ('object_words', 22), ('lod_context', 13)]:
        if len(r[field]) != length or any(type(n) is not int or not 0 <= n <= 0xffffffff for n in r[field]):
            raise ValueError('invalid Off Road transform field: '+field)


def trig(angle, table):
    if type(angle) is not int or not 0 <= angle <= 0xffffffff or len(table) != 16386:
        raise ValueError('invalid Off Road angle/table')
    t = lambda i: F.load(table[i+1])
    fraction = F.integer(angle & 0x1ffff)*F.load(0xef000040)
    shift = signed(angle << 1) >> 17
    i, j = abs(shift), 16383-abs(shift)
    sine, cosine = t(i), t(j)
    if not angle & 0x80000000:
        if shift >= 0:
            return (sine+(t(i+1)-sine)*fraction,
                    (cosine+(t(j-1)-cosine)*fraction).reload())
        return (sine+(t(i-1)-sine)*fraction,
                ((cosine-t(j+1))*fraction-cosine).reload())
    if shift >= 0:
        return ((sine-t(i+1))*fraction-sine,
                ((cosine-t(j-1))*fraction-cosine).reload())
    return ((sine-t(i-1))*fraction-sine,
            (cosine+(t(j+1)-cosine)*fraction).reload())


def prepare(r, table):
    validate(r, table)
    obj = r['object_words']
    flags = obj[5]
    if flags & 0x200e:
        raise ValueError('unsupported Off Road local/billboard transform')
    v = list(map(F.load, obj[11:14]))
    m = list(map(F.load, r['view']))
    out = [0]*12
    for a in (0, 4, 8):
        out[a+3] = (((v[0]*m[a]+m[a+3])+v[1]*m[a+1])+v[2]*m[a+2]).store()
    if flags & 1:
        for a in (0, 1, 2, 4, 5, 6, 8, 9, 10):
            out[a] = r['view'][a]
        return out
    if flags & 0x10:
        sine, cosine = trig(obj[15], table)
        for a in (0, 4, 8):
            out[a] = ((-sine)*m[a+2]+cosine*m[a]).store()
            out[a+1] = r['view'][a+1]
            out[a+2] = (sine*m[a]+(cosine*m[a+2]).reload()).store()
        return out
    sx, cx = trig(obj[14], table)
    sy, cy = trig(obj[15], table)
    sz, cz = trig(obj[16], table)
    a = (cy*sx)*sz-cz*sy
    b = (sy*sx).reload()
    c = cy*cz+(sy*sx)*sz
    d = (cy*sz-cz*b).reload()
    e = (cy*sx)*cz+sy*sz
    for row in (0, 4, 8):
        out[row] = ((m[row]*c-(cx*m[row+1])*sz)+m[row+2]*a).store()
        out[row+1] = ((m[row]*d+(cx*m[row+1])*cz)-m[row+2]*e).store()
        out[row+2] = (((m[row]*sy)*cx+m[row+1]*sx)+(m[row+2]*cy)*cx).store()
    return out


def select_lod(r):
    obj = r['object_words']
    flags = obj[5]
    current, mode, primary, behind, ahead, upper, lower, *thresholds = r['lod_context']
    if not flags & 0x20 or mode != primary:
        return 0, None
    delta = signed(obj[8]-current)
    adjustment = 0
    if delta > signed(upper):
        adjustment = ahead
    if delta <= signed(lower):
        adjustment = behind
    relative = signed(delta+adjustment)
    pair = 4 if flags & 0x2000 else 2 if flags & 0x80 else 0
    index = int(relative >= signed(thresholds[pair]))
    if index and flags & 0x2040 and relative >= signed(thresholds[pair+1]):
        index = 2
    return index, relative
