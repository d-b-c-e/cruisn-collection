"""Probe saved World active objects, gated by exact original-DMA reconstruction.

Projected-box hits are only hypotheses. A zero exact-match baseline is a raw
diagnostic failure, not evidence that any candidate would fill the margin.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import struct

from analyze_vunit_margin_gap import PACKET, intersects, projected_box
from scenery_c31 import F
from screen_world_active_margin import HEADS, analyze as census
from vunit_display_scene import load as original_scene
from world_host_scenery import (camera_center, fast_quads, model_counts, project,
                                reciprocal_table, rotation_matrix)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(run, rom_path, revision, points, source_tap_run=None, boxes=None):
    boxes = boxes or {}
    base = census(run, rom_path, revision)
    frame = base['source_frame']
    capture = run / 'run/capture'
    ram_path = capture / f'ram_{frame:06d}.bin'
    fast_path = capture / f'ram3_{frame:06d}.bin'
    source_kind = 'end-of-frame RAM dump'
    if source_tap_run is not None:
        source_report = json.loads((source_tap_run / 'report.json').read_text(encoding='utf-8'))
        original_report = json.loads((run / 'report.json').read_text(encoding='utf-8'))
        if (source_report.get('passed') is not True or
                source_report['case'] != original_report['case'] or
                source_report['emulator_source']['executable_sha256'] !=
                original_report['emulator_source']['executable_sha256'] or
                source_report['evidence']['gl_captures']['files'] !=
                original_report['evidence']['gl_captures']['files'] or
                source_report['vunit_original_mirror']['result']['sha256'] !=
                original_report['vunit_original_mirror']['result']['sha256']):
            raise ValueError('source tap replay differs from matched original evidence')
        source = source_report['vunit_original_mirror']['result']['host_completion']['visible']
        if source['frame'] != frame:
            raise ValueError('source tap captured a different visible scene')
        stem = f'world-source-{frame}'
        tap = source_tap_run / 'run'
        with (tap / f'{stem}-receipt.csv').open(newline='', encoding='utf-8') as stream:
            receipt = list(csv.DictReader(stream))
        if receipt != [{'frame': str(frame), 'pc': '6a',
                        'scene_address': '61ee' if revision == 24 else '658f',
                        'rom': 'crusnwld24' if revision == 24 else 'crusnwld'}]:
            raise ValueError('source tap did not match requested scene PC/frame/revision')
        ram_path, fast_path = tap / f'{stem}-ram.bin', tap / f'{stem}-fast.bin'
        if ram_path.stat().st_size != 0x80000 or fast_path.stat().st_size != 0x2000:
            raise ValueError('source-time RAM captures are incomplete')
        source_kind = 'scene-boundary Lua read tap'
    ram, fast, rom = ram_path.read_bytes(), fast_path.read_bytes(), rom_path.read_bytes()

    def read(p):
        if 0 <= p < 0x20000:
            return struct.unpack_from('<I', ram, p*4)[0]
        if 0x809800 <= p < 0x80a000:
            return struct.unpack_from('<I', fast, (p-0x809800)*4)[0]
        if 0xc00000 <= p < 0x1000000:
            return struct.unpack_from('<I', rom, (p-0xc00000)*4)[0]
        raise ValueError(f'unmapped World operand {p:x}')

    camera = [read(read(0x41)+i) for i in range(3)]
    view = [read(read(0x43)+i) for i in range(9)]
    origin = read(0x47)+2
    table = read(0x4d)
    # Near-plane vertices in the saved New York 3596 scene reach index -95.
    # Read the surrounding original C31 table words rather than treating a
    # narrower diagnostic capture window as a projection failure.
    reciprocal = reciprocal_table({i: read(table+i) for i in range(-128,5000)}, 240000)
    original = original_scene(run / 'run').current
    original_keys = {tuple(map(int, quad)) for quad in original}
    packet_path = run / 'run/vunit-fade-producer.bin'
    packet_bytes = packet_path.read_bytes()
    receipt = json.loads((run / 'report.json').read_text(encoding='utf-8'))[
        'vunit_original_mirror']['result']['fade_metadata']
    if (not packet_bytes.startswith(b'VFD1') or (len(packet_bytes)-4) % PACKET.size or
            sha(packet_path) != receipt['sha256']):
        raise ValueError('host packet stream differs from source receipt')
    packets = list(PACKET.iter_unpack(packet_bytes[4:]))
    if len(packets) != receipt['captured'] or any(packet[0] != frame for packet in packets):
        raise ValueError('host packets do not match the selected source frame')
    host_keys = {tuple(packet[3:19]) for packet in packets}
    totals = Counter()
    errors = []
    hits = {label: [] for label in (*points, *boxes)}
    seen = set()
    for global_addr in HEADS[revision]:
        p = read(read(global_addr))
        while p:
            if p in seen or not 0x1000 <= p <= 0x20000-32:
                raise ValueError('active list changed after census')
            seen.add(p)
            address = p
            obj = [read(p+i) for i in range(32)]
            p = obj[0]
            if obj[14] & 0x3861 != 0x1000:
                continue
            totals['class_1000_objects'] += 1
            try:
                center = camera_center(obj, camera, view)
                depth = center[2].fix()
                if not 1000 <= depth < 240000:
                    totals['outside_depth'] += 1
                    continue
                model = obj[13]
                if obj[14] & 0x200 and depth > 10000:
                    model = read(model - (4 if obj[14] & 4 and depth > 15000 else 3))
                pairs, singles, polygons = model_counts(read(model+2))
                material = read(model+1)
                radius = read(model)
                if depth <= 0 or depth >= 80000 or radius > 0x7fffffff:
                    stock_horizontal_rejected = False
                else:
                    reciprocal_at_center = F.load(read(table+min(4999, depth >> 4)))
                    extent = F.integer(radius)*reciprocal_at_center
                    projected_x = center[0]*reciprocal_at_center
                    left = projected_x+extent+F.load(read(origin))
                    right = (left-extent-extent)-F.integer(512)
                    stock_horizontal_rejected = ((left.exponent != -128 and left.mantissa < 0)
                                                 or (right.exponent != -128 and right.mantissa >= 0))
                record = {
                    'model_words': [read(model+i) for i in range(3+2*(pairs+singles)+2*polygons)],
                    'material_words': [read(material+i) for i in range(3*polygons)],
                    'object_words': obj,
                    'matrix': [v.store() for v in rotation_matrix(obj, view)],
                    'camera_space': [v.store() for v in center] + [read(origin), read(origin+1)],
                    'fast': True, 'end_pc': 0x242,
                }
                # Reference fast_quads returns the 15 authored words; the DMA
                # journal's reserved 16th word is zero in this comparison.
                quads = [quad+[0] for quad in fast_quads(record, project(record, reciprocal))]
                totals['projected_objects'] += 1
                totals['projected_quads'] += len(quads)
                totals['exact_original_dma_quads'] += sum(tuple(q) in original_keys for q in quads)
                totals['exact_host_packet_quads'] += sum(tuple(q) in host_keys for q in quads)
                for quad in quads:
                    box = projected_box(quad)
                    for label, (x,y) in points.items():
                        if box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                            hits[label].append({'object': hex(address), 'model': hex(model),
                                                'depth': depth, 'radius': radius,
                                                'stock_horizontal_rejected': stock_horizontal_rejected,
                                                'bounds': list(box),
                                                'quad_words': quad,
                                                'exact_original_dma': tuple(quad) in original_keys,
                                                'exact_host_packet': tuple(quad) in host_keys})
                    for label, roi in boxes.items():
                        if intersects(box, roi):
                            hits[label].append({'object': hex(address), 'model': hex(model),
                                                'depth': depth, 'radius': radius,
                                                'stock_horizontal_rejected': stock_horizontal_rejected,
                                                'bounds': list(box),
                                                'quad_words': quad,
                                                'exact_original_dma': tuple(quad) in original_keys,
                                                'exact_host_packet': tuple(quad) in host_keys})
            except (ValueError, IndexError, struct.error) as exc:
                totals['projection_errors'] += 1
                if len(errors) < 8:
                    errors.append({'object': hex(address), 'error': str(exc)})
    threshold = max(32, len(original)//20)
    baseline = totals['exact_original_dma_quads'] >= threshold and not totals['projection_errors']
    return {
        'passed': baseline,
        'baseline_qualified': baseline,
        'reason': None if baseline else 'Insufficient exact original-DMA reconstruction; projected-box hits are unqualified.',
        'baseline_minimum_exact_quads': threshold,
        'source_kind': source_kind,
        'revision': revision,
        'source_frame': frame,
        'original_dma_quads': len(original),
        'host_packets': len(packets),
        'counts': dict(totals),
        'errors': errors,
        'probes': ([{'label': label, 'native_point': list(point),
                     'projected_box_hits': hits[label]} for label, point in points.items()] +
                   [{'label': label, 'native_box': list(box),
                     'projected_box_hits': hits[label]} for label, box in boxes.items()]),
        'source_sha256': {'program_ram': sha(ram_path), 'c31_ram': sha(fast_path),
                          'rom': sha(rom_path), 'original_dma': sha(run / 'run/capture/quads.bin'),
                          'host_packets': sha(packet_path)},
        'scope': 'Offline active-object projection hypothesis. Exact original DMA baseline is required '
                 'before inferring gap coverage, material quality, or a renderer policy.',
    }


def point(value):
    parts = value.split(':')
    if len(parts) != 3:
        raise argparse.ArgumentTypeError('probe must be LABEL:X:Y')
    try:
        return parts[0], (int(parts[1]), int(parts[2]))
    except ValueError as exc:
        raise argparse.ArgumentTypeError('probe coordinates must be integers') from exc


def rectangle(value):
    parts = value.split(':')
    if len(parts) != 5:
        raise argparse.ArgumentTypeError('probe box must be LABEL:X0:Y0:X1:Y1')
    try:
        box = tuple(map(int, parts[1:]))
    except ValueError as exc:
        raise argparse.ArgumentTypeError('probe box coordinates must be integers') from exc
    if box[0] > box[2] or box[1] > box[3]:
        raise argparse.ArgumentTypeError('probe box coordinates are reversed')
    return parts[0], box


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--revision', type=int, choices=(24,25), required=True)
    parser.add_argument('--source-tap-run', type=Path,
                        help='passing same-case read-tap replay; use source-time RAM instead of end-of-frame RAM')
    parser.add_argument('--probe', action='append', type=point, default=[])
    parser.add_argument('--probe-box', action='append', type=rectangle, default=[])
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if not args.probe and not args.probe_box:
        parser.error('at least one --probe or --probe-box is required')
    if args.report.exists():
        raise ValueError('refusing to overwrite projection probe')
    result = probe(args.run, args.rom, args.revision, dict(args.probe),
                   args.source_tap_run, dict(args.probe_box))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS' if result['passed'] else 'FAIL', result['counts'])
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
