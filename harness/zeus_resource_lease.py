"""Check sealed-to-ready Zeus resource bytes; raw operands remain local.

Texture coverage follows bounded positive-perspective UV extrema, with two texels
of padding and the shader's negative-coordinate clamp. Row-block spans are an
independent conservative subset of the native whole-rectangle page coverage.
This verifies sampled resource residency, not foreground occlusion or far range.
"""
import math
import struct

WAVE_BYTES = 16777216
PAGE_BYTES = 4096


def texture_pages(quads):
    if len(quads) % 260 or len(quads) > 131072*260:
        raise ValueError('lease polygon size')
    pages = set(); work = 0
    for start in range(0, len(quads), 260):
        s = struct.unpack_from('<17I', quads, start)
        nv, flags, width, kind = s[1], s[9], s[4], s[2] & 3
        if not 3 <= nv <= 8:
            raise ValueError('lease vertex count')
        if flags & (1 | 256):
            continue
        if width not in (16, 32, 64, 128, 256):
            raise ValueError('lease texture width')
        uv = []
        for i in range(nv):
            v = struct.unpack_from('<6f', quads, start+68+i*24)
            if not math.isfinite(v[5]) or v[5] <= 0:
                raise ValueError('lease perspective weight')
            pair = (v[3]/v[5]/256, v[4]/v[5]/256)
            if any(not math.isfinite(x) for x in pair):
                raise ValueError('lease texture coordinate')
            uv.append(pair)
        if any(abs(x) > 65536 for pair in uv for x in pair):
            return set(range(4096))
        lo = [max(0, math.floor(min(p[c] for p in uv))-2) for c in range(2)]
        hi = [max(1, math.ceil(max(p[c] for p in uv))+2) for c in range(2)]
        two = bool(flags & (64 | 128))
        period = 2 if two or kind == 1 else 4
        def address(x, y):
            if two:
                return 2*((y >> 1)*width*2+((x >> 1) << 2)+((y & 1) << 1)+(x & 1))
            if kind == 0:
                return (y >> 2)*width*4+((x >> 2) << 3)+((y & 3) << 1)+((x >> 1) & 1)
            if kind == 1:
                return (y >> 1)*width*2+((x >> 2) << 3)+((y & 1) << 2)+(x & 3)
            return (y >> 2)*width*4+((x >> 1) << 3)+((y & 3) << 1)+(x & 1)
        for row in range(lo[1]//period, hi[1]//period+1):
            first = address(lo[0], max(lo[1], row*period))
            last = address(hi[0], min(hi[1], row*period+period-1))+int(two)
            base = s[3]*8+first; size = last-first+1
            if size >= WAVE_BYTES:
                return set(range(4096))
            for page in range(base//PAGE_BYTES, (base+size-1)//PAGE_BYTES+1):
                pages.add(page % 4096)
                work += 1
                if work > 2000000:
                    raise ValueError('lease independent coverage budget')
    return pages


def verify(sealed, ready, instances, quads, mask, cpu):
    if (len(sealed) != WAVE_BYTES or len(ready) != WAVE_BYTES or len(instances) % 44 or
            len(mask) != 4096 or any(x not in (0, 1) for x in mask)):
        raise ValueError('lease resource snapshot size')
    pages = {i for i, bit in enumerate(mask) if bit}
    required = texture_pages(quads)
    if not required <= pages or len(pages) != int(cpu['texture_pages']):
        raise ValueError('lease texture coverage incomplete')
    for page in pages:
        start = page*PAGE_BYTES
        if sealed[start:start+PAGE_BYTES] != ready[start:start+PAGE_BYTES]:
            raise ValueError('lease texture bytes changed')
    model_bytes = 0; count = 0; models = set()
    for row in struct.iter_unpack('<11I', instances):
        base, words, palette = row[3], row[4], row[6]
        start = 8*((base & 1023)+((base >> 16) & 2047)*1024)
        size = 8*(words+1)
        if words > 0xc800 or start+size > WAVE_BYTES or palette*8+512 > WAVE_BYTES:
            raise ValueError('lease resource span')
        if sealed[start:start+size] != ready[start:start+size]:
            raise ValueError('lease model bytes changed')
        if sealed[palette*8:palette*8+512] != ready[palette*8:palette*8+512]:
            raise ValueError('lease palette bytes changed')
        key = (row[0], base, words)
        if key not in models:
            model_bytes += size; models.add(key)
        count += 1
    if (count != int(cpu['palette_checks']) or len(models) > int(cpu['model_checks']) or
            model_bytes > int(cpu['model_bytes'])):
        raise ValueError('lease resource counts')
    return dict(passed=True, rendered_instances=count, rendered_model_spans=len(models), rendered_model_bytes=model_bytes,
                palettes=count, checked_texture_pages=len(pages), required_texture_pages=len(required))
