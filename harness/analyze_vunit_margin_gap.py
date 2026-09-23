"""Inspect a matched V-Unit host scene and completed indexed mirror.

Reports conservative projected-quad bounds and exact saved fine pixels.
It does not infer missing source geometry or approve a visual repair.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

from vunit_original_mirror import verify as verify_mirror
from vunit_display_scene import load as load_original_scene


PACKET = struct.Struct('<IHH16HI4II')


def projected_box(words):
    if len(words) != 16 or any(type(v) is not int or not 0 <= v <= 65535 for v in words):
        raise ValueError('invalid host quad words')
    coords = struct.unpack('<8h', struct.pack('<8H', *words[2:10]))
    return (min(coords[::2]), min(coords[1::2]),
            max(coords[::2]), max(coords[1::2]))


def intersects(a, b):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def native_box(fine_box, width, height, scale, margin, native_height):
    if (not 1 <= scale <= 6 or not 0 <= margin <= 256 or native_height not in (400, 401)
            or width != (512 + 2 * margin) * scale or height != native_height * scale
            or not 0 <= fine_box[0] <= fine_box[2] < width
            or not 0 <= fine_box[1] <= fine_box[3] < height):
        raise ValueError('unqualified fine/native page geometry')
    # The indexed planes are bottom-up; retain both possible coarse boundary
    # rows so a one-pixel raster convention cannot falsely exclude a polygon.
    return (fine_box[0] // scale - margin,
            (height - 1 - fine_box[3]) // scale,
            fine_box[2] // scale - margin,
            (height - fine_box[1]) // scale)


def original_evidence(original_case, reference_case, reference_report, reference_mirror, source, box):
    other = Path(original_case)
    report = json.loads((other/'report.json').read_text(encoding='utf-8'))
    run = other/'run'
    if report.get('passed') is not True or report.get('case') != reference_report.get('case'):
        raise ValueError('original-command capture does not match the passing recording')
    if (json.loads((run/'invocation.json').read_text(encoding='utf-8'))['executable_sha256'] !=
            json.loads((Path(reference_case)/'run'/'invocation.json').read_text(encoding='utf-8'))['executable_sha256']):
        raise ValueError('original-command executable differs')
    mirror = verify_mirror(report['vunit_original_mirror'], run)
    if (any(mirror[k] != reference_mirror[k] for k in ('frame','width','height','visible_page')) or
            mirror['sha256'] != reference_mirror['sha256'] or
            report['evidence']['gl_captures']['files'] != reference_report['evidence']['gl_captures']['files']):
        raise ValueError('original-command capture differs from matched completed image')
    game = reference_report['vunit_original_mirror']['metadata_game']
    with (run/f'{game}-host-scenes.csv').open(encoding='utf-8', newline='') as stream:
        scene_rows = [row for row in csv.DictReader(stream)
                      if int(row['frame']) == source['frame']]
    if (len(scene_rows) != 1 or int(scene_rows[0]['page']) != source['page_control'] or
            int(scene_rows[0]['quads']) != source['prepared_quads'] or
            scene_rows[0]['quads_hash'] != source['prepared_quads_hash']):
        raise ValueError('original-command run host source differs')
    log = run/'capture/quads.bin'
    if hashlib.sha256(log.read_bytes()).hexdigest() != report['capture']['sha256']['quads.bin']:
        raise ValueError('original-command journal differs from capture receipt')
    selected = load_original_scene(run)
    current = selected.report['current']
    if (not current['first_frame'] <= source['frame'] <= current['last_frame'] or
            current['physical_draw_page'] != reference_mirror['visible_page'] or
            current['page_control'] != source['page_control']):
        raise ValueError('original-command group does not match source/page')
    boxes = [projected_box([int(v) for v in quad]) for quad in selected.current]
    hits = [i for i, candidate in enumerate(boxes) if intersects(candidate, box)]
    nearby = [(i, candidate) for i, candidate in enumerate(boxes)
              if candidate[0] <= box[0] <= candidate[2] and
                 candidate[1] <= box[3] + 16 and candidate[3] >= box[1] - 16]
    nearby.sort(key=lambda pair: (max(box[1] - pair[1][3], pair[1][1] - box[3], 0), pair[0]))
    return dict(current_group=current, intersecting_ordinals=hits,
                nearby_projected=[dict(ordinal=i, bounds=list(bounds),
                                       flags=int(selected.current[i][0]),
                                       palette=int(selected.current[i][1]),
                                       texture=int(selected.current[i][14]))
                                  for i, bounds in nearby[:20]],
                journal_sha256=report['capture']['sha256']['quads.bin'],
                source_scene_sha256=hashlib.sha256((run/f'{game}-host-scenes.csv').read_bytes()).hexdigest(),
                scope='Matching completed pixels and same-page DMA group; conservative bounds only, not raster ownership.')


def analyze(case, samples, fine_box, original_case=None):
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
    env = json.loads((run/'invocation.json').read_text(encoding='utf-8'))['environment']
    scale, margin, native_height = (int(env[key]) for key in
        ('MIDV_GL_SCALE', 'MIDV_GL_MARGIN', 'MIDV_GL_HEIGHT'))
    width, height, page = (mirror[k] for k in ('width','height','visible_page'))
    box = native_box(fine_box, width, height, scale, margin, native_height)
    boxes = [projected_box(p[3:19]) for p in packets]
    hits = [i for i, candidate in enumerate(boxes) if intersects(candidate, box)]
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
    result = dict(passed=True, scope='Conservative projected host bounds and indexed fine pixels '
                'for one verified source/display pair; no polygon raster/texture or temporal acceptance.',
                source_frame=source['frame'], completed_frame=mirror['frame'], page=page,
                source_hash=source['prepared_quads_hash'], packets=len(packets),
                fine_box=list(fine_box), native_box=list(box),
                native_mapping=dict(scale=scale, margin=margin, height=native_height,
                                    scope='Conservative bottom-up fine-to-coarse interval'),
                intersecting_packet_ordinals=hits,
                samples=pixels, evidence_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                                for p in (report_path,run/'invocation.json',*paths,
                                                          run/'vunit-fade-producer.bin')})
    if original_case is not None:
        result['original_commands'] = original_evidence(original_case, case, report, mirror, source, box)
    return result


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
    parser.add_argument('--fine-box', type=rectangle, required=True,
                        help='indexed mirror X0:Y0:X1:Y1; native box is derived from verified scale/margin')
    parser.add_argument('--original-run', type=Path,
                        help='passing same-case completed mirror with an exact original DMA capture')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite prior diagnostic')
    result = analyze(args.case, args.sample, args.fine_box, args.original_run)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('passed','source_frame','completed_frame','packets',
                                            'intersecting_packet_ordinals','samples')}))


if __name__ == '__main__':
    main()
