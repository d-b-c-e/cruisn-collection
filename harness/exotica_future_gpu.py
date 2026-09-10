"""Verify bounded owned future packets and private GPU receipts.

These checks establish delivery, resource/geometry ownership, and readback
integrity. Pixel correctness requires the separate insertion renderer.
"""
import csv
import hashlib
import math
from pathlib import Path
import re
import struct
import numpy as np
from exotica_active import fingerprint
from zeus_wide_packet import parse, MAX_PACKET


def framebuffer(buffers, margin, page, draw):
    sizes = {len(b) for b in buffers}
    if len(buffers) != 4 or len(sizes) != 1:
        raise ValueError('future readback sizes differ')
    size = sizes.pop()
    scales = [s for s in range(1, 5) if size == (512+2*margin)*1024*s*s*4]
    if len(scales) != 1 or page not in (0, 400):
        raise ValueError('future readback dimensions')
    scale = scales[0]; width = (512+2*margin)*scale; height = 1024*scale
    bc, bd, ac, ad = buffers
    changed = []
    for before, after, depth in ((bc, ac, False), (bd, ad, True)):
        a = np.frombuffer(before, '<f4' if depth else '<u4').reshape(height, width)
        b = np.frombuffer(after, '<f4' if depth else '<u4').reshape(height, width)
        if depth and any(not np.all(np.isfinite(v) & (v >= 0) & (v <= 1)) for v in (a, b)):
            raise ValueError('future readback nonfinite/out-of-range depth')
        if (not np.array_equal(a[:page*scale], b[:page*scale]) or
                not np.array_equal(a[(page+400)*scale:], b[(page+400)*scale:])):
            raise ValueError('future draw changed another page')
        changed.append(int(np.count_nonzero(a != b)))
    if not draw and any(changed):
        raise ValueError('future observe changed private target')
    return dict(width=width, height=height, color_differences=changed[0], depth_differences=changed[1],
                other_page_unchanged=True, sha256=[hashlib.sha256(b).hexdigest() for b in buffers])


def snapshot(directory, cpu, gpu, mode):
    directory = Path(directory); frame = int(cpu['frame'])
    path = directory/f'exotica-future-{frame}.xwd'
    if not 32 <= path.stat().st_size <= MAX_PACKET:
        raise ValueError('future snapshot packet budget')
    wire = path.read_bytes(); packet = parse(wire); material = packet['materials']
    material_size = struct.unpack_from('<I', wire, 4)[0]
    host = directory/f'exotica-host-{frame}'
    read_host = lambda suffix: Path(str(host)+suffix).read_bytes()
    quads = b''.join(wire[i+4:i+264] for i in range(32+material_size, len(wire), 264))
    if (wire[32:32+material_size] != read_host('-materials.bin') or quads != read_host('-quads.bin') or
            material['scene'] != int(cpu['scene']) or material['frame'] != frame or not material['snapshot'] or
            packet['draw'] != (mode == 2) or packet['multiplier'] != int(cpu['multiplier']) or
            packet['page'] != int(gpu['page']) or len(wire) != int(gpu['bytes']) or
            len(packet['quads']) != int(cpu['quads']) or fingerprint(quads) != cpu['hash']):
        raise ValueError('future packet ownership/ordered geometry differs')
    instances = read_host('-instances.bin'); cursor = 0
    if len(instances) % 44:
        raise ValueError('future instance descriptor size')
    for values in struct.iter_unpack('<11I', instances):
        first, count = values[9:11]
        if first != cursor or first+count > len(packet['quads']):
            raise ValueError('future instance quad bounds')
        for quad in packet['quads'][first:first+count]:
            if material['palettes'][quad['palette']][:2] != values[6:8]:
                raise ValueError('future instance palette ownership')
        cursor += count
    vertices = sum(3*(q['state'][1]-2) for q in packet['quads']) if mode == 2 else 0
    if cursor != int(cpu['quads']) or vertices != int(gpu['vertices']):
        raise ValueError('future triangle fan count differs')
    buffers = [(directory/f'exotica-future-{frame}-{suffix}.bin').read_bytes()
               for suffix in ('before-color', 'before-depth', 'after-color', 'after-depth')]
    result = framebuffer(buffers, packet['margin'], packet['page'], mode == 2)
    return dict(frame=frame, quads=cursor, vertices=vertices, packet_sha256=hashlib.sha256(wire).hexdigest(), **result)


def verify(directory, scenes, text, mode, captures):
    initial = re.findall(r'^MIDZ_HOST_FUTURE=(\d+)$', text, re.M)
    final = re.findall(r'^MIDZ_HOST_FUTURE_GPU_RESULT complete=(\d+) scenes=(\d+) quads=(\d+) snapshots=(\d+) written=(\d+) failed=(\d+) rejected=(\d+)$', text, re.M)
    if not mode:
        if initial or final:
            raise ValueError('disabled future drawing ran')
        return None
    if mode not in (1, 2) or initial != [str(mode)]:
        raise ValueError('future mode acknowledgment differs')
    total = sum(int(r['quads']) for r in scenes)
    if not scenes or final != [('1', str(len(scenes)), str(total), str(len(captures)), str(4*len(captures)), '0', '0')]:
        raise ValueError('future GPU completion/writer differs')
    def rows(name):
        path = Path(directory)/name
        if path.stat().st_size > 8*1024*1024:
            raise ValueError('future log budget')
        with path.open(encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))
    gpu, materials = rows('exotica-future-gpu.csv'), rows('exotica-host-materials.csv')
    if len(gpu) != len(scenes) or len(materials) != len(scenes):
        raise ValueError('future producer/consumer count differs')
    sampled = []
    for cpu, received, material in zip(scenes, gpu, materials):
        count = int(cpu['quads']); frame = int(cpu['frame']); vertices = int(received['vertices'])
        if (any(cpu[k] != received[k] for k in ('scene', 'frame', 'quads', 'multiplier', 'hash')) or
                any(cpu[k] != material[k] for k in ('scene', 'frame')) or
                int(received['mode']) != mode or int(received['page']) not in (0, 400) or
                int(received['bytes']) != 32+int(material['bytes'])+264*count or
                not 0 <= count <= 131072 or not re.fullmatch('[0-9a-f]{16}', received['hash']) or
                (not 3*count <= vertices <= 18*count or vertices % 3 if mode == 2 else vertices != 0) or
                int(received['snapshot']) != int(frame in captures) or
                not math.isfinite(float(received['host_us'])) or float(received['host_us']) < 0):
            raise ValueError('future ordered scene/geometry receipt differs')
        if frame in captures:
            sampled.append(snapshot(directory, cpu, received, mode))
    if [r['frame'] for r in sampled] != sorted(captures):
        raise ValueError('future snapshot frame coverage differs')
    return dict(passed=True, scenes=len(scenes), quads=total, snapshots=sampled, pixel_policy_verified=False,
                scope='Owned future delivery, ordered geometry, material bindings, private readback integrity. Separate insertion oracle and visual/handover acceptance required.')
