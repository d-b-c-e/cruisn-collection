"""One-frame original-only indexed mirror qualification; no display policy."""
import hashlib
import json
import csv
import math
import re
import struct
import numpy as np
from pathlib import Path

KEYS = ('MIDV_GL_ORIGINAL_MIRROR', 'MIDV_GL_MIRROR_FRAME', 'MIDV_WORLD_HOST_FADE_METADATA',
        'MIDV_WORLD_HOST_DISTANCE_FADE')


def add_arguments(parser):
    parser.add_argument('--vunit-original-mirror-frame', type=int,
                        help='candidate-only World indexed mirror snapshot; physical FFB off')
    parser.add_argument('--world-host-fade-metadata', action='store_true',
                        help='transport all host depths and authored road flags; no fading yet')
    parser.add_argument('--world-host-distance-fade', action='store_true',
                        help='candidate-only20k distance envelope using qualified metadata and original mirror')


def configure(args, rom, settings, frames):
    frame = getattr(args, 'vunit_original_mirror_frame', None)
    metadata = getattr(args, 'world_host_fade_metadata', False)
    fade = getattr(args, 'world_host_distance_fade', False)
    if fade and not metadata:
        raise ValueError('distance fade requires explicit qualified metadata')
    if frame is None:
        if metadata or any(settings.get(k, '0') != '0' for k in KEYS):
            raise ValueError('original mirror requires explicit replay selection')
        return None
    if (rom not in ('crusnwld24', 'crusnwld') or not getattr(args, 'candidate', None)
            or getattr(args, 'headless', False) or getattr(args, 'native_renderer', False)
            or settings.get('MIDV_GL') != '1' or settings.get('MIDV_FFB') != '0'
            or settings.get('MIDV_GL_BATCH_VRAM', '1') != '1'
            or not 1 <= frame < frames - 1):
        raise ValueError('original mirror requires candidate World GL, FFB0, batched CPU and a frame before drain')
    host = settings.get('MIDV_WORLD_HOST_SCENERY', '0') == '2'
    if host and settings.get('MIDV_WORLD_HOST_LAYER') != '3':
        raise ValueError('original mirror requires split and tagged host ownership')
    result = dict(frame=frame, auxiliary=host)
    if metadata:
        first = int(settings.get('MIDV_WORLD_HOST_FIRST', '0'))
        last = int(settings.get('MIDV_WORLD_HOST_LAST', '0'))
        if (not host or settings.get('MIDV_WORLD_HOST_FUTURE') != '1'
                or settings.get('MIDV_WORLD_HOST_FAR_COVERAGE') != '1'
                or not 1 <= first <= frame <= last < frames - 1):
            raise ValueError('fade metadata requires bounded future/coverage draw through capture and before drain')
        settings['MIDV_WORLD_HOST_FADE_METADATA'] = '1'
        result.update(fade_metadata=True, first=first, last=last)
    elif settings.get('MIDV_WORLD_HOST_FADE_METADATA', '0') != '0':
        raise ValueError('fade metadata requires explicit replay selection')
    if fade:
        settings['MIDV_WORLD_HOST_DISTANCE_FADE'] = '1'
        result['distance_fade'] = True
    elif settings.get('MIDV_WORLD_HOST_DISTANCE_FADE', '0') != '0':
        raise ValueError('distance fade requires explicit replay selection')
    settings.update(MIDV_GL_ORIGINAL_MIRROR='1', MIDV_GL_MIRROR_FRAME=str(frame))
    return result


def verify(trial, directory):
    directory = Path(directory)
    metadata = verify_metadata(trial, directory)
    path = directory / 'vunit-mirror.json'
    if not trial:
        if path.exists() or next(directory.glob('vunit-mirror-*.bin'), None):
            raise ValueError('unrequested original mirror evidence')
        return None
    if not path.is_file() or path.stat().st_size > 4096:
        raise ValueError('missing or oversized original mirror receipt')
    row = json.loads(path.read_text(encoding='utf-8'))
    fields = {'frame', 'width', 'height', 'visible_page', 'ordinary_quads',
              'auxiliary_quads', 'cpu_blits', 'original_resets'}
    if set(row) != fields or any(type(v) is not int or v < 0 for v in row.values()):
        raise ValueError('invalid original mirror receipt')
    if (row['frame'] != trial['frame'] or row['visible_page'] not in (0, 1)
            or not 512 <= row['width'] <= 4096 or not 256 <= row['height'] <= 4096
            or not row['ordinary_quads'] or not row['cpu_blits'] or not row['original_resets']
            or bool(row['auxiliary_quads']) != trial['auxiliary']):
        raise ValueError('incomplete original mirror activity')
    digests = {}
    for page in range(2):
        for plane in range(4):
            name = f"vunit-mirror-{row['frame']}-page{page}-plane{plane}.bin"
            source = directory / name
            expected = row['width'] * row['height'] * (1 if plane & 1 else 2)
            if not source.is_file() or source.stat().st_size != expected:
                raise ValueError('missing or wrong-size original mirror plane')
            with source.open('rb') as stream:
                digests[name] = hashlib.file_digest(stream, 'sha256').hexdigest()
        if not trial['auxiliary']:
            for plane in (0, 1):
                prefix = f"vunit-mirror-{row['frame']}-page{page}-plane"
                if digests[prefix+str(plane)+'.bin'] != digests[prefix+str(plane+2)+'.bin']:
                    raise ValueError('original-only mirror differs from ordinary target')
    opacity = []
    if trial.get('distance_fade'):
        for page in range(2):
            name = f"vunit-mirror-{row['frame']}-page{page}-alpha.bin"
            path = directory/name
            if not path.is_file() or path.stat().st_size != row['width']*row['height']*4:
                raise ValueError('missing or wrong-size distance fade opacity')
            data = path.read_bytes()
            values = np.frombuffer(data, dtype='<f4')
            if not np.isfinite(values).all() or not np.all((values >= 0) & (values <= 1)):
                raise ValueError('invalid distance fade opacity')
            digests[name] = hashlib.sha256(data).hexdigest()
            opacity.append(dict(page=page, partial=int(((values > 0) & (values < 1)).sum()),
                                zero=int((values == 0).sum()), opaque=int((values == 1).sum())))
    if {p.name for p in directory.glob('vunit-mirror-*.bin')} != set(digests):
        raise ValueError('unexpected original mirror planes')
    result = dict(**row, sha256=digests, passed=True)
    if metadata:
        result['fade_metadata'] = metadata
    if opacity:
        result['opacity'] = opacity
    return result


def verify_metadata(trial, directory):
    """Qualify both FIFO boundaries, decoded depths, and each captured scene hash."""
    directory = Path(directory)
    paths = [directory/f'vunit-fade-{name}.bin' for name in ('producer', 'consumer')]
    stderr = directory/'stderr.log'
    text = stderr.read_text(encoding='utf-8', errors='replace') if stderr.exists() else ''
    receipt = re.findall(r'^MIDV_FADE_METADATA packets=(\d+) roads=(\d+) captured=(\d+)$', text, re.M)
    if not trial or not trial.get('fade_metadata'):
        if receipt or any(p.exists() for p in paths):
            raise ValueError('unrequested fade metadata')
        return None
    if len(receipt) != 1 or any(not p.is_file() or not 4 <= p.stat().st_size <= 16*1024*1024 for p in paths):
        raise ValueError('missing or oversized fade metadata')
    data, other = (p.read_bytes() for p in paths)
    if data != other or data[:4] != b'VFD1' or (len(data)-4) % 64:
        raise ValueError('fade metadata FIFO bytes differ or malformed')
    packets = list(struct.iter_unpack('<IHH16HI4II', data[4:]))
    crossings = roads = 0
    for packet in packets:
        frame, pc, pad = packet[:3]
        limit, *words, policy = packet[19:]
        if frame != trial['frame'] or pad != 3 or limit != 240000 or policy not in (0, 1):
            raise ValueError('invalid fade metadata identity or policy')
        depths = []
        for word in words:
            exponent = int.from_bytes(bytes([word >> 24]), 'little', signed=True)
            value = math.ldexp((word & 0x7fffff) | 0x800000, exponent-23)
            if word & 0x800000 or not 9 <= exponent <= 18 or not 1000 <= value < 480000:
                raise ValueError('invalid fade metadata depth')
            depths.append(value)
        if all(z >= limit for z in depths):
            raise ValueError('outside-only fade quad')
        crossings += any(z >= limit for z in depths)
        roads += policy
    with (directory/'world-host-scenes.csv').open(encoding='utf-8', newline='') as stream:
        scenes = list(csv.DictReader(stream))
    if not scenes or any(not trial['first'] <= int(s['frame']) <= trial['last'] for s in scenes):
        raise ValueError('fade scene interval differs')
    totals = tuple(map(int, receipt[0]))
    expected_totals = (sum(int(s['quads']) for s in scenes), sum(int(s['road_quads']) for s in scenes), len(packets))
    if totals != expected_totals or not totals[0]:
        raise ValueError('incomplete fade consumer coverage')
    at = 0
    for scene in (s for s in scenes if int(s['frame']) == trial['frame']):
        group = packets[at:at+int(scene['quads'])];at += len(group)
        if len(group) != int(scene['quads']) or sum(p[-1] for p in group) != int(scene['road_quads']):
            raise ValueError('fade scene road/count mismatch')
        fingerprint = 14695981039346656037
        for packet in group:
            if packet[1] != int(scene['page']):
                raise ValueError('fade page differs')
            for byte in struct.pack('<16H', *packet[3:19]):
                fingerprint = ((fingerprint ^ byte) * 1099511628211) & 0xffffffffffffffff
        if f'{fingerprint:016x}' != scene['quads_hash']:
            raise ValueError('fade original quad bytes/order differ')
    if at != len(packets):
        raise ValueError('unclaimed fade packets')
    result = dict(passed=True, total_packets=totals[0], total_roads=totals[1], captured=len(packets),
                  captured_roads=roads, captured_crossings=crossings, sha256=hashlib.sha256(data).hexdigest())
    if not packets:
        result['capture_scope'] = 'No host quads at this completed frame; aggregate coverage only'
    return result


def compare_originals(control, candidate):
    """Compare verified same-frame receipts; input/resource qualification is separate."""
    if not control.get('passed') or not candidate.get('passed'):
        raise ValueError('original mirror comparison requires verified receipts')
    for field in ('frame', 'width', 'height', 'visible_page', 'ordinary_quads', 'original_resets'):
        if control[field] != candidate[field]:
            raise ValueError('original mirror sequence differs: '+field)
    keys = [f"vunit-mirror-{control['frame']}-page{page}-plane{plane}.bin"
            for page in range(2) for plane in (2, 3)]
    if any(control['sha256'][k] != candidate['sha256'][k] for k in keys):
        raise ValueError('original mirror pixels changed between runs')
    return dict(passed=True, frame=control['frame'], original_planes_exact=keys)
