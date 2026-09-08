"""Summarize read-only game distance gates; this is not visual acceptance.

Input is distance_capability.lua's bounded CSV. Values describe the game's
actual culler visits, not all scenery in a level or pending/unloaded objects.
"""
import argparse
import csv
import math
from pathlib import Path
import sys

from verification import sha256_file, write_json

PROFILES = {
    'crusnusa': (0xcc, 0xd6, 4999, 80000),
    'crusnwld24': (0xa1, 0xb4, 4999, 80000),
    'crusnwld': (0xa1, 0xb4, 4999, 80000),
    'offroadc': (0x1c36, 0x1c45, 63679, 47296),
    'crusnexo': (0x6888, 0x688c, 4999, 204800),
}


def summarize(path, rom):
    far_pc, table_pc, table_max, stock_far = PROFILES[rom]
    frames, objects, far_frames, table_frames = set(), set(), set(), set()
    far_tests = far_rejected = table_reads = clamped_reads = beyond_80k = 0
    extension_bins = {label: 0 for label in ('up_to_1.25x', 'up_to_2x', 'up_to_3x', 'above_3x')}
    depth_min = index_min = math.inf
    depth_max = index_max = -math.inf
    previous = 0
    with Path(path).open(newline='', encoding='utf-8') as stream:
        for row in csv.DictReader(stream):
            frame, pc, obj = int(row['frame']), int(row['pc'], 16), int(row['object'], 16)
            if frame < 1 or frame < previous or not 0x1000 <= obj < (0x40000 if rom == 'crusnexo' else 0x20000):
                raise ValueError('invalid frame ordering or object address')
            previous = frame
            frames.add(frame)
            if row['kind'] == 'far':
                depth, radius, limit = (float(row[k]) for k in ('depth_minus_radius', 'radius', 'limit'))
                if pc != far_pc or not all(map(math.isfinite, (depth, radius, limit))) or radius < 0 or limit != stock_far:
                    raise ValueError('invalid far gate or unexpected baseline limit')
                far_tests += 1
                far_frames.add(frame)
                objects.add(obj)
                depth_min, depth_max = min(depth_min, depth), max(depth_max, depth)
                # Exotica tests depth+radius, unlike the other families. Off
                # Road uses >= rather than > at its floating-point far branch.
                tested = depth + 2 * radius if rom == 'crusnexo' else depth
                rejected = tested >= limit if rom == 'offroadc' else tested > limit
                far_rejected += rejected
                if rejected:
                    label = ('up_to_1.25x' if tested <= 1.25 * limit else 'up_to_2x'
                             if tested <= 2 * limit else 'up_to_3x' if tested <= 3 * limit else 'above_3x')
                    extension_bins[label] += 1
                beyond_80k += depth > 80000
            elif row['kind'] == 'table':
                index = int(row['index'])
                if pc != table_pc or not (-4096 if rom == 'offroadc' else 0) <= index <= table_max:
                    raise ValueError('invalid reciprocal consumer/index')
                table_reads += 1
                table_frames.add(frame)
                clamped_reads += index == table_max
                index_min, index_max = min(index_min, index), max(index_max, index)
            else:
                raise ValueError('unknown distance observation kind')
    if not far_tests or not table_reads:
        raise ValueError('both distance gates must be observed')
    return dict(schema=1, rom=rom, source_sha256=sha256_file(path),
                frames=[min(frames), max(frames)], observed_frames=len(frames),
                far_frames=len(far_frames), table_frames=len(table_frames),
                stock_far=stock_far, far_tests=far_tests, far_rejected=far_rejected,
                observed_objects=len(objects), depth_minus_radius=[depth_min, depth_max],
                beyond_80000=beyond_80k, rejected_distance_bins=extension_bins,
                table_reads=table_reads, table_indices=[index_min, index_max],
                table_maximum=table_max, clamped_reads=clamped_reads,
                conclusion='observed culler limits only; no visible-distance or residency acceptance')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--rom', required=True, choices=PROFILES)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    result = summarize(args.csv, args.rom)
    write_json(args.output, result)
    print(f"{args.rom}: {result['far_rejected']}/{result['far_tests']} far rejects; "
          f"{result['clamped_reads']}/{result['table_reads']} reciprocal clamps")
    return 0


if __name__ == '__main__':
    sys.exit(main())
