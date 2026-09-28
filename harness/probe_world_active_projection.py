"""Probe saved World active objects, gated by exact original-DMA reconstruction.

Projected-box hits are only hypotheses. A zero exact-match baseline is a raw
diagnostic failure, not evidence that any candidate would fill the margin.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from analyze_vunit_margin_gap import projected_box
from scenery_c31 import F
from screen_world_active_margin import HEADS, analyze as census
from vunit_display_scene import load as original_scene
from world_host_scenery import (camera_center, fast_quads, model_counts, project,
                                reciprocal_table, rotation_matrix)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(run, rom_path, revision, points):
    base = census(run, rom_path, revision)
    frame = base['source_frame']
    capture = run / 'run/capture'
    ram_path = capture / f'ram_{frame:06d}.bin'
    fast_path = capture / f'ram3_{frame:06d}.bin'
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
    reciprocal = reciprocal_table({i: read(table+i) for i in range(-80,5000)}, 240000)
    original = original_scene(run / 'run').current
    original_keys = {tuple(map(int, quad)) for quad in original}
    totals = Counter()
    errors = []
    hits = {label: [] for label in points}
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
                for label, (x,y) in points.items():
                    for quad in quads:
                        box = projected_box(quad)
                        if box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                            hits[label].append({'object': hex(address), 'model': hex(model),
                                                'depth': depth, 'bounds': list(box),
                                                'exact_original_dma': tuple(quad) in original_keys})
            except (ValueError, IndexError, struct.error) as exc:
                totals['projection_errors'] += 1
                if len(errors) < 8:
                    errors.append({'object': hex(address), 'error': str(exc)})
    baseline = totals['exact_original_dma_quads'] > 0 and not totals['projection_errors']
    return {
        'passed': baseline,
        'baseline_qualified': baseline,
        'reason': None if baseline else 'No exact original-DMA reconstruction; projected-box hits are unqualified.',
        'source_frame': frame,
        'original_dma_quads': len(original),
        'counts': dict(totals),
        'errors': errors,
        'probes': [{'label': label, 'native_point': list(point),
                    'unqualified_projected_box_hits': hits[label]} for label, point in points.items()],
        'source_sha256': {'program_ram': sha(ram_path), 'c31_ram': sha(fast_path),
                          'rom': sha(rom_path), 'original_dma': sha(run / 'run/capture/quads.bin')},
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--revision', type=int, choices=(24,25), required=True)
    parser.add_argument('--probe', action='append', type=point, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite projection probe')
    result = probe(args.run, args.rom, args.revision, dict(args.probe))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS' if result['passed'] else 'FAIL', result['counts'])
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
