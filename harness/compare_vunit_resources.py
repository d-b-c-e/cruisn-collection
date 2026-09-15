"""Compare original V-Unit DMA and resource captures without launching a game.

Equality establishes preservation of the captured original data. It does not
certify added host geometry, resource ownership over time, or displayed pixels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

SIZES = {'videoram.bin': 2*1024*1024, 'textureram.bin': 8*1024*1024,
         'paletteram.bin': 32768*4}
MAX_QUAD_BYTES = 512*1024*1024
RECORD = struct.Struct('<IH16H')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def validate(directory, frame):
    directory = Path(directory)
    if type(frame) is not int or frame < 1:
        raise ValueError('positive capture frame required')
    path = directory/'meta.txt'
    if not 0 < path.stat().st_size <= 1024:
        raise ValueError('invalid V-Unit metadata size')
    text = path.read_text(encoding='ascii')
    match = re.fullmatch(r'frame (\d+)\npage_control (\d+)\n'
                         r'visible_page_offset 0x([0-9a-f]+)\nvisarea (\d+) (\d+)\n', text)
    if not match:
        raise ValueError('invalid V-Unit metadata fields')
    captured, page = map(int, match.group(1, 2))
    offset = int(match[3], 16)
    width, height = map(int, match.group(4, 5))
    if (captured != frame or not 0 <= page <= 65535 or
            offset != (0x40000 if page & 1 else 0) or
            not 0 <= width <= 511 or not 0 <= height <= 511):
        raise ValueError('V-Unit capture frame, page or visible bounds mismatch')
    files = {'meta.txt': {'bytes': path.stat().st_size, 'sha256': digest(path)}}
    for name, size in SIZES.items():
        path = directory/name
        if path.stat().st_size != size:
            raise ValueError(f'incomplete or unsupported V-Unit resource: {name}')
        files[name] = {'bytes': size, 'sha256': digest(path)}
    path = directory/'quads.bin'
    size = path.stat().st_size
    if not 4+RECORD.size <= size <= MAX_QUAD_BYTES or (size-4) % RECORD.size:
        raise ValueError('incomplete or oversized V-Unit DMA journal')
    first = previous = None
    count = 0
    h = hashlib.sha256()
    with path.open('rb') as stream:
        magic = stream.read(4)
        if magic != b'MVQ1':
            raise ValueError('unsupported V-Unit DMA journal')
        h.update(magic)
        for block in iter(lambda: stream.read(RECORD.size*32768), b''):
            h.update(block)
            for record in RECORD.iter_unpack(block):
                current = record[0]
                if previous is not None and current < previous:
                    raise ValueError('V-Unit DMA frame order moved backwards')
                if first is None:
                    first = current
                previous = current
                count += 1
    if count != (size-4)//RECORD.size or not first <= frame <= previous:
        raise ValueError('V-Unit DMA journal does not span the capture frame')
    files['quads.bin'] = {'bytes': size, 'sha256': h.hexdigest()}
    return dict(frame=frame, page_control=page, visible_page_offset=offset,
                visarea=[width, height], dma_records=count, first_dma_frame=first,
                last_dma_frame=previous, files=files)


def compare(reference, candidate, frame):
    a, b = validate(reference, frame), validate(candidate, frame)
    changed = [name for name in a['files'] if a['files'][name] != b['files'][name]]
    return dict(schema=1, passed=not changed, differing_files=changed,
                reference=a, candidate=b,
                original_bytes=sum(v['bytes'] for v in a['files'].values()),
                scope='Exact original DMA history and captured framebuffer, texture, palette and metadata. '
                      'Not added-scene ownership, temporal handover or displayed-pixel acceptance.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('reference', type=Path)
    ap.add_argument('candidate', type=Path)
    ap.add_argument('--frame', type=int, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args(argv)
    try:
        result = compare(args.reference, args.candidate, args.frame)
    except (OSError, ValueError, UnicodeError, struct.error) as exc:
        result = dict(schema=1, passed=False, error=str(exc))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
