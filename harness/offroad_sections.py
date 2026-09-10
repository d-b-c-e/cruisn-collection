"""Independent bounded Off Road 1.63 static section reference (no guest writes).

Only ordinary default-binding descriptors are qualified. This does not establish
material residency, GPU visibility, clipping or complete dynamic-object coverage.
"""
EXCLUDED = 0x3f800000
FIELDS = (5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)


def span(p, n):
    return 0xc00000 <= p and 0 < n <= 65536 and p+n <= 0x1000000


def frontier(read):
    base, count = read(0x1b4b4), read(0x1b4cc)
    pointers = [read(a) for a in (0x1b4b5, 0x1b4b7, 0x1b4ba)]
    if not any([base, count, *pointers]):
        return dict(track=0, count=0, current=0, front=0, back=0, pretrack=True, partial=False)
    if not 1 <= count <= 128 or not span(base, 4*count) or read(0x1b4bd) != 1:
        raise ValueError('Off Road track/mode guard')
    table = [[read(base+4*i+j) for j in range(4)] for i in range(count)]
    if any(row[1] != i or bool(row[0] & 1) != (i == 0) or
           bool(row[0] & 0x80000000) != (i == count-1) for i, row in enumerate(table)):
        raise ValueError('Off Road section order/end markers')
    if any(not base <= p < base+4*count or (p-base) % 4 for p in pointers):
        raise ValueError('Off Road frontier pointer')
    current, front, back = [(p-base)//4 for p in pointers]
    numbers = [read(a) for a in (0x1b4b6, 0x1b4b8, 0x1b4bb)]
    lead = read(0x1b4b9)
    # The one-scene counter delay also occurs with front at the final section.
    # Excluding a following section there naturally leaves an empty future range.
    partial = lead == front-current+1
    if (not back <= current <= front or numbers != [current, front, back] or
            not (partial or lead == front-current) or read(0x1b4bc) != current-back):
        raise ValueError('Off Road incomplete loader frontier')
    return dict(track=base, count=count, current=current, front=front, back=back, pretrack=False, partial=partial)


def descriptor(definition, number, ordinal, count, binding):
    if len(definition) != 11 or len(binding) != 3 or not 1 <= count <= 256 or not 0 <= ordinal < count or not 0 <= number <= 255:
        raise ValueError('Off Road section descriptor cardinality')
    if any(not isinstance(v, int) or not 0 <= v <= 0xffffffff for v in [*definition, *binding]):
        raise ValueError('Off Road descriptor word')
    if definition[0] & EXCLUDED:
        return None
    if not span(definition[1], 7) or not span(binding[0], 1) or binding[1] > 0x7fff or binding[2] > 0xffff:
        raise ValueError('Off Road model/material address')
    obj = [0]*22
    obj[5:9] = [definition[0], (count-1-ordinal)*0x1000000+number*0x10000+0x8000,
                definition[3], definition[2]]
    obj[11:17] = definition[5:11]
    obj[17:21] = [*binding, definition[1]]
    return obj


def sections(read, loaded=False):
    f = frontier(read)
    rows = []
    if not f['pretrack']:
        binding = [read(a) for a in (0x1b4cd, 0x1b4cf, 0x1b4ce)]
        interval = range(f['back'], f['front']+1) if loaded else range(f['front']+1+int(f['partial']), f['count'])
        for number in interval:
            entry = f['track']+number*4
            data = read(entry+3)
            if not span(data, 17):
                raise ValueError('Off Road section data')
            count = read(data+16)
            if not 1 <= count <= 256 or not span(data+17, count*11) or len(rows)+count > 32768:
                raise ValueError('Off Road section budget')
            for ordinal in range(count):
                source = data+17+ordinal*11
                words = [read(source+i) for i in range(11)]
                obj = descriptor(words, number, ordinal, count, binding)
                rows.append(dict(entry=entry, source=source, number=number, ordinal=ordinal,
                                 flags=words[0], supported=obj is not None,
                                 words=obj or [0]*22, definition=words))
    return dict(frontier=f, sources=rows)
