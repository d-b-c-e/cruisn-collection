"""Independent HMT1/private-GPU receipt verification. Raw game bytes stay local."""
import csv
import hashlib
import math
from pathlib import Path
import re
import struct
from page_image import HEADER, MASK, page_hash

SIZE, PAGE, MAX_ROWS = 16777216, 4096, 4096
MAX_PACKET = 32 + 64 + 4096 * 4100 + MAX_ROWS * 1032


def parse(wire):
    if not 32 <= len(wire) <= MAX_PACKET:
        raise ValueError('material packet length')
    magic, frame, scene, wave_size, rows, snapshot, reserved = struct.unpack_from('<IIQ4I', wire)
    if (magic != 0x31544d48 or not 1800 <= frame <= 16001 or not scene or reserved
            or snapshot not in (0, 1) or rows > MAX_ROWS or
            len(wire) != 32 + wave_size + rows * 1032 or wave_size < HEADER.size):
        raise ValueError('material packet header')
    pim = wire[32:32 + wave_size]
    tag, size, page, count, base, generation, old_hash, new_hash, full, *pad = HEADER.unpack_from(pim)
    if (tag != 0x314d4950 or size != SIZE or page != PAGE or count > 4096 or any(pad)
            or len(pim) != 64 + count * 4100 or base == MASK or generation != base + 1
            or full not in (0, 1) or bool(full) != (base == 0) or (full and (count != 4096 or old_hash))):
        raise ValueError('material page header')
    pages = []
    for i in range(count):
        offset = 64 + i * 4100
        index, = struct.unpack_from('<I', pim, offset)
        if index >= 4096 or (pages and index <= pages[-1][0]):
            raise ValueError('material page order')
        pages.append((index, pim[offset + 4:offset + 4100]))
    palettes = []
    for i in range(rows):
        offset = 32 + wave_size + i * 1032
        base_address, control = struct.unpack_from('<II', wire, offset)
        if control != 0x0084003f or base_address * 8 + 512 > SIZE:
            raise ValueError('private palette layout')
        palettes.append((base_address, control, wire[offset + 8:offset + 1032]))
    return dict(frame=frame, scene=scene, generation=generation, base_hash=old_hash,
                hash=new_hash, snapshot=bool(snapshot), pages=pages, palettes=palettes)


def palette_bytes(wave, base):
    words = struct.unpack_from('<256H', wave, base * 8)
    return struct.pack('<256I', *[(((c >> 10) & 31) << 19) | (((c >> 5) & 31) << 11) | ((c & 31) << 3) for c in words])


def snapshot(directory, frame):
    prefix = Path(directory) / f'exotica-host-{frame}'
    read = lambda suffix: Path(str(prefix) + suffix).read_bytes()
    wire, wave, gpu_wave = read('-materials.bin'), read('-wave.bin'), read('-gpu-wave.bin')
    p = parse(wire)
    if p['frame'] != frame or not p['snapshot'] or len(wave) != SIZE or gpu_wave != wave:
        raise ValueError('private GPU snapshot differs from device WaveRAM')
    root = 0
    for offset in range(0, SIZE, PAGE):
        root ^= page_hash(offset // PAGE, wave[offset:offset + PAGE])
    if root != p['hash'] or any(data != wave[index*PAGE:(index+1)*PAGE] for index, data in p['pages']):
        raise ValueError('private page integrity differs from device WaveRAM')
    instances = read('-instances.bin')
    if len(instances) % 44 or len(instances) > MAX_ROWS * 44:
        raise ValueError('material instance size')
    expected = []
    for values in struct.iter_unpack('<11I', instances):
        key = (values[6], values[7])
        if key not in expected:
            expected.append(key)
    if [(base, control) for base, control, colors in p['palettes']] != expected:
        raise ValueError('private palette ownership differs from scene instances')
    for base, control, colors in p['palettes']:
        if colors != palette_bytes(wave, base):
            raise ValueError('private colors differ from current WaveRAM')
    colors = b''.join(row[2] for row in p['palettes'])
    if read('-gpu-palettes.bin') != colors:
        raise ValueError('private GPU colors differ from owned palette rows')
    return dict(frame=frame, scene=p['scene'], generation=p['generation'], pages=len(p['pages']),
                palettes=len(p['palettes']), root=f'{root:016x}',
                wave_sha256=hashlib.sha256(wave).hexdigest(),
                palette_sha256=hashlib.sha256(colors).hexdigest(),
                packet_sha256=hashlib.sha256(wire).hexdigest())


def verify_live(directory, scenes, captures, text):
    def rows(name):
        path = Path(directory) / name
        if path.stat().st_size > 8*1024*1024:
            raise ValueError('material log budget')
        with path.open(encoding='utf-8', newline='') as stream:
            return list(csv.DictReader(stream))
    producer, gpu = rows('exotica-host-materials.csv'), rows('exotica-host-materials-gpu.csv')
    if not producer or len(producer) != len(scenes) or len(gpu) != len(producer):
        raise ValueError('material queue did not drain every scene')
    previous = 0
    for i, (source, sent, received) in enumerate(zip(scenes, producer, gpu)):
        fields = ('scene', 'frame', 'generation', 'pages', 'palettes', 'bytes', 'hash')
        if any(sent[k] != received[k] for k in fields):
            raise ValueError('material producer/consumer receipt differs')
        if (sent['scene'] != source['scene'] or sent['frame'] != source['frame'] or
                int(sent['scene']) <= previous or int(sent['generation']) != i+1 or
                not 0 <= int(sent['pages']) <= 4096 or not 0 <= int(sent['palettes']) <= MAX_ROWS or
                int(sent['bytes']) != 32 + 64 + int(sent['pages'])*4100 + int(sent['palettes'])*1032 or
                not re.fullmatch('[0-9a-f]{16}', sent['hash'])):
            raise ValueError('material frame/generation/budget contract')
        for row in (sent, received):
            for key, value in row.items():
                if key.endswith('_us') and (not math.isfinite(float(value)) or float(value) < 0):
                    raise ValueError('invalid material timing')
        previous = int(sent['scene'])
    end = re.findall(r'^MIDZ_HOST_MATERIALS_RESULT queued=(\d+) hash=([0-9a-f]{16})$', text, re.M)
    gpu_end = re.findall(r'^MIDZ_HOST_MATERIALS_GPU_RESULT complete=(\d+) received=(\d+) snapshots=(\d+) hash=([0-9a-f]{16})$', text, re.M)
    expected = (str(len(producer)), producer[-1]['hash'])
    if end != [expected] or gpu_end != [('1', expected[0], str(len(captures)), expected[1])]:
        raise ValueError('material final generation or capture acknowledgment')
    sampled = [snapshot(directory, frame) for frame in captures]
    by_generation = {int(r['generation']): r for r in producer}
    for row in sampled:
        sent = by_generation.get(row['generation'])
        if not sent or sent['hash'] != row['root'] or int(sent['scene']) != row['scene']:
            raise ValueError('sampled material snapshot/queue mismatch')
    return dict(passed=True, scenes=len(scenes), snapshots=sampled,
                scope='Private material upload/ownership; no added drawing or general lifetime/handover acceptance.')
