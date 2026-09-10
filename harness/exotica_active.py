"""Independent owned active-margin packet and original framebuffer checks.

Raw snapshots stay local. These checks do not establish a general scene oracle,
transparent occlusion, or a useful increase in far drawing distance.
"""
import csv
import hashlib
import math
from pathlib import Path
import re
import struct
from zeus_host_materials import parse as parse_material


def parse(wire):
    if not 32 <= len(wire) < 64*1024*1024:
        raise ValueError('active packet size')
    magic, size, count, margin, page, draw, pad0, pad1 = struct.unpack_from('<8I', wire)
    if (magic != 0x31444d58 or count > 131072 or margin > 120 or page not in (0, 400)
            or draw not in (0, 1) or pad0 or pad1 or len(wire) != 32+size+264*count):
        raise ValueError('active packet header')
    material = parse_material(wire[32:32+size])
    quads, palette_rows, vertices = [], [], 0
    for index in range(count):
        offset = 32+size+264*index
        palette, = struct.unpack_from('<I', wire, offset)
        state = struct.unpack_from('<17I', wire, offset+4)
        frame, nv = state[:2]
        flags = state[9]
        if (palette >= len(material['palettes']) or frame != material['frame'] or
                not 3 <= nv <= 8 or state[11] != page or state[12] or
                state[13] or state[15] != 511 or not state[14] <= state[16] <= 399 or
                not flags & 8 or flags & ~0x2df or state[7] > 256 or state[8] > 256):
            raise ValueError('active polygon state')
        bias, = struct.unpack('<i', struct.pack('<I', state[10]))
        for n in range(nv):
            v = struct.unpack_from('<6f', wire, offset+72+n*24)
            z = max(v[2], bias) if flags & 512 else v[2]+bias
            z = z if flags & 4 else v[2]
            if (any(not math.isfinite(f) for f in v) or v[5] <= 0 or
                    not 0 <= v[2] <= 16777215 or not 0 <= z <= 16777215):
                raise ValueError('active polygon D24 contract')
        quads.append(wire[offset+4:offset+264]);palette_rows.append(palette)
        vertices += 3*(nv-2)
    return dict(material=material, material_wire=wire[32:32+size], margin=margin,
                page=page, draw=bool(draw), quads=b''.join(quads),
                palette_rows=palette_rows, vertices=vertices)


def fingerprint(data):
    value = 14695981039346656037
    for byte in data:
        value = ((value ^ byte)*1099511628211) & 0xffffffffffffffff
    return f'{value:016x}'


def framebuffer(before, after, depth_before, depth_after, width, height, page, margin, draw):
    scale = height//1024
    if (scale not in (1, 2, 3, 4) or height != 1024*scale or
            width != (512+2*margin)*scale or page not in (0, 400) or not 0 <= margin <= 120):
        raise ValueError('active framebuffer dimensions')
    if any(len(b) != width*height*4 for b in (before, after, depth_before, depth_after)):
        raise ValueError('active framebuffer snapshot size')
    if depth_before != depth_after:
        raise ValueError('active draw changed original depth')
    if not draw and before != after:
        raise ValueError('active observe changed original color')
    changed = 0
    for y in range(height):
        live = page*scale <= y < (page+400)*scale
        x, count = (margin*scale, 512*scale) if live else (0, width)
        start, end = (y*width+x)*4, (y*width+x+count)*4
        if before[start:end] != after[start:end]:
            raise ValueError('active draw changed color outside margins')
        if live:
            for left, right in ((0, margin*scale), ((512+margin)*scale, width)):
                a, b = (y*width+left)*4, (y*width+right)*4
                # Usually whole rows match; avoid a Python loop for those rows.
                if before[a:b] != after[a:b]:
                    changed += sum(before[k:k+4] != after[k:k+4] for k in range(a, b, 4))
    return dict(original_depth_unchanged=True, outside_color_unchanged=True,
                changed_margin_pixels=changed,
                color_sha256=[hashlib.sha256(b).hexdigest() for b in (before, after)])


def sealed_snapshot(cpu, context, ram, ready, internal, instances):
    if len(ram) != 0x100000 or len(ready) != 0x100000 or len(internal) != 2048 or len(instances) % 44:
        raise ValueError('sealed scene snapshot size')
    camera = struct.unpack_from('<3I', ram, 0xfeb*4)
    advanced = camera != struct.unpack_from('<3I', ready, 0xfeb*4)
    if list(camera) != context['position'] or int(cpu['camera_advanced']) != int(advanced):
        raise ValueError('sealed scene camera ownership')
    for address, key in ((0x67bf, 'view'), (0x67c0, 'alternate')):
        pointer, = struct.unpack_from('<I', ram, address*4)
        if not 0x87fe00 <= pointer <= 0x880000-9:
            raise ValueError('sealed scene matrix pointer')
        if list(struct.unpack_from('<9I', internal, (pointer-0x87fe00)*4)) != context[key]:
            raise ValueError('sealed scene matrix ownership')
    seen = set()
    for instance in struct.iter_unpack('<11I', instances):
        slot = instance[1]
        if not 0x1000 <= slot <= 0x40000-31 or 0x30000 <= slot < 0x32000 or slot in seen:
            raise ValueError('sealed instance slot ownership')
        seen.add(slot)
        if ram[(slot+17)*4:(slot+19)*4] != ready[(slot+17)*4:(slot+19)*4]:
            raise ValueError('sealed instance material binding changed')
    return dict(camera_advanced=advanced, instance_bindings_checked=len(seen))


def snapshot(directory, frame, cpu, gpu, mode):
    prefix = Path(directory)/f'exotica-active-{frame}'
    read = lambda suffix: Path(str(prefix)+suffix).read_bytes()
    packet = parse(read('-packet.bin'))
    if (packet['material_wire'] != read('-materials.bin') or packet['quads'] != read('-quads.bin') or
            packet['material']['frame'] != frame or packet['material']['scene'] != int(cpu['scene']) or
            not packet['material']['snapshot'] or packet['draw'] != (mode == 2) or
            packet['margin'] != int(gpu['margin']) or packet['page'] != int(gpu['page']) or
            fingerprint(packet['quads']) != cpu['hash']):
        raise ValueError('active snapshot ownership or geometry differs')
    instances = read('-instances.bin')
    if len(instances) != int(cpu['instances'])*44 or len(read('-ram.bin')) != 0x100000:
        raise ValueError('active instance or RAM snapshot size')
    palette_keys = [(r[0], r[1]) for r in packet['material']['palettes']]
    quad = 0
    for values in struct.iter_unpack('<11I', instances):
        first, count = values[9:11]
        if first != quad or first+count > len(packet['palette_rows']):
            raise ValueError('active instance quad ownership')
        for palette in packet['palette_rows'][first:first+count]:
            if palette_keys[palette] != (values[6], values[7]):
                raise ValueError('active instance palette ownership')
        quad += count
    if quad != int(cpu['quads']):
        raise ValueError('active instance quad total')
    vertices = packet['vertices'] if mode == 2 and packet['margin'] else 0
    if vertices != int(gpu['vertices']):
        raise ValueError('active GPU triangle fan count')
    result = framebuffer(read('-gpu-before-color.bin'), read('-gpu-after-color.bin'),
                         read('-gpu-before-depth.bin'), read('-gpu-after-depth.bin'),
                         int(gpu['width']), int(gpu['height']), packet['page'], packet['margin'], mode == 2)
    if 'sealed_frame' in cpu:
        from verify_exotica_live_scene import decode_context
        result['sealed'] = sealed_snapshot(cpu, decode_context(read('-context.bin')), read('-ram.bin'),
            read('-ready-ram.bin'), read('-end-internal.bin'), instances)
    return dict(frame=frame, quads=quad, vertices=vertices, **result)


def verify(directory, scenes, text, mode, captures):
    initial = re.findall(r'^MIDZ_HOST_ACTIVE=(\d+)$', text, re.M)
    sealed = re.findall(r'^MIDZ_HOST_ACTIVE_SEALED=(\d+)$', text, re.M)
    final = re.findall(r'^MIDZ_HOST_ACTIVE_RESULT complete=(\d+) scenes=(\d+) quads=(\d+) remaining=(\d+)$', text, re.M)
    gpu_final = re.findall(r'^MIDZ_HOST_ACTIVE_GPU_RESULT complete=(\d+) scenes=(\d+) quads=(\d+)$', text, re.M)
    writer = re.findall(r'^MIDZ_HOST_ACTIVE_WRITER submitted=(\d+) written=(\d+) failed=(\d+) rejected=(\d+) peak_bytes=(\d+) write_total_us=(\d+) write_max_us=(\d+) drain_us=(\d+) waits=(\d+) wait_us=(\d+)$', text, re.M)
    if not mode:
        if initial or final or gpu_final or writer or sealed:
            raise ValueError('disabled Exotica active margins ran')
        return None
    if mode not in (1, 2) or initial != [str(mode)] or len(final) != 1 or len(gpu_final) != 1:
        raise ValueError('active margin acknowledgment')
    if sealed not in ([], ['1']):
        raise ValueError('active sealed scene acknowledgment')
    if len(writer) != 1:
        raise ValueError('missing active margin writer completion')
    submitted, written, failed, rejected, peak, total_us, max_us, drain_us, waits, wait_us = map(int, writer[0])
    if (submitted != 4*len(captures) or written != submitted or failed or rejected or
            peak > 512*1024*1024 or max_us > total_us or waits > submitted):
        raise ValueError('incomplete active margin writer')
    def rows(name):
        path = Path(directory)/name
        if path.stat().st_size > 8*1024*1024:
            raise ValueError('active margin log budget')
        with path.open(encoding='utf-8', newline='') as stream:
            return list(csv.DictReader(stream))
    cpu, gpu, fences = (rows(f) for f in ('exotica-active-scenes.csv', 'exotica-active-gpu.csv', 'exotica-host-fences.csv'))
    if not 0 < len(scenes) <= 10002 or any(len(r) != len(scenes) for r in (cpu, gpu, fences)):
        raise ValueError('active margin scene count')
    total = sum(int(r['quads']) for r in cpu)
    if final != [('1', str(len(scenes)), str(total), '0')] or gpu_final != [('1', str(len(scenes)), str(total))]:
        raise ValueError('incomplete active margin producer/consumer')
    sampled = []
    for source, sent, received, fence in zip(scenes, cpu, gpu, fences):
        if (any(sent[k] != source[k] for k in ('scene', 'scene_frame', 'frame')) or
                any(sent[k] != received[k] for k in ('scene', 'frame', 'quads')) or
                sent['scene'] != fence['scene'] or sent['ready_frame'] != fence['ready_frame'] or
                int(sent['ready_frame'])-int(sent['frame']) not in (0, 1) or int(sent['guest_cycles']) or
                int(received['mode']) != mode or not re.fullmatch('[0-9a-f]{16}', sent['hash'])):
            raise ValueError('active margin scene/frame/cycle ownership')
        objects, candidates, submitted, instances, quads, excluded = (int(sent[k]) for k in
            ('objects', 'candidates', 'already_submitted', 'instances', 'quads', 'excluded_raster'))
        if (not 0 <= submitted <= candidates <= objects <= 4096 or
                not 0 <= instances+excluded <= candidates-submitted or not 0 <= quads <= 131072):
            raise ValueError('active margin object budget')
        if bool(sealed) != ('sealed_frame' in sent):
            raise ValueError('active sealed scene schema mismatch')
        if sealed and (sent['sealed_frame'] != fence['end_frame'] or
                int(sent['camera_advanced']) not in (0, 1) or
                int(sent['binding_checks']) != candidates-submitted or
                not 0 <= int(sent['changed_objects']) <= int(sent['binding_checks'])):
            raise ValueError('active sealed scene boundary or binding counts')
        margin, width, height, page, vertices, saved = (int(received[k]) for k in
            ('margin', 'width', 'height', 'page', 'vertices', 'snapshot'))
        scale = height//1024
        if (not 0 <= margin <= 120 or scale not in (1, 2, 3, 4) or height != 1024*scale or
                width != (512+2*margin)*scale or page not in (0, 400) or
                (vertices != 0 if mode == 1 or margin == 0 else not 3*quads <= vertices <= 18*quads) or
                saved not in (0, 1) or bool(saved) != (int(sent['frame']) in captures)):
            raise ValueError('active margin GPU dimensions/counts')
        for row in (sent, received):
            for key, value in row.items():
                if key.endswith('_us') and (not math.isfinite(float(value)) or float(value) < 0):
                    raise ValueError('active margin timing')
        if saved:
            sampled.append(snapshot(directory, int(sent['frame']), sent, received, mode))
    if sorted(s['frame'] for s in sampled) != sorted(captures):
        raise ValueError('active margin snapshot completion')
    return dict(passed=True, mode=mode, scenes=len(scenes), quads=total, snapshots=sampled, sealed_at_scene_end=bool(sealed),
                scope='Current margin geometry and private D24 preservation; far distance and full occlusion remain unproven.')
