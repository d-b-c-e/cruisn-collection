"""Inspect a matched V-Unit host scene and completed indexed mirror.

Reports conservative projected-quad bounds and exact saved fine pixels.
It does not infer missing source geometry or approve a visual repair.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

from vunit_original_mirror import verify as verify_mirror


PACKET = struct.Struct('<IHH16HI4II')


def projected_box(words):
    if len(words) != 16 or any(type(v) is not int or not 0 <= v <= 65535 for v in words):
        raise ValueError('invalid host quad words')
    coords = struct.unpack('<8h', struct.pack('<8H', *words[2:10]))
    return (min(coords[::2]), min(coords[1::2]),
            max(coords[::2]), max(coords[1::2]))


def intersects(a, b):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def analyze(case, samples, box):
    case = Path(case)
    report_path = case/'report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if report.get('passed') is not True:
        raise ValueError('requires a passing replay with matched host metadata')
    trial = report['vunit_original_mirror']
    run = case/'run'
    mirror = verify_mirror(trial, run)
    completion = mirror['host_completion']
    source = completion['visible']
    if (not completion['captured_preparation_matches_visible'] or not source or
            not source['complete'] or source['frame'] != trial['metadata_frame'] or
            mirror['visible_page'] != source['physical_page']):
        raise ValueError('source does not belong to completed visible page')
    raw = (run/'vunit-fade-producer.bin').read_bytes()
    if (not raw.startswith(b'VFD1') or (len(raw)-4) % PACKET.size or
            hashlib.sha256(raw).hexdigest() != mirror['fade_metadata']['sha256']):
        raise ValueError('host packet bytes differ from verified metadata')
    packets = list(PACKET.iter_unpack(raw[4:]))
    if len(packets) != mirror['fade_metadata']['captured']:
        raise ValueError('captured host packet count differs')
    if any(p[0] != source['frame'] or p[1] != source['page_control'] for p in packets):
        raise ValueError('host packet source/page differs from completed scene')
    boxes = [projected_box(p[3:19]) for p in packets]
    hits = [i for i, candidate in enumerate(boxes) if intersects(candidate, box)]
    width, height, page = (mirror[k] for k in ('width','height','visible_page'))
    prefix = f'vunit-mirror-{mirror["frame"]}-page{page}-plane'
    paths = [run/(prefix+str(n)+'.bin') for n in range(4)]
    extended = np.fromfile(paths[0], dtype='<u2').reshape(height, width)
    mask = np.fromfile(paths[1], dtype='u1').reshape(height, width)
    original = np.fromfile(paths[2], dtype='<u2').reshape(height, width)
    original_mask = np.fromfile(paths[3], dtype='u1').reshape(height, width)
    pixels = []
    for x, y in samples:
        if not 0 <= x < width or not 0 <= y < height:
            raise ValueError('sample outside mirrored fine page')
        pixels.append(dict(x=x, y=y, extended_pen=int(extended[y,x]),
                           original_pen=int(original[y,x]), extended_tag=int(mask[y,x]),
                           original_tag=int(original_mask[y,x])))
    return dict(passed=True, scope='Conservative projected host bounds and indexed fine pixels '
                'for one verified source/display pair; no polygon raster/texture or temporal acceptance.',
                source_frame=source['frame'], completed_frame=mirror['frame'], page=page,
                source_hash=source['prepared_quads_hash'], packets=len(packets),
                native_box=list(box), intersecting_packet_ordinals=hits,
                samples=pixels, evidence_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                                for p in (report_path,*paths,run/'vunit-fade-producer.bin')})


def point(text):
    try:
        values = tuple(map(int, text.split(':')))
    except ValueError as exc:
        raise argparse.ArgumentTypeError('sample must be X:Y') from exc
    if len(values) != 2:
        raise argparse.ArgumentTypeError('sample must be X:Y')
    return values


def rectangle(text):
    try:
        values = tuple(map(int, text.split(':')))
    except ValueError as exc:
        raise argparse.ArgumentTypeError('box must be X0:Y0:X1:Y1') from exc
    if len(values) != 4 or values[0] > values[2] or values[1] > values[3]:
        raise argparse.ArgumentTypeError('box must be X0:Y0:X1:Y1')
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', type=Path)
    parser.add_argument('--sample', action='append', type=point, required=True)
    parser.add_argument('--native-box', type=rectangle, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite prior diagnostic')
    result = analyze(args.case, args.sample, args.native_box)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('passed','source_frame','completed_frame','packets',
                                            'intersecting_packet_ordinals','samples')}))


if __name__ == '__main__':
    main()
