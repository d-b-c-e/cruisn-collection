"""Census exact sampled USA host objects across one saved detailed trace.

Submission is not completed visibility; this locates source activation only.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct

from screen_vunit_panorama_strips import sha


def screen(source_report, traced, rom_path):
    report = json.loads(source_report.read_text(encoding='utf-8'))
    if not report.get('passed') or not report.get('sampled_object_summaries'):
        raise ValueError('no qualified sampled host objects')
    target = {int(item['object'], 16): item['packets']
              for item in report['sampled_object_summaries']}
    detailed = traced / 'report.json'
    run_report = json.loads(detailed.read_text(encoding='utf-8'))
    if not run_report.get('passed') or sha(detailed) != report['sha256']['detailed_report']:
        raise ValueError('detailed replay differs from sampled source')
    path = traced / 'run/usa-host-quads.csv'
    rom = rom_path.read_bytes()
    if len(rom) != 0x1000000:
        raise ValueError('incomplete USA program ROM snapshot')
    digest = hashlib.sha256()
    counts = defaultdict(int)
    depths = {}
    models = defaultdict(set)
    with path.open('rb') as stream:
        header = stream.readline()
        digest.update(header)
        if header.strip().split(b',')[:4] != [b'frame', b'time', b'page', b'object']:
            raise ValueError('unexpected USA detailed trace schema')
        for line in stream:
            digest.update(line)
            fields = line.split(b',', 6)
            object_id = int(fields[3])
            if object_id in target:
                key = (object_id, int(fields[0]), int(fields[2]))
                counts[key] += 1
                depth = int(fields[5])
                models[key].add(int(fields[4]))
                low, high = depths.get(key, (depth, depth))
                depths[key] = (min(low, depth), max(high, depth))
    if digest.hexdigest() != report['traced_host']['sha256']['quads']:
        raise ValueError('detailed geometry source hash differs')
    selected = report['selected_host']
    for object_id, expected in target.items():
        if counts[(object_id, selected['frame'], selected['page_control'])] != expected:
            raise ValueError('source-scene object count differs from sampled source')
    objects = []
    def model_radius(address):
        if not 0xc00000 <= address < 0x1000000:
            raise ValueError('host model address outside ROM snapshot')
        return struct.unpack_from('<I', rom, 4 * (address - 0xc00000))[0]

    for object_id in sorted(target):
        scenes = [dict(frame=frame, page_control=page, packets=n,
                       source_depth_range=list(depths[(obj, frame, page)]),
                       model_radii=[dict(model=hex(model), radius=model_radius(model))
                                    for model in sorted(models[(obj, frame, page)])])
                  for (obj, frame, page), n in sorted(counts.items()) if obj == object_id]
        objects.append(dict(object=hex(object_id), first_scene=scenes[0],
                            last_scene=scenes[-1], scenes=len(scenes),
                            sampled_scene_packets=target[object_id], timeline=scenes))
    return dict(schema=2, passed=True,
                scope='Host submission of three screenshot-selected objects; '
                      'not completed visibility, occlusion, LOD or whole bridge.',
                completed_sample_frame=report['completed_frame'],
                selected_source_scene=selected, objects=objects,
                sha256={'sampled_source_report': sha(source_report),
                        'detailed_replay_report': sha(detailed),
                        'detailed_host_quads': digest.hexdigest(),
                        'program_rom': sha(rom_path)})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sampled-source', type=Path, required=True)
    ap.add_argument('--traced', type=Path, required=True)
    ap.add_argument('--program-rom', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite USA activation screen')
    result = screen(args.sampled_source, args.traced, args.program_rom)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', [(x['object'], x['first_scene']['frame'], x['last_scene']['frame'])
                   for x in result['objects']])


if __name__ == '__main__':
    main()
