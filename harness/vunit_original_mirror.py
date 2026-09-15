"""One-frame original-only indexed mirror qualification; no display policy."""
import hashlib
import json
from pathlib import Path

KEYS = ('MIDV_GL_ORIGINAL_MIRROR', 'MIDV_GL_MIRROR_FRAME')


def add_arguments(parser):
    parser.add_argument('--vunit-original-mirror-frame', type=int,
                        help='candidate-only World indexed mirror snapshot; physical FFB off')


def configure(args, rom, settings, frames):
    frame = getattr(args, 'vunit_original_mirror_frame', None)
    if frame is None:
        if any(settings.get(k, '0') != '0' for k in KEYS):
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
    settings.update(MIDV_GL_ORIGINAL_MIRROR='1', MIDV_GL_MIRROR_FRAME=str(frame))
    return dict(frame=frame, auxiliary=host)


def verify(trial, directory):
    directory = Path(directory)
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
    if {p.name for p in directory.glob('vunit-mirror-*.bin')} != set(digests):
        raise ValueError('unexpected original mirror planes')
    return dict(**row, sha256=digests, passed=True)


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
